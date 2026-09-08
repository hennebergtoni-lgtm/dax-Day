from datetime import datetime, timedelta, timezone

import pytest

from daxlab.research.fibonacci_retracement import (
    CausalImpulseAnchor,
    in_zone,
    normalized_retracement,
    retracement_levels,
    validate_retracement_observation,
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


def _anchor() -> CausalImpulseAnchor:
    base = datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc)
    return CausalImpulseAnchor(
        rule_id="CONFIRMED_BREAKOUT_IMPULSE",
        start_price=100.0,
        start_time=base,
        end_price=160.0,
        end_time=base + timedelta(minutes=10),
        confirmation_time=base + timedelta(minutes=15),
    )


def test_causal_anchor_accepts_observation_after_confirmation_before_entry():
    anchor = _anchor()
    validate_retracement_observation(
        anchor,
        observation_time=anchor.confirmation_time + timedelta(minutes=5),
        entry_time=anchor.confirmation_time + timedelta(minutes=10),
    )


def test_causal_anchor_rejects_unknown_rule():
    base = datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="unknown Fibonacci anchor rule"):
        CausalImpulseAnchor(
            rule_id="BEST_SWING_AFTER_THE_FACT",
            start_price=100.0,
            start_time=base,
            end_price=160.0,
            end_time=base + timedelta(minutes=5),
            confirmation_time=base + timedelta(minutes=10),
        )


def test_causal_anchor_rejects_backdated_confirmation_ordering():
    base = datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="invalid Fibonacci anchor timestamp ordering"):
        CausalImpulseAnchor(
            rule_id="STRUCTURE_CONFIRMED_IMPULSE",
            start_price=100.0,
            start_time=base,
            end_price=160.0,
            end_time=base + timedelta(minutes=10),
            confirmation_time=base + timedelta(minutes=5),
        )


def test_causal_anchor_rejects_naive_timestamps():
    base = datetime(2026, 9, 8, 9, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        CausalImpulseAnchor(
            rule_id="OR_COMPLETED_IMPULSE",
            start_price=100.0,
            start_time=base,
            end_price=160.0,
            end_time=base + timedelta(minutes=5),
            confirmation_time=base + timedelta(minutes=10),
        )


def test_observation_must_follow_confirmation():
    anchor = _anchor()
    with pytest.raises(ValueError, match="must follow anchor confirmation"):
        validate_retracement_observation(
            anchor,
            observation_time=anchor.confirmation_time,
        )


def test_observation_cannot_be_after_entry():
    anchor = _anchor()
    with pytest.raises(ValueError, match="cannot occur after entry"):
        validate_retracement_observation(
            anchor,
            observation_time=anchor.confirmation_time + timedelta(minutes=10),
            entry_time=anchor.confirmation_time + timedelta(minutes=5),
        )
