import json
from pathlib import Path


def test_static_web_does_not_publish_current_host_state() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())

    assert web["schema_version"] == "DAXLAB_WEB_STATIC_STATUS_V2"
    assert web["runtime_truth_included"] is False
    assert "host_readiness" not in web
    assert web["runtime_boundary"]["static_file_must_not_be_used_for_current_health"] is True
