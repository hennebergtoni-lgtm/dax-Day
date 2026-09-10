"""Fail-closed restart reconciliation for replay/SHADOW runtime freshness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from daxlab.runtime.checkpoint import ReplayCheckpoint


@dataclass(frozen=True, slots=True)
class RestartReconcileResult:
    checkpoint_time_iso: str
    latest_closed_bar_time_iso: str
    gap_seconds: float
    replay_gap_detected: bool
    safe_to_resume: bool
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def _parse_aware(value: str, *, field: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeError(f"{field} must be timezone-aware")
    return parsed


def reconcile_restart_freshness(
    checkpoint: ReplayCheckpoint,
    *,
    latest_closed_bar_time_iso: str,
) -> RestartReconcileResult:
    """Compare persisted progress with the latest known closed bar.

    A latest bar older than the checkpoint indicates timeline regression/corruption and fails
    closed. A later latest bar is a replay gap that must be handled explicitly by the caller;
    this function never skips bars or authorizes execution.
    """
    if not checkpoint.last_event_time_iso:
        raise RuntimeError("checkpoint last_event_time_iso missing")

    checkpoint_time = _parse_aware(
        checkpoint.last_event_time_iso, field="checkpoint last_event_time_iso"
    )
    latest_time = _parse_aware(
        latest_closed_bar_time_iso, field="latest_closed_bar_time_iso"
    )
    gap_seconds = (latest_time - checkpoint_time).total_seconds()
    if gap_seconds < 0:
        raise RuntimeError("latest closed bar precedes checkpoint timeline")

    return RestartReconcileResult(
        checkpoint_time_iso=checkpoint_time.isoformat(),
        latest_closed_bar_time_iso=latest_time.isoformat(),
        gap_seconds=gap_seconds,
        replay_gap_detected=gap_seconds > 0,
        safe_to_resume=True,
    )
