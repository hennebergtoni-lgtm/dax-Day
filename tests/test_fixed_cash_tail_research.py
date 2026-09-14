from __future__ import annotations

from math import inf, nan
import random

import pytest

from daxlab.research.boost001 import (
    FixedCashResearchConfig, SleeveConfig, fixed_cash_tail_research,
    resample_indices, simulate_fixed_cash,
)
from daxlab.research.failure_analysis import trade_sequence_dna


@pytest.mark.parametrize("value", [nan, inf, -inf, True, "100", 10**1000])
@pytest.mark.parametrize("field", ["initial_capital", "cash_risk", "capital_floor"])
def test_fixed_cash_nonfinite_or_wrong_type_rejects(field, value):
    args = dict(initial_capital=100, cash_risk=10, capital_floor=0, horizon_trades=3)
    args[field] = value
    with pytest.raises(ValueError):
        FixedCashResearchConfig(**args)


@pytest.mark.parametrize("field", ["initial_capital", "risk_fraction", "max_eur_risk", "ruin_floor"])
def test_existing_sleeve_config_nonfinite_rejects(field):
    with pytest.raises(ValueError):
        SleeveConfig(**{field: nan})


def test_cash_hand_calculation_floor_and_risk_never_exceeds_fixed_baseline():
    config = FixedCashResearchConfig(100, 10, 85, 4)
    result = simulate_fixed_cash([-1, -1, -2, 100], config)
    assert result["cash_risks"] == (10, 5)
    assert result["final_capital"] == 85
    assert result["floor_hit"] is True
    assert result["max_cash_drawdown"] == 15
    assert result["trades_observed"] == 2


def test_cash_loss_below_one_r_is_not_clamped_or_disguised():
    result = simulate_fixed_cash([-20], FixedCashResearchConfig(100, 10, 0, 1))
    assert result["final_capital"] == -100
    assert result["floor_hit"]
    assert result["max_cash_drawdown"] == 200


def test_exact_horizon_and_finite_return_required():
    config = FixedCashResearchConfig(100, 10, 0, 2)
    for values in ([1], [1, nan], [True, 1]):
        with pytest.raises(ValueError):
            simulate_fixed_cash(values, config)


@pytest.mark.parametrize("mode", ["SESSION_BLOCK", "CLUSTER_BLOCK", "REGIME_RUN"])
def test_sampling_preserves_each_contiguous_unit_and_marks_terminal_censoring(mode):
    class FirstUnit:
        def choice(self, units):
            return units[0]
    indices, censored = resample_indices(5, horizon=3, mode=mode, block_length=1,
                                         labels=["a", "a", "b", "b", "b"], rng=FirstUnit())
    assert indices == (0, 1, 0)
    assert censored is True


def test_circular_block_keeps_order_wrap_and_terminal_censoring():
    class LastStart:
        def randrange(self, size):
            return size - 1
    indices, censored = resample_indices(5, horizon=4, mode="CIRCULAR_BLOCK",
                                         block_length=3, labels=None, rng=LastStart())
    assert indices == (4, 0, 1, 4)
    assert censored


@pytest.mark.parametrize("mode", ["SESSION_BLOCK", "CLUSTER_BLOCK"])
def test_noncontiguous_session_cluster_cannot_be_merged(mode):
    with pytest.raises(ValueError):
        resample_indices(3, horizon=3, mode=mode, block_length=1,
                         labels=["a", "b", "a"], rng=random.Random(0))


def test_regime_runs_can_recur_without_claiming_transition_preservation():
    config = FixedCashResearchConfig(100, 2, 10, 4)
    result = fixed_cash_tail_research([1, -1, 1], [0.1] * 3, config,
                                     source_sha256="a" * 64, paths=5, mode="REGIME_RUN",
                                     labels=["up", "down", "up"])
    assert result["regime_transition_probabilities_preserved"] is False


@pytest.mark.parametrize("mode", ["IID", "CIRCULAR_BLOCK", "SESSION_BLOCK", "CLUSTER_BLOCK", "REGIME_RUN"])
def test_seed_provenance_and_cost_stresses_are_deterministic(mode):
    config = FixedCashResearchConfig(100, 2, 10, 6)
    kwargs = dict(source_sha256="a" * 64, paths=20, mode=mode, seed=9,
                  block_length=2, labels=["a", "a", "b", "b"])
    result = fixed_cash_tail_research([1, -1, 2, -2], [0.1] * 4, config, **kwargs)
    assert result == fixed_cash_tail_research([1, -1, 2, -2], [0.1] * 4, config, **kwargs)
    stressed = [result["cost_stresses"][str(f)]["final_capital"]["median"] for f in (1.0, 1.5, 2.0)]
    assert stressed == sorted(stressed, reverse=True)
    other = fixed_cash_tail_research([1, -1, 2, -2], [0.1] * 4, config, **{**kwargs, "seed": 10})
    assert result["identity_sha256"] != other["identity_sha256"]
    assert result["execution_capability"] == "NONE"


@pytest.mark.parametrize("change", [
    {"source_sha256": "missing"}, {"paths": True}, {"paths": 0},
    {"mode": "magic"}, {"block_length": 5}, {"seed": True},
])
def test_missing_identity_and_invalid_or_unbounded_work_reject(change):
    kwargs = dict(source_sha256="a" * 64, paths=2, mode="IID", seed=0, block_length=1)
    kwargs.update(change)
    with pytest.raises(ValueError):
        fixed_cash_tail_research([1, -1], [0.1, 0.1],
                                 FixedCashResearchConfig(100, 2, 0, 4), **kwargs)


def test_gross_cost_alignment_and_no_fabricated_costs():
    config = FixedCashResearchConfig(100, 2, 0, 2)
    for gross, costs in (([], []), ([1], []), ([1], [-0.1]), ([nan], [0.1])):
        with pytest.raises(ValueError):
            fixed_cash_tail_research(gross, costs, config, source_sha256="a" * 64, paths=1)


def test_drawdown_recovery_and_open_episode_are_hand_calculated():
    result = trade_sequence_dna([2, -1, -2, 3, -1])
    assert result["drawdown_episodes"] == [
        {"start_boundary": 1, "recovery_boundary": 4, "duration_trades": 3,
         "depth_r": 3.0, "right_censored": False},
        {"start_boundary": 4, "recovery_boundary": None, "duration_trades": 1,
         "depth_r": 1.0, "right_censored": True},
    ]
    assert result["max_loss_streak"] == 2
    assert result["underwater_trade_boundaries"] == 3
    assert result["max_drawdown_r"] == 3


def test_negative_net_profit_has_no_misleading_concentration_share():
    result = trade_sequence_dna([2, -3, -1])
    assert result["net_profit_concentration_share"] is None
    assert result["top_winner_removal"]["1"]["gross_profit_share"] == 1
    assert result["top_winner_removal"]["1"]["net_r_after_removal"] == -4


def test_empty_sample_and_causal_finite_validation():
    assert trade_sequence_dna([])["inference_state"] == "INSUFFICIENT_SAMPLE"
    with pytest.raises(ValueError):
        trade_sequence_dna([nan])
