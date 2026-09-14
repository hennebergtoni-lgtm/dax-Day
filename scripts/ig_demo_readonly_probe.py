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
from pathlib import Path
from typing import Any, Mapping

from daxlab.adapters.ig_market_data import IgClosedM5CandleSource, IgClosedM5Feed
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
}
_REQUIRED_CREDENTIAL_KEYS = {"IG_USERNAME", "IG_PASSWORD", "IG_API_KEY"}


def _credentials_from_file(path: Path) -> IgDemoCredentials:
    if not path.is_file():
        raise RuntimeError(f"credentials file not found: {path}")
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
            raise RuntimeError(f"duplicate credentials key: {key}")
        values[key] = value
    missing = sorted(_REQUIRED_CREDENTIAL_KEYS - values.keys())
    if missing:
        raise RuntimeError(f"credentials file missing required keys: {', '.join(missing)}")
    unexpected = sorted(values.keys() - _REQUIRED_CREDENTIAL_KEYS)
    if unexpected:
        raise RuntimeError(f"credentials file contains unexpected keys: {', '.join(unexpected)}")
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


def _number_or_none(value: object) -> float | None:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


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
                "account_type": raw.get("accountType"),
                "currency": raw.get("currency"),
                "preferred": raw.get("preferred"),
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
        "name": instrument.get("name"),
        "type": instrument.get("type"),
        "expiry": instrument.get("expiry"),
        "lot_size": _number_or_none(instrument.get("lotSize")),
        "value_of_one_pip": instrument.get("valueOfOnePip"),
        "one_pip_means": instrument.get("onePipMeans"),
        "margin_factor": _number_or_none(instrument.get("marginFactor")),
        "margin_factor_unit": instrument.get("marginFactorUnit"),
        "force_open_allowed": instrument.get("forceOpenAllowed"),
        "stops_limits_allowed": instrument.get("stopsLimitsAllowed"),
        "controlled_risk_allowed": instrument.get("controlledRiskAllowed"),
        "min_deal_size": dealing_rules.get("minDealSize"),
        "market_order_preference": dealing_rules.get("marketOrderPreference"),
        "trailing_stops_preference": dealing_rules.get("trailingStopsPreference"),
        "market_status": snapshot.get("marketStatus"),
        "bid": _number_or_none(snapshot.get("bid")),
        "offer": _number_or_none(snapshot.get("offer")),
        "update_time": snapshot.get("updateTimeUTC") or snapshot.get("updateTime"),
    }


def _closed_candles(
    prices_payload: Mapping[str, object],
    *,
    epic: str,
    instrument_id: str,
    observed_at: datetime,
) -> list[dict[str, object]]:
    prices = _list_field(prices_payload, "prices")
    feed = IgClosedM5Feed(epic=epic, observed_at=observed_at, prices=tuple(prices))
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
    def walk(value: object) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).casefold() in FORBIDDEN_OUTPUT_KEYS:
                    raise RuntimeError(f"forbidden evidence key: {key}")
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            lowered = value.casefold()
            if "x-security-token" in lowered or "x-ig-api-key" in lowered:
                raise RuntimeError("forbidden credential marker in evidence")

    walk(payload)


def _fingerprint(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def collect_probe(
    *,
    credentials_file: Path,
    epic: str,
    instrument_id: str,
    bars: int,
) -> dict[str, object]:
    credentials = _credentials_from_file(credentials_file)
    client = IgDemoReadOnlyClient(credentials=credentials)
    observed_at = datetime.now(timezone.utc)
    try:
        client.login()
        accounts = client.accounts()
        positions = client.positions()
        working_orders = client.working_orders()
        market = client.market(epic)
        prices = client.m5_prices(epic, max_bars=bars)
    finally:
        client.logout()

    candles = _closed_candles(
        prices,
        epic=epic,
        instrument_id=instrument_id,
        observed_at=observed_at,
    )
    evidence: dict[str, object] = {
        "schema": SCHEMA,
        "observed_at_utc": observed_at.isoformat(),
        "environment": "IG_DEMO",
        "evidence_state": "IG_DEMO_READONLY_BROKER_EVIDENCE",
        "execution_capability": client.execution_capability,
        "order_execution_enabled": client.order_execution_enabled,
        "accounts": _safe_accounts(accounts),
        "open_positions_count": len(_list_field(positions, "positions")),
        "working_orders_count": len(_list_field(working_orders, "workingOrders")),
        "market": _safe_market(market, expected_epic=epic),
        "closed_m5_count": len(candles),
        "latest_closed_m5": None if not candles else candles[-1],
    }
    _assert_credential_free(evidence)
    evidence["fingerprint"] = _fingerprint(evidence)
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

    evidence = collect_probe(
        credentials_file=args.credentials_file,
        epic=args.epic,
        instrument_id=args.instrument_id,
        bars=args.bars,
    )
    rendered = json.dumps(evidence, indent=2, sort_keys=True)
    print(rendered)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"WROTE {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
