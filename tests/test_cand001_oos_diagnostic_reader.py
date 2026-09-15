import json

import pytest

from daxlab.research.cand001_oos_aggregation import aggregate_cand001_oos
from daxlab.research.cand001_oos_cost_consistency import audit_cand001_oos_cost_consistency
from daxlab.research.cand001_oos_diagnostic_evidence import (
    DIAGNOSTIC_FILENAME,
    write_cand001_oos_diagnostic_evidence,
)
from daxlab.research.cand001_oos_diagnostic_reader import (
    load_cand001_oos_diagnostic_evidence,
)
from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
)
from daxlab.research.cand001_oos_stability import build_cand001_oos_stability_diagnostics
from daxlab.runtime.decision import stable_fingerprint


DATASET_SHA = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"


def _measurement(
    window: int,
    cost_model: str,
    multiplier: float,
    *,
    gross_r: float,
    completed_trades: int,
) -> Cand001OosMeasurement:
    base_cost = 0.10 if completed_trades else 0.0
    cost_r = base_cost * multiplier
    net_r = gross_r - cost_r
    seed = {"window": window, "cost": cost_model}
    if completed_trades == 0:
        profit_factor = None
    elif net_r > 0:
        profit_factor = None
    elif net_r < 0:
        profit_factor = 0.0
    else:
        profit_factor = 1.0
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
        profit_factor=profit_factor,
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
            measurements.append(
                _measurement(
                    window,
                    cost_model,
                    multiplier,
                    gross_r=gross_r,
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


def _write(tmp_path):
    bundle = _bundle()
    aggregation = aggregate_cand001_oos(bundle)
    cost = audit_cand001_oos_cost_consistency(bundle, aggregation)
    stability = build_cand001_oos_stability_diagnostics(bundle, aggregation, cost)
    path = tmp_path / DIAGNOSTIC_FILENAME
    written = write_cand001_oos_diagnostic_evidence(
        path,
        bundle,
        aggregation,
        cost,
        stability,
    )
    return path, bundle, aggregation, written


def test_reader_round_trips_only_canonical_diagnostic_evidence(tmp_path) -> None:
    path, bundle, aggregation, written = _write(tmp_path)

    verified = load_cand001_oos_diagnostic_evidence(
        path,
        measurement=bundle,
        aggregation=aggregation,
    )

    assert verified.evidence == written
    assert verified.execution_capability == "NONE"
    assert verified.order_execution_enabled is False
    assert len(verified.verification_fingerprint) == 64


@pytest.mark.parametrize(
    ("mutation", "match"),
    (
        (lambda payload: payload.__setitem__("unknown_field", True), "field mismatch"),
        (lambda payload: payload.pop("economic_claim"), "field mismatch"),
        (
            lambda payload: payload["stability"]["cost_reports"][0].__setitem__(
                "total_net_r", 999.0
            ),
            "does not match recomputed canonical evidence",
        ),
        (
            lambda payload: payload.__setitem__("artifact_fingerprint", "0" * 64),
            "does not match recomputed canonical evidence",
        ),
        (
            lambda payload: payload.__setitem__("order_execution_enabled", True),
            "does not match recomputed canonical evidence",
        ),
    ),
)
def test_reader_rejects_schema_metric_fingerprint_and_safety_tampering(
    tmp_path,
    mutation,
    match,
) -> None:
    path, bundle, aggregation, _ = _write(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutation(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match=match):
        load_cand001_oos_diagnostic_evidence(
            path,
            measurement=bundle,
            aggregation=aggregation,
        )


def test_reader_requires_fixed_filename(tmp_path) -> None:
    path, bundle, aggregation, _ = _write(tmp_path)
    wrong = tmp_path / "copied.json"
    wrong.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(ValueError, match="diagnostic filename"):
        load_cand001_oos_diagnostic_evidence(
            wrong,
            measurement=bundle,
            aggregation=aggregation,
        )
