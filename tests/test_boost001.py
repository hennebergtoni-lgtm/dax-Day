from daxlab.research.boost001 import (
    SleeveConfig,
    bootstrap_ruin_probability,
    simulate_sleeve,
)


def test_losses_do_not_trigger_risk_escalation() -> None:
    result = simulate_sleeve(
        [-1.0, -1.0, -1.0],
        SleeveConfig(initial_capital=200.0, risk_fraction=0.10, max_eur_risk=50.0),
    )
    risks = [step.euro_risk for step in result.steps]
    assert risks == [20.0, 18.0, 16.2]


def test_euro_cap_bounds_risk() -> None:
    result = simulate_sleeve(
        [1.0, 1.0],
        SleeveConfig(initial_capital=200.0, risk_fraction=0.50, max_eur_risk=15.0),
    )
    assert all(step.euro_risk <= 15.0 for step in result.steps)


def test_bootstrap_ruin_probability_is_seed_deterministic() -> None:
    config = SleeveConfig(
        initial_capital=200.0,
        risk_fraction=0.25,
        max_eur_risk=50.0,
        ruin_floor=20.0,
    )
    outcomes = [-1.0, -1.0, -1.0, 1.5]
    first = bootstrap_ruin_probability(
        outcomes, config, paths=200, trades_per_path=20, seed=7
    )
    second = bootstrap_ruin_probability(
        outcomes, config, paths=200, trades_per_path=20, seed=7
    )
    assert first == second
    assert 0.0 <= first <= 1.0


def test_booster_simulation_does_not_modify_signal_sequence() -> None:
    outcomes = [-1.0, 1.5, 0.0, 2.0]
    preserved = list(outcomes)
    simulate_sleeve(outcomes, SleeveConfig())
    assert outcomes == preserved
