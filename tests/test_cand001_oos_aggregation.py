from dataclasses import replace
from datetime import date, datetime, time, timedelta

import pandas as pd
import pytest

from daxlab.research.cand001_oos_aggregation import (
    CAND001_OOS_AGGREGATION_SCHEMA,
    aggregate_cand001_oos,
)
from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
    run_cand001_oos_measurements,
)
from daxlab.runtime.decision import stable_fingerprint


DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"


def _session(days: int = 70) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    index: list[pd.Timestamp] = []
    start = date(2014, 1, 1)
    for day_index in range(days):
        day = start + timedelta(days=day_index)
        for bar_index in range(4):
            stamp = datetime.combine(day, time(9, 0)) + timedelta(minutes=5 * bar_index)
            index.append(pd.Timestamp(stamp, tz="Europe/Berlin"))
            rows.append({"open": 100.0, "high": 100.2, "low": 99.8, "close": 100.0})
    return pd.DataFrame(rows, index=pd.DatetimeIndex(index, name="timestamp"))


def _measurement(
    window: int,
    cost_model: str,
    multiplier: float,
    *,
    net_r: float,
    profit_factor: float | None,
    completed_trades: int,
    max_drawdown_r: float,
    open_trade: bool = False,
) -> Cand001OosMeasurement:
    seed = {"window": window, "cost": cost_model}
    return Cand001OosMeasurement(
        window_number=window,
        window_fingerprint=stable_fingerprint({"window": window}),
        oos_start=f"2014-03-{window:02d}",
        oos_end=f"2014-03-{window + 1:02d}",
        cost_model=cost_model,
        cost_multiplier=multiplier,
        fill_model_fingerprint=stable_fingerprint({"fill": cost_model}),
        replay_report_fingerprint=stable_fingerprint({"replay": seed}),
        result_fingerprint=stable_fingerprint({"result": seed}),
        processed_bars=20,
        processed_sessions=1,
        directional_signals=completed_trades,
        admitted_trades=completed_trades,
        completed_trades=completed_trades,
        open_trade_at_end=open_trade,
        gross_r=net_r + 0.2 * completed_trades,
        cost_r=0.2 * completed_trades,
        net_r=net_r,
        average_net_r=None if completed_trades == 0 else net_r / completed_trades,
        median_net_r=None if completed_trades == 0 else net_r / completed_trades,
        profit_factor=profit_factor,
        max_drawdown_r=max_drawdown_r,
        trade_records_fingerprint=stable_fingerprint({"trades": seed}),
    )


def _bundle() -> Cand001OosMeasurementBundle:
    specs = {
        "normal": (1.0, ((2.0, 2.0), (-1.0, 0.5), (0.0, None))),
        "stress_1.5x": (1.5, ((1.5, 1.75), (-1.2, 0.4), (0.0, None))),
        "stress_2x": (2.0, ((1.0, 1.5), (-1.4, 0.3), (0.0, None))),
    }
    measurements: list[Cand001OosMeasurement] = []
    for cost_model, (multiplier, windows) in specs.items():
        for number, (net_r, pf) in enumerate(windows, start=1):
            measurements.append(
                _measurement(
                    number,
                    cost_model,
                    multiplier,
                    net_r=net_r,
                    profit_factor=pf,
                    completed_trades=0 if number == 3 else 2,
                    max_drawdown_r=float(number),
                    open_trade=(number == 3 and cost_model == "normal"),
                )
            )
    return Cand001OosMeasurementBundle(
        schema_version="DAXLAB_CAND001_OOS_WF_MEASUREMENT_V1",
        dataset_fingerprint=DATASET_SHA,
        contract_fingerprint="a" * 64,
        candidate_id="CAND-001",
        config_fingerprint="b" * 64,
        source_session_days=105,
        window_count=3,
        cost_model_count=3,
        measurement_count=9,
        measurements=tuple(measurements),
        bundle_fingerprint="c" * 64,
    )


def test_aggregation_over_runner_null_case_is_deterministic_and_non_executable() -> None:
    measured = run_cand001_oos_measurements(_session(), dataset_fingerprint=DATASET_SHA)

    first = aggregate_cand001_oos(measured)
    second = aggregate_cand001_oos(measured)

    assert first == second
    assert first.schema_version == CAND001_OOS_AGGREGATION_SCHEMA
    assert first.window_count == 1
    assert len(first.cost_summaries) == 3
    assert len(first.degradations) == 2
    assert all(summary.completed_trades == 0 for summary in first.cost_summaries)
    assert all(summary.total_net_r == 0.0 for summary in first.cost_summaries)
    assert first.execution_capability == "NONE"
    assert first.order_execution_enabled is False


def test_cost_summary_and_degradation_math_are_explicit() -> None:
    result = aggregate_cand001_oos(_bundle())
    normal, stress_15, stress_2 = result.cost_summaries

    assert normal.cost_model == "normal"
    assert normal.total_net_r == pytest.approx(1.0)
    assert normal.completed_trades == 4
    assert (normal.positive_windows, normal.negative_windows, normal.flat_windows) == (1, 1, 1)
    assert normal.median_window_net_r == pytest.approx(0.0)
    assert normal.median_defined_window_profit_factor == pytest.approx(1.25)
    assert normal.aggregate_profit_factor_complete is True
    assert normal.aggregate_profit_factor == pytest.approx(1.25)
    assert normal.worst_window_number == 2
    assert normal.worst_window_net_r == pytest.approx(-1.0)
    assert normal.max_window_drawdown_r == pytest.approx(3.0)
    assert normal.open_trade_at_end_windows == 1

    assert stress_15.total_net_r == pytest.approx(0.3)
    assert stress_15.aggregate_profit_factor == pytest.approx(1.075)
    assert stress_2.total_net_r == pytest.approx(-0.4)
    assert stress_2.aggregate_profit_factor == pytest.approx(0.9)

    first_degradation, second_degradation = result.degradations
    assert (first_degradation.from_multiplier, first_degradation.to_multiplier) == (1.0, 1.5)
    assert first_degradation.delta_total_net_r == pytest.approx(-0.7)
    assert (second_degradation.from_multiplier, second_degradation.to_multiplier) == (1.5, 2.0)
    assert second_degradation.delta_total_net_r == pytest.approx(-0.7)


def test_pf_one_zero_net_window_is_marked_incomplete_not_invented() -> None:
    bundle = _bundle()
    changed = list(bundle.measurements)
    changed[0] = replace(changed[0], net_r=0.0, profit_factor=1.0)
    modified = replace(bundle, measurements=tuple(changed))

    result = aggregate_cand001_oos(modified)
    normal = result.cost_summaries[0]

    assert normal.aggregate_profit_factor_complete is False
    assert normal.aggregate_profit_factor is None


def test_full_source_payload_is_bound_even_if_old_result_id_is_left_in_place() -> None:
    original_bundle = _bundle()
    original = aggregate_cand001_oos(original_bundle)

    changed = list(original_bundle.measurements)
    changed[0] = replace(changed[0], max_drawdown_r=999.0)
    tampered_payload_bundle = replace(original_bundle, measurements=tuple(changed))
    tampered = aggregate_cand001_oos(tampered_payload_bundle)

    assert changed[0].result_fingerprint == original_bundle.measurements[0].result_fingerprint
    assert tampered.source_payload_fingerprint != original.source_payload_fingerprint
    assert tampered.aggregation_fingerprint != original.aggregation_fingerprint


def test_aggregation_rejects_incomplete_cost_window_coverage() -> None:
    bundle = _bundle()
    changed = list(bundle.measurements)
    changed[0] = replace(changed[0], cost_model="other", cost_multiplier=0.5)
    modified = replace(bundle, measurements=tuple(changed), cost_model_count=4)

    with pytest.raises(ValueError, match="does not cover every OOS window"):
        aggregate_cand001_oos(modified)
