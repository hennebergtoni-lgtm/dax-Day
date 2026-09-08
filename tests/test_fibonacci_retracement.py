import pytest

from daxlab.research.fibonacci_retracement import (
    in_zone,
    normalized_retracement,
    retracement_levels,
)


def test_long_impulse_levels_are_measured_back_from_end():
    levels = retracement_levels(100.0, 160.0)
    assert levels.direction == "long"
    assert levels.r50 == pytest.approx(130.0)
    assert levels.r618 == pytest.approx(122.92)


def test_short_impulse_levels_are_symmetric():
    levels = retracement_levels(160.0, 100.0)
    assert levels.direction == "short"
    assert levels.r50 == pytest.approx(130.0)
    assert levels.r618 == pytest.approx(137.08)


def test_normalized_retracement_is_direction_agnostic():
    assert normalized_retracement(100, 160, 130) == pytest.approx(0.5)
    assert normalized_retracement(160, 100, 130) == pytest.approx(0.5)


def test_zero_impulse_is_rejected():
    with pytest.raises(ValueError):
        retracement_levels(100, 100)


def test_zone_check_is_order_independent():
    assert in_zone(0.5, 0.382, 0.618)
    assert in_zone(0.5, 0.618, 0.382)
