import pytest

from daxlab.research.failure_controls import (
    FAILURE_CONTROLS,
    GateCategory,
    control_for,
)


def test_every_fail001_control_has_a_technical_category():
    assert len(FAILURE_CONTROLS) == 16
    assert all(control.categories for control in FAILURE_CONTROLS)
    assert len({control.failure_id for control in FAILURE_CONTROLS}) == len(FAILURE_CONTROLS)


def test_data_failure_maps_to_hard_data_gate():
    control = control_for("data_quality")
    assert control.categories == (GateCategory.DATA_GATE,)
    assert control.safeguard == "UNSAFE_DATA_NO_TRADE"


def test_drift_cannot_be_a_self_optimization_control():
    control = control_for("STRATEGY_DRIFT")
    assert control.categories == (GateCategory.MONITORING_GATE,)
    assert "NO_SELF_OPTIMIZE" in control.safeguard


def test_unknown_failure_is_not_silently_accepted():
    with pytest.raises(KeyError):
        control_for("invented_failure")
