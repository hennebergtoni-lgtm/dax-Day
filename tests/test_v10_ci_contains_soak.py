from pathlib import Path


def test_ci_runs_offline_shadow_soak_smoke() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "Offline SHADOW soak smoke" in workflow
    assert "python scripts/shadow_soak_smoke.py" in workflow
