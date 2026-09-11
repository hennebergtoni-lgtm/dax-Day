from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "runtime-status-snapshot.yml"


def test_runtime_status_snapshot_detects_untracked_first_snapshot() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "git status --porcelain -- web/runtime_status.json" in source
    assert "git diff --quiet -- web/runtime_status.json" not in source
    assert "git add web/runtime_status.json" in source
    assert "Update MT5 SHADOW runtime status snapshot" in source
