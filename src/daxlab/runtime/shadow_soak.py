"""Deterministic multi-bar SHADOW soak runner for synthetic/offline evidence only.

This module has no broker dependency and no order capability. It exercises the
observation, duplicate-suppression, checkpoint and recovery surfaces over longer
closed-M5 sequences before a real Windows MT5 host is available.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_observation import (
    ShadowDecision,
    ShadowObservationInput,
    build_shadow_decision,
)

_EVIDENCE_STATE = "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"
_CHECKPOINT_SCHEMA = "DAXLAB_SHADOW_SOAK_CHECKPOINT_V1"
_RESULT_SCHEMA = "DAXLAB_SHADOW_SOAK_RESULT_V1"


@dataclass(frozen=True, slots=True)
class SoakFault:
    host_read_only_healthy: bool = True
    feed_fresh: bool = True
    clock_ok: bool = True
    single_instance_lock_held: bool = True


@dataclass(frozen=True, slots=True)
class SoakCheckpoint:
    schema_version: str
    processed_count: int
    last_bar_fingerprint: str | None
    seen_decision_ids: tuple[str, ...]
    payload_sha256: str


@dataclass(frozen=True, slots=True)
class SoakResult:
    schema_version: str
    evidence_state: str
    symbol: str
    decisions: tuple[ShadowDecision, ...]
    processed: int
    blocked: int
    duplicates_suppressed: int
    run_fingerprint: str
    checkpoint: SoakCheckpoint
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def bar_fingerprint(bar: Mt5Bar) -> str:
    return _hash(
        {
            "open_time": bar.open_time.isoformat(),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
        }
    )


def initial_soak_checkpoint() -> SoakCheckpoint:
    return _checkpoint(0, None, ())


def verify_soak_checkpoint(checkpoint: SoakCheckpoint) -> None:
    if checkpoint.schema_version != _CHECKPOINT_SCHEMA:
        raise ValueError("shadow soak checkpoint schema mismatch")
    if checkpoint.processed_count < 0:
        raise ValueError("shadow soak checkpoint processed_count invalid")
    if checkpoint.last_bar_fingerprint is not None:
        _require_sha(checkpoint.last_bar_fingerprint, "last_bar_fingerprint")
    if len(set(checkpoint.seen_decision_ids)) != len(checkpoint.seen_decision_ids):
        raise ValueError("shadow soak checkpoint contains duplicate decision IDs")
    for value in checkpoint.seen_decision_ids:
        _require_sha(value, "seen_decision_id")
    expected = _checkpoint_hash(
        checkpoint.processed_count,
        checkpoint.last_bar_fingerprint,
        checkpoint.seen_decision_ids,
    )
    if checkpoint.payload_sha256 != expected:
        raise ValueError("shadow soak checkpoint hash mismatch")


def run_shadow_soak(
    bars: Iterable[Mt5Bar],
    *,
    symbol: str = "DE40",
    checkpoint: SoakCheckpoint | None = None,
    faults: Mapping[int, SoakFault] | None = None,
) -> SoakResult:
    if not symbol.strip():
        raise ValueError("symbol must be non-empty")
    state = checkpoint or initial_soak_checkpoint()
    verify_soak_checkpoint(state)

    seen = set(state.seen_decision_ids)
    decisions: list[ShadowDecision] = []
    duplicates = 0
    last_bar_fingerprint = state.last_bar_fingerprint
    ordered = tuple(bars)
    fault_map = faults or {}

    for index, bar in enumerate(ordered):
        if bar.open_time.tzinfo is None:
            raise ValueError("shadow soak bars must be timezone-aware")
        fingerprint = bar_fingerprint(bar)
        fault = fault_map.get(index, SoakFault())
        observed_at = bar.open_time + timedelta(minutes=5, seconds=1)
        observation = ShadowObservationInput(
            observed_at=observed_at,
            symbol=symbol,
            closed_bar_fingerprint=fingerprint,
            host_read_only_healthy=fault.host_read_only_healthy,
            feed_fresh=fault.feed_fresh,
            clock_ok=fault.clock_ok,
            single_instance_lock_held=fault.single_instance_lock_held,
        )
        decision = build_shadow_decision(observation)
        if decision.action != "NO_ORDER":
            raise RuntimeError("shadow soak emitted order-capable action")
        if decision.decision_id in seen:
            duplicates += 1
            continue
        seen.add(decision.decision_id)
        decisions.append(decision)
        last_bar_fingerprint = fingerprint

    processed = state.processed_count + len(decisions)
    checkpoint_out = _checkpoint(processed, last_bar_fingerprint, tuple(sorted(seen)))
    blocked = sum(
        item.reason_codes != ("OBSERVATION_ONLY_NO_ORDER",) for item in decisions
    )
    run_fingerprint = _hash(
        {
            "prior_processed": state.processed_count,
            "decision_ids": [item.decision_id for item in decisions],
            "checkpoint_sha256": checkpoint_out.payload_sha256,
        }
    )
    return SoakResult(
        schema_version=_RESULT_SCHEMA,
        evidence_state=_EVIDENCE_STATE,
        symbol=symbol,
        decisions=tuple(decisions),
        processed=processed,
        blocked=blocked,
        duplicates_suppressed=duplicates,
        run_fingerprint=run_fingerprint,
        checkpoint=checkpoint_out,
    )


def soak_summary(result: SoakResult) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "evidence_state": result.evidence_state,
        "symbol": result.symbol,
        "processed": result.processed,
        "blocked": result.blocked,
        "duplicates_suppressed": result.duplicates_suppressed,
        "run_fingerprint": result.run_fingerprint,
        "checkpoint_sha256": result.checkpoint.payload_sha256,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def soak_recovery_payload(result: SoakResult) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "DAXLAB_SHADOW_SOAK_RECOVERY_V1",
        "evidence_state": _EVIDENCE_STATE,
        "checkpoint": asdict(result.checkpoint),
        "decision_ids": [item.decision_id for item in result.decisions],
        "run_fingerprint": result.run_fingerprint,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    payload["payload_sha256"] = _hash(payload)
    return payload


def verify_soak_recovery_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != "DAXLAB_SHADOW_SOAK_RECOVERY_V1":
        raise ValueError("shadow soak recovery schema mismatch")
    if payload.get("evidence_state") != _EVIDENCE_STATE:
        raise ValueError("shadow soak evidence state mismatch")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("shadow soak recovery execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("shadow soak recovery must keep execution disabled")
    expected = payload.get("payload_sha256")
    if not isinstance(expected, str):
        raise ValueError("shadow soak recovery hash missing")
    unhashed = dict(payload)
    unhashed.pop("payload_sha256", None)
    if _hash(unhashed) != expected:
        raise ValueError("shadow soak recovery hash mismatch")
    checkpoint_raw = payload.get("checkpoint")
    if not isinstance(checkpoint_raw, Mapping):
        raise ValueError("shadow soak checkpoint missing")
    verify_soak_checkpoint(SoakCheckpoint(**checkpoint_raw))


def _checkpoint(
    processed_count: int,
    last_bar_fingerprint: str | None,
    seen_decision_ids: tuple[str, ...],
) -> SoakCheckpoint:
    return SoakCheckpoint(
        schema_version=_CHECKPOINT_SCHEMA,
        processed_count=processed_count,
        last_bar_fingerprint=last_bar_fingerprint,
        seen_decision_ids=seen_decision_ids,
        payload_sha256=_checkpoint_hash(
            processed_count,
            last_bar_fingerprint,
            seen_decision_ids,
        ),
    )


def _checkpoint_hash(
    processed_count: int,
    last_bar_fingerprint: str | None,
    seen_decision_ids: tuple[str, ...],
) -> str:
    return _hash(
        {
            "schema_version": _CHECKPOINT_SCHEMA,
            "processed_count": processed_count,
            "last_bar_fingerprint": last_bar_fingerprint,
            "seen_decision_ids": list(seen_decision_ids),
        }
    )


def _require_sha(value: str, field: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    int(value, 16)


def _hash(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
