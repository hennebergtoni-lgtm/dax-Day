"""One-session, read-only IG Step2238 readiness evidence collector.

The runner uses login plus GET-only resources and one logout.  It emits only
credential-free, hash-bound files, never overwrites a namespace, and contains no
dealing route or execution promotion.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Callable, Mapping
from uuid import uuid4

COLLECTOR_PATH = Path(__file__).resolve()
REPO_ROOT = COLLECTOR_PATH.parents[1]
sys.path.insert(0, str(COLLECTOR_PATH.parent))
sys.path.insert(0, str(REPO_ROOT / "src"))

from daxlab.adapters.ig_market_data import (  # noqa: E402
    DEFAULT_MAX_AGE,
    closed_m5_price_rows,
)
from daxlab.adapters.ig_rest_readonly import (  # noqa: E402
    IgDemoReadOnlyClient,
    IgReadinessRead,
)

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object  # noqa: E402
from daxlab.runtime.single_instance import SingleInstanceLock  # noqa: E402

from ig_demo_readonly_probe import (  # noqa: E402
    DEFAULT_EPIC,
    DEFAULT_INSTRUMENT_ID,
    _assert_credential_free,
    _closed_candles,
    _credentials_from_file,
    _list_field,
    _safe_accounts,
)


SCHEMA = "DAXLAB_IG_PREDEMO_READINESS_V3"
MANIFEST_SCHEMA = "DAXLAB_IG_PREDEMO_READINESS_MANIFEST_V3"
ERROR_CODES = {
    "HEAD_MISMATCH",
    "HEAD_QUERY_FAILED",
    "STATE_RUNTIME_ROOT_UNAVAILABLE",
    "NAMESPACE_EXISTS",
    "CREDENTIALS_FILE_UNAVAILABLE_OR_INVALID",
    "IG_AUTHENTICATION_FAILED_NO_RETRY",
    "IG_SESSION_READ_FAILED_NO_RETRY",
    "IG_READINESS_MATRIX_INCOMPLETE",
    "IG_READINESS_DERIVATION_INCOMPLETE",
    "IG_SESSION_CLEANUP_FAILED",
    "EVIDENCE_INVALID",
    "EVIDENCE_PUBLICATION_FAILED",
    "RAW_PERSISTENCE_FAILED",
    "PYTHON_COLLECTOR_UNCLASSIFIED_FAILURE",
}

READ_RESOURCE_CONTRACTS = (
    ("ACCOUNTS", "ACCOUNTS_V1"),
    ("POSITIONS_A", "POSITIONS_V2"),
    ("WORKING_ORDERS_A", "WORKING_ORDERS_V2"),
    ("MARKET_V4", "MARKET_V4"),
    ("ACTIVITY_HISTORY", "ACTIVITY_HISTORY_V3"),
    ("M5_PRICES", "PRICES_V3"),
    ("POSITIONS_B", "POSITIONS_V2"),
    ("WORKING_ORDERS_B", "WORKING_ORDERS_V2"),
)


def _fingerprint(value: object) -> str:
    rendered = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return sha256(rendered.encode()).hexdigest()


def _num(value: object) -> float | None:
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if isfinite(result) else None


def _rule(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    unit = value.get("unit")
    return {
        "value": _num(value.get("value")),
        "unit": unit if unit in {"POINTS", "PERCENTAGE"} else None,
    }


def _hashed_identifier(value: object) -> str | None:
    return sha256(value.encode()).hexdigest() if isinstance(value, str) and value else None


def _safe_epic(value: object) -> str | None:
    # Provider identifiers, never arbitrary URLs, exception text or credentials.
    if isinstance(value, str) and len(value) <= 64 and value.startswith("IX.D.") and all(
        c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789." for c in value
    ):
        return value
    return None


def _safe_login_context(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("login context invalid")
    fingerprint = value.get("account_context_fingerprint")
    if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(
        c not in "0123456789abcdef" for c in fingerprint
    ):
        fingerprint = None
    return {
        "environment": "IG_DEMO" if value.get("environment") == "IG_DEMO" else None,
        "account_type": value.get("account_type")
        if value.get("account_type") in ("CFD", "SPREADBET", "STOCKBROKING") else None,
        "currency": value.get("currency") if value.get("currency") in (
            "EUR", "GBP", "USD", "CHF", "JPY", "AUD", "CAD", "NZD", "SGD",
            "HKD", "SEK", "NOK", "DKK", "ZAR",
        ) else None,
        "dealing_enabled": value.get("dealing_enabled")
        if type(value.get("dealing_enabled")) is bool else None,
        "timezone_offset_hours": _num(value.get("timezone_offset_hours")),
        "account_context_fingerprint": fingerprint,
    }


def _position_view(entry: object) -> dict[str, object]:
    if not isinstance(entry, Mapping):
        raise ValueError("position entry must be an object")
    position = entry.get("position")
    market = entry.get("market")
    if not isinstance(position, Mapping) or not isinstance(market, Mapping):
        raise ValueError("position entry shape invalid")
    return {
        "deal_fingerprint": _hashed_identifier(position.get("dealId")),
        "epic": _safe_epic(market.get("epic")),
        "direction": position.get("direction")
        if position.get("direction") in {"BUY", "SELL"}
        else None,
        "size": _num(position.get("size")),
        "level": _num(position.get("level")),
        "stop_level": _num(position.get("stopLevel")),
        "limit_level": _num(position.get("limitLevel")),
    }


def _order_view(entry: object) -> dict[str, object]:
    if not isinstance(entry, Mapping):
        raise ValueError("working-order entry must be an object")
    order = entry.get("workingOrderData")
    if not isinstance(order, Mapping):
        raise ValueError("working-order entry shape invalid")
    return {
        "deal_fingerprint": _hashed_identifier(order.get("dealId")),
        "epic": _safe_epic(order.get("epic")),
        "direction": order.get("direction")
        if order.get("direction") in {"BUY", "SELL"}
        else None,
        "size": _num(order.get("orderSize")),
        "level": _num(order.get("orderLevel")),
        "stop_distance": _num(order.get("stopDistance")),
        "limit_distance": _num(order.get("limitDistance")),
    }


def _inventory_view(
    positions: Mapping[str, object], orders: Mapping[str, object]
) -> dict[str, object]:
    safe_positions = [_position_view(value) for value in _list_field(positions, "positions")]
    safe_orders = [_order_view(value) for value in _list_field(orders, "workingOrders")]
    safe_positions.sort(key=_fingerprint)
    safe_orders.sort(key=_fingerprint)
    payload = {"positions": safe_positions, "working_orders": safe_orders}
    return payload | {"fingerprint": _fingerprint(payload)}


def _market_view(
    payload: Mapping[str, object], *, epic: str, observed_at: datetime
) -> dict[str, object]:
    instrument = payload.get("instrument")
    rules = payload.get("dealingRules")
    snapshot = payload.get("snapshot")
    if not all(isinstance(value, Mapping) for value in (instrument, rules, snapshot)):
        raise ValueError("market v4 response shape invalid")
    assert isinstance(instrument, Mapping)
    assert isinstance(rules, Mapping)
    assert isinstance(snapshot, Mapping)
    if instrument.get("epic") != epic and instrument.get("marketId") != epic:
        raise ValueError("market epic mismatch")
    quote_epoch = _num(snapshot.get("updateTimestampUTC"))
    quote_time = None
    quote_age = None
    if quote_epoch is not None:
        quote_time = datetime.fromtimestamp(quote_epoch, tz=timezone.utc)
        quote_age = (observed_at - quote_time).total_seconds()
        if quote_age < 0:
            quote_age = None
    minimum = _rule(rules.get("minDealSize"))
    minimum_value = None if minimum is None else minimum["value"]
    minimum_unit = None if minimum is None else minimum["unit"]
    stop_rules = {
        "min_normal": _rule(rules.get("minNormalStopOrLimitDistance")),
        "min_controlled": _rule(rules.get("minControlledRiskStopDistance")),
        "max_stop_or_limit": _rule(rules.get("maxStopOrLimitDistance")),
        "controlled_risk_spacing": _rule(rules.get("controlledRiskSpacing")),
    }
    return {
        "epic": epic,
        "instrument_type": instrument.get("type")
        if instrument.get("type") in ("INDICES", "CURRENCIES", "COMMODITIES", "SHARES")
        else None,
        "expiry": instrument.get("expiry")
        if instrument.get("expiry") in ("DFB", "-") else None,
        "unit": instrument.get("unit")
        if instrument.get("unit") in {"AMOUNT", "CONTRACTS", "SHARES"}
        else None,
        "market_status": snapshot.get("marketStatus")
        if snapshot.get("marketStatus") in (
            "TRADEABLE", "CLOSED", "EDITS_ONLY", "OFFLINE", "ON_AUCTION", "SUSPENDED"
        ) else None,
        "bid": _num(snapshot.get("bid")),
        "ask": _num(snapshot.get("ask")),
        "quote_time_utc": None if quote_time is None else quote_time.isoformat(),
        "quote_age_seconds": quote_age,
        "quote_fresh": quote_age is not None and quote_age <= 60.0,
        "decimal_places_factor": _num(snapshot.get("decimalPlacesFactor")),
        "scaling_factor": _num(snapshot.get("scalingFactor")),
        "tick_size": None,
        "tick_size_reason": "NOT_DERIVED_FROM_DECIMAL_PLACES_OR_SCALING_FACTOR",
        "quantity_min": minimum_value if minimum_unit == "POINTS" else None,
        "quantity_step": None,
        "quantity_max": None,
        "cash_per_tick_per_quantity": None,
        "value_of_one_pip": _num(instrument.get("valueOfOnePip")),
        "one_pip_means": None,  # Free provider prose is not an economics authority.
        "margin_factor": _num(instrument.get("marginFactor")),
        "margin_factor_unit": instrument.get("marginFactorUnit")
        if instrument.get("marginFactorUnit") in ("POINTS", "PERCENTAGE") else None,
        "stops_limits_allowed": instrument.get("stopsLimitsAllowed")
        if isinstance(instrument.get("stopsLimitsAllowed"), bool)
        else None,
        "controlled_risk_allowed": instrument.get("controlledRiskAllowed")
        if isinstance(instrument.get("controlledRiskAllowed"), bool)
        else None,
        "force_open_allowed": instrument.get("forceOpenAllowed")
        if isinstance(instrument.get("forceOpenAllowed"), bool)
        else None,
        "streaming_prices_available": instrument.get("streamingPricesAvailable")
        if isinstance(instrument.get("streamingPricesAvailable"), bool)
        else None,
        "stop_constraints": stop_rules,
        "native_stop_constraints_verified": all(
            value is not None and value["value"] is not None and value["unit"] is not None
            for key, value in stop_rules.items()
            if key in {"min_normal", "max_stop_or_limit"}
        ),
        "economics_verified": False,
        "economics_blockers": [
            "TICK_SIZE_UNVERIFIED",
            "QUANTITY_INCREMENT_UNVERIFIED",
            "MAX_SIZE_UNVERIFIED",
            "TICK_VALUE_SEMANTICS_UNVERIFIED",
        ],
    }


def _observation_view(client: IgDemoReadOnlyClient) -> list[dict[str, object]]:
    return [
        {
            "resource": item.resource,
            "request_started_at_utc": item.request_started_at.isoformat(),
            "response_observed_at_utc": item.response_observed_at.isoformat(),
            "server_date_utc": None
            if item.server_date_utc is None
            else item.server_date_utc.isoformat(),
            "request_id_fingerprint": item.request_id_fingerprint,
        }
        for item in client.read_observations
    ]


def _result_payload(results: Mapping[str, Any], name: str) -> Mapping[str, object] | None:
    result = results[name]
    return result.payload if result.status == "PASS" else None


def _fallback_read(
    resource: str,
    endpoint_family: str,
    *,
    status: str = "UNKNOWN",
    reason_code: str | None = None,
    started: datetime | None = None,
    observed: datetime | None = None,
) -> IgReadinessRead:
    return IgReadinessRead(
        resource=resource,
        endpoint_family=endpoint_family,
        status=status,
        reason_code=reason_code or f"IG_READ_{resource}_UNCLASSIFIED",
        response_shape_status="NOT_EVALUATED",
        request_started_at=started,
        response_observed_at=observed,
        http_status_class=None,
        provider_error_code=None,
        request_id_fingerprint=None,
        server_date_utc=None,
        payload=None,
    )


def _initial_readiness_rows() -> list[dict[str, object]]:
    return [
        _fallback_read(resource, endpoint).safe_view()
        for resource, endpoint in READ_RESOURCE_CONTRACTS
    ]


def _sanitized_raw_row(
    row: object, *, resource: str, endpoint_family: str
) -> dict[str, object]:
    if not isinstance(row, dict):
        raise ValueError("raw readiness row must be an object")
    status = row.get("status")
    reason = row.get("reason_code")
    shape = row.get("response_shape_status")
    http_class = row.get("http_status_class")
    provider_code = row.get("provider_error_code")
    request_id = row.get("request_id_fingerprint")
    if row.get("resource") != resource or row.get("endpoint_family") != endpoint_family:
        raise ValueError("raw readiness identity mismatch")
    if status not in {"PASS", "FAIL", "BLOCKED", "UNKNOWN"}:
        raise ValueError("raw readiness status invalid")
    if not isinstance(reason, str) or not reason or not reason.isascii() or any(
        character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for character in reason
    ):
        raise ValueError("raw readiness reason invalid")
    if not isinstance(shape, str) or not shape or not shape.isascii() or any(
        character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for character in shape
    ):
        raise ValueError("raw readiness shape invalid")
    if http_class not in {
        None, "HTTP_1XX", "HTTP_2XX", "HTTP_3XX", "HTTP_4XX", "HTTP_5XX", "HTTP_OTHER"
    }:
        raise ValueError("raw readiness HTTP class invalid")
    if provider_code is not None and (
        not isinstance(provider_code, str)
        or not provider_code
        or len(provider_code) > 96
        or not provider_code.isascii()
        or not provider_code.startswith(("error.", "endpoint.", "invalid.", "system."))
        or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789.-" for character in provider_code)
    ):
        raise ValueError("raw readiness provider code invalid")
    if request_id is not None and (
        not isinstance(request_id, str)
        or len(request_id) != 64
        or any(character not in "0123456789abcdef" for character in request_id)
    ):
        raise ValueError("raw readiness request fingerprint invalid")
    timestamps: dict[str, str | None] = {}
    for key in (
        "request_started_at_utc", "response_observed_at_utc", "server_date_utc"
    ):
        value = row.get(key)
        if value is not None and (
            not isinstance(value, str)
            or len(value) > 64
            or any(character not in "0123456789T:+.-" for character in value)
        ):
            raise ValueError("raw readiness timestamp invalid")
        if value is not None:
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
                raise ValueError("raw readiness timestamp must be UTC-aware")
        timestamps[key] = value
    return {
        "resource": resource,
        "endpoint_family": endpoint_family,
        "status": status,
        "reason_code": reason,
        "http_status_class": http_class,
        "provider_error_code": provider_code,
        "response_shape_status": shape,
        "request_started_at_utc": timestamps["request_started_at_utc"],
        "response_observed_at_utc": timestamps["response_observed_at_utc"],
        "request_id_fingerprint": request_id,
        "server_date_utc": timestamps["server_date_utc"],
    }


def _matrix_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    safe_rows: list[dict[str, object]] = []
    for index, (resource, endpoint) in enumerate(READ_RESOURCE_CONTRACTS):
        try:
            row = rows[index]
            safe_rows.append(
                _sanitized_raw_row(row, resource=resource, endpoint_family=endpoint)
            )
        except Exception:
            safe_rows.append(_fallback_read(resource, endpoint).safe_view())
    counts = {
        status: sum(row["status"] == status for row in safe_rows)
        for status in ("PASS", "FAIL", "BLOCKED", "UNKNOWN")
    }
    return {
        "status": "PASS" if counts["PASS"] == len(READ_RESOURCE_CONTRACTS) else "BLOCKED",
        "required_resources": len(READ_RESOURCE_CONTRACTS),
        "row_count": len(safe_rows),
        "counts": counts,
        "resources": safe_rows,
        "no_retry": True,
        "single_login": True,
        "single_cleanup": True,
    }


def _emergency_matrix(
    preserved_rows: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    fallback_rows = [
        {
            "resource": resource,
            "endpoint_family": endpoint,
            "status": "UNKNOWN",
            "reason_code": f"IG_READ_{resource}_UNCLASSIFIED",
            "http_status_class": None,
            "provider_error_code": None,
            "response_shape_status": "NOT_EVALUATED",
            "request_started_at_utc": None,
            "response_observed_at_utc": None,
            "request_id_fingerprint": None,
            "server_date_utc": None,
        }
        for resource, endpoint in READ_RESOURCE_CONTRACTS
    ]
    rows = fallback_rows
    if isinstance(preserved_rows, list) and len(preserved_rows) == 8:
        preserved: list[dict[str, object]] = []
        for index, (resource, endpoint) in enumerate(READ_RESOURCE_CONTRACTS):
            try:
                preserved.append(
                    _sanitized_raw_row(
                        preserved_rows[index], resource=resource, endpoint_family=endpoint
                    )
                )
            except Exception:
                preserved.append(fallback_rows[index])
        rows = preserved
    counts = {
        status: sum(row.get("status") == status for row in rows)
        for status in ("PASS", "FAIL", "BLOCKED", "UNKNOWN")
    }
    return {
        "status": "BLOCKED",
        "required_resources": 8,
        "row_count": 8,
        "counts": counts,
        "resources": rows,
        "no_retry": True,
        "single_login": True,
        "single_cleanup": True,
    }


def _safe_matrix_snapshot(rows: list[dict[str, object]]) -> dict[str, object]:
    try:
        return _matrix_from_rows(rows)
    except Exception:
        return _emergency_matrix(rows)


def _authenticated_after_read(client: IgDemoReadOnlyClient) -> bool:
    try:
        return client.authenticated is True
    except AttributeError:
        # Minimal collector test doubles represent an already authenticated owner.
        return True
    except Exception:
        # Failure to inspect a local health property is not proof that the
        # authenticated session was lost. The next independent GET stays guarded.
        return True


def _safe_utc_now() -> datetime:
    try:
        return datetime.now(timezone.utc)
    except Exception:
        # Diagnostic fallback only. A local clock API exception must not suppress
        # the eight rows that were allocated before authentication.
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _guarded_resource_read(
    client: IgDemoReadOnlyClient,
    *,
    resource: str,
    endpoint_family: str,
    epic: str,
    history_from: datetime,
    history_to: datetime,
    bars: int,
    authentication_available: bool,
) -> IgReadinessRead:
    if not authentication_available:
        return _fallback_read(
            resource,
            endpoint_family,
            status="BLOCKED",
            reason_code="IG_READ_AUTH_PRECONDITION_BLOCKED",
        )
    started = _safe_utc_now()
    try:
        if resource == "ACCOUNTS":
            result = client.readiness_accounts()
        elif resource in {"POSITIONS_A", "POSITIONS_B"}:
            result = client.readiness_positions(resource)
        elif resource in {"WORKING_ORDERS_A", "WORKING_ORDERS_B"}:
            result = client.readiness_working_orders(resource)
        elif resource == "MARKET_V4":
            result = client.readiness_market_v4(epic)
        elif resource == "ACTIVITY_HISTORY":
            result = client.readiness_account_activity(
                from_utc=history_from, to_utc=history_to
            )
        elif resource == "M5_PRICES":
            result = client.readiness_m5_prices(epic, max_bars=bars)
        else:  # pragma: no cover - immutable contract exhaustiveness
            raise RuntimeError("unknown readiness resource")
        if (
            not isinstance(result, IgReadinessRead)
            or result.resource != resource
            or result.endpoint_family != endpoint_family
        ):
            raise TypeError("readiness resource result contract invalid")
        result.safe_view()
        return result
    except Exception:
        return _fallback_read(
            resource,
            endpoint_family,
            reason_code=f"IG_READ_{resource}_UNCLASSIFIED",
            started=started,
            observed=_safe_utc_now(),
        )


def _blocked(reason: str) -> dict[str, object]:
    return {"status": "BLOCKED", "reason_code": reason}


def _clock_projection(
    reads: list[IgReadinessRead], account: Mapping[str, object]
) -> dict[str, object]:
    server_dates = [
        item.server_date_utc.isoformat() for item in reads if item.server_date_utc
    ]
    return {
        "local_clock": "UTC_AWARE",
        "provider_server_dates_observed": len(server_dates),
        "server_date_values_utc": server_dates,
        "broker_timezone_offset_hours": account.get("timezone_offset_hours"),
        "session_clock_verified": bool(server_dates)
        and account.get("timezone_offset_hours") is not None,
    }


def _dependent_projection(
    inventory: Mapping[str, object],
    history_scope: Mapping[str, object],
    market: Mapping[str, object],
    market_data: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    economics_status = (
        "PASS"
        if market.get("economics_verified") is True
        else "UNKNOWN"
        if market.get("status") == "PASS"
        else "BLOCKED"
    )
    return {
        "inventory_stability": {
            "status": inventory["status"], "reason_code": inventory["reason_code"]
        },
        "history_completeness": {
            "status": history_scope["status"],
            "reason_code": history_scope["reason_code"],
        },
        "economics": {
            "status": economics_status,
            "reason_code": "NONE"
            if economics_status == "PASS"
            else "NATIVE_ECONOMICS_FIELDS_UNVERIFIED"
            if economics_status == "UNKNOWN"
            else "MARKET_V4_READ_INCOMPLETE",
        },
        "m5_freshness": {
            "status": market_data["status"],
            "reason_code": market_data["reason_code"],
        },
    }


def _build_components(evidence: Mapping[str, object]) -> dict[str, dict[str, object]]:
    inventory = evidence["inventory"]
    assert isinstance(inventory, Mapping)
    return {
        "READ_MATRIX.json": {
            "schema": SCHEMA,
            "authenticated_read_matrix": evidence["authenticated_read_matrix"],
            "dependent_conclusions": evidence["dependent_conclusions"],
        },
        "ACCOUNT.json": {"schema": SCHEMA, "account": evidence["account"]},
        "INVENTORY.json": {"schema": SCHEMA, "inventory": inventory},
        "MARKET.json": {"schema": SCHEMA, "market": evidence["market"]},
        "CLOCK.json": {"schema": SCHEMA, "clock": evidence["clock"]},
        "HISTORY_SCOPE.json": {"schema": SCHEMA, "history_scope": evidence["history_scope"]},
    }


def _finalize_evidence(
    evidence: dict[str, object], *, cleanup_status: str, cleanup_error_code: str
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    evidence["session_cleanup"] = {
        "status": cleanup_status,
        "error_code": cleanup_error_code,
        "attempts": 1,
    }
    evidence.pop("fingerprint", None)
    _assert_credential_free(evidence)
    evidence["fingerprint"] = _fingerprint(evidence)
    return evidence, _build_components(evidence)


OBSERVATION_SCHEMA = "DAXLAB_IG_READINESS_OBSERVATION_V1"


class ReadinessObservationWriter:
    """One collector writer: immutable sanitized slots, retained after publication.

    A receipt commits a byte hash only after readback. Unreceipted slots remain
    UNKNOWN on recovery. No broker I/O, state migration or namespace reuse.
    """

    def __init__(self, namespace: Path, *, head: str, evidence_scope: str) -> None:
        if len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
            raise ValueError("invalid observation head")
        if evidence_scope not in {"SYNTHETIC", "REAL_BROKER_READ"}:
            raise ValueError("invalid observation scope")
        self.namespace = namespace
        self.head = head
        self.scope = evidence_scope
        self.lock = SingleInstanceLock(namespace.with_suffix(".lock"), head)
        self.confirmed: list[int] = []
        self.failed = False

    def start(self) -> None:
        try:
            self.lock.acquire()
            self.namespace.mkdir(parents=True, exist_ok=False)
            header = {
                "schema": OBSERVATION_SCHEMA, "exact_head": self.head,
                "namespace_fingerprint": _fingerprint(str(self.namespace.resolve())),
                "evidence_scope": self.scope,
                "resources": [name for name, _ in READ_RESOURCE_CONTRACTS],
                "execution_capability": "NONE", "order_execution_enabled": False,
            }
            atomic_write_json(self.namespace / "MANIFEST.json", header, overwrite=False)
        except Exception:
            self.failed = True
            self.lock.release()
            raise

    def close(self) -> None:
        self.lock.release()

    def record(self, index: int, row: dict[str, object]) -> None:
        if not self.lock.held or type(index) is not int or not 0 <= index < 8:
            raise ValueError("observation writer ownership invalid")
        resource, endpoint = READ_RESOURCE_CONTRACTS[index]
        safe = _sanitized_raw_row(row, resource=resource, endpoint_family=endpoint)
        _assert_credential_free(safe)
        record = {
            "schema": OBSERVATION_SCHEMA, "exact_head": self.head,
            "evidence_scope": self.scope, "slot": index, "row": safe,
            "payload_hash": _fingerprint(safe),
        }
        path = self.namespace / f"{index:02d}.json"
        atomic_write_json(path, record, overwrite=False)
        if read_json_object(path) != record:
            raise OSError("observation readback mismatch")
        receipt = {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest()}
        atomic_write_json(self.namespace / f"{index:02d}.receipt.json", receipt, overwrite=False)
        self.confirmed.append(index)

    def seal(self) -> None:
        if not self.lock.held or self.confirmed != list(range(8)):
            raise ValueError("observation set incomplete")
        files = {
            f"{i:02d}.receipt.json": sha256(
                (self.namespace / f"{i:02d}.receipt.json").read_bytes()
            ).hexdigest() for i in range(8)
        }
        atomic_write_json(self.namespace / "COMPLETE.json", {"files": files}, overwrite=False)

    def status(self) -> dict[str, object]:
        return {
            "status": "BLOCKED" if self.failed else "PASS",
            "reason_code": "RAW_PERSISTENCE_FAILED" if self.failed else "NONE",
            "confirmed_slots": list(self.confirmed),
            "evidence_scope": self.scope,
        }


def recover_readiness_observations(
    namespace: Path, *, expected_head: str
) -> dict[str, object]:
    """Read committed raw outcomes only; never repeat provider reads or re-date."""
    with SingleInstanceLock(namespace.with_suffix(".lock"), expected_head):
        header = read_json_object(namespace / "MANIFEST.json")
        if (
            header.get("schema") != OBSERVATION_SCHEMA
            or header.get("exact_head") != expected_head
            or header.get("namespace_fingerprint") != _fingerprint(str(namespace.resolve()))
            or header.get("resources") != [name for name, _ in READ_RESOURCE_CONTRACTS]
            or header.get("evidence_scope") not in {"SYNTHETIC", "REAL_BROKER_READ"}
            or header.get("execution_capability") != "NONE"
            or header.get("order_execution_enabled") is not False
        ):
            raise ValueError("observation manifest binding invalid")
        seal_path = namespace / "COMPLETE.json"
        if seal_path.exists():
            seal = read_json_object(seal_path)
            expected_files = {
                f"{i:02d}.receipt.json": sha256(
                    (namespace / f"{i:02d}.receipt.json").read_bytes()
                ).hexdigest() for i in range(8)
            }
            if seal != {"files": expected_files}:
                raise ValueError("observation complete hash list mismatch")
        rows = _initial_readiness_rows()
        confirmed = []
        for index, (resource, endpoint) in enumerate(READ_RESOURCE_CONTRACTS):
            receipt_path = namespace / f"{index:02d}.receipt.json"
            if not receipt_path.exists():
                continue
            receipt = read_json_object(receipt_path)
            path = namespace / f"{index:02d}.json"
            if receipt != {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest()}:
                raise ValueError("observation byte hash mismatch")
            record = read_json_object(path)
            safe = _sanitized_raw_row(record.get("row"), resource=resource, endpoint_family=endpoint)
            if record != {
                "schema": OBSERVATION_SCHEMA, "exact_head": expected_head,
                "evidence_scope": header["evidence_scope"], "slot": index,
                "row": safe, "payload_hash": _fingerprint(safe),
            }:
                raise ValueError("observation source binding mismatch")
            rows[index] = safe
            confirmed.append(index)
        return {
            "authenticated_read_matrix": _safe_matrix_snapshot(rows),
            "confirmed_slots": confirmed, "evidence_scope": header["evidence_scope"],
            "replayed": True, "execution_capability": "NONE", "order_execution_enabled": False,
        }


def collect(
    client: IgDemoReadOnlyClient,
    *,
    epic: str,
    instrument_id: str,
    bars: int,
    raw_rows: list[dict[str, object]] | None = None,
    observation_writer: ReadinessObservationWriter | None = None,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Collect eight guarded raw reads, then independently derive conclusions."""
    if raw_rows is None:
        raw_rows = _initial_readiness_rows()
    if len(raw_rows) != len(READ_RESOURCE_CONTRACTS):
        raise ValueError("raw readiness sink must contain exactly eight rows")
    started = _safe_utc_now()
    history_from = started - timedelta(days=7)
    reads: list[IgReadinessRead] = []
    authentication_available = True
    for index, (resource, endpoint_family) in enumerate(READ_RESOURCE_CONTRACTS):
        result = _guarded_resource_read(
            client,
            resource=resource,
            endpoint_family=endpoint_family,
            epic=epic,
            history_from=history_from,
            history_to=started,
            bars=bars,
            authentication_available=authentication_available,
        )
        reads.append(result)
        try:
            raw_rows[index] = result.safe_view()
        except Exception:
            replacement = _fallback_read(resource, endpoint_family)
            reads[-1] = replacement
            raw_rows[index] = replacement.safe_view()
        if observation_writer is not None:
            try:
                observation_writer.record(index, raw_rows[index])
            except Exception:
                observation_writer.failed = True
        if authentication_available and not _authenticated_after_read(client):
            authentication_available = False

    if observation_writer is not None:
        try:
            observation_writer.seal()
        except Exception:
            observation_writer.failed = True
    results = {item.resource: item for item in reads}
    derived_processing: dict[str, dict[str, str]] = {}
    try:
        matrix = _matrix_from_rows(raw_rows)
        derived_processing["MATRIX_CONSTRUCTION"] = {
            "status": "PASS", "reason_code": "NONE"
        }
    except Exception:
        matrix = _emergency_matrix(raw_rows)
        derived_processing["MATRIX_CONSTRUCTION"] = {
            "status": "BLOCKED", "reason_code": "READ_MATRIX_CONSTRUCTION_FAILED"
        }
    try:
        price_observed = results["M5_PRICES"].response_observed_at or _safe_utc_now()
    except Exception:
        price_observed = started

    try:
        account = _safe_login_context(client.login_context)
        accounts = _result_payload(results, "ACCOUNTS")
        account_evidence: dict[str, object] = account | {
            "accounts": [] if accounts is None else _safe_accounts(accounts),
            "active_context_bound_to_single_session": True,
            "resource_status": results["ACCOUNTS"].status,
        }
        derived_processing["LOGIN_CONTEXT"] = {
            "status": "PASS", "reason_code": "NONE"
        }
    except Exception:
        account = {}
        account_evidence = _blocked("LOGIN_CONTEXT_PROJECTION_FAILED") | {
            "accounts": [],
            "active_context_bound_to_single_session": False,
            "resource_status": results["ACCOUNTS"].status,
        }
        derived_processing["LOGIN_CONTEXT"] = {
            "status": "BLOCKED", "reason_code": "LOGIN_CONTEXT_PROJECTION_FAILED"
        }

    try:
        position_a = _result_payload(results, "POSITIONS_A")
        order_a = _result_payload(results, "WORKING_ORDERS_A")
        position_b = _result_payload(results, "POSITIONS_B")
        order_b = _result_payload(results, "WORKING_ORDERS_B")
        if any(value is None for value in (position_a, order_a, position_b, order_b)):
            raise ValueError("inventory bracket resource incomplete")
        assert position_a is not None and order_a is not None
        assert position_b is not None and order_b is not None
        inventory_a = _inventory_view(position_a, order_a)
        inventory_b = _inventory_view(position_b, order_b)
        stable = inventory_a["fingerprint"] == inventory_b["fingerprint"]
        active_count = len(inventory_b["positions"]) + len(inventory_b["working_orders"])
        inventory = {
            "status": "PASS" if stable else "UNKNOWN",
            "reason_code": "NONE" if stable else "INVENTORY_BRACKET_CHANGED",
            "first": inventory_a, "second": inventory_b,
            "stable_across_bracket": stable,
            "stable_inventory_fingerprint": inventory_b["fingerprint"] if stable else None,
            "positions_count": len(inventory_b["positions"]),
            "working_orders_count": len(inventory_b["working_orders"]),
            "foreign_or_manual_inventory_present": active_count > 0,
            "atomic": False,
            "scope": "TWO_STABLE_READS_IN_ONE_AUTHENTICATED_SESSION",
        }
        derived_processing["INVENTORY"] = {
            "status": "PASS", "reason_code": "NONE"
        }
    except Exception:
        inventory = _blocked("INVENTORY_BRACKET_READS_INCOMPLETE") | {
            "stable_across_bracket": False,
            "stable_inventory_fingerprint": None,
            "positions_count": None,
            "working_orders_count": None,
            "foreign_or_manual_inventory_present": None,
            "atomic": False,
            "scope": "UNPROVEN",
        }
        derived_processing["INVENTORY"] = {
            "status": "BLOCKED", "reason_code": "INVENTORY_DERIVATION_FAILED"
        }

    try:
        history = _result_payload(results, "ACTIVITY_HISTORY")
        if history is None:
            raise ValueError("activity history read incomplete")
        paging = history.get("metadata")
        next_page = (
            paging.get("paging", {}).get("next")
            if isinstance(paging, Mapping)
            and isinstance(paging.get("paging"), Mapping)
            else None
        )
        activities = history["activities"]
        if not isinstance(activities, list):
            raise TypeError("activity history entries invalid")
        history_scope = {
            "status": "PASS" if not next_page else "UNKNOWN",
            "reason_code": "NONE"
            if not next_page
            else "ACTIVITY_HISTORY_NEXT_PAGE_PRESENT",
            "from_utc": history_from.isoformat(),
            "to_utc": started.isoformat(),
            "entries_count": len(activities),
            "scope_complete": not next_page,
            "absolute_complete": False,
        }
        derived_processing["HISTORY"] = {"status": "PASS", "reason_code": "NONE"}
    except Exception:
        history_scope = _blocked("ACTIVITY_HISTORY_READ_INCOMPLETE") | {
            "from_utc": history_from.isoformat(), "to_utc": started.isoformat(),
            "entries_count": None, "scope_complete": False, "absolute_complete": False,
        }
        derived_processing["HISTORY"] = {
            "status": "BLOCKED", "reason_code": "HISTORY_DERIVATION_FAILED"
        }

    try:
        market_raw = _result_payload(results, "MARKET_V4")
        if market_raw is None:
            raise ValueError("market read incomplete")
        market = _market_view(market_raw, epic=epic, observed_at=price_observed)
        market["status"] = "PASS"
        market["reason_code"] = "NONE"
        derived_processing["MARKET_ECONOMICS"] = {
            "status": "PASS", "reason_code": "NONE"
        }
    except Exception:
        market = _blocked("MARKET_ECONOMICS_READ_INCOMPLETE") | {
            "epic": epic, "economics_verified": False,
            "economics_blockers": ["MARKET_V4_UNAVAILABLE_OR_INVALID"],
        }
        derived_processing["MARKET_ECONOMICS"] = {
            "status": "BLOCKED", "reason_code": "MARKET_DERIVATION_FAILED"
        }

    try:
        prices = _result_payload(results, "M5_PRICES")
        if prices is None or results["M5_PRICES"].request_started_at is None:
            raise ValueError("M5 read incomplete")
        price_started = results["M5_PRICES"].request_started_at
        raw_prices = _list_field(prices, "prices")
        closed_rows = closed_m5_price_rows(raw_prices, observed_at=price_started)
        candles = _closed_candles(
            prices, epic=epic, instrument_id=instrument_id,
            observed_at=price_observed, closed_as_of=price_started,
        )
        latest_close = datetime.fromisoformat(candles[-1]["close_time"])
        market_data = {
            "status": "PASS", "reason_code": "NONE", "raw_rows": len(raw_prices),
            "closed_rows": len(closed_rows), "latest_closed_m5": candles[-1],
            "latest_closed_age_seconds": (price_observed - latest_close).total_seconds(),
            "freshness_max_age_seconds": DEFAULT_MAX_AGE.total_seconds(),
            "fresh": (price_observed - latest_close) <= DEFAULT_MAX_AGE,
            "timestamp_semantics": "INTERVAL_START", "freshness_basis": "TRUE_CLOSE_TIME",
        }
        derived_processing["M5"] = {"status": "PASS", "reason_code": "NONE"}
    except Exception:
        market_data = _blocked("M5_FRESHNESS_READ_INCOMPLETE") | {
            "raw_rows": None, "closed_rows": None, "latest_closed_m5": None,
            "latest_closed_age_seconds": None,
            "freshness_max_age_seconds": DEFAULT_MAX_AGE.total_seconds(), "fresh": False,
            "timestamp_semantics": "INTERVAL_START", "freshness_basis": "TRUE_CLOSE_TIME",
        }
        derived_processing["M5"] = {
            "status": "BLOCKED", "reason_code": "M5_DERIVATION_FAILED"
        }

    try:
        clock = _clock_projection(reads, account)
        derived_processing["CLOCK"] = {"status": "PASS", "reason_code": "NONE"}
    except Exception:
        clock = {
            "local_clock": "UNKNOWN",
            "provider_server_dates_observed": 0,
            "server_date_values_utc": [],
            "broker_timezone_offset_hours": None,
            "session_clock_verified": False,
        }
        derived_processing["CLOCK"] = {
            "status": "BLOCKED", "reason_code": "CLOCK_DERIVATION_FAILED"
        }
    try:
        dependent = _dependent_projection(inventory, history_scope, market, market_data)
        derived_processing["DEPENDENT_CONCLUSIONS"] = {
            "status": "PASS", "reason_code": "NONE"
        }
    except Exception:
        dependent = {
            name: {"status": "BLOCKED", "reason_code": "DERIVATION_FAILED"}
            for name in (
                "inventory_stability", "history_completeness", "economics", "m5_freshness"
            )
        }
        derived_processing["DEPENDENT_CONCLUSIONS"] = {
            "status": "BLOCKED", "reason_code": "DEPENDENT_DERIVATION_FAILED"
        }
    try:
        provider_queries = sum(item.request_started_at is not None for item in reads)
        derived_processing["EVIDENCE_ENRICHMENT"] = {
            "status": "PASS", "reason_code": "NONE"
        }
    except Exception:
        provider_queries = sum(
            row.get("request_started_at_utc") is not None for row in raw_rows
        )
        derived_processing["EVIDENCE_ENRICHMENT"] = {
            "status": "BLOCKED", "reason_code": "EVIDENCE_ENRICHMENT_FAILED"
        }
    evidence: dict[str, object] = {
        "schema": SCHEMA,
        "raw_persistence": (observation_writer.status() if observation_writer is not None
                            else {"status": "UNKNOWN", "reason_code": "NOT_REQUESTED"}),
        "environment": "IG_DEMO",
        "instrument_id": instrument_id,
        "collected_at_utc": price_observed.isoformat(),
        "execution_capability": "NONE",
        "order_execution_enabled": False,
        "account": account_evidence,
        "market": market,
        "inventory": inventory,
        "history_scope": history_scope,
        "clock": clock,
        "market_data": market_data,
        "authenticated_read_matrix": matrix,
        "dependent_conclusions": dependent,
        "derived_processing": derived_processing,
        "derived_processing_complete": False,
        "provider_queries": provider_queries,
        "single_authenticated_session": True,
        "session_cleanup": {"status": "PENDING", "error_code": "NONE", "attempts": 0},
        "unknowns_preserved": True,
    }
    try:
        components = _build_components(evidence)
        derived_processing["COMPONENT_CONSTRUCTION"] = {
            "status": "PASS", "reason_code": "NONE"
        }
    except Exception:
        components = {}
        derived_processing["COMPONENT_CONSTRUCTION"] = {
            "status": "BLOCKED", "reason_code": "COMPONENT_CONSTRUCTION_FAILED"
        }
    evidence["derived_processing_complete"] = all(
        value["status"] == "PASS" for value in derived_processing.values()
    )
    return evidence, components


def _head(repo_root: Path = REPO_ROOT) -> str:
    canonical_root = repo_root.resolve(strict=True)
    result = subprocess.run(
        ["git", "-C", str(canonical_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
        encoding="utf-8",
        errors="strict",
    )
    return result.stdout.strip()


def _publish(
    namespace: Path,
    evidence: Mapping[str, object],
    components: Mapping[str, Mapping[str, object]],
    *,
    head: str,
    status: str = "SUCCESS",
    error_code: str = "NONE",
    synthetic_sink: Callable[[Mapping[str, bytes]], Mapping[str, object]] | None = None,
) -> None:
    if namespace.exists():
        raise FileExistsError("namespace exists")
    namespace.parent.mkdir(parents=True, exist_ok=True)
    staging = namespace.with_name(f".{namespace.name}.partial-{uuid4().hex}")
    staging.mkdir(exist_ok=False)
    summary = {
        "status": status,
        "error_code": error_code,
        "namespace": str(namespace),
        "readiness_fingerprint": evidence["fingerprint"],
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    try:
        allowed_components = {
            "READ_MATRIX.json", "ACCOUNT.json", "INVENTORY.json", "MARKET.json",
            "CLOCK.json", "HISTORY_SCOPE.json",
        }
        if set(components) - allowed_components:
            raise ValueError("unapproved evidence component")
        files = {"READINESS.json": evidence, **components, "SUMMARY.json": summary}
        hashes: dict[str, str] = {}
        for name, payload in files.items():
            _assert_credential_free(payload)
            rendered = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
            (staging / name).write_bytes(rendered.encode("utf-8"))
            hashes[name] = sha256(rendered.encode()).hexdigest()
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "exact_head": head,
            "files": hashes,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }
        manifest["fingerprint"] = _fingerprint(manifest)
        (staging / "MANIFEST.json").write_bytes(
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )
        for name, expected_hash in hashes.items():
            if sha256((staging / name).read_bytes()).hexdigest() != expected_hash:
                raise OSError("staging evidence readback mismatch")
        staging.rename(namespace)
        for name, expected_hash in hashes.items():
            if sha256((namespace / name).read_bytes()).hexdigest() != expected_hash:
                raise OSError("published evidence readback mismatch")
        if synthetic_sink is not None:
            # A fixed injected acceptance channel, never a new remote publisher.
            original = {name: (namespace / name).read_bytes() for name in (*hashes, "MANIFEST.json")}
            expected = {
                "target": "SYNTHETIC_ACCEPTANCE",
                "receipt": {name: sha256(data).hexdigest() for name, data in original.items()},
                "readback": dict(original),
            }
            readback = synthetic_sink(dict(original))
            if not isinstance(readback, Mapping) or dict(readback) != expected:
                raise OSError("synthetic transfer receipt or readback incomplete")
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--credentials-file", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--namespace", type=Path, required=True)
    parser.add_argument("--epic", default=DEFAULT_EPIC)
    parser.add_argument("--instrument-id", default=DEFAULT_INSTRUMENT_ID)
    parser.add_argument("--bars", type=int, default=40)
    parser.add_argument("--pre-auth-precheck", action="store_true")
    args = parser.parse_args()
    client = None
    login_succeeded = False
    observation_writer = None
    raw_rows = _initial_readiness_rows()
    phase = "VALIDATE"
    try:
        if args.namespace.is_absolute() or ".." in args.namespace.parts:
            raise RuntimeError("EVIDENCE_INVALID")
        phase = "RUNTIME"
        runtime_root = args.runtime_root.resolve(strict=True)
        namespace = runtime_root / args.namespace
        phase = "HEAD"
        head = _head()
        if head != args.expected_head:
            raise RuntimeError("HEAD_MISMATCH")
        if namespace.exists():
            raise RuntimeError("NAMESPACE_EXISTS")
        phase = "CREDENTIAL"
        credentials = _credentials_from_file(args.credentials_file)
        if args.pre_auth_precheck:
            print(json.dumps({
                "status": "SUCCESS",
                "error_code": "NONE",
                "pre_auth_precheck": "PASS",
                "exact_head": head,
                "execution_capability": "NONE",
                "order_execution_enabled": False,
            }, sort_keys=True))
            return 0
        phase = "PERSISTENCE"
        observation_writer = ReadinessObservationWriter(
            namespace.with_name(namespace.name + ".observations"),
            head=head, evidence_scope="REAL_BROKER_READ",
        )
        observation_writer.start()
        client = IgDemoReadOnlyClient(credentials)
        phase = "LOGIN"
        client.login()
        login_succeeded = True
        phase = "READ"
        evidence, components = collect(
            client,
            epic=args.epic,
            instrument_id=args.instrument_id,
            bars=args.bars,
            raw_rows=raw_rows,
            observation_writer=observation_writer,
        )
        phase = "CLEANUP"
        cleanup_error_code = "NONE"
        try:
            client.logout()
        except Exception:
            cleanup_error_code = "IG_SESSION_CLEANUP_FAILED"
        client = None
        phase = "EVIDENCE"
        evidence["authenticated_read_matrix"] = _safe_matrix_snapshot(raw_rows)
        evidence, components = _finalize_evidence(
            evidence,
            cleanup_status="PASS" if cleanup_error_code == "NONE" else "FAIL",
            cleanup_error_code=cleanup_error_code,
        )
        matrix = evidence["authenticated_read_matrix"]
        assert isinstance(matrix, Mapping)
        matrix_complete = (
            matrix.get("status") == "PASS"
            and matrix.get("row_count") == len(READ_RESOURCE_CONTRACTS)
        )
        derivation_complete = evidence.get("derived_processing_complete") is True
        result_code = (
            "RAW_PERSISTENCE_FAILED"
            if observation_writer.failed
            else "IG_READINESS_MATRIX_INCOMPLETE"
            if not matrix_complete
            else "IG_READINESS_DERIVATION_INCOMPLETE"
            if not derivation_complete
            else cleanup_error_code
        )
        result_status = "SUCCESS" if result_code == "NONE" else "BLOCKED"
        phase = "PUBLISH"
        _publish(
            namespace, evidence, components, head=head,
            status=result_status, error_code=result_code,
        )
    except Exception as exc:
        failed_phase = phase
        cleanup_error_code = "NONE"
        if client is not None and failed_phase != "CLEANUP":
            try:
                client.logout()
            except Exception:
                cleanup_error_code = "IG_SESSION_CLEANUP_FAILED"
        code = str(exc) if str(exc) in ERROR_CODES else {
            "LOGIN": "IG_AUTHENTICATION_FAILED_NO_RETRY",
            "READ": "IG_SESSION_READ_FAILED_NO_RETRY",
            "CLEANUP": "IG_SESSION_CLEANUP_FAILED",
            "EVIDENCE": "EVIDENCE_INVALID",
            "PUBLISH": "EVIDENCE_PUBLICATION_FAILED",
            "PERSISTENCE": "RAW_PERSISTENCE_FAILED",
            "CREDENTIAL": "CREDENTIALS_FILE_UNAVAILABLE_OR_INVALID",
            "RUNTIME": "STATE_RUNTIME_ROOT_UNAVAILABLE",
            "HEAD": "HEAD_QUERY_FAILED",
            "VALIDATE": "EVIDENCE_INVALID",
        }.get(failed_phase, "PYTHON_COLLECTOR_UNCLASSIFIED_FAILURE")
        failure_payload: dict[str, object] = {
            "status": "BLOCKED",
            "error_code": code,
            "failure_phase": failed_phase,
            "cleanup_error_code": cleanup_error_code,
            "login_success": login_succeeded,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }
        if observation_writer is not None:
            failure_payload["raw_persistence"] = observation_writer.status()
        if login_succeeded:
            failure_matrix = _safe_matrix_snapshot(raw_rows)
            failure_payload["readiness_matrix_counts"] = failure_matrix["counts"]
            failure_payload["readiness_matrix"] = failure_matrix["resources"]
            failure_payload["readiness_matrix_row_count"] = failure_matrix["row_count"]
        print(json.dumps(failure_payload, sort_keys=True))
        return 2
    finally:
        if observation_writer is not None:
            observation_writer.close()
    matrix_counts = matrix.get("counts") if isinstance(matrix.get("counts"), Mapping) else {}
    print(json.dumps({
        "status": result_status,
        "error_code": result_code,
        "namespace": str(namespace),
        "failure_phase": None if result_status == "SUCCESS" else (
            "READ" if not matrix_complete or not derivation_complete else "CLEANUP"
        ),
        "cleanup_error_code": cleanup_error_code,
        "login_success": login_succeeded,
        "readiness_matrix_counts": matrix_counts,
        "readiness_matrix": matrix.get("resources"),
        "readiness_matrix_row_count": matrix.get("row_count"),
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }, sort_keys=True))
    return 0 if result_status == "SUCCESS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
