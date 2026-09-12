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
from daxlab.runtime.decision import stable_fingerprint


DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"


def _measurement(
    cost_model: str,
    multiplier: float,
    *,
    cost_r: float,
    net_r: float,
    directional_signals: int = 1,
    gross_r: float = 1.0,
) -> Cand001OosMeasurement:
    return Cand001OosMeasurement(
        window_number=1,
        window_fingerprint="a" * 64,
        oos_start="2014-01-01",
        oos_end="2014-01-20",
        cost_model=cost_model,
        cost_multiplier=multiplier,
        fill_model_fingerprint=stable_fingerprint({"fill": cost_model}),
        replay_report_fingerprint=stable_fingerprint({"replay": cost_model}),
        result_fingerprint=stable_fingerprint({"result": cost_model}),
        processed_bars=2060,
        processed_sessions=20,
        directional_signals=directional_signals,
        admitted_trades=1,
        completed_trades=1,
        open_trade_at_end=False,
        gross_r=gross_r,
        cost_r=cost_r,
        net_r=net_r,
        average_net_r=net_r,
        median_net_r=net_r,
        profit_factor=None,
        max_drawdown_r=0.0,
        trade_records_fingerprint=stable_fingerprint({"trade": cost_model}),
    )


def _bundle() -> Cand001OosMeasurementBundle:
    measurements = (
        _measurement("normal", 1.0, cost_r=0.10, net_r=0.90),
        _measurement("stress_1.5x", 1.5, cost_r=0.15, net_r=0.85),
        _measurement("stress_2x", 2.0, cost_r=0.20, net_r=0.80),
    )
    return Cand001OosMeasurementBundle(
        schema_version="DAXLAB_CAND001_OOS_WF_MEASUREMENT_V1",
        dataset_fingerprint=DATASET_SHA,
        contract_fingerprint="b" * 64,
        candidate_id="CAND-001",
        config_fingerprint="c" * 64,
        source_session_days=65,
        window_count=1,
        cost_model_count=3,
        measurement_count=3,
        measurements=measurements,
        bundle_fingerprint="d" * 64,
    )


def _audit(bundle: Cand001OosMeasurementBundle):
    return audit_cand001_oos_cost_consistency(bundle, aggregate_cand001_oos(bundle))


def test_clean_cost_only_stress_passes_integrity_audit() -> None:
    result = _audit(_bundle())

    assert result.state is CostConsistencyState.PASS
    assert result.passed_windows == 1
    assert result.failed_windows == 0
    assert result.blockers == ()
    assert result.window_audits[0].state is CostConsistencyState.PASS
    assert "COST_DEPENDENT" in result.trade_record_identity_policy
    assert result.execution_capability == "NONE"
    assert result.order_execution_enabled is False


def test_signal_path_drift_is_integrity_failure() -> None:
    bundle = _bundle()
    changed = list(bundle.measurements)
    changed[1] = replace(changed[1], directional_signals=2)
    drifted = replace(bundle, measurements=tuple(changed))

    result = _audit(drifted)

    assert result.state is CostConsistencyState.FAIL
    assert "WINDOW_1:PATH_INVARIANT_DRIFT:directional_signals" in result.blockers


def test_gross_r_drift_is_integrity_failure() -> None:
    bundle = _bundle()
    changed = list(bundle.measurements)
    changed[2] = replace(changed[2], gross_r=1.1, net_r=0.9)
    drifted = replace(bundle, measurements=tuple(changed))

    result = _audit(drifted)

    assert result.state is CostConsistencyState.FAIL
    assert "WINDOW_1:PATH_INVARIANT_DRIFT:gross_r" in result.blockers


def test_cost_scaling_drift_is_integrity_failure_even_when_net_identity_holds() -> None:
    bundle = _bundle()
    changed = list(bundle.measurements)
    changed[1] = replace(changed[1], cost_r=0.17, net_r=0.83)
    drifted = replace(bundle, measurements=tuple(changed))

    result = _audit(drifted)

    assert result.state is CostConsistencyState.FAIL
    assert "WINDOW_1:COST_SCALING_DRIFT" in result.blockers


def test_net_r_identity_drift_is_integrity_failure() -> None:
    bundle = _bundle()
    changed = list(bundle.measurements)
    changed[1] = replace(changed[1], net_r=0.99)
    drifted = replace(bundle, measurements=tuple(changed))

    result = _audit(drifted)

    assert result.state is CostConsistencyState.FAIL
    assert "WINDOW_1:NET_R_IDENTITY_DRIFT:stress_1.5x" in result.blockers


def test_noncanonical_aggregation_is_rejected_before_interpretation() -> None:
    bundle = _bundle()
    aggregation = aggregate_cand001_oos(bundle)
    bad = replace(aggregation, source_bundle_fingerprint="e" * 64)

    with pytest.raises(ValueError, match="not the canonical result"):
        audit_cand001_oos_cost_consistency(bundle, bad)
