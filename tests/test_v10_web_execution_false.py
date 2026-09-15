import json
from pathlib import Path


def test_all_static_v2_execution_surfaces_remain_non_executable() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())

    assert "mt5_adapter" not in web
    assert "host_readiness" not in web
    assert "synthetic_shadow_soak" not in web
    assert web["historical_sequential_replay"]["execution_capability"] == "NONE"
    assert web["historical_sequential_replay"]["order_execution_enabled"] is False
    assert web["forward_monitoring"]["execution_capability"] == "NONE"
    assert web["forward_monitoring"]["order_execution_enabled"] is False
    assert web["readiness"]["paper"] == "BLOCKED"
    assert web["readiness"]["live"] == "BLOCKED"
