from daxlab.contracts import REFERENCE_COSTS, REFERENCE_WF
from daxlab.reference.v11_2 import V11_2, assert_reference_invariants


def test_v11_2_reference_invariants() -> None:
    assert_reference_invariants()
    assert V11_2.oos_trades == 1384
    assert V11_2.oos_return_r == -68.1095
    assert V11_2.raw_m5_rows == 481824
    assert V11_2.m5_session_bars == 172319
    assert V11_2.m5_bars_per_day == 103
    assert (
        V11_2.dataset_session_ohlc_sha256
        == "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
    )


def test_walk_forward_contract_is_frozen() -> None:
    assert (REFERENCE_WF.train_days, REFERENCE_WF.oos_days, REFERENCE_WF.step_days) == (45, 20, 20)


def test_cost_stress_contract() -> None:
    assert [(c.name, c.multiplier) for c in REFERENCE_COSTS] == [
        ("normal", 1.0),
        ("stress_1.5x", 1.5),
        ("stress_2x", 2.0),
    ]
