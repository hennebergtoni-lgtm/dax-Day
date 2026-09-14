"""One credential-free IG RAW observation or offline comparison; no Candidate run.

Raw snapshots are observation artifacts, never resumable Candidate evidence.
Timestamp hypotheses and observed revisions are separate facts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from math import isfinite
from pathlib import Path
import platform
import re
import sys
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ig_demo_readonly_probe import (  # noqa: E402
    DEFAULT_EPIC, DEFAULT_MAX_AGE,
    _assert_credential_free, _credentials_from_file, _fingerprint,
)
from ig_cand001_shadow_e2e import HostTestBlocked, check_code, require, utc  # noqa: E402
from daxlab.adapters.ig_market_data import raw_snapshot_time_utc  # noqa: E402
from daxlab.adapters.ig_rest_readonly import IgDemoReadOnlyClient, IgReadOnlyError  # noqa: E402
from daxlab.runtime.atomic_json import atomic_write_json, read_json_object  # noqa: E402
from daxlab.runtime.single_instance import SingleInstanceLock  # noqa: E402

SCHEMA = "DAX_IG_RAW_M5_TIMESTAMP_OBSERVATION_V2"
HISTORICAL_INTERVAL_END_HYPOTHESIS = "IG_MINUTE_5_SNAPSHOT_UTC_INTERVAL_END_V1"
PRICE_FIELDS = ("openPrice", "highPrice", "lowPrice", "closePrice")
VOLUME_FIELDS = ("lastTradedVolume", "volume")


def number(value: object) -> object:
    require(value is None or (type(value) in (int, float) and isfinite(value)),
            "RAW_NON_NUMERIC_FIELD")
    return value


def project_row(raw: Mapping[str, object], *, row_index: int = 0,
                requested: datetime | None = None, observed: datetime | None = None) -> dict[str, Any]:
    # No arbitrary provider string, header, payload, account or extra key is copied.
    timestamp = raw.get("snapshotTimeUTC")
    require(isinstance(timestamp, str) and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)?", timestamp
    ) is not None, "RAW_INVALID_TIMESTAMP")
    wire_time = raw_snapshot_time_utc(raw)
    event, close = wire_time - timedelta(minutes=5), wire_time
    selected: dict[str, Any] = {"snapshotTimeUTC": timestamp}
    for field in PRICE_FIELDS:
        quote = raw.get(field)
        require(isinstance(quote, Mapping), "RAW_INVALID_QUOTE")
        require("bid" in quote and "ask" in quote, "RAW_INVALID_QUOTE")
        selected[field] = {key: number(quote[key]) for key in ("bid", "ask", "lastTraded")
                           if key in quote}
    for field in VOLUME_FIELDS:
        if field in raw:
            selected[field] = number(raw[field])
    def hypothesis(start: datetime, end: datetime) -> dict[str, Any]:
        closed = end <= requested if requested is not None else None
        age = (observed - end).total_seconds() if observed else None
        freshness = ("UNKNOWN" if closed is None or age is None else "NOT_CLOSED" if not closed
                     else "FRESH" if age <= DEFAULT_MAX_AGE.total_seconds() else "STALE")
        return {
            "event_time": start.isoformat(), "close_time": end.isoformat(),
            "verification_state": "UNVERIFIED", "is_closed": closed,
            "closed_state": "UNKNOWN" if closed is None else "CLOSED" if closed else "NOT_CLOSED",
            "freshness_seconds": age, "freshness_state": freshness,
            "provider_finalization_state": "UNKNOWN", "candidate_finalized": False,
        }
    row = {
        "raw_row_index": row_index,
        "raw": selected,
        "raw_timestamp": timestamp,
        "raw_timestamp_age_at_request_seconds": (requested - close).total_seconds() if requested else None,
        "raw_timestamp_age_at_response_seconds": (observed - close).total_seconds() if observed else None,
        # No chosen normalization/closure/freshness while timestamp semantics is unresolved.
        "normalized_event_time": None, "normalized_close_time": None,
        "closed_state": "UNKNOWN", "is_closed": None,
        "provider_finalization_state": "UNKNOWN", "candidate_finalized": False,
        "freshness_seconds": None, "freshness_state": "UNKNOWN", "provider_revision_state": "UNKNOWN",
        "normalized_current_adapter_hypothesis": {
            **hypothesis(event, close),
            "timestamp_contract": HISTORICAL_INTERVAL_END_HYPOTHESIS,
        },
        "interval_start_hypothesis": hypothesis(wire_time, wire_time + timedelta(minutes=5)),
    }
    row["fingerprint"] = _fingerprint(row)
    return row


def snapshot(prices: object, *, head: str, requested: datetime,
             observed: datetime) -> dict[str, Any]:
    require(isinstance(prices, list) and len(prices) >= 2, "RAW_INSUFFICIENT_ROWS")
    require(all(isinstance(row, Mapping) for row in prices), "RAW_INVALID_ROWS")
    rows = [project_row(row, row_index=index, requested=requested, observed=observed)
            for index, row in enumerate(prices)]
    times = [utc(row["normalized_current_adapter_hypothesis"]["close_time"]) for row in rows]
    require(all(b - a == timedelta(minutes=5) for a, b in zip(times, times[1:])),
            "RAW_NONCONTIGUOUS_TIMESTAMPS")
    require(requested.utcoffset() == observed.utcoffset() == timedelta(0) and observed >= requested,
            "CLOCK_INVALID_UTC")
    require(re.fullmatch(r"[0-9a-f]{40}", head) is not None, "GOVERNANCE_INVALID_HEAD")
    payload = {
        "schema": SCHEMA, "exact_code_head": head, "data_source": "IG_DEMO_REST_PRICES_V3",
        "epic": DEFAULT_EPIC, "resolution": "MINUTE_5", "requested_max_bars": 40,
        "request_started_at_utc": requested.isoformat(),
        "response_observed_at_utc": observed.isoformat(), "raw_m5_count": len(rows), "rows": rows,
        "timestamp_semantics": "UNKNOWN", "provider_finality": "UNKNOWN",
        "freshness_max_age_seconds": DEFAULT_MAX_AGE.total_seconds(),
        "provider_semantics_classification": "OTHER_UNKNOWN", "classification_state": "UNVERIFIED",
        "candidate_processing_performed": False,
        "execution_capability": "NONE", "order_execution_enabled": False,
    }
    _assert_credential_free(payload)
    payload["fingerprint"] = _fingerprint(payload)
    return payload


def validate_snapshot(payload: dict[str, Any]) -> None:
    _assert_credential_free(payload)
    require(payload.get("schema") == SCHEMA, "RAW_EVIDENCE_SCHEMA_MISMATCH")
    expected = snapshot([row["raw"] for row in payload["rows"]], head=payload["exact_code_head"],
                        requested=utc(payload["request_started_at_utc"]),
                        observed=utc(payload["response_observed_at_utc"]))
    require(payload == expected, "RAW_EVIDENCE_CONTRACT_OR_HASH_MISMATCH")


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    validate_snapshot(before)
    validate_snapshot(after)
    require(before["exact_code_head"] == after["exact_code_head"], "GOVERNANCE_HEAD_MISMATCH")
    require(utc(before["response_observed_at_utc"]) < utc(after["request_started_at_utc"]),
            "RAW_OBSERVATIONS_NOT_SEQUENTIAL")
    old = {row["raw"]["snapshotTimeUTC"]: row for row in before["rows"]}
    comparisons = []
    for row in after["rows"]:
        raw = row["raw"]
        prior = old.get(raw["snapshotTimeUTC"])
        if prior is None:
            continue
        changes = {}
        field_diffs = []
        for field in (*PRICE_FIELDS, *VOLUME_FIELDS):
            # Missing versus explicitly null is a wire difference, not silently normalized.
            if (field in prior["raw"]) != (field in raw) or prior["raw"].get(field) != raw.get(field):
                changes[field] = {"before_present": field in prior["raw"],
                                  "after_present": field in raw,
                                  "before": prior["raw"].get(field), "after": raw.get(field)}
            keys = ("bid", "ask", "lastTraded") if field in PRICE_FIELDS else (None,)
            for key in keys:
                first = prior["raw"][field] if key is not None else prior["raw"]
                later = raw[field] if key is not None else raw
                name = key if key is not None else field
                first_present, later_present = name in first, name in later
                first_value, later_value = first.get(name), later.get(name)
                field_diffs.append({
                    "field": f"{field}.{key}" if key is not None else field,
                    "before_present": first_present, "after_present": later_present,
                    "before": first_value, "after": later_value,
                    "changed": first_present != later_present or first_value != later_value,
                })
        ohlc_changed = any(field in changes for field in PRICE_FIELDS)
        volume_changed = any(field in changes for field in VOLUME_FIELDS)
        mutation_type = ("MIXED" if ohlc_changed and volume_changed else "OHLC_ONLY" if ohlc_changed
                         else "VOLUME_ONLY" if volume_changed else "UNCHANGED")
        timestamp = utc(row["normalized_current_adapter_hypothesis"]["close_time"])
        comparisons.append({
            "snapshotTimeUTC": raw["snapshotTimeUTC"], "changed_fields": changes,
            "field_diffs": field_diffs, "observed_mutation_type": mutation_type,
            "first_raw_row_index": prior["raw_row_index"], "later_raw_row_index": row["raw_row_index"],
            "before_bars_back_from_raw_tail": before["raw_m5_count"] - 1 - prior["raw_row_index"],
            "after_bars_back_from_raw_tail": after["raw_m5_count"] - 1 - row["raw_row_index"],
            "first_seen_at": before["response_observed_at_utc"],
            "later_seen_at": after["response_observed_at_utc"],
            "seen_time_scope": "THIS_COMPARISON_PAIR",
            "observation_age_basis": "RAW_TIMESTAMP_NOT_VERIFIED_CLOSE_TIME",
            "age_at_first_observation_seconds": prior["raw_timestamp_age_at_response_seconds"],
            "age_at_later_observation_seconds": row["raw_timestamp_age_at_response_seconds"],
            "before_request_age_seconds": (utc(before["request_started_at_utc"]) - timestamp).total_seconds(),
            "after_request_age_seconds": (utc(after["request_started_at_utc"]) - timestamp).total_seconds(),
            "observed_across_next_m5_boundary": (
                utc(before["response_observed_at_utc"]) < timestamp + timedelta(minutes=5)
                <= utc(after["request_started_at_utc"])
            ),
        })
    require(len(comparisons) >= 2, "RAW_INSUFFICIENT_COMMON_TIMESTAMPS")
    result = {
        "schema": "DAX_IG_RAW_M5_COMPARISON_V2", "exact_code_head": before["exact_code_head"],
        "before_fingerprint": before["fingerprint"], "after_fingerprint": after["fingerprint"],
        "before_request_started_at_utc": before["request_started_at_utc"],
        "before_response_observed_at_utc": before["response_observed_at_utc"],
        "after_request_started_at_utc": after["request_started_at_utc"],
        "after_response_observed_at_utc": after["response_observed_at_utc"],
        "common_raw_timestamp_count": len(comparisons),
        "changed_raw_timestamp_count": sum(bool(row["changed_fields"]) for row in comparisons),
        "comparisons": comparisons, "timestamp_semantics": "UNKNOWN",
        "provider_semantics_classification": "OTHER_UNKNOWN", "classification_state": "UNVERIFIED",
        "historical_closed_bar_revision": "UNKNOWN",
        "revision_duration_upper_bound_seconds": None,
        "unchanged_observation_is_not_finality_proof": True,
        "execution_capability": "NONE", "order_execution_enabled": False,
    }
    result["fingerprint"] = _fingerprint(result)
    return result


def collect_authenticated(client, *, head: str, clock=lambda: datetime.now(timezone.utc)):
    """One prices observation using caller-owned auth; never login/logout/refresh."""
    require(client.execution_capability == "NONE" and client.order_execution_enabled is False,
            "SAFETY_EXECUTION_CAPABILITY")
    require(client.authenticated, "IG_SESSION_NOT_AUTHENTICATED")
    requested = clock()
    response = client.m5_prices(DEFAULT_EPIC, max_bars=40)
    observed = clock()
    return snapshot(response.get("prices"), head=head, requested=requested, observed=observed)


def collect(credentials_file: Path, *, head: str, client_factory=IgDemoReadOnlyClient,
            clock=lambda: datetime.now(timezone.utc)) -> dict[str, Any]:
    client = client_factory(_credentials_from_file(credentials_file))
    require(client.execution_capability == "NONE" and client.order_execution_enabled is False,
            "SAFETY_EXECUTION_CAPABILITY")
    try:
        client.login()  # Exactly one attempt. No inventory, market or dealing request.
        return collect_authenticated(client, head=head, clock=clock)
    finally:
        client.logout()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--credentials-file", type=Path)
    parser.add_argument("--compare", type=Path, nargs=2, metavar=("BEFORE", "AFTER"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        require(bool(args.compare) != bool(args.credentials_file), "RAW_SELECT_ONE_MODE")
        head = check_code(args.expected_head)
        if not args.compare:
            require(platform.system() == "Windows", "GOVERNANCE_WINDOWS_HOST_REQUIRED")
        with SingleInstanceLock(args.output.with_suffix(".lock"), "IG_RAW_M5_DIAGNOSTIC"):
            require(not args.output.exists(), "RAW_OUTPUT_ALREADY_EXISTS")
            if args.compare:
                payload = compare(*(read_json_object(path) for path in args.compare))
                require(payload["exact_code_head"] == head, "GOVERNANCE_HEAD_MISMATCH")
            else:
                payload = collect(args.credentials_file, head=head)
            check_code(head)
            atomic_write_json(args.output, payload, overwrite=False)
        print(json.dumps({"status": "OBSERVATION_ONLY", "schema": payload["schema"],
                          "fingerprint": payload["fingerprint"], "timestamp_semantics": "UNKNOWN",
                          "execution_capability": "NONE", "order_execution_enabled": False}))
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, HostTestBlocked) else "RAW_DIAGNOSTIC_FAILED"
        if isinstance(exc, IgReadOnlyError) and re.search(r"\bHTTP 401\b", str(exc)):
            code = "IG_AUTHENTICATION_FAILED_NO_RETRY"
        print(json.dumps({"status": "BLOCKED", "error_code": code,
                          "prior_evidence_is_not_current": True,
                          "execution_capability": "NONE", "order_execution_enabled": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
