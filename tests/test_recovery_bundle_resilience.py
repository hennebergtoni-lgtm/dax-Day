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


def _write_surface(directory: Path) -> None:
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
    bundle = RecoveryBundleManifest.build(
        source_commit_sha="abc123",
        run_manifest=run,
        checkpoint=checkpoint,
        decision_log=decisions,
        status="IN_PROGRESS",
    )
    write_recovery_bundle(
        directory,
        bundle=bundle,
        run_manifest=run,
        checkpoint=checkpoint,
        decision_log=decisions,
    )


def test_recovery_bundle_rejects_missing_checksums(tmp_path: Path) -> None:
    _write_surface(tmp_path)
    (tmp_path / "SHA256SUMS").unlink()
    with pytest.raises(RuntimeError, match="checksums missing"):
        verify_recovery_bundle(tmp_path)


def test_recovery_bundle_rejects_missing_payload(tmp_path: Path) -> None:
    _write_surface(tmp_path)
    (tmp_path / "checkpoint.json").unlink()
    with pytest.raises(RuntimeError, match="file missing: checkpoint.json"):
        verify_recovery_bundle(tmp_path)


def test_recovery_bundle_rejects_corrupt_checksum_entry(tmp_path: Path) -> None:
    _write_surface(tmp_path)
    checksums = tmp_path / "SHA256SUMS"
    lines = checksums.read_text(encoding="utf-8").splitlines()
    checksums.write_text(lines[0] + "\nnot-a-valid-checksum-line\n", encoding="utf-8")
    with pytest.raises((RuntimeError, ValueError)):
        verify_recovery_bundle(tmp_path)


def test_recovery_bundle_rewrite_restores_verified_surface(tmp_path: Path) -> None:
    _write_surface(tmp_path)
    original = (tmp_path / "checkpoint.json").read_text(encoding="utf-8")
    (tmp_path / "checkpoint.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        verify_recovery_bundle(tmp_path)

    # Simulate recovery from the still-known canonical source by recreating the bundle.
    _write_surface(tmp_path)
    verify_recovery_bundle(tmp_path)
    assert (tmp_path / "checkpoint.json").read_text(encoding="utf-8") == original


def test_orphan_temp_file_does_not_override_verified_bundle(tmp_path: Path) -> None:
    _write_surface(tmp_path)
    (tmp_path / ".checkpoint.json.tmp").write_text("corrupt partial write", encoding="utf-8")
    verify_recovery_bundle(tmp_path)
    assert (tmp_path / "checkpoint.json").exists()
