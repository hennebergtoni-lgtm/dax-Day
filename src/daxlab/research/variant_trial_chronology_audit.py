from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from daxlab.research.variant_trial_chronology import (
    TrialChronologyResult,
    evaluate_trial_chronology,
)
from daxlab.research.variant_trial_git_evidence import collect_trial_chronology_evidence
from daxlab.research.variant_trial_registry import parse_registry_payload


def audit_trial_chronology(
    *,
    repo_root: str | Path,
    trial_id: str,
    declaration_ref: str,
    result_ref: str,
    result_artifact_path: str,
    registry_path: str = "research/VARIANT_TRIAL_REGISTRY_V1.json",
) -> TrialChronologyResult:
    """Run the full read-only chronology audit for one persisted trial declaration."""
    root = Path(repo_root).expanduser().resolve()
    registry_file = root / registry_path
    if not registry_file.is_file():
        raise ValueError("current registry file does not exist")
    try:
        payload: Any = json.loads(registry_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("current registry JSON is invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("current registry JSON must be an object")
    declarations = parse_registry_payload(payload)

    clean_trial_id = trial_id.strip()
    matches = [row for row in declarations if row.trial_id == clean_trial_id]
    if len(matches) != 1:
        raise ValueError("trial_id must resolve to exactly one registry declaration")
    declaration = matches[0]

    evidence = collect_trial_chronology_evidence(
        repo_root=root,
        trial_id=declaration.trial_id,
        declaration_record_hash=declaration.record_hash,
        declaration_ref=declaration_ref,
        result_ref=result_ref,
        registry_path=registry_path,
        result_artifact_path=result_artifact_path,
    )
    return evaluate_trial_chronology(declaration.to_payload(), evidence)
