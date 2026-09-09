from pathlib import Path


def test_ci_retains_v112_engine_probe_and_replay_smoke() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "V11.2 engine surface probe" in workflow
    assert "python scripts/probe_v112_engine.py" in workflow
    assert "Guarded V11.2 replay smoke" in workflow
    assert "python scripts/v112_replay_smoke.py" in workflow
