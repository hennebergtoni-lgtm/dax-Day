import pytest

from daxlab.runtime.contracts import DataQualityState
from daxlab.runtime.decision import FinalAction
from daxlab.runtime.gates import RuntimeSafetySnapshot, evaluate_runtime_safety


def snapshot(**overrides):
    values = {
        "data_quality": DataQualityState.OK,
        "feed_connected": True,
        "spread": 0.2,
        "max_spread": 1.0,
        "contradictory_state": False,
    }
    values.update(overrides)
    return RuntimeSafetySnapshot(**values)


def test_safe_runtime_allows_requested_trade():
    gate = evaluate_runtime_safety(snapshot())
    assert gate.allowed is True
    assert gate.blockers == ()
    assert gate.guard_action(FinalAction.TRADE) is FinalAction.TRADE


@pytest.mark.parametrize(
    "quality",
    [
        DataQualityState.STALE,
        DataQualityState.GAP,
        DataQualityState.DUPLICATE,
        DataQualityState.OUT_OF_ORDER,
        DataQualityState.CLOCK_SKEW,
        DataQualityState.SOURCE_DISAGREEMENT,
        DataQualityState.UNSAFE,
    ],
)
def test_every_unsafe_data_state_forces_no_trade(quality):
    gate = evaluate_runtime_safety(snapshot(data_quality=quality))
    assert gate.allowed is False
    assert "DATA_UNSAFE" in gate.blockers
    assert gate.guard_action(FinalAction.TRADE) is FinalAction.NO_TRADE


@pytest.mark.parametrize(
    ("overrides", "blocker"),
    [
        ({"feed_connected": False}, "FEED_INTERRUPTION"),
        ({"spread": 1.01}, "EXTREME_SPREAD"),
        ({"contradictory_state": True}, "CONTRADICTORY_STATE"),
    ],
)
def test_execution_failures_force_no_trade(overrides, blocker):
    gate = evaluate_runtime_safety(snapshot(**overrides))
    assert gate.allowed is False
    assert blocker in gate.blockers
    assert gate.guard_action(FinalAction.TRADE) is FinalAction.NO_TRADE


def test_multiple_failures_are_all_auditable():
    gate = evaluate_runtime_safety(
        snapshot(
            data_quality=DataQualityState.GAP,
            feed_connected=False,
            spread=2.0,
            contradictory_state=True,
        )
    )
    assert gate.blockers == (
        "DATA_UNSAFE",
        "FEED_INTERRUPTION",
        "EXTREME_SPREAD",
        "CONTRADICTORY_STATE",
    )
    assert gate.guard_action(FinalAction.TRADE) is FinalAction.NO_TRADE
