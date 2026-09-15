from __future__ import annotations

from pathlib import Path


_LEGACY_DOCUMENT_MARKERS = (
    "src/daxlab/runtime/recovery.py",
    "runtime/recovery.py",
    "recovery_bundle_manifest.json",
)
_ALLOWED_PROVENANCE_DOCS = {
    "docs/ARCHITECTURE_HYGIENE_AUDIT_V5.md",
    "docs/CURRENT_WORK_STEP.md",
    "docs/CURRENT_WORK_STEP_ARCHIVE_THROUGH_2154_PRE_CLOSE.md",
    "docs/DAX_BOT_1X_MIGRATION_BACKLOG_STEP_2000.md",
    "docs/MASTERSTAND.md",
    "docs/PROBLEM_SOLUTION_REGISTRY.md",
    "docs/PROJECT_KNOWLEDGE_INDEX.md",
    "docs/RECOVERY_CANONICALIZATION_AUDIT_V1.md",
    "docs/V8_RECOVERY_HYGIENE_DECISION.md",
}


def test_legacy_recovery_document_references_are_confined_to_provenance_docs() -> None:
    """Keep legacy recovery mentions historical instead of creating new active contracts."""
    root = Path(__file__).resolve().parents[1]
    unexpected: dict[str, list[str]] = {}

    for path in (root / "docs").rglob("*.md"):
        relative = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8")
        matched = [marker for marker in _LEGACY_DOCUMENT_MARKERS if marker in text]
        if matched and relative not in _ALLOWED_PROVENANCE_DOCS:
            unexpected[relative] = matched

    assert unexpected == {}, (
        "legacy runtime/recovery.py references escaped the reviewed provenance set; "
        f"review these documents before retirement: {unexpected}"
    )
