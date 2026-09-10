from datetime import datetime, timezone

import pytest

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_resume_anchor import (
    bars_after_resume_anchor,
    reconcile_shadow_resume_anchor,
)
from daxlab.runtime.shadow_soak import run_shadow_soak


def _bar(minute: int, close: float | None = None) -> Mt5Bar:
    value = float(100 + minute)
    return Mt5Bar(
        open_time=datetime(2026, 9, 10, 9, minute, tzinfo=timezone.utc),
        open=value,
        high=value + 2.0,
        low=value - 2.0,
        close=value + 1.0 if close is None else close,
    )


def test_fresh_start_returns_all_bars() -> None:
    bars = (_bar(0), _bar(5), _bar(10))
    result = reconcile_shadow_resume_anchor(bars, checkpoint=None)
    assert result.fresh_start is True
    assert result.catchup_bar_count == 3
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False
    assert bars_after_resume_anchor(bars, result=result) == bars


def test_empty_fresh_start_is_safe() -> None:
    result = reconcile_shadow_resume_anchor((), checkpoint=None)
    assert result.fresh_start is True
    assert result.feed_bar_count == 0
    assert result.catchup_bar_count == 0
    assert bars_after_resume_anchor((), result=result) == ()


def test_unique_anchor_mid_feed_returns_only_following_bars() -> None:
    prior = (_bar(0), _bar(5))
    checkpoint = run_shadow_soak(prior).checkpoint
    feed = (_bar(0), _bar(5), _bar(10), _bar(15))
    result = reconcile_shadow_resume_anchor(feed, checkpoint=checkpoint)
    assert result.fresh_start is False
    assert result.anchor_index == 1
    assert result.catchup_bar_count == 2
    assert bars_after_resume_anchor(feed, result=result) == (_bar(10), _bar(15))


def test_anchor_at_end_has_zero_catchup() -> None:
    bars = (_bar(0), _bar(5))
    checkpoint = run_shadow_soak(bars).checkpoint
    result = reconcile_shadow_resume_anchor(bars, checkpoint=checkpoint)
    assert result.anchor_index == 1
    assert result.catchup_bar_count == 0
    assert bars_after_resume_anchor(bars, result=result) == ()


def test_missing_anchor_fails_closed() -> None:
    checkpoint = run_shadow_soak((_bar(0), _bar(5))).checkpoint
    with pytest.raises(RuntimeError, match="anchor not found"):
        reconcile_shadow_resume_anchor((_bar(10), _bar(15)), checkpoint=checkpoint)


def test_duplicate_anchor_fails_closed() -> None:
    anchor_bar = _bar(5)
    checkpoint = run_shadow_soak((_bar(0), anchor_bar)).checkpoint
    with pytest.raises(RuntimeError, match="strictly chronological"):
        reconcile_shadow_resume_anchor((anchor_bar, anchor_bar, _bar(10)), checkpoint=checkpoint)


def test_feed_change_after_reconcile_fails_closed() -> None:
    bars = (_bar(0), _bar(5), _bar(10))
    checkpoint = run_shadow_soak((_bar(0), _bar(5))).checkpoint
    result = reconcile_shadow_resume_anchor(bars, checkpoint=checkpoint)
    changed = (_bar(0), _bar(5), _bar(10, close=999.0))
    with pytest.raises(RuntimeError, match="feed changed"):
        bars_after_resume_anchor(changed, result=result)


def test_unsorted_feed_fails_closed() -> None:
    checkpoint = run_shadow_soak((_bar(0), _bar(5))).checkpoint
    with pytest.raises(RuntimeError, match="strictly chronological"):
        reconcile_shadow_resume_anchor((_bar(5), _bar(0), _bar(10)), checkpoint=checkpoint)


def test_naive_bar_time_fails_closed() -> None:
    aware = _bar(0)
    naive = Mt5Bar(
        open_time=datetime(2026, 9, 10, 9, 5),
        open=105.0,
        high=107.0,
        low=103.0,
        close=106.0,
    )
    with pytest.raises(RuntimeError, match="timezone-aware"):
        reconcile_shadow_resume_anchor((aware, naive), checkpoint=None)


def test_report_is_deterministic() -> None:
    bars = (_bar(0), _bar(5), _bar(10))
    checkpoint = run_shadow_soak((_bar(0), _bar(5))).checkpoint
    first = reconcile_shadow_resume_anchor(bars, checkpoint=checkpoint)
    second = reconcile_shadow_resume_anchor(bars, checkpoint=checkpoint)
    assert first == second
    assert first.report_sha256 == second.report_sha256
