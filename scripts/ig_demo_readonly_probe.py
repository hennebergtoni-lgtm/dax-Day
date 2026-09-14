"""Redacted IG Demo read-only host probe for the DAX SHADOW lane.

This probe accepts a local credentials file outside the repository, performs only
IG Demo authentication and GET reads, normalizes closed M5 candles through the
canonical IG adapter, and emits credential-free evidence. It has no dealing,
order, cancel or modify capability.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from math import isfinite
from pathlib import Path
import re
from typing import Mapping

from daxlab.adapters.ig_market_data import (
    DEFAULT_MAX_AGE, TIMESTAMP_CONTRACT, IgClosedM5CandleSource, IgClosedM5Feed,
    closed_m5_price_rows, ig_m5_interval,
)
from daxlab.adapters.ig_rest_readonly import IgDemoCredentials, IgDemoReadOnlyClient
from daxlab.domain.market import InstrumentId


SCHEMA = "DAXLAB_IG_DEMO_READONLY_PROBE_V1"
DEFAULT_EPIC = "IX.D.DAX.IFMM.IP"
DEFAULT_INSTRUMENT_ID = "DAX_CFD_IG_DE40_CASH_1EUR"
FORBIDDEN_OUTPUT_KEYS = {
    "api_key",
    "apikey",
    "cst",
    "email",
    "identifier",
    "login",
    "password",
    "secret",
    "security_token",
    "token",
    "authorization", "account_id", "account_number", "database_url", "private_key",
}
_REQUIRED_CREDENTIAL_KEYS = {"IG_USERNAME", "IG_PASSWORD", "IG_API_KEY"}


def _credentials_from_file(path: Path) -> IgDemoCredentials:
    if not path.is_file():
        raise RuntimeError("credentials file not found")
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise RuntimeError("credentials file contains malformed line")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key in values:
            raise RuntimeError("duplicate credentials key")
        values[key] = value
    missing = sorted(_REQUIRED_CREDENTIAL_KEYS - values.keys())
    if missing:
        raise RuntimeError(f"credentials file missing required keys: {', '.join(missing)}")
    unexpected = sorted(values.keys() - _REQUIRED_CREDENTIAL_KEYS)
    if unexpected:
        raise RuntimeError("credentials file contains unexpected keys")
    return IgDemoCredentials(
        identifier=values["IG_USERNAME"],
        password=values["IG_PASSWORD"],
        api_key=values["IG_API_KEY"],
    )


def _list_field(payload: Mapping[str, object], key: str) -> list[object]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise RuntimeError(f"IG payload requires list field {key}")
    return value


def _mapping_field(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise RuntimeError(f"IG payload requires object field {key}")
    return value


def _inventory_count(payload: Mapping[str, object], key: str) -> int:
    entries = _list_field(payload, key)
    if any(not isinstance(entry, Mapping) for entry in entries):
        raise RuntimeError("IG inventory entry must be an object")
    return len(entries)


def _number_or_none(value: object) -> float | None:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        result = float(value)
    except OverflowError:
        return None
    return result if isfinite(result) else None


def _enum_or_none(value: object, allowed: set[str]) -> str | None:
    return value if isinstance(value, str) and value in allowed else None


def _bool_or_none(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _decimal_wire_or_none(value: object) -> float | None:
    if isinstance(value, str):
        if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value):
            return None
        value = float(value)
    return _number_or_none(value)


def _rule_or_none(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    return {"value": _number_or_none(value.get("value")),
            "unit": _enum_or_none(value.get("unit"), {"POINTS", "PERCENTAGE"})}


def _utc_wire_time_or_none(value: object) -> str | None:
    # A time-of-day lacks the source date. Preserve that limitation, never
    # construct a broker date from the local clock or fall back to local updateTime.
    if not isinstance(value, str):
        return None
    if re.fullmatch(r"[0-2][0-9]:[0-5][0-9]:[0-5][0-9]", value):
        try:
            datetime.strptime(value, "%H:%M:%S")
        except ValueError:
            return None
        return value
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|\+00:00)?", value):
        return None
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value


def _safe_accounts(payload: Mapping[str, object]) -> list[dict[str, object]]:
    safe: list[dict[str, object]] = []
    for raw in _list_field(payload, "accounts"):
        if not isinstance(raw, Mapping):
            raise RuntimeError("IG account entry must be an object")
        balance = raw.get("balance")
        if not isinstance(balance, Mapping):
            balance = {}
        safe.append(
            {
                "account_type": _enum_or_none(raw.get("accountType"), {"CFD", "SPREADBET", "STOCKBROKING"}),
                "currency": _enum_or_none(raw.get("currency"), {"EUR", "GBP", "USD", "CHF", "JPY", "AUD", "CAD", "NZD", "SGD", "HKD", "SEK", "NOK", "DKK", "ZAR"}),
                "preferred": _bool_or_none(raw.get("preferred")),
                "balance": _number_or_none(balance.get("balance")),
                "available": _number_or_none(balance.get("available")),
                "deposit": _number_or_none(balance.get("deposit")),
                "profit_loss": _number_or_none(balance.get("profitLoss")),
            }
        )
    return safe


def _safe_market(payload: Mapping[str, object], *, expected_epic: str) -> dict[str, object]:
    instrument = _mapping_field(payload, "instrument")
    dealing_rules = _mapping_field(payload, "dealingRules")
    snapshot = _mapping_field(payload, "snapshot")
    epic = instrument.get("epic")
    if epic != expected_epic:
        raise RuntimeError("IG market detail epic mismatch")
    return {
        "epic": epic,
        "name": _enum_or_none(instrument.get("name"), {"Germany 40", "Deutschland 40", "DAX 40"}),
        "type": _enum_or_none(instrument.get("type"), {"INDICES", "CFD"}),
        "expiry": _enum_or_none(instrument.get("expiry"), {"DFB", "-"}),
        "lot_size": _number_or_none(instrument.get("lotSize")),
        "value_of_one_pip": _decimal_wire_or_none(instrument.get("valueOfOnePip")),
        "one_pip_means": _enum_or_none(instrument.get("onePipMeans"), {"1 Index Point", "1 index point", "1 point"}),
        "margin_factor": _number_or_none(instrument.get("marginFactor")),
        "margin_factor_unit": _enum_or_none(instrument.get("marginFactorUnit"), {"PERCENTAGE", "POINTS"}),
        "force_open_allowed": _bool_or_none(instrument.get("forceOpenAllowed")),
        "stops_limits_allowed": _bool_or_none(instrument.get("stopsLimitsAllowed")),
        "controlled_risk_allowed": _bool_or_none(instrument.get("controlledRiskAllowed")),
        "min_deal_size": _rule_or_none(dealing_rules.get("minDealSize")),
        "market_order_preference": _enum_or_none(dealing_rules.get("marketOrderPreference"), {"AVAILABLE", "NOT_AVAILABLE"}),
        "trailing_stops_preference": _enum_or_none(dealing_rules.get("trailingStopsPreference"), {"AVAILABLE", "NOT_AVAILABLE"}),
        "market_status": _enum_or_none(snapshot.get("marketStatus"), {"TRADEABLE", "CLOSED", "OFFLINE", "EDIT", "AUCTION", "AUCTION_NO_EDIT", "SUSPENDED"}),
        "bid": _number_or_none(snapshot.get("bid")),
        "offer": _number_or_none(snapshot.get("offer")),
        "update_time_utc": _utc_wire_time_or_none(snapshot.get("updateTimeUTC")),
        "quote_freshness_state": "UNKNOWN",
        "quote_freshness_threshold": "UNVERIFIED_THRESHOLD",
        "quote_time_semantics": "IG_UPDATE_TIME_UTC_MAY_LACK_SOURCE_DATE",
    }


def _closed_candles(
    prices_payload: Mapping[str, object],
    *,
    epic: str,
    instrument_id: str,
    observed_at: datetime,
    closed_as_of: datetime | None = None,
) -> list[dict[str, object]]:
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("IG observed_at must be timezone-aware")
    if closed_as_of is not None and closed_as_of > observed_at:
        raise ValueError("IG price request observation clock moved backwards")
    prices = _list_field(prices_payload, "prices")
    closed_prices = closed_m5_price_rows(prices, observed_at=closed_as_of or observed_at)
    feed = IgClosedM5Feed(epic=epic, observed_at=observed_at, prices=tuple(closed_prices))
    source = IgClosedM5CandleSource(
        feed_provider=lambda: feed,
        epic=epic,
        instrument_id=InstrumentId(instrument_id),
    )
    candles: list[dict[str, object]] = []
    while True:
        candle = source.next_candle()
        if candle is None:
            break
        candles.append(
            {
                "event_time": candle.event_time.isoformat(),
                "close_time": candle.close_time.isoformat(),
                "snapshot_time_utc": candle.close_time.isoformat(),
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
                "source": candle.source,
            }
        )
    return candles


def _assert_credential_free(payload: object) -> None:
    forbidden = {re.sub(r"[^a-z0-9]", "", k.casefold()) for k in FORBIDDEN_OUTPUT_KEYS}
    def walk(value: object) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if re.sub(r"[^a-z0-9]", "", str(key).casefold()) in forbidden:
                    raise RuntimeError("forbidden evidence key")
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            lowered = value.casefold()
            if ("x-security-token" in lowered or "x-ig-api-key" in lowered
                    or "-----begin private key-----" in lowered
                    or re.search(r"\bbearer\s+|(?:postgres(?:ql)?|mysql)://|\b(?:api[_-]?)?token\s*[:=]", lowered)):
                raise RuntimeError("forbidden credential marker in evidence")

    walk(payload)


def _fingerprint(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def collect_probe_with_candles(
    *,
    credentials_file: Path,
    epic: str,
    instrument_id: str,
    bars: int,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """One existing live read, returning the SAME validated bars for SHADOW callers."""
    credentials = _credentials_from_file(credentials_file)
    client = IgDemoReadOnlyClient(credentials=credentials)
    collection_started_at = datetime.now(timezone.utc)
    try:
        client.login()
        accounts = client.accounts()
        positions = client.positions()
        working_orders = client.working_orders()
        market = client.market(epic)
        market_observed_at = datetime.now(timezone.utc)
        price_request_started_at = datetime.now(timezone.utc)
        prices = client.m5_prices(epic, max_bars=bars)
        observed_at = datetime.now(timezone.utc)
    finally:
        client.logout()

    candles = _closed_candles(
        prices,
        epic=epic,
        instrument_id=instrument_id,
        observed_at=observed_at,
        closed_as_of=price_request_started_at,
    )
    evidence: dict[str, object] = {
        "schema": SCHEMA,
        "observed_at_utc": observed_at.isoformat(),
        "collection_started_at_utc": collection_started_at.isoformat(),
        "market_response_observed_at_utc": market_observed_at.isoformat(),
        "price_request_started_at_utc": price_request_started_at.isoformat(),
        "observation_time_source": "LOCAL_RESPONSE_OBSERVATION_CLOCK_NOT_BROKER_CLOCK",
        "environment": "IG_DEMO",
        "evidence_state": "IG_DEMO_READONLY_BROKER_EVIDENCE",
        "execution_capability": client.execution_capability,
        "order_execution_enabled": client.order_execution_enabled,
        "accounts": _safe_accounts(accounts),
        "open_positions_count": _inventory_count(positions, "positions"),
        "working_orders_count": _inventory_count(working_orders, "workingOrders"),
        "market": _safe_market(market, expected_epic=epic),
        "closed_m5_count": len(candles),
        "raw_m5_count": len(_list_field(prices, "prices")),
        "not_closed_m5_count": len(_list_field(prices, "prices")) - len(candles),
        "latest_raw_m5_time_utc": ig_m5_interval(_list_field(prices, "prices")[-1])[1].isoformat(),
        "latest_closed_m5": None if not candles else candles[-1],
        "m5_timestamp_contract": TIMESTAMP_CONTRACT,
        "m5_freshness_state": "FRESH",
        "m5_freshness_max_age_seconds": DEFAULT_MAX_AGE.total_seconds(),
        "latest_closed_m5_age_seconds": (observed_at - datetime.fromisoformat(candles[-1]["close_time"])).total_seconds(),
        "inventory_is_atomic": False,
        "inventory_history_complete": False,
        "inventory_freshness_state": "UNKNOWN",
        "inventory_freshness_threshold": "UNVERIFIED_THRESHOLD",
        "reconciliation_state": "UNKNOWN",
        "protection_state": "UNKNOWN",
    }
    _assert_credential_free(evidence)
    evidence["fingerprint"] = _fingerprint(evidence)
    return evidence, candles


def collect_probe(
    *, credentials_file: Path, epic: str, instrument_id: str, bars: int,
) -> dict[str, object]:
    evidence, _ = collect_probe_with_candles(
        credentials_file=credentials_file, epic=epic, instrument_id=instrument_id, bars=bars,
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file", required=True, type=Path)
    parser.add_argument("--epic", default=DEFAULT_EPIC)
    parser.add_argument("--instrument-id", default=DEFAULT_INSTRUMENT_ID)
    parser.add_argument("--bars", type=int, default=40)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 2 <= args.bars <= 1000:
        parser.error("--bars must be between 2 and 1000")

    try:
        evidence = collect_probe(
            credentials_file=args.credentials_file,
            epic=args.epic,
            instrument_id=args.instrument_id,
            bars=args.bars,
        )
    except (RuntimeError, ValueError, OSError) as exc:
        # Print only closed local error codes, never provider text or traceback chains.
        reasons = {
            "IG candle source requires fresh M5 data": "STALE_M5_HISTORY",
            "IG M5 history response remains paginated": "INCOMPLETE_M5_PAGINATION",
            "IG price request observation clock moved backwards": "LOCAL_CLOCK_REVERSED",
        }
        print(json.dumps({"schema": SCHEMA, "environment": "IG_DEMO",
                          "evidence_state": "BLOCKED", "error_code": reasons.get(str(exc), "IG_PROBE_FAILED"),
                          "execution_capability": "NONE", "order_execution_enabled": False}))
        return 2
    rendered = json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"WROTE {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
