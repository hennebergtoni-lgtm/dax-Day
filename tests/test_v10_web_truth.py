import json
from pathlib import Path


def test_static_v2_web_never_claims_current_host_paper_or_live_truth() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())

    assert web["schema_version"] == "DAXLAB_WEB_STATIC_STATUS_V2"
    assert web["runtime_truth_included"] is False
    assert "host_readiness" not in web
    assert "synthetic_shadow_soak" not in web
    assert web["paper_preparation"]["paper_started"] is False
    assert web["paper_preparation"]["broker_adapter_present"] is False
    assert web["readiness"]["paper"] == "BLOCKED"
    assert web["readiness"]["live"] == "BLOCKED"
