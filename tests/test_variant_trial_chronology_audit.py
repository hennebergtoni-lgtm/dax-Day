from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from daxlab.research.variant_trial_chronology import BLOCKED, VERIFIED
from daxlab.research.variant_trial_chronology_audit import audit_trial_chronology
from daxlab.research.variant_trial_registry import declare_trial, registry_payload


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return proc.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test Runner")
    (repo / "research").mkdir()
    return repo


def _write_registry(repo: Path, rows) -> None:
    (repo / "research" / "VARIANT_TRIAL_REGISTRY_V1.json").write_text(
        json.dumps(registry_payload(rows), sort_keys=True), encoding="utf-8"
    )


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _trial(trial_id: str = "trial-001"):
    return declare_trial(
        [],
        trial_id=trial_id,
        experiment_id="exp-001",
        hypothesis_trial_id="hyp-001",
        family_id="TEST001",
        variant_key="variant-a",
        parameters={"window": 5},
        declared_at_utc="2026-09-10T04:00:00Z",
        declaration_mode="PREDECLARED",
        source_commit="1" * 40,
    )


def test_end_to_end_valid_predeclaration_is_verified(tmp_path: Path):
    repo = _init_repo(tmp_path)
    trial = _trial()
    _write_registry(repo, [trial])
    declaration_commit = _commit(repo, "declare")

    result = repo / "results" / "trial-001.json"
    result.parent.mkdir()
    result.write_text("{}", encoding="utf-8")
    result_commit = _commit(repo, "result")

    audited = audit_trial_chronology(
        repo_root=repo,
        trial_id=trial.trial_id,
        declaration_ref=declaration_commit,
        result_ref=result_commit,
        result_artifact_path="results/trial-001.json",
    )
    assert audited.status == VERIFIED
    assert audited.verified_predeclared is True


def test_end_to_end_result_present_at_declaration_is_blocked(tmp_path: Path):
    repo = _init_repo(tmp_path)
    trial = _trial()
    _write_registry(repo, [trial])
    result = repo / "results" / "trial-001.json"
    result.parent.mkdir()
    result.write_text("{}", encoding="utf-8")
    declaration_commit = _commit(repo, "declare with result")

    (repo / "later.txt").write_text("later", encoding="utf-8")
    result_commit = _commit(repo, "later")

    audited = audit_trial_chronology(
        repo_root=repo,
        trial_id=trial.trial_id,
        declaration_ref=declaration_commit,
        result_ref=result_commit,
        result_artifact_path="results/trial-001.json",
    )
    assert audited.status == BLOCKED
    assert "RESULT_ALREADY_PRESENT_AT_DECLARATION_COMMIT" in audited.blockers


def test_unknown_trial_is_rejected_before_git_evidence_collection(tmp_path: Path):
    repo = _init_repo(tmp_path)
    trial = _trial()
    _write_registry(repo, [trial])
    commit = _commit(repo, "declare")
    with pytest.raises(ValueError, match="exactly one"):
        audit_trial_chronology(
            repo_root=repo,
            trial_id="unknown",
            declaration_ref=commit,
            result_ref=commit,
            result_artifact_path="results/unknown.json",
        )
