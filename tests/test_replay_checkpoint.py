import pytest

from daxlab.runtime.checkpoint import ReplayCheckpoint, assert_resume_compatible
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.manifests import DecisionLogManifest, RunManifest


def test_resume_accepts_same_run_manifest() -> None:
    manifest = RunManifest.build(
        dataset_fingerprint="data",
        engine_fingerprint="engine",
        config={"rr": 1.5},
        mode=RuntimeMode.REPLAY,
    )
    checkpoint = ReplayCheckpoint.build(
        run_manifest=manifest,
        processed_candles=100,
        last_event_time_iso="2026-01-02T10:00:00+00:00",
        decision_log=DecisionLogManifest(100, 10, 90, "decisions"),
    )
    assert_resume_compatible(checkpoint, manifest)


def test_resume_blocks_config_drift() -> None:
    first = RunManifest.build(
        dataset_fingerprint="data",
        engine_fingerprint="engine",
        config={"rr": 1.5},
        mode=RuntimeMode.REPLAY,
    )
    changed = RunManifest.build(
        dataset_fingerprint="data",
        engine_fingerprint="engine",
        config={"rr": 2.0},
        mode=RuntimeMode.REPLAY,
    )
    checkpoint = ReplayCheckpoint.build(
        run_manifest=first,
        processed_candles=100,
        last_event_time_iso="2026-01-02T10:00:00+00:00",
        decision_log=DecisionLogManifest(100, 10, 90, "decisions"),
    )
    with pytest.raises(RuntimeError, match="run-manifest mismatch"):
        assert_resume_compatible(checkpoint, changed)
