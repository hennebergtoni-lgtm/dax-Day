from __future__ import annotations

from pathlib import Path


_LEGACY_MODULE = Path("src/daxlab/runtime/recovery.py")
_THIS_TEST = Path("tests/test_legacy_recovery_retirement_audit.py")
_LEGACY_CONSUMER_MARKERS = (
    "from daxlab.runtime.recovery import",
    "import daxlab.runtime.recovery",
    "from daxlab.runtime import recovery",
    "recovery_bundle_manifest.json",
)


def test_no_active_code_consumer_depends_on_legacy_recovery_contract() -> None:
    """Expose code/test/script blockers before legacy recovery.py can be retired."""
    root = Path(__file__).resolve().parents[1]
    offenders: dict[str, list[str]] = {}

    for top in ("src", "scripts", "tests"):
        for path in (root / top).rglob("*.py"):
            relative = path.relative_to(root)
            if relative in {_LEGACY_MODULE, _THIS_TEST}:
                continue
            text = path.read_text(encoding="utf-8")
            matched = [marker for marker in _LEGACY_CONSUMER_MARKERS if marker in text]
            if matched:
                offenders[str(relative)] = matched

    assert offenders == {}, (
        "legacy runtime/recovery.py still has active code/test/script consumers; "
        f"retirement is blocked by {offenders}"
    )
