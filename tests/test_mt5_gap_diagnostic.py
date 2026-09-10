from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.mt5_gap_diagnostic import diagnose_m5_gaps
from daxlab.runtime.mt5_readonly import Mt5Bar


def _bar(ts: datetime, price: float = 25000.0) -> Mt5Bar:
    return Mt5Bar(open_time=ts, open=price, high=price + 2, low=price - 2, close=price + 1)


def test_no_gap_sequence_reports_no_gaps() -> None:
    start = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    bars = [_bar(start + timedelta(minutes=5 * i)) for i in range(4)]
    report = diagnose_m5_gaps(bars)
    assert report.status == "NO_GAPS"
    assert report.gaps == ()
    assert report.auto_accepted_gap_count == 0
    assert report.requires_human_review is False
    assert report.execution_capability == "NONE"
    assert report.order_execution_enabled is False


def test_larger_gap_is_diagnostic_only_and_never_auto_accepted() -> None:
    start = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    report = diagnose_m5_gaps([_bar(start), _bar(start + timedelta(minutes=20))])
    assert report.status == "DIAGNOSTIC_ONLY"
    assert len(report.gaps) == 1
    gap = report.gaps[0]
    assert gap.delta_seconds == 1200
    assert gap.missing_m5_intervals == 3
    assert gap.classification == "UNVERIFIED_SESSION_GAP"
    assert report.auto_accepted_gap_count == 0
    assert report.requires_human_review is True


def test_non_m5_aligned_gap_fails_closed() -> None:
    start = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="non-M5-aligned"):
        diagnose_m5_gaps([_bar(start), _bar(start + timedelta(minutes=7))])


def test_time_regression_fails_closed() -> None:
    start = datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="strictly increasing"):
        diagnose_m5_gaps([_bar(start), _bar(start - timedelta(minutes=5))])


def test_naive_timestamp_fails_closed() -> None:
    naive = datetime(2026, 9, 10, 8, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        diagnose_m5_gaps([_bar(naive)])
