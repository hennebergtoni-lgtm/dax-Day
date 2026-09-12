from dataclasses import replace

import pytest

from daxlab.research.cand001_oos_aggregation import aggregate_cand001_oos
from daxlab.research.cand001_oos_cost_consistency import (
    CostConsistencyState,
    audit_cand001_oos_cost_consistency,
)
from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
)
from daxlab.research.cand001_oos_stability import (
    CAND001_OOS_STABILITY_SCHEMA,
    build_cand001_oos_stability_diagnostics,
)
from daxlab.runtime.decision import stable_fingerprint


DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"


def _measurement(
    window: int,
    cost_model: str,
    multiplier: float,
    *,
    gross_r: float,
    cost_r: float,
    completed_trades: int,
) -> Cand001OosMeasurement:
    net_r = gross_r - cost_r
    if completed_trades == 0:
        pf = None
    elif net_r > 0:
        pf = None
    elif net_r < 0:
        pf = 0.0
    else:
        pf = 1.0
    seed = {"window": window, "cost": cost_model}
    return Cand001OosMeasurement(
        window_number=window,
        window_fingerprint=stable_fingerprint({"window": window}),
        oos_start=f"2014-01-{window:02d}",
        oos_end=f"2014-01-{window + 1:02d}",
        cost_model=cost_model,
        cost_multiplier=multiplier,
        fill_model_fingerprint=stable_fingerprint({"fill": cost_model}),
        replay_report_fingerprint=stable_fingerprint({"replay": seed}),
        result_fingerprint=stable_fingerprint({"result": seed}),
        processed_bars=2060,
        processed_sessions=20,
        directional_signals=completed_trades,
        admitted_trades=completed_trades,
        completed_trades=completed_trades,
        open_trade_at_end=False,
        gross_r=gross_r,
        cost_r=cost_r,
        net_r=net_r,
        average_net_r=None if completed_trades == 0 else net_r / completed_trades,
        median_net_r=None if completed_trades == 0 else net_r / completed_trades,
        profit_factor=pf,
        max_drawdown_r=max(0.0, -net_r),
        trade_records_fingerprint=stable_fingerprint({"trades": seed}),
    )


def _bundle() -> Cand001OosMeasurementBundle:
    gross = (1.1, -1.9, -0.9, 0.0)
    completed = (1, 1, 1, 0)
    measurements: list[Cand001OosMeasurement] = []
    for cost_model, multiplier in (
        ("normal", 1.0),
        ("stress_1.5x", 1.5),
        ("stress_2x", 2.0),
    ):
        for window, (gross_r, count) in enumerate(zip(gross, completed, strict=True), start=1):
            base_cost = 0.10 if count else 0.0
            measurements.append(
                _measurement(
                    window,
                    cost_model,
                    multiplier,
                    gross_r=gross_r,
                    cost_r=base_cost * multiplier,
                    completed_trades=count,
                )
            )
    return Cand001OosMeasurementBundle(
        schema_version="DAXLAB_CAND001_OOS_WF_MEASUREMENT_V1",
        dataset_fingerprint=DATASET_SHA,
        contract_fingerprint="a" * 64,
        candidate_id="CAND-001",
        config_fingerprint="b" * 64,
        source_session_days=125,
        window_count=4,
        cost_model_count=3,
        measurement_count=12,
        measurements=tuple(measurements),
        bundle_fingerprint="c" * 64,
    )


def _diagnostics(bundle: Cand001OosMeasurementBundle):
    aggregation = aggregate_cand001_oos(bundle)
    consistency = audit_cand001_oos_cost_consistency(bundle, aggregation)
    assert consistency.state is CostConsistencyState.PASS
    return build_cand001_oos_stability_diagnostics(bundle, aggregation, consistency)


def test_descriptive_stability_metrics_are_deterministic() -> None:
    bundle = _bundle()

    first = _diagnostics(bundle)
    second = _diagnostics(bundle)

    assert first == second
    assert first.schema_version == CAND001_OOS_STABILITY_SCHEMA
    assert first.descriptive_only is True
    assert first.composite_score is None
    assert first.automatic_promotion is False
    assert "PBO_DSR_NOT_APPLIED" in first.multiple_testing_policy
    assert first.execution_capability == "NONE"
    assert first.order_execution_enabled is False


def test_normal_cost_temporal_distribution_and_drawdown_are_explicit() -> None:
    result = _diagnostics(_bundle())
    normal = result.cost_reports[0]

    assert normal.cost_model == "normal"
    assert normal.total_net_r == pytest.approx(-2.0)
    assert normal.mean_window_net_r == pytest.approx(-0.5)
    assert normal.median_window_net_r == pytest.approx(-0.5)
    assert normal.positive_window_rate == pytest.approx(0.25)
    assert normal.negative_window_rate == pytest.approx(0.50)
    assert normal.flat_window_rate == pytest.approx(0.25)
    assert normal.zero_trade_windows == 1
    assert normal.mean_completed_trades_per_window == pytest.approx(0.75)
    assert normal.median_completed_trades_per_window == pytest.approx(1.0)
    assert normal.longest_positive_window_streak == 1
    assert normal.longest_negative_window_streak == 2
    assert normal.cumulative_window_net_r_max_drawdown == pytest.approx(3.0)
    assert normal.first_half_windows == 2
    assert normal.second_half_windows == 2
    assert normal.first_half_total_net_r == pytest.approx(-1.0)
    assert normal.second_half_total_net_r == pytest.approx(-1.0)
    assert normal.first_half_trades == 2
    assert normal.second_half_trades == 1
    assert normal.second_minus_first_mean_window_net_r == pytest.approx(0.0)
    assert normal.second_minus_first_trades_per_window == pytest.approx(-0.5)


def test_stability_requires_canonical_pass_cost_consistency() -> None:
    bundle = _bundle()
    aggregation = aggregate_cand001_oos(bundle)
    consistency = audit_cand001_oos_cost_consistency(bundle, aggregation)
    forged = replace(consistency, source_bundle_fingerprint="d" * 64)

    with pytest.raises(ValueError, match="not canonical"):
        build_cand001_oos_stability_diagnostics(bundle, aggregation, forged)


def test_stability_rejects_failed_cost_consistency() -> None:
    bundle = _bundle()
    changed = list(bundle.measurements)
    changed[4] = replace(changed[4], directional_signals=2)
    drifted = replace(bundle, measurements=tuple(changed))
    aggregation = aggregate_cand001_oos(drifted)
    consistency = audit_cand001_oos_cost_consistency(drifted, aggregation)
    assert consistency.state is CostConsistencyState.FAIL

    with pytest.raises(ValueError, match="requires PASS"):
        build_cand001_oos_stability_diagnostics(drifted, aggregation, consistency)
