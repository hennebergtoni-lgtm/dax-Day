import json
from pathlib import Path


def test_static_web_excludes_synthetic_soak_runtime_markers() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())

    assert web["status_scope"] == "STATIC_VERSIONED_EVIDENCE_ONLY"
    assert web["runtime_truth_included"] is False
    assert "synthetic_shadow_soak" not in web
    assert web["runtime_boundary"]["current_candidate_contract"] == (
        "docs/CAND001_OPERATOR_TELEMETRY_V1.md"
    )
