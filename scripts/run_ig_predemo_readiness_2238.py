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
from typing import Any, Mapping
from uuid import uuid4

COLLECTOR_PATH = Path(__file__).resolve()
REPO_ROOT = COLLECTOR_PATH.parents[1]
sys.path.insert(0, str(COLLECTOR_PATH.parent))
sys.path.insert(0, str(REPO_ROOT / "src"))

from daxlab.adapters.ig_market_data import (  # noqa: E402
    DEFAULT_MAX_AGE,
    closed_m5_price_rows,
)
from daxlab.adapters.ig_rest_readonly import IgDemoReadOnlyClient  # noqa: E402

from ig_demo_readonly_probe import (  # noqa: E402
    DEFAULT_EPIC,
    DEFAULT_INSTRUMENT_ID,
    _assert_credential_free,
    _closed_candles,
    _credentials_from_file,
    _list_field,
    _safe_accounts,
)


SCHEMA = "DAXLAB_IG_PREDEMO_READINESS_V2"
MANIFEST_SCHEMA = "DAXLAB_IG_PREDEMO_READINESS_MANIFEST_V2"
ERROR_CODES = {
    "HEAD_MISMATCH",
    "HEAD_QUERY_FAILED",
    "STATE_RUNTIME_ROOT_UNAVAILABLE",
    "NAMESPACE_EXISTS",
    "CREDENTIALS_FILE_UNAVAILABLE_OR_INVALID",
    "IG_AUTHENTICATION_FAILED_NO_RETRY",
    "IG_SESSION_READ_FAILED_NO_RETRY",
    "IG_READINESS_MATRIX_INCOMPLETE",
    "IG_SESSION_CLEANUP_FAILED",
    "EVIDENCE_INVALID",
    "EVIDENCE_PUBLICATION_FAILED",
    "PYTHON_COLLECTOR_UNCLASSIFIED_FAILURE",
}


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


def _position_view(entry: object) -> dict[str, object]:
    if not isinstance(entry, Mapping):
        raise ValueError("position entry must be an object")
    position = entry.get("position")
    market = entry.get("market")
    if not isinstance(position, Mapping) or not isinstance(market, Mapping):
        raise ValueError("position entry shape invalid")
    return {
        "deal_fingerprint": _hashed_identifier(position.get("dealId")),
        "epic": market.get("epic") if isinstance(market.get("epic"), str) else None,
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
        "epic": order.get("epic") if isinstance(order.get("epic"), str) else None,
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
        if isinstance(instrument.get("type"), str)
        else None,
        "expiry": instrument.get("expiry")
        if isinstance(instrument.get("expiry"), str)
        else None,
        "unit": instrument.get("unit")
        if instrument.get("unit") in {"AMOUNT", "CONTRACTS", "SHARES"}
        else None,
        "market_status": snapshot.get("marketStatus")
        if isinstance(snapshot.get("marketStatus"), str)
        else None,
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
        "one_pip_means": instrument.get("onePipMeans")
        if isinstance(instrument.get("onePipMeans"), str)
        else None,
        "margin_factor": _num(instrument.get("marginFactor")),
        "margin_factor_unit": instrument.get("marginFactorUnit")
        if isinstance(instrument.get("marginFactorUnit"), str)
        else None,
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


def _matrix_summary(results: list[Any]) -> dict[str, object]:
    counts = {status: sum(item.status == status for item in results)
              for status in ("PASS", "FAIL", "BLOCKED", "UNKNOWN")}
    return {
        "status": "PASS" if counts["PASS"] == len(results) else "BLOCKED",
        "required_resources": len(results),
        "counts": counts,
        "resources": [item.safe_view() for item in results],
        "no_retry": True,
        "single_login": True,
        "single_cleanup": True,
    }


def _blocked(reason: str) -> dict[str, object]:
    return {"status": "BLOCKED", "reason_code": reason}


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


def collect(
    client: IgDemoReadOnlyClient, *, epic: str, instrument_id: str, bars: int
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Collect all Step2238 evidence in one already-authenticated session."""
    started = datetime.now(timezone.utc)
    account = dict(client.login_context)
    history_from = started - timedelta(days=7)
    reads = [
        client.readiness_accounts(),
        client.readiness_positions("POSITIONS_A"),
        client.readiness_working_orders("WORKING_ORDERS_A"),
        client.readiness_market_v4(epic),
        client.readiness_account_activity(from_utc=history_from, to_utc=started),
        client.readiness_m5_prices(epic, max_bars=bars),
        client.readiness_positions("POSITIONS_B"),
        client.readiness_working_orders("WORKING_ORDERS_B"),
    ]
    results = {item.resource: item for item in reads}
    matrix = _matrix_summary(reads)
    price_observed = results["M5_PRICES"].response_observed_at or datetime.now(timezone.utc)

    accounts = _result_payload(results, "ACCOUNTS")
    account_evidence: dict[str, object] = account | {
        "accounts": [] if accounts is None else _safe_accounts(accounts),
        "active_context_bound_to_single_session": True,
        "resource_status": results["ACCOUNTS"].status,
    }

    inventory: dict[str, object]
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
    except (AssertionError, KeyError, RuntimeError, TypeError, ValueError):
        inventory = _blocked("INVENTORY_BRACKET_READS_INCOMPLETE") | {
            "stable_across_bracket": False,
            "stable_inventory_fingerprint": None,
            "positions_count": None,
            "working_orders_count": None,
            "foreign_or_manual_inventory_present": None,
            "atomic": False,
            "scope": "UNPROVEN",
        }

    history = _result_payload(results, "ACTIVITY_HISTORY")
    if history is None:
        history_scope = _blocked("ACTIVITY_HISTORY_READ_INCOMPLETE") | {
            "from_utc": history_from.isoformat(), "to_utc": started.isoformat(),
            "entries_count": None, "scope_complete": False, "absolute_complete": False,
        }
    else:
        paging = history.get("metadata")
        next_page = paging.get("paging", {}).get("next") if isinstance(paging, Mapping) and isinstance(paging.get("paging"), Mapping) else None
        activities = history["activities"]
        assert isinstance(activities, list)
        history_scope = {
            "status": "PASS" if not next_page else "UNKNOWN",
            "reason_code": "NONE" if not next_page else "ACTIVITY_HISTORY_NEXT_PAGE_PRESENT",
            "from_utc": history_from.isoformat(), "to_utc": started.isoformat(),
            "entries_count": len(activities), "scope_complete": not next_page,
            "absolute_complete": False,
        }

    market_raw = _result_payload(results, "MARKET_V4")
    try:
        if market_raw is None:
            raise ValueError("market read incomplete")
        market = _market_view(market_raw, epic=epic, observed_at=price_observed)
        market["status"] = "PASS"
        market["reason_code"] = "NONE"
    except (KeyError, RuntimeError, TypeError, ValueError):
        market = _blocked("MARKET_ECONOMICS_READ_INCOMPLETE") | {
            "epic": epic, "economics_verified": False,
            "economics_blockers": ["MARKET_V4_UNAVAILABLE_OR_INVALID"],
        }

    prices = _result_payload(results, "M5_PRICES")
    try:
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
    except (IndexError, KeyError, RuntimeError, TypeError, ValueError):
        market_data = _blocked("M5_FRESHNESS_READ_INCOMPLETE") | {
            "raw_rows": None, "closed_rows": None, "latest_closed_m5": None,
            "latest_closed_age_seconds": None,
            "freshness_max_age_seconds": DEFAULT_MAX_AGE.total_seconds(), "fresh": False,
            "timestamp_semantics": "INTERVAL_START", "freshness_basis": "TRUE_CLOSE_TIME",
        }

    server_dates = [item.server_date_utc.isoformat() for item in reads if item.server_date_utc]
    clock = {
        "local_clock": "UTC_AWARE", "provider_server_dates_observed": len(server_dates),
        "server_date_values_utc": server_dates,
        "broker_timezone_offset_hours": account.get("timezone_offset_hours"),
        "session_clock_verified": bool(server_dates) and account.get("timezone_offset_hours") is not None,
    }
    economics_status = (
        "PASS" if market.get("economics_verified") is True
        else "UNKNOWN" if market.get("status") == "PASS"
        else "BLOCKED"
    )
    dependent = {
        "inventory_stability": {
            "status": inventory["status"], "reason_code": inventory["reason_code"]
        },
        "history_completeness": {
            "status": history_scope["status"], "reason_code": history_scope["reason_code"]
        },
        "economics": {
            "status": economics_status,
            "reason_code": "NONE" if economics_status == "PASS" else (
                "NATIVE_ECONOMICS_FIELDS_UNVERIFIED" if economics_status == "UNKNOWN"
                else "MARKET_V4_READ_INCOMPLETE"
            ),
        },
        "m5_freshness": {
            "status": market_data["status"], "reason_code": market_data["reason_code"]
        },
    }
    evidence: dict[str, object] = {
        "schema": SCHEMA,
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
        "provider_queries": sum(item.request_started_at is not None for item in reads),
        "single_authenticated_session": True,
        "session_cleanup": {"status": "PENDING", "error_code": "NONE", "attempts": 0},
        "unknowns_preserved": True,
    }
    return _finalize_evidence(evidence, cleanup_status="PENDING", cleanup_error_code="NONE")


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
        files = {"READINESS.json": evidence, **components, "SUMMARY.json": summary}
        hashes: dict[str, str] = {}
        for name, payload in files.items():
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
        client = IgDemoReadOnlyClient(credentials)
        phase = "LOGIN"
        client.login()
        phase = "READ"
        evidence, components = collect(
            client, epic=args.epic, instrument_id=args.instrument_id, bars=args.bars
        )
        phase = "CLEANUP"
        cleanup_error_code = "NONE"
        try:
            client.logout()
        except Exception:
            cleanup_error_code = "IG_SESSION_CLEANUP_FAILED"
        client = None
        evidence, components = _finalize_evidence(
            evidence,
            cleanup_status="PASS" if cleanup_error_code == "NONE" else "FAIL",
            cleanup_error_code=cleanup_error_code,
        )
        matrix = evidence["authenticated_read_matrix"]
        assert isinstance(matrix, Mapping)
        matrix_complete = matrix.get("status") == "PASS"
        result_code = (
            "IG_READINESS_MATRIX_INCOMPLETE" if not matrix_complete
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
            "PUBLISH": "EVIDENCE_PUBLICATION_FAILED",
            "CREDENTIAL": "CREDENTIALS_FILE_UNAVAILABLE_OR_INVALID",
            "RUNTIME": "STATE_RUNTIME_ROOT_UNAVAILABLE",
            "HEAD": "HEAD_QUERY_FAILED",
            "VALIDATE": "EVIDENCE_INVALID",
        }.get(failed_phase, "PYTHON_COLLECTOR_UNCLASSIFIED_FAILURE")
        print(json.dumps({
            "status": "BLOCKED",
            "error_code": code,
            "failure_phase": failed_phase,
            "cleanup_error_code": cleanup_error_code,
            "execution_capability": "NONE",
            "order_execution_enabled": False,
        }, sort_keys=True))
        return 2
    matrix_counts = matrix.get("counts") if isinstance(matrix.get("counts"), Mapping) else {}
    print(json.dumps({
        "status": result_status,
        "error_code": result_code,
        "namespace": str(namespace),
        "failure_phase": None if result_status == "SUCCESS" else (
            "READ" if not matrix_complete else "CLEANUP"
        ),
        "cleanup_error_code": cleanup_error_code,
        "readiness_matrix_counts": matrix_counts,
        "readiness_matrix": matrix.get("resources"),
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }, sort_keys=True))
    return 0 if result_status == "SUCCESS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
