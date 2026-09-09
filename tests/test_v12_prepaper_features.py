from __future__ import annotations

from dataclasses import replace

import pytest

from daxlab.research.v12_prepaper_features import (
    ClosedBar,
    adx_feature,
    body_quality,
    range_compression,
    retest_staleness,
)


def _bars(count: int = 50) -> list[ClosedBar]:
    bars: list[ClosedBar] = []
    close = 100.0
    for idx in range(count):
        drift = 0.7 if idx % 4 != 0 else -0.2
        open_ = close
        close = open_ + drift
        bars.append(
            ClosedBar(
                open=open_,
                high=max(open_, close) + 0.4 + (idx % 3) * 0.1,
                low=min(open_, close) - 0.3,
                close=close,
            )
        )
    return bars


def test_future_bars_cannot_change_features_at_same_asof() -> None:
    bars = _bars()
    asof = 35
    body_before = body_quality(bars, asof)
    compression_before = range_compression(bars, asof, lookback=14)
    adx_before = adx_feature(bars, asof, period=14)

    mutated = list(bars)
    for idx in range(asof + 1, len(mutated)):
        mutated[idx] = replace(mutated[idx], open=9999.0, high=10001.0, low=9998.0, close=10000.0)

    assert body_quality(mutated, asof) == body_before
    assert range_compression(mutated, asof, lookback=14) == compression_before
    assert adx_feature(mutated, asof, period=14) == adx_before


def test_features_are_deterministic() -> None:
    bars = _bars()
    assert body_quality(bars, 20) == body_quality(bars, 20)
    assert range_compression(bars, 20) == range_compression(bars, 20)
    assert adx_feature(bars, 35) == adx_feature(bars, 35)
    assert retest_staleness(breakout_index=10, asof_index=15) == 5


def test_warmup_fails_closed() -> None:
    bars = _bars(20)
    assert range_compression(bars, 5, lookback=14) is None
    assert adx_feature(bars, 19, period=14) is None


def test_same_or_future_breakout_is_not_valid_staleness() -> None:
    assert retest_staleness(breakout_index=8, asof_index=8) is None
    assert retest_staleness(breakout_index=9, asof_index=8) is None


def test_invalid_asof_and_invalid_ohlc_fail_closed() -> None:
    bars = _bars(5)
    with pytest.raises(IndexError):
        body_quality(bars, 5)
    with pytest.raises(ValueError):
        ClosedBar(open=10.0, high=9.0, low=8.0, close=10.0)


def test_body_quality_is_bounded() -> None:
    feature = body_quality([ClosedBar(open=10, high=12, low=9, close=11.5)], 0)
    assert 0.0 <= feature.body_fraction <= 1.0
    assert 0.0 <= feature.close_location <= 1.0
    assert feature.direction == 1
