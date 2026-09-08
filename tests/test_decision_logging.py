from datetime import datetime, timezone

import pytest

from daxlab.runtime.decision import DecisionRecord, FinalAction, stable_fingerprint


def test_config_fingerprint_is_order_independent_and_deterministic():
    assert stable_fingerprint({"a": 1, "b": 2}) == stable_fingerprint({"b": 2, "a": 1})


def test_no_trade_is_a_first_class_logged_decision():
    event_time = datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc)
    kwargs = dict(
        event_time=event_time,
        data_fingerprint="data",
        regime="UNKNOWN",
        structure="NONE",
        setup="NONE",
        filter_results={"data_safe": False},
        blockers=("DATA_UNSAFE",),
        risk_result="BLOCKED",
        config={"risk": 0.5},
        core_version="core-v1",
        final_action=FinalAction.NO_TRADE,
    )
    left = DecisionRecord.build(**kwargs)
    right = DecisionRecord.build(**kwargs)
    assert left.decision_id == right.decision_id
    assert left.final_action is FinalAction.NO_TRADE
    assert left.blockers == ("DATA_UNSAFE",)


def test_blocker_cannot_produce_trade():
    with pytest.raises(ValueError, match="blocked decision"):
        DecisionRecord.build(
            event_time=datetime(2026, 1, 2, 9, 0, tzinfo=timezone.utc),
            data_fingerprint="data",
            regime="KNOWN",
            structure="ORB",
            setup="breakout",
            filter_results={},
            blockers=("DATA_UNSAFE",),
            risk_result="ALLOWED",
            config={},
            core_version="core-v1",
            final_action=FinalAction.TRADE,
        )
