import pytest

from daxlab.runtime.checkpoint import ReplayCheckpoint
from daxlab.runtime.restart_reconcile import reconcile_restart_freshness


def _checkpoint(last_event_time_iso: str | None) -> ReplayCheckpoint:
    return ReplayCheckpoint(
        run_manifest_fingerprint="run",
        processed_candles=103,
        last_event_time_iso=last_event_time_iso,
        decision_log_fingerprint="decisions",
    )


def test_same_closed_bar_is_safe_without_gap() -> None:
    result = reconcile_restart_freshness(
        _checkpoint("2026-09-10T09:00:00+00:00"),
        latest_closed_bar_time_iso="2026-09-10T09:00:00+00:00",
    )
    assert result.safe_to_resume is True
    assert result.replay_gap_detected is False
    assert result.gap_seconds == 0.0
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_newer_closed_bar_reports_replay_gap() -> None:
    result = reconcile_restart_freshness(
        _checkpoint("2026-09-10T09:00:00+00:00"),
        latest_closed_bar_time_iso="2026-09-10T09:10:00+00:00",
    )
    assert result.safe_to_resume is True
    assert result.replay_gap_detected is True
    assert result.gap_seconds == 600.0


def test_timeline_regression_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="precedes checkpoint timeline"):
        reconcile_restart_freshness(
            _checkpoint("2026-09-10T09:10:00+00:00"),
            latest_closed_bar_time_iso="2026-09-10T09:05:00+00:00",
        )


def test_missing_checkpoint_time_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="last_event_time_iso missing"):
        reconcile_restart_freshness(
            _checkpoint(None), latest_closed_bar_time_iso="2026-09-10T09:05:00+00:00"
        )


def test_naive_time_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="timezone-aware"):
        reconcile_restart_freshness(
            _checkpoint("2026-09-10T09:00:00"),
            latest_closed_bar_time_iso="2026-09-10T09:05:00+00:00",
        )
