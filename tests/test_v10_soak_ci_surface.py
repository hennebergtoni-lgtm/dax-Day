from pathlib import Path


def test_soak_smoke_is_unconditional_inside_ci_job() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    segment = workflow.split("- name: Offline SHADOW soak smoke", 1)[1].split("- name:", 1)[0]
    assert "if:" not in segment
    assert "python scripts/shadow_soak_smoke.py" in segment
