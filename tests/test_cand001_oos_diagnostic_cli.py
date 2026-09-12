import json
from pathlib import Path
import subprocess
import sys

from daxlab.research.cand001_oos_aggregation import aggregate_cand001_oos
from daxlab.research.cand001_oos_evidence_export import write_cand001_oos_evidence_directory
from daxlab.research.cand001_oos_measurement_runner import (
    Cand001OosMeasurement,
    Cand001OosMeasurementBundle,
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


def _base_evidence(tmp_path: Path) -> Path:
    bundle = _bundle()
    aggregation = aggregate_cand001_oos(bundle)
    evidence_dir = tmp_path / "base-evidence"
    write_cand001_oos_evidence_directory(evidence_dir, bundle, aggregation)
    return evidence_dir


def _snapshot(directory: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(directory.iterdir())}


def _script() -> Path:
    return Path(__file__).resolve().parents[1] / "scripts" / "build_cand001_oos_diagnostics.py"


def test_cli_builds_only_standalone_diagnostics_and_preserves_base_evidence(tmp_path) -> None:
    evidence_dir = _base_evidence(tmp_path)
    before = _snapshot(evidence_dir)
    output_dir = tmp_path / "diagnostics"

    result = subprocess.run(
        [
            sys.executable,
            str(_script()),
            "--evidence-dir",
            str(evidence_dir),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(result.stdout.strip())
    assert summary["status"] == "DIAGNOSTIC_EVIDENCE_WRITTEN"
    assert summary["execution_capability"] == "NONE"
    assert summary["order_execution_enabled"] is False
    assert summary["automatic_promotion"] is False
    assert summary["threshold_policy"] == "NO_COMPOSITE_SCORE_NO_PASS_THRESHOLD"
    assert {path.name for path in output_dir.iterdir()} == {"diagnostics.json"}
    assert _snapshot(evidence_dir) == before


def test_cli_refuses_same_output_directory_as_base_evidence(tmp_path) -> None:
    evidence_dir = _base_evidence(tmp_path)
    before = _snapshot(evidence_dir)

    result = subprocess.run(
        [
            sys.executable,
            str(_script()),
            "--evidence-dir",
            str(evidence_dir),
            "--output-dir",
            str(evidence_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "must be separate from base OOS evidence" in result.stderr
    assert _snapshot(evidence_dir) == before


def test_cli_refuses_overwriting_existing_diagnostic_artifact(tmp_path) -> None:
    evidence_dir = _base_evidence(tmp_path)
    output_dir = tmp_path / "diagnostics"
    command = [
        sys.executable,
        str(_script()),
        "--evidence-dir",
        str(evidence_dir),
        "--output-dir",
        str(output_dir),
    ]

    subprocess.run(command, check=True, capture_output=True, text=True)
    first = (output_dir / "diagnostics.json").read_bytes()
    second = subprocess.run(command, check=False, capture_output=True, text=True)

    assert second.returncode != 0
    assert "refusing to overwrite diagnostic evidence" in second.stderr
    assert (output_dir / "diagnostics.json").read_bytes() == first
