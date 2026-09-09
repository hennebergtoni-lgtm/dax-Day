from pathlib import Path


def test_ci_retains_recovery_reconstruction_preflight() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "Recovery reconstruction preflight" in workflow
    assert "python scripts/recovery_preflight.py" in workflow
