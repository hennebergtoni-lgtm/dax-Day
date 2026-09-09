import json
from pathlib import Path


def test_v10_web_status_never_claims_real_host_paper_or_live() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    assert web["host_readiness"]["state"] == "AWAITING_REAL_WINDOWS_HOST"
    assert web["host_readiness"]["real_host_evidence_present"] is False
    assert web["synthetic_shadow_soak"]["evidence_state"] == (
        "SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE"
    )
    assert web["paper_preparation"]["paper_started"] is False
    assert web["paper_preparation"]["broker_adapter_present"] is False
    assert web["readiness"]["paper"] == "BLOCKED"
    assert web["readiness"]["live"] == "BLOCKED"
