from dataclasses import replace
import json

import pytest

from daxlab.research.cand001_oos_aggregation import aggregate_cand001_oos
from daxlab.research.cand001_oos_cost_consistency import (
    CostConsistencyState,
    audit_cand001_oos_cost_consistency,
)
from daxlab.research.cand001_oos_diagnostic_evidence import (
    CAND001_OOS_DIAGNOSTIC_EVIDENCE_SCHEMA,
    DIAGNOSTIC_FILENAME,
    build_cand001_oos_diagnostic_evidence,
    write_cand001_oos_diagnostic_evidence,
)
from daxlab.research.cand001_oos_evidence_export import (
    AGGREGATION_FILENAME,
    MANIFEST_FILENAME,
    MEASUREMENTS_FILENAME,
    build_cand001_oos_evidence_payloads,
)
from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
)
from daxlab.research.cand001_oos_stability import (
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


def _sources():
    bundle = _bundle()
    aggregation = aggregate_cand001_oos(bundle)
    cost = audit_cand001_oos_cost_consistency(bundle, aggregation)
    assert cost.state is CostConsistencyState.PASS
    stability = build_cand001_oos_stability_diagnostics(bundle, aggregation, cost)
    return bundle, aggregation, cost, stability


def test_diagnostic_evidence_is_deterministic_and_bound_to_base_export() -> None:
    bundle, aggregation, cost, stability = _sources()
    base = build_cand001_oos_evidence_payloads(bundle, aggregation)

    first = build_cand001_oos_diagnostic_evidence(bundle, aggregation, cost, stability)
    second = build_cand001_oos_diagnostic_evidence(bundle, aggregation, cost, stability)

    assert first == second
    assert first.schema_version == CAND001_OOS_DIAGNOSTIC_EVIDENCE_SCHEMA
    assert first.source_measurement_bundle_fingerprint == bundle.bundle_fingerprint
    assert first.source_aggregation_fingerprint == aggregation.aggregation_fingerprint
    assert first.source_base_export_manifest_fingerprint == base.manifest.manifest_fingerprint
    assert first.source_cost_consistency_fingerprint == cost.audit_fingerprint
    assert first.source_stability_fingerprint == stability.diagnostics_fingerprint
    assert first.cost_consistency["state"] == "PASS"
    assert first.stability["descriptive_only"] is True
    assert first.stability["composite_score"] is None
    assert first.threshold_policy == "NO_COMPOSITE_SCORE_NO_PASS_THRESHOLD"
    assert first.automatic_promotion is False
    assert first.execution_capability == "NONE"
    assert first.order_execution_enabled is False


def test_diagnostic_evidence_rejects_noncanonical_cost_or_stability() -> None:
    bundle, aggregation, cost, stability = _sources()

    forged_cost = replace(cost, source_bundle_fingerprint="d" * 64)
    with pytest.raises(ValueError, match="cost-consistency evidence is not canonical"):
        build_cand001_oos_diagnostic_evidence(bundle, aggregation, forged_cost, stability)

    forged_stability = replace(stability, source_bundle_fingerprint="e" * 64)
    with pytest.raises(ValueError, match="stability evidence is not canonical"):
        build_cand001_oos_diagnostic_evidence(bundle, aggregation, cost, forged_stability)


def test_diagnostic_write_is_standalone_immutable_and_does_not_modify_base_contract(tmp_path) -> None:
    bundle, aggregation, cost, stability = _sources()
    target = tmp_path / "diagnostic-evidence" / DIAGNOSTIC_FILENAME

    evidence = write_cand001_oos_diagnostic_evidence(
        target,
        bundle,
        aggregation,
        cost,
        stability,
    )

    assert target.exists()
    assert {path.name for path in target.parent.iterdir()} == {DIAGNOSTIC_FILENAME}
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["artifact_fingerprint"] == evidence.artifact_fingerprint
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False

    # The frozen Step-2107 base export remains an exactly three-file contract.
    assert {MEASUREMENTS_FILENAME, AGGREGATION_FILENAME, MANIFEST_FILENAME} == {
        "measurements.json",
        "aggregation.json",
        "manifest.json",
    }

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_cand001_oos_diagnostic_evidence(
            target,
            bundle,
            aggregation,
            cost,
            stability,
        )


def test_diagnostic_write_requires_fixed_filename(tmp_path) -> None:
    bundle, aggregation, cost, stability = _sources()

    with pytest.raises(ValueError, match="diagnostic filename"):
        write_cand001_oos_diagnostic_evidence(
            tmp_path / "wrong.json",
            bundle,
            aggregation,
            cost,
            stability,
        )
