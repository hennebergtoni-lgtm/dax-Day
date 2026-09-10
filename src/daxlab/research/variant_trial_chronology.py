from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

VERIFIED = "VERIFIED_PREDECLARED"
BLOCKED = "BLOCKED_CHRONOLOGY_UNVERIFIED"
_GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


@dataclass(frozen=True)
class TrialChronologyEvidence:
    trial_id: str
    declaration_record_hash: str
    declaration_commit: str
    result_commit: str
    declaration_present_at_commit: bool
    declaration_commit_is_ancestor_of_result: bool
    result_artifact_present_at_declaration_commit: bool


@dataclass(frozen=True)
class TrialChronologyResult:
    status: str
    blockers: tuple[str, ...]
    trial_id: str
    declaration_commit: str
    result_commit: str
    verified_predeclared: bool

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": "DAXLAB_VARIANT_TRIAL_CHRONOLOGY_V1",
            "status": self.status,
            "blockers": list(self.blockers),
            "trial_id": self.trial_id,
            "declaration_commit": self.declaration_commit,
            "result_commit": self.result_commit,
            "verified_predeclared": self.verified_predeclared,
        }


def _nonempty(value: str, label: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _git_sha(value: str, label: str) -> str:
    text = _nonempty(value, label).lower()
    if not _GIT_SHA_RE.fullmatch(text):
        raise ValueError(f"{label} must be a 40-character Git SHA")
    return text


def evaluate_trial_chronology(
    declaration: Mapping[str, object],
    evidence: TrialChronologyEvidence,
) -> TrialChronologyResult:
    """Evaluate predeclaration chronology from independently resolved Git evidence.

    This function never executes Git and never trusts a declaration's self-asserted
    chronology fields. It only elevates a claimed PREDECLARED trial when the
    declaration record/hash and commit ancestry are independently supported.
    """
    trial_id = _nonempty(str(declaration.get("trial_id", "")), "trial_id")
    mode = str(declaration.get("declaration_mode", "")).strip().upper()
    record_hash = _nonempty(str(declaration.get("record_hash", "")), "record_hash")
    if not re.fullmatch(r"[0-9a-f]{64}", record_hash):
        raise ValueError("record_hash must be lowercase SHA256 hex")

    declaration_commit = _git_sha(evidence.declaration_commit, "declaration_commit")
    result_commit = _git_sha(evidence.result_commit, "result_commit")
    blockers: set[str] = set()

    if evidence.trial_id.strip() != trial_id:
        blockers.add("TRIAL_ID_MISMATCH")
    if evidence.declaration_record_hash != record_hash:
        blockers.add("DECLARATION_RECORD_HASH_MISMATCH")
    if mode != "PREDECLARED":
        blockers.add("DECLARATION_NOT_CLAIMED_PREDECLARED")
    if not evidence.declaration_present_at_commit:
        blockers.add("DECLARATION_NOT_PRESENT_AT_DECLARATION_COMMIT")
    if not evidence.declaration_commit_is_ancestor_of_result:
        blockers.add("DECLARATION_COMMIT_NOT_ANCESTOR_OF_RESULT")
    if evidence.result_artifact_present_at_declaration_commit:
        blockers.add("RESULT_ALREADY_PRESENT_AT_DECLARATION_COMMIT")
    if declaration_commit == result_commit:
        blockers.add("DECLARATION_AND_RESULT_COMMIT_IDENTICAL")

    ordered = tuple(sorted(blockers))
    verified = not ordered
    return TrialChronologyResult(
        status=VERIFIED if verified else BLOCKED,
        blockers=ordered,
        trial_id=trial_id,
        declaration_commit=declaration_commit,
        result_commit=result_commit,
        verified_predeclared=verified,
    )
