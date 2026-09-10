from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from daxlab.research.variant_trial_git_evidence import collect_trial_chronology_evidence
from daxlab.research.variant_trial_registry import declare_trial, registry_payload


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
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


def _write_payload(repo: Path, payload: dict[str, object]) -> None:
    (repo / "research" / "VARIANT_TRIAL_REGISTRY_V1.json").write_text(
        json.dumps(payload, sort_keys=True), encoding="utf-8"
    )


def _make_trial(trial_id: str):
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


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def test_collects_positive_git_chronology_evidence(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write_payload(repo, registry_payload([]))
    _commit_all(repo, "genesis")

    trial = _make_trial("trial-001")
    _write_payload(repo, registry_payload([trial]))
    declaration_commit = _commit_all(repo, "declare trial")

    result_path = repo / "results" / "trial-001.json"
    result_path.parent.mkdir()
    result_path.write_text('{"return_r": 1.25}', encoding="utf-8")
    result_commit = _commit_all(repo, "add result")

    evidence = collect_trial_chronology_evidence(
        repo_root=repo,
        trial_id=trial.trial_id,
        declaration_record_hash=trial.record_hash,
        declaration_ref=declaration_commit,
        result_ref=result_commit,
        result_artifact_path="results/trial-001.json",
    )
    assert evidence.declaration_present_at_commit is True
    assert evidence.declaration_commit_is_ancestor_of_result is True
    assert evidence.result_artifact_present_at_declaration_commit is False
    assert evidence.declaration_commit == declaration_commit
    assert evidence.result_commit == result_commit


def test_result_already_present_at_declaration_commit_is_detected(tmp_path: Path):
    repo = _init_repo(tmp_path)
    trial = _make_trial("trial-002")
    _write_payload(repo, registry_payload([trial]))
    result_path = repo / "results" / "trial-002.json"
    result_path.parent.mkdir()
    result_path.write_text('{"return_r": 9.0}', encoding="utf-8")
    declaration_commit = _commit_all(repo, "declaration and existing result")

    marker = repo / "later.txt"
    marker.write_text("later", encoding="utf-8")
    result_commit = _commit_all(repo, "later commit")

    evidence = collect_trial_chronology_evidence(
        repo_root=repo,
        trial_id=trial.trial_id,
        declaration_record_hash=trial.record_hash,
        declaration_ref=declaration_commit,
        result_ref=result_commit,
        result_artifact_path="results/trial-002.json",
    )
    assert evidence.result_artifact_present_at_declaration_commit is True


def test_missing_declaration_hash_is_not_treated_as_present(tmp_path: Path):
    repo = _init_repo(tmp_path)
    trial = _make_trial("trial-003")
    _write_payload(repo, registry_payload([trial]))
    declaration_commit = _commit_all(repo, "declare trial")
    result_path = repo / "results" / "trial-003.json"
    result_path.parent.mkdir()
    result_path.write_text("{}", encoding="utf-8")
    result_commit = _commit_all(repo, "result")

    evidence = collect_trial_chronology_evidence(
        repo_root=repo,
        trial_id=trial.trial_id,
        declaration_record_hash="d" * 64,
        declaration_ref=declaration_commit,
        result_ref=result_commit,
        result_artifact_path="results/trial-003.json",
    )
    assert evidence.declaration_present_at_commit is False


def test_tampered_historical_registry_is_rejected(tmp_path: Path):
    repo = _init_repo(tmp_path)
    trial = _make_trial("trial-tampered")
    payload = registry_payload([trial])
    payload["head_hash"] = "f" * 64
    _write_payload(repo, payload)
    commit = _commit_all(repo, "tampered registry")

    with pytest.raises(ValueError, match="integrity validation"):
        collect_trial_chronology_evidence(
            repo_root=repo,
            trial_id=trial.trial_id,
            declaration_record_hash=trial.record_hash,
            declaration_ref=commit,
            result_ref=commit,
            result_artifact_path="results/missing.json",
        )


def test_unsafe_repository_path_is_rejected(tmp_path: Path):
    repo = _init_repo(tmp_path)
    _write_payload(repo, registry_payload([]))
    commit = _commit_all(repo, "genesis")
    with pytest.raises(ValueError, match="safe relative path"):
        collect_trial_chronology_evidence(
            repo_root=repo,
            trial_id="trial-004",
            declaration_record_hash="e" * 64,
            declaration_ref=commit,
            result_ref=commit,
            result_artifact_path="../secret.txt",
        )


def test_collector_source_contains_no_git_write_operations():
    source = Path("src/daxlab/research/variant_trial_git_evidence.py").read_text(
        encoding="utf-8"
    ).lower()
    for forbidden in (
        '"commit"',
        '"push"',
        '"checkout"',
        '"switch"',
        '"reset"',
        '"clean"',
        '"add"',
        '"tag"',
    ):
        assert forbidden not in source
