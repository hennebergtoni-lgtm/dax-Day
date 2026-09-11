import pytest

from daxlab.runtime.candidate_sizing import (
    CAND001_SIMULATION_SIZING_POLICY_VERSION,
    Cand001SimulationSizingPolicy,
    QuantitySemantic,
)


def test_cand001_default_size_is_one_normalized_simulation_unit() -> None:
    policy = Cand001SimulationSizingPolicy()

    assert policy.policy_version == CAND001_SIMULATION_SIZING_POLICY_VERSION
    assert policy.quantity == 1.0
    assert policy.quantity_semantic is QuantitySemantic.NORMALIZED_SIMULATION_UNIT
    assert policy.broker_volume_semantics is False
    assert policy.account_risk_semantics is False


def test_cand001_sizing_policy_is_deterministic() -> None:
    first = Cand001SimulationSizingPolicy()
    second = Cand001SimulationSizingPolicy()

    assert first == second
    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", 0.5),
        ("quantity", 2.0),
        ("quantity_semantic", "BROKER_LOTS"),
        ("broker_volume_semantics", True),
        ("account_risk_semantics", True),
        ("policy_version", "OTHER"),
    ],
)
def test_cand001_sizing_policy_rejects_noncanonical_semantics(field, value) -> None:
    with pytest.raises(ValueError):
        Cand001SimulationSizingPolicy(**{field: value})


def test_sizing_policy_is_not_a_broker_or_account_risk_formula() -> None:
    policy = Cand001SimulationSizingPolicy()

    assert policy.broker_volume_semantics is False
    assert policy.account_risk_semantics is False
