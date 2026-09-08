from pathlib import Path

import pytest

from daxlab.runtime.checkpoint import ReplayCheckpoint
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.manifests import DecisionLogManifest, RunManifest
from daxlab.runtime.recovery_bundle import (
    RecoveryBundleManifest,
    verify_recovery_bundle,
    write_recovery_bundle,
)


def _surface() -> tuple[RunManifest, DecisionLogManifest, ReplayCheckpoint]:
    run = RunManifest.build(
        dataset_fingerprint="dataset",
        engine_fingerprint="engine",
        config={"rr": 1.5},
        mode=RuntimeMode.REPLAY,
    )
    decisions = DecisionLogManifest(
        decisions=2,
        trades=1,
        no_trades=1,
        decision_ids_fingerprint="decision-log",
    )
    checkpoint = ReplayCheckpoint.build(
        run_manifest=run,
        processed_candles=103,
        last_event_time_iso="2026-09-08T17:30:00+02:00",
        decision_log=decisions,
    )
    return run, decisions, checkpoint


def test_recovery_bundle_round_trip(tmp_path: Path) -> None:
    run, decisions, checkpoint = _surface()
    bundle = RecoveryBundleManifest.build(
        source_commit_sha="abc123",
        run_manifest=run,
        checkpoint=checkpoint,
        decision_log=decisions,
        status="IN_PROGRESS",
    )
    hashes = write_recovery_bundle(
        tmp_path,
        bundle=bundle,
        run_manifest=run,
        checkpoint=checkpoint,
        decision_log=decisions,
    )
    assert len(hashes) == 4
    verify_recovery_bundle(tmp_path)


def test_recovery_bundle_detects_tampering(tmp_path: Path) -> None:
    run, decisions, checkpoint = _surface()
    bundle = RecoveryBundleManifest.build(
        source_commit_sha="abc123",
        run_manifest=run,
        checkpoint=checkpoint,
        decision_log=decisions,
        status="COMPLETED",
    )
    write_recovery_bundle(
        tmp_path,
        bundle=bundle,
        run_manifest=run,
        checkpoint=checkpoint,
        decision_log=decisions,
    )
    (tmp_path / "checkpoint.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        verify_recovery_bundle(tmp_path)


def test_recovery_bundle_rejects_unknown_status() -> None:
    run, decisions, checkpoint = _surface()
    with pytest.raises(ValueError, match="invalid recovery bundle status"):
        RecoveryBundleManifest.build(
            source_commit_sha="abc123",
            run_manifest=run,
            checkpoint=checkpoint,
            decision_log=decisions,
            status="MAYBE",
        )
