#!/usr/bin/env python3
"""Export local credential-free MT5 SHADOW evidence to Neon.

This exporter is observation-only. It never imports MetaTrader5, never calls an
order API, and has no control path back to the Windows SHADOW supervisor. It
reads already-persisted local heartbeat/bundle/Decision/Candidate operator
artifacts and appends deduplicated telemetry to PostgreSQL.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Mapping

import psycopg

from daxlab.runtime.atomic_json import read_json_object
from daxlab.runtime.candidate_operator_telemetry import validate_candidate_operator_snapshot
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle

_HEARTBEAT_SCHEMA = "DAXLAB_MT5_SHADOW_HEARTBEAT_V1"
_ALLOWED_HEARTBEAT_STATUS = {"GREEN", "BLOCKED", "ERROR", "STOPPED"}
_FORBIDDEN_KEYS = {
    "login",
    "password",
    "token",
    "secret",
    "email",
    "phone",
    "account_id",
    "account_number",
    "api_key",
    "otp",
}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _payload_sha256(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _assert_sha256(value: Any, *, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc


def _assert_credential_free(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise ValueError(f"forbidden telemetry field: {key}")
            _assert_credential_free(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_credential_free(item)


def _validate_heartbeat(payload: Mapping[str, Any]) -> None:
    _assert_credential_free(payload)
    if payload.get("schema_version") != _HEARTBEAT_SCHEMA:
        raise ValueError("unsupported MT5 SHADOW heartbeat schema")
    if payload.get("status") not in _ALLOWED_HEARTBEAT_STATUS:
        raise ValueError("unsupported MT5 SHADOW heartbeat status")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("telemetry heartbeat execution capability must be NONE")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("telemetry heartbeat order execution must be disabled")
    blockers = payload.get("blockers")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        raise ValueError("telemetry heartbeat blockers must be a list of strings")


def _validate_decision(payload: Mapping[str, Any]) -> None:
    _assert_credential_free(payload)
    _assert_sha256(payload.get("decision_id"), field="decision_id")
    _assert_sha256(payload.get("closed_bar_fingerprint"), field="closed_bar_fingerprint")
    _assert_sha256(payload.get("reference_engine_sha256"), field="reference_engine_sha256")
    if payload.get("action") != "NO_ORDER":
        raise ValueError("telemetry Decision action must be NO_ORDER")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("telemetry Decision execution capability must be NONE")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("telemetry Decision order execution must be disabled")
    if not isinstance(payload.get("observed_at"), str) or not payload["observed_at"]:
        raise ValueError("telemetry Decision observed_at must be non-empty")
    if not isinstance(payload.get("symbol"), str) or not payload["symbol"].strip():
        raise ValueError("telemetry Decision symbol must be non-empty")
    if not isinstance(payload.get("reference_experiment_id"), str) or not payload[
        "reference_experiment_id"
    ].strip():
        raise ValueError("telemetry Decision reference experiment must be non-empty")
    reasons = payload.get("reason_codes")
    if not isinstance(reasons, list) or not reasons or not all(isinstance(item, str) for item in reasons):
        raise ValueError("telemetry Decision reason_codes must be a non-empty list of strings")


def _bar_fingerprint(bar: Any) -> str:
    """Match the validated MT5 feed's canonical OHLC fingerprint contract."""
    return _payload_sha256(
        {
            "open_time": bar.open_time.isoformat(),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
        }
    )


def _insert_heartbeat(conn: psycopg.Connection, payload: Mapping[str, Any]) -> int:
    _validate_heartbeat(payload)
    payload_hash = _payload_sha256(payload)
    result = conn.execute(
        """
        insert into mt5_shadow_heartbeats (
            observed_at_utc, schema_version, status, symbol, bundle_sha256,
            closed_m5_bars, latest_closed_bar_age_seconds,
            single_instance_lock_held, processed_total, new_decisions,
            duplicates_suppressed, evidence_state, cross_cycle_status,
            cross_cycle_overlapping_bars, cross_cycle_identical_overlaps,
            cross_cycle_mutated_overlaps, blockers, history_archive_status,
            execution_capability, order_execution_enabled, payload_sha256, payload
        ) values (
            %s, %s, %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s::jsonb, %s,
            %s, %s, %s, %s::jsonb
        )
        on conflict (payload_sha256) do nothing
        returning id
        """,
        (
            payload["observed_at_utc"],
            payload["schema_version"],
            payload["status"],
            payload.get("symbol"),
            payload.get("bundle_sha256"),
            payload["closed_m5_bars"],
            payload.get("latest_closed_bar_age_seconds"),
            payload["single_instance_lock_held"],
            payload.get("processed_total"),
            payload["new_decisions"],
            payload["duplicates_suppressed"],
            payload.get("evidence_state"),
            payload["cross_cycle_status"],
            payload["cross_cycle_overlapping_bars"],
            payload["cross_cycle_identical_overlaps"],
            payload["cross_cycle_mutated_overlaps"],
            json.dumps(payload["blockers"], separators=(",", ":")),
            payload.get("history_archive_status"),
            payload["execution_capability"],
            payload["order_execution_enabled"],
            payload_hash,
            _canonical(payload),
        ),
    ).fetchone()
    return 1 if result is not None else 0


def _insert_bars(conn: psycopg.Connection, bundle_payload: Mapping[str, Any]) -> int:
    _assert_credential_free(bundle_payload)
    bundle = parse_windows_mt5_bundle(bundle_payload)
    if bundle.feed is None:
        return 0
    symbol = bundle.host.symbols[0].name if bundle.host.symbols else None
    if not symbol:
        raise ValueError("MT5 SHADOW bundle has no resolved symbol")

    inserted = 0
    for bar in bundle.feed.bars:
        result = conn.execute(
            """
            insert into mt5_shadow_bars (
                symbol, open_time, open, high, low, close,
                bar_fingerprint, bundle_sha256, broker_timezone,
                timestamp_interpretation, execution_capability,
                order_execution_enabled
            ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'NONE', false)
            on conflict (symbol, bar_fingerprint) do nothing
            returning id
            """,
            (
                symbol,
                bar.open_time,
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                _bar_fingerprint(bar),
                bundle.fingerprint,
                bundle.feed.broker_timezone,
                bundle.feed.timestamp_interpretation,
            ),
        ).fetchone()
        inserted += 1 if result is not None else 0
    return inserted


def _load_decision_outbox(state_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    outbox_dir = state_dir / "decision_outbox"
    if not outbox_dir.exists():
        return []
    items: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(outbox_dir.glob("*.json")):
        payload = read_json_object(path)
        _validate_decision(payload)
        if path.stem != payload["decision_id"]:
            raise ValueError("Decision outbox filename does not match decision_id")
        items.append((path, payload))
    return items


def _insert_decision(conn: psycopg.Connection, payload: Mapping[str, Any]) -> int:
    _validate_decision(payload)
    payload_hash = _payload_sha256(payload)
    result = conn.execute(
        """
        insert into mt5_shadow_decisions (
            decision_id, observed_at, symbol, closed_bar_fingerprint,
            action, reason_codes, reference_experiment_id,
            reference_engine_sha256, execution_capability,
            order_execution_enabled, payload_sha256, payload
        ) values (
            %s, %s, %s, %s,
            %s, %s::jsonb, %s,
            %s, %s, %s, %s, %s::jsonb
        )
        on conflict (decision_id) do nothing
        returning id
        """,
        (
            payload["decision_id"],
            payload["observed_at"],
            payload["symbol"],
            payload["closed_bar_fingerprint"],
            payload["action"],
            json.dumps(payload["reason_codes"], separators=(",", ":")),
            payload["reference_experiment_id"],
            payload["reference_engine_sha256"],
            payload["execution_capability"],
            payload["order_execution_enabled"],
            payload_hash,
            _canonical(payload),
        ),
    ).fetchone()
    return 1 if result is not None else 0


def _insert_candidate_operator_snapshot(
    conn: psycopg.Connection,
    payload: Mapping[str, Any],
) -> int:
    validate_candidate_operator_snapshot(payload)
    decision = payload["decision"]
    runtime = payload["runtime"]
    virtual_position = payload["virtual_position"]
    outcome = payload["outcome"]
    safety = payload["safety"]
    payload_hash = _payload_sha256(payload)
    result = conn.execute(
        """
        insert into cand001_operator_snapshots (
            generated_at, schema_version, core_version, candidate_id,
            config_fingerprint, decision_action, decision_id,
            last_bar_id, last_bar_close_time, freshness_seconds, health_state,
            virtual_status, outcome_id, outcome_net_r, snapshot_fingerprint,
            execution_capability, order_execution_enabled, payload_sha256, payload
        ) values (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s::jsonb
        )
        on conflict (snapshot_fingerprint) do nothing
        returning id
        """,
        (
            payload["generated_at"],
            payload["schema_version"],
            payload["core_version"],
            payload["candidate_id"],
            payload["config_fingerprint"],
            decision["action"],
            decision["decision_id"],
            runtime.get("last_bar_id"),
            runtime.get("last_bar_close_time"),
            runtime.get("freshness_seconds"),
            runtime.get("health_state"),
            virtual_position.get("status"),
            outcome.get("outcome_id"),
            outcome.get("net_r"),
            payload["snapshot_fingerprint"],
            safety["execution_capability"],
            safety["order_execution_enabled"],
            payload_hash,
            _canonical(payload),
        ),
    ).fetchone()
    return 1 if result is not None else 0


def export_once(*, state_dir: Path, database_url: str) -> tuple[int, int, int]:
    heartbeat_path = state_dir / "heartbeat.json"
    bundle_path = state_dir / "latest_bundle.json"
    candidate_operator_path = state_dir / "candidate_operator_snapshot.json"
    if not heartbeat_path.exists():
        raise FileNotFoundError(f"heartbeat missing: {heartbeat_path}")
    if not bundle_path.exists():
        raise FileNotFoundError(f"latest bundle missing: {bundle_path}")

    heartbeat = read_json_object(heartbeat_path)
    bundle_payload = read_json_object(bundle_path)
    decision_items = _load_decision_outbox(state_dir)
    candidate_operator = (
        read_json_object(candidate_operator_path)
        if candidate_operator_path.exists()
        else None
    )
    if candidate_operator is not None:
        validate_candidate_operator_snapshot(candidate_operator)

    with psycopg.connect(database_url, connect_timeout=15) as conn:
        with conn.transaction():
            heartbeats_inserted = _insert_heartbeat(conn, heartbeat)
            bars_inserted = _insert_bars(conn, bundle_payload)
            decisions_inserted = sum(
                _insert_decision(conn, payload) for _, payload in decision_items
            )
            if candidate_operator is not None:
                _insert_candidate_operator_snapshot(conn, candidate_operator)

        # The transaction has committed. Removing a staged file is now only an
        # acknowledgement. A crash before unlink is harmless: the next export
        # retries and UNIQUE(decision_id) makes the database write idempotent.
        for path, _ in decision_items:
            path.unlink()

    # Preserve the established public return contract for existing callers.
    return heartbeats_inserted, bars_inserted, decisions_inserted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=".runtime/mt5_shadow")
    args = parser.parse_args()

    database_url = os.environ.get("NEON_DATABASE_URL")
    if not database_url:
        raise SystemExit("NEON_DATABASE_URL is not configured")

    heartbeats, bars, decisions = export_once(
        state_dir=Path(args.state_dir).resolve(),
        database_url=database_url,
    )
    print(
        "MT5 SHADOW telemetry export OK | "
        f"heartbeats_inserted={heartbeats} | bars_inserted={bars} | "
        f"decisions_inserted={decisions} | candidate_operator_snapshot=OPTIONAL | "
        "execution_capability=NONE | order_execution_enabled=false"
    )


if __name__ == "__main__":
    main()
