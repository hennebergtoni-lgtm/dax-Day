from pathlib import Path


def test_no_new_production_imports_of_legacy_runtime_recovery() -> None:
    root = Path(__file__).resolve().parents[1] / "src"
    forbidden = "daxlab.runtime.recovery import"
    offenders = []
    for path in root.rglob("*.py"):
        if path.name == "recovery.py":
            continue
        text = path.read_text(encoding="utf-8")
        if forbidden in text:
            offenders.append(str(path.relative_to(root.parent)))
    assert offenders == [], (
        "new production code must use daxlab.runtime.recovery_bundle; "
        f"legacy recovery imports found in {offenders}"
    )
