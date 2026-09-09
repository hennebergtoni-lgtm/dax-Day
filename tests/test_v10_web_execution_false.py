import json
from pathlib import Path


def test_all_exposed_v10_execution_flags_remain_false() -> None:
    root = Path(__file__).resolve().parents[1]
    web = json.loads((root / "web/status.json").read_text())
    assert web["mt5_adapter"]["order_execution_enabled"] is False
    assert web["host_readiness"]["order_execution_enabled"] is False
    assert web["synthetic_shadow_soak"]["order_execution_enabled"] is False
