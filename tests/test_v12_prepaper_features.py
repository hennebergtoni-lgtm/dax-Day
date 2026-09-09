from __future__ import annotations

from dataclasses import replace

import pytest

from daxlab.research.v12_prepaper_features import (
    ClosedBar,
    adx_feature,
    body_quality,
    comp001_atr14,
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
    comp001_before = comp001_atr14(bars, asof)
    adx_before = adx_feature(bars, asof, period=14)

    mutated = list(bars)
    for idx in range(asof + 1, len(mutated)):
        mutated[idx] = replace(mutated[idx], open=9999.0, high=10001.0, low=9998.0, close=10000.0)

    assert body_quality(mutated, asof) == body_before
    assert range_compression(mutated, asof, lookback=14) == compression_before
    assert comp001_atr14(mutated, asof) == comp001_before
    assert adx_feature(mutated, asof, period=14) == adx_before


def test_features_are_deterministic() -> None:
    bars = _bars()
    assert body_quality(bars, 20) == body_quality(bars, 20)
    assert range_compression(bars, 20) == range_compression(bars, 20)
    assert comp001_atr14(bars, 20) == comp001_atr14(bars, 20)
    assert adx_feature(bars, 35) == adx_feature(bars, 35)
    assert retest_staleness(breakout_index=10, asof_index=15) == 5


def test_warmup_fails_closed() -> None:
    bars = _bars(20)
    assert range_compression(bars, 5, lookback=14) is None
    assert comp001_atr14(bars, 13) is None
    assert adx_feature(bars, 19, period=14) is None


def test_comp001_uses_fixed_recent_three_over_wilder_atr14() -> None:
    bars = _bars(20)
    feature = comp001_atr14(bars, 14)
    assert feature is not None

    trs: list[float] = []
    for idx in range(1, 15):
        current = bars[idx]
        previous = bars[idx - 1]
        trs.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )

    expected_atr14 = sum(trs) / 14
    expected_recent = sum(trs[-3:]) / 3
    assert feature.atr14 == pytest.approx(expected_atr14)
    assert feature.recent_tr_mean_3 == pytest.approx(expected_recent)
    assert feature.ratio == pytest.approx(expected_recent / expected_atr14)


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
