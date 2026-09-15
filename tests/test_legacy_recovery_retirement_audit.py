from __future__ import annotations

from pathlib import Path


_LEGACY_MODULE = Path("src/daxlab/runtime/recovery.py")
_AUDIT_ONLY_FILES = {
    Path("tests/test_legacy_recovery_retirement_audit.py"),
    Path("tests/test_legacy_recovery_document_provenance.py"),
    Path("tests/test_recovery_module_boundary.py"),
}
_ACTIVE_TEXT_SUFFIXES = {".py", ".ps1", ".sh", ".yml", ".yaml", ".toml", ".json"}
_LEGACY_CONSUMER_MARKERS = (
    "daxlab.runtime.recovery import",
    "import daxlab.runtime.recovery",
    "from daxlab.runtime import recovery",
    "recovery_bundle_manifest.json",
)


def test_no_active_surface_depends_on_legacy_recovery_contract() -> None:
    """Expose active code/config/script blockers before legacy recovery.py can retire."""
    root = Path(__file__).resolve().parents[1]
    offenders: dict[str, list[str]] = {}

    for top in ("src", "scripts", "tests", ".github", "web"):
        base = root / top
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _ACTIVE_TEXT_SUFFIXES:
                continue
            relative = path.relative_to(root)
            if relative == _LEGACY_MODULE or relative in _AUDIT_ONLY_FILES:
                continue
            text = path.read_text(encoding="utf-8")
            matched = [marker for marker in _LEGACY_CONSUMER_MARKERS if marker in text]
            if matched:
                offenders[str(relative)] = matched

    assert offenders == {}, (
        "legacy runtime/recovery.py still has active code/config/script consumers; "
        f"retirement is blocked by {offenders}"
    )


def test_retirement_decision_stays_retain_with_reason_until_compatibility_is_proved() -> None:
    """Do not convert zero active imports into deletion proof."""
    root = Path(__file__).resolve().parents[1]
    audit = (root / "docs/RECOVERY_CANONICALIZATION_AUDIT_V1.md").read_text(encoding="utf-8")

    assert "Current retirement decision: `RETAIN_WITH_REASON`" in audit
    assert "runtime/recovery.py` = **LEGACY / FROZEN / RETAIN_WITH_REASON**" in audit
    assert "No new code may import the legacy module" in audit
    assert "Retirement unlock conditions" in audit
    assert "tested compatibility reader/migration path" in audit
    assert "does **not** prove that deleting" in audit
