from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Sequence

from daxlab.research.variant_trial_chronology import TrialChronologyEvidence
from daxlab.research.variant_trial_registry import parse_registry_payload

_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class GitCommandResult:
    returncode: int
    stdout: str
    stderr: str


def _run_git(repo_root: Path, args: Sequence[str]) -> GitCommandResult:
    """Run one allowlisted read-only Git command."""
    allowed = {"rev-parse", "merge-base", "show"}
    if not args or args[0] not in allowed:
        raise ValueError("git command is not allowlisted for chronology evidence")
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    return GitCommandResult(proc.returncode, proc.stdout, proc.stderr)


def _resolve_commit(repo_root: Path, ref: str) -> str:
    text = ref.strip()
    if not text:
        raise ValueError("commit ref must be non-empty")
    result = _run_git(repo_root, ("rev-parse", "--verify", f"{text}^{{commit}}"))
    if result.returncode != 0:
        raise ValueError("commit ref could not be resolved")
    sha = result.stdout.strip().lower()
    if not _GIT_SHA_RE.fullmatch(sha):
        raise ValueError("resolved commit is not a 40-character Git SHA")
    return sha


def _show_path(repo_root: Path, commit: str, path: str) -> str | None:
    clean_path = path.strip().replace("\\", "/")
    if not clean_path or clean_path.startswith("/") or ".." in clean_path.split("/"):
        raise ValueError("repository path must be a safe relative path")
    result = _run_git(repo_root, ("show", f"{commit}:{clean_path}"))
    if result.returncode == 0:
        return result.stdout
    return None


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = _run_git(repo_root, ("merge-base", "--is-ancestor", ancestor, descendant))
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise ValueError("git ancestry check failed")


def collect_trial_chronology_evidence(
    *,
    repo_root: str | Path,
    trial_id: str,
    declaration_record_hash: str,
    declaration_ref: str,
    result_ref: str,
    registry_path: str = "research/VARIANT_TRIAL_REGISTRY_V1.json",
    result_artifact_path: str,
) -> TrialChronologyEvidence:
    """Collect read-only Git evidence for one declared trial."""
    root = Path(repo_root).expanduser().resolve()
    if not (root / ".git").exists():
        raise ValueError("repo_root must be a Git working tree root")
    clean_trial_id = trial_id.strip()
    if not clean_trial_id:
        raise ValueError("trial_id must be non-empty")
    record_hash = declaration_record_hash.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", record_hash):
        raise ValueError("declaration_record_hash must be lowercase SHA256 hex")

    declaration_commit = _resolve_commit(root, declaration_ref)
    result_commit = _resolve_commit(root, result_ref)

    registry_text = _show_path(root, declaration_commit, registry_path)
    declaration_present = False
    if registry_text is not None:
        try:
            payload = json.loads(registry_text)
        except json.JSONDecodeError as exc:
            raise ValueError("registry JSON at declaration commit is invalid") from exc
        if not isinstance(payload, dict):
            raise ValueError("registry JSON at declaration commit must be an object")
        try:
            declarations = parse_registry_payload(payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("registry at declaration commit failed integrity validation") from exc
        declaration_present = any(
            row.trial_id == clean_trial_id and row.record_hash == record_hash
            for row in declarations
        )

    ancestor = _is_ancestor(root, declaration_commit, result_commit)
    result_present = _show_path(root, declaration_commit, result_artifact_path) is not None

    return TrialChronologyEvidence(
        trial_id=clean_trial_id,
        declaration_record_hash=record_hash,
        declaration_commit=declaration_commit,
        result_commit=result_commit,
        declaration_present_at_commit=declaration_present,
        declaration_commit_is_ancestor_of_result=ancestor,
        result_artifact_present_at_declaration_commit=result_present,
    )
