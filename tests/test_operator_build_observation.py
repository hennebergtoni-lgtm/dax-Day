from copy import deepcopy
from datetime import timedelta
import importlib.util
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest

from daxlab.runtime.mt5_shadow_supervisor import (
    parse_supervisor_build_observation,
    supervisor_build_observation,
)
from test_operator_console_projection import console_sources, project


def test_build_observation_preserves_startup_identity_and_time_on_later_queries():
    raw, snapshot, hb, now, _ = console_sources()
    original = supervisor_build_observation(commit_sha="1" * 40, tracked_checkout_clean=True, observed_at=now)
    hb["build_observation"] = original
    hb["candidate_snapshot_fingerprint"] = snapshot["snapshot_fingerprint"]
    first = project(raw, snapshot, hb, now)
    later = project(raw, snapshot, hb, now + timedelta(seconds=10))
    assert first["build_identity"] == later["build_identity"]
    assert later["build_identity"]["runtime_commit"] == "1" * 40
    assert parse_supervisor_build_observation(original) == original
    assert later["provenance"]["candidate_cycle_binding"] == "BOUND"


@pytest.mark.parametrize("clean", [False, None])
def test_dirty_or_unknown_checkout_does_not_claim_exact_running_code(clean):
    _, _, _, now, _ = console_sources()
    obs = supervisor_build_observation(commit_sha="1" * 40, tracked_checkout_clean=clean, observed_at=now)
    assert obs["state"] == "UNKNOWN"


def test_legacy_heartbeat_remains_accepted_with_unknown_running_commit():
    raw, snapshot, hb, now, _ = console_sources()
    view = project(raw, snapshot, hb, now)
    assert view["build_identity"]["state"] == "UNKNOWN"
    assert view["build_identity"]["runtime_commit"] is None
    assert view["provenance"]["candidate_cycle_binding"] == "LEGACY_UNBOUND_OR_MISMATCH"


@pytest.mark.parametrize("field,value", [("commit_sha", "2" * 40), ("state", "GREEN"), ("observed_at", "2026-09-11T00:00:00+00:00")])
def test_build_observation_tampering_rejects(field, value):
    _, _, _, now, _ = console_sources()
    obs = supervisor_build_observation(commit_sha="1" * 40, tracked_checkout_clean=True, observed_at=now)
    obs[field] = value
    with pytest.raises(ValueError):
        parse_supervisor_build_observation(obs)


def test_other_candidate_snapshot_in_current_heartbeat_is_not_rendered_as_current():
    raw, snapshot, hb, now, _ = console_sources()
    hb["candidate_snapshot_fingerprint"] = "f" * 64
    view = project(raw, snapshot, hb, now)
    assert view["system"]["SNAPSHOT AGE"]["state"] == "STALE"
    assert "HEARTBEAT_CANDIDATE_SNAPSHOT_MISMATCH" in view["blockers"]


def test_supervisor_persists_observation_in_same_existing_heartbeat_and_history(tmp_path, monkeypatch):
    scripts = Path("scripts").resolve()
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location("supervisor_observation_test", scripts / "mt5_shadow_supervisor.py")
    runner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runner
    spec.loader.exec_module(runner)
    _, snapshot, hb, now, _ = console_sources()
    original = deepcopy(hb)
    obs = supervisor_build_observation(commit_sha="1" * 40, tracked_checkout_clean=True, observed_at=now)
    result = runner._persist_heartbeat(
        tmp_path / "heartbeat.json", tmp_path / "heartbeat_history", hb,
        max_history_entries=2, build_observation=obs,
        candidate_snapshot_fingerprint=snapshot["snapshot_fingerprint"],
    )
    assert hb == original
    assert result["build_observation"] == obs
    assert result["candidate_snapshot_fingerprint"] == snapshot["snapshot_fingerprint"]
    assert result["execution_capability"] == "NONE"
    assert result["order_execution_enabled"] is False
    monkeypatch.setattr(runner.subprocess, "run", Mock(side_effect=OSError("postgresql://secret")))
    assert runner._observe_startup_build()["state"] == "UNKNOWN"
