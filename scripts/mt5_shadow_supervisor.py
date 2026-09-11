#!/usr/bin/env python3
"""Continuous credential-free Windows MT5 read-only SHADOW supervisor.

This script has no order API. It reuses the existing `mt5_windows_probe.collect_probe`
function, persists provenance-bound legacy SHADOW resume/heartbeat state plus a small
Decision outbox, and runs CAND-001 only behind the same GREEN read-only host/cross-cycle
gates. Windows Task Scheduler remains the process restart owner.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import signal
import threading
from typing import Any, Iterable, Mapping

from mt5_windows_probe import collect_probe

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.candidate_shadow_host_cycle import run_cand001_shadow_host_cycle
from daxlab.runtime.candidate_virtual_outcome import Cand001VirtualOutcomeEvidence
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.mt5_heartbeat_history import archive_heartbeat_snapshot
from daxlab.runtime.mt5_shadow_integration import mt5_shadow_resume_payload
from daxlab.runtime.mt5_shadow_supervisor import (
    load_mt5_resume_payload,
    process_mt5_shadow_cycle,
    supervisor_error_heartbeat,
    supervisor_stopped_heartbeat,
    with_history_archive_status,
)
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.paper_contracts import ExecutionIntent
from daxlab.runtime.shadow_observation import ShadowDecision
from daxlab.runtime.single_instance import SingleInstanceLock

_IDENTITY = "DAXLAB_MT5_SHADOW_SUPERVISOR_V1"


def _load_resume(path: Path):
    if not path.exists():
        return None
    return load_mt5_resume_payload(read_json_object(path))


def _load_previous_bundle(path: Path):
    if not path.exists():
        return None
    return read_json_object(path)


def _load_candidate_checkpoint(path: Path) -> Mapping[str, Any] | None:
    if not path.exists():
        return None
    return read_json_object(path)


def _decision_payload(decision: ShadowDecision) -> dict[str, Any]:
    if decision.action != "NO_ORDER":
        raise ValueError("SHADOW Decision outbox accepts NO_ORDER only")
    payload = asdict(decision)
    payload["reason_codes"] = list(decision.reason_codes)
    payload["execution_capability"] = "NONE"
    payload["order_execution_enabled"] = False
    return payload


def _intent_payload(intent: ExecutionIntent) -> dict[str, Any]:
    return {
        "schema_version": intent.schema_version,
        "decision_id": intent.decision_id,
        "run_manifest_fingerprint": intent.run_manifest_fingerprint,
        "created_at": intent.created_at.isoformat(),
        "symbol": intent.symbol,
        "side": intent.side.value,
        "quantity": intent.quantity,
        "requested_price": intent.requested_price,
        "stop_price": intent.stop_price,
        "target_price": intent.target_price,
        "client_order_id": intent.client_order_id,
        "evidence_state": "SHADOW_SIMULATION_INTENT",
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def _outcome_payload(outcome: Cand001VirtualOutcomeEvidence) -> dict[str, Any]:
    return {
        "schema_version": outcome.schema_version,
        "cost_semantics_version": outcome.cost_semantics_version,
        "outcome_id": outcome.outcome_id,
        "lifecycle_id": outcome.lifecycle_id,
        "decision_id": outcome.decision_id,
        "fill_model_fingerprint": outcome.fill_model_fingerprint,
        "closed_at": outcome.closed_at.isoformat(),
        "exit_reason": outcome.exit_reason.value,
        "side": outcome.side.value,
        "filled_price": outcome.filled_price,
        "exit_price": outcome.exit_price,
        "planned_risk_points": outcome.planned_risk_points,
        "gross_points": outcome.gross_points,
        "configured_cost_points": outcome.configured_cost_points,
        "gross_r": outcome.gross_r,
        "cost_r": outcome.cost_r,
        "net_r": outcome.net_r,
        "dated_outcome": outcome.dated_outcome.to_payload(),
        "execution_capability": outcome.execution_capability,
        "order_execution_enabled": outcome.order_execution_enabled,
    }


def _manifest_payload(manifest: RunManifest) -> dict[str, Any]:
    return {
        "dataset_fingerprint": manifest.dataset_fingerprint,
        "engine_fingerprint": manifest.engine_fingerprint,
        "config_fingerprint": manifest.config_fingerprint,
        "mode": manifest.mode.value,
        "manifest_fingerprint": manifest.manifest_fingerprint,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def _persist_decision_outbox(
    outbox_dir: Path,
    decisions: Iterable[ShadowDecision],
) -> int:
    """Atomically stage deterministic Decisions before resume state can advance."""
    items = tuple(decisions)
    if not items:
        return 0
    outbox_dir.mkdir(parents=True, exist_ok=True)
    for decision in items:
        atomic_write_json(
            outbox_dir / f"{decision.decision_id}.json",
            _decision_payload(decision),
        )
    return len(items)


def _persist_candidate_publications(
    *,
    intent_outbox_dir: Path,
    outcome_outbox_dir: Path,
    intents: Iterable[ExecutionIntent],
    outcomes: Iterable[Cand001VirtualOutcomeEvidence],
) -> tuple[int, int]:
    intent_items = tuple(intents)
    outcome_items = tuple(outcomes)
    if intent_items:
        intent_outbox_dir.mkdir(parents=True, exist_ok=True)
        for intent in intent_items:
            atomic_write_json(
                intent_outbox_dir / f"{intent.client_order_id}.json",
                _intent_payload(intent),
            )
    if outcome_items:
        outcome_outbox_dir.mkdir(parents=True, exist_ok=True)
        for outcome in outcome_items:
            atomic_write_json(
                outcome_outbox_dir / f"{outcome.outcome_id}.json",
                _outcome_payload(outcome),
            )
    return len(intent_items), len(outcome_items)


def _persist_heartbeat(
    heartbeat_path: Path,
    history_dir: Path,
    heartbeat: Mapping[str, Any],
    *,
    max_history_entries: int,
) -> dict[str, Any]:
    """Persist current heartbeat and best-effort bounded history with visible status."""
    archived = with_history_archive_status(heartbeat, archived=True)
    try:
        archive_heartbeat_snapshot(
            history_dir,
            archived,
            max_entries=max_history_entries,
        )
    except Exception:
        current = with_history_archive_status(heartbeat, archived=False)
        atomic_write_json(heartbeat_path, current)
        return current
    atomic_write_json(heartbeat_path, archived)
    return archived


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="DE40")
    parser.add_argument("--bars", type=int, default=20)
    parser.add_argument("--max-age-seconds", type=float, default=600.0)
    parser.add_argument("--broker-timezone", required=True)
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    parser.add_argument("--state-dir", default=".runtime/mt5_shadow")
    parser.add_argument("--heartbeat-history-max-entries", type=int, default=2000)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    if args.interval_seconds < 1.0:
        raise SystemExit("--interval-seconds must be >= 1")
    if args.bars < 2:
        raise SystemExit("--bars must be >= 2")
    if args.heartbeat_history_max_entries < 1:
        raise SystemExit("--heartbeat-history-max-entries must be >= 1")

    state_dir = Path(args.state_dir).resolve()
    heartbeat_path = state_dir / "heartbeat.json"
    heartbeat_history_dir = state_dir / "heartbeat_history"
    decision_outbox_dir = state_dir / "decision_outbox"
    resume_path = state_dir / "resume.json"
    latest_bundle_path = state_dir / "latest_bundle.json"
    rejected_bundle_path = state_dir / "rejected_bundle.json"
    candidate_checkpoint_path = state_dir / "candidate_checkpoint.json"
    candidate_manifest_path = state_dir / "candidate_manifest.json"
    candidate_operator_snapshot_path = state_dir / "candidate_operator_snapshot.json"
    candidate_intent_outbox_dir = state_dir / "candidate_intent_outbox"
    candidate_outcome_outbox_dir = state_dir / "candidate_outcome_outbox"
    lock_path = state_dir / "supervisor.lock"
    state_dir.mkdir(parents=True, exist_ok=True)

    stop = threading.Event()

    def request_stop(signum, frame) -> None:
        del signum, frame
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    lock = SingleInstanceLock(path=lock_path, identity=_IDENTITY)
    try:
        lock.acquire()
    except Exception:
        # A losing second instance must never overwrite the legitimate owner's
        # shared heartbeat, history, resume state, or Decision/Candidate evidence.
        return 4

    try:
        try:
            resume_state = _load_resume(resume_path)
            previous_bundle_payload = _load_previous_bundle(latest_bundle_path)
            candidate_checkpoint = _load_candidate_checkpoint(candidate_checkpoint_path)
        except Exception:
            _persist_heartbeat(
                heartbeat_path,
                heartbeat_history_dir,
                supervisor_error_heartbeat(error_code="RESUME_OR_BUNDLE_STATE_INVALID"),
                max_history_entries=args.heartbeat_history_max_entries,
            )
            return 3

        while not stop.is_set():
            try:
                bundle_payload = collect_probe(
                    configured_symbol=args.symbol,
                    bars=args.bars,
                    max_age_seconds=args.max_age_seconds,
                    broker_timezone=args.broker_timezone,
                )
                cycle = process_mt5_shadow_cycle(
                    bundle_payload,
                    resume_state=resume_state,
                    single_instance_lock_held=lock.held,
                    previous_bundle_payload=previous_bundle_payload,
                )

                if cycle.heartbeat.get("cross_cycle_status") == "BLOCKED":
                    atomic_write_json(rejected_bundle_path, bundle_payload)
                else:
                    atomic_write_json(latest_bundle_path, bundle_payload)
                    previous_bundle_payload = bundle_payload
                    if rejected_bundle_path.exists():
                        rejected_bundle_path.unlink()

                # Durably stage legacy Decision evidence before advancing resume.
                _persist_decision_outbox(decision_outbox_dir, cycle.decisions)

                # CAND-001 is a subordinate observer of the same validated host cycle.
                # It cannot run when legacy/cross-cycle safety is not GREEN.
                if cycle.heartbeat.get("status") == "GREEN" and cycle.heartbeat.get(
                    "cross_cycle_status"
                ) != "BLOCKED":
                    candidate_cycle = run_cand001_shadow_host_cycle(
                        parse_windows_mt5_bundle(bundle_payload),
                        single_instance_lock_held=lock.held,
                        checkpoint_payload=candidate_checkpoint,
                    )
                    # Publication evidence is staged first. If the process crashes
                    # before checkpoint advancement, deterministic filenames make a
                    # replay overwrite the same evidence rather than lose it.
                    _persist_candidate_publications(
                        intent_outbox_dir=candidate_intent_outbox_dir,
                        outcome_outbox_dir=candidate_outcome_outbox_dir,
                        intents=candidate_cycle.intents_to_publish,
                        outcomes=candidate_cycle.outcomes_to_publish,
                    )
                    atomic_write_json(
                        candidate_manifest_path,
                        _manifest_payload(candidate_cycle.manifest),
                    )
                    atomic_write_json(
                        candidate_checkpoint_path,
                        candidate_cycle.checkpoint_payload,
                    )
                    candidate_checkpoint = candidate_cycle.checkpoint_payload
                    if candidate_cycle.latest_operator_snapshot is not None:
                        atomic_write_json(
                            candidate_operator_snapshot_path,
                            candidate_cycle.latest_operator_snapshot.as_dict(),
                        )

                if cycle.resume_state is not None:
                    resume_state = cycle.resume_state
                    atomic_write_json(resume_path, mt5_shadow_resume_payload(resume_state))
                _persist_heartbeat(
                    heartbeat_path,
                    heartbeat_history_dir,
                    cycle.heartbeat,
                    max_history_entries=args.heartbeat_history_max_entries,
                )
            except Exception:
                _persist_heartbeat(
                    heartbeat_path,
                    heartbeat_history_dir,
                    supervisor_error_heartbeat(error_code="PROBE_OR_CYCLE_FAILED"),
                    max_history_entries=args.heartbeat_history_max_entries,
                )
                if args.once:
                    return 2

            if args.once:
                return 0
            stop.wait(args.interval_seconds)
    finally:
        lock.release()
        if stop.is_set():
            _persist_heartbeat(
                heartbeat_path,
                heartbeat_history_dir,
                supervisor_stopped_heartbeat(),
                max_history_entries=args.heartbeat_history_max_entries,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
