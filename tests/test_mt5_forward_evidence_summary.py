import pytest

from daxlab.runtime.mt5_forward_evidence_summary import summarize_forward_evidence
from daxlab.runtime.mt5_gap_diagnostic import GapDiagnosticReport


def _heartbeat(status: str = "GREEN", **overrides):
    payload = {
        "status": status,
        "blockers": [],
        "processed_total": 3,
        "new_decisions": 1,
        "duplicates_suppressed": 2,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    payload.update(overrides)
    return payload


def test_green_only_summary() -> None:
    summary = summarize_forward_evidence([_heartbeat(), _heartbeat(processed_total=5)])
    assert summary.status == "GREEN_ONLY"
    assert summary.heartbeat_count == 2
    assert summary.green_count == 2
    assert summary.max_processed_total == 5
    assert summary.total_new_decisions == 2
    assert summary.total_duplicates_suppressed == 4
    assert summary.blocker_counts == ()
    assert summary.execution_capability == "NONE"
    assert summary.order_execution_enabled is False


def test_blocked_heartbeat_is_aggregated() -> None:
    summary = summarize_forward_evidence([
        _heartbeat(),
        _heartbeat(status="BLOCKED", blockers=["HISTORICAL_BAR_MUTATION"], new_decisions=0),
    ])
    assert summary.status == "BLOCKED_PRESENT"
    assert summary.blocked_count == 1
    assert summary.blocker_counts == (("HISTORICAL_BAR_MUTATION", 1),)


def test_error_has_priority() -> None:
    summary = summarize_forward_evidence([
        _heartbeat(status="BLOCKED", blockers=["X"], new_decisions=0),
        _heartbeat(status="ERROR", blockers=["PROBE_OR_CYCLE_FAILED"], processed_total=None, new_decisions=0),
    ])
    assert summary.status == "ERROR_PRESENT"
    assert summary.error_count == 1


def test_gap_review_required_is_visible() -> None:
    report = GapDiagnosticReport(
        status="DIAGNOSTIC_ONLY",
        gaps=(),
        auto_accepted_gap_count=0,
        requires_human_review=True,
    )
    summary = summarize_forward_evidence([_heartbeat()], gap_reports=[report])
    assert summary.status == "REVIEW_REQUIRED"
    assert summary.gap_reports_with_review_required == 1


def test_no_evidence_summary() -> None:
    summary = summarize_forward_evidence([])
    assert summary.status == "NO_EVIDENCE"
    assert summary.heartbeat_count == 0


def test_credential_key_is_rejected() -> None:
    heartbeat = _heartbeat()
    heartbeat["password"] = "never"
    with pytest.raises(ValueError, match="forbidden evidence key"):
        summarize_forward_evidence([heartbeat])


def test_order_capability_is_rejected() -> None:
    with pytest.raises(ValueError, match="execution_capability"):
        summarize_forward_evidence([_heartbeat(execution_capability="PAPER")])
    with pytest.raises(ValueError, match="order_execution_enabled"):
        summarize_forward_evidence([_heartbeat(order_execution_enabled=True)])


def test_invalid_counters_fail_closed() -> None:
    with pytest.raises(ValueError, match="decision counters"):
        summarize_forward_evidence([_heartbeat(new_decisions=-1)])
