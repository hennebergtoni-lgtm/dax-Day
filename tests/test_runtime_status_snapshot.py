from __future__ import annotations

import importlib.util
from pathlib import Path

_SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_runtime_status_snapshot.py"
_SPEC = importlib.util.spec_from_file_location("build_runtime_status_snapshot", _SNAPSHOT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("failed to load runtime snapshot builder")
snapshot = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(snapshot)


def test_snapshot_source_has_no_mt5_or_order_api() -> None:
    source = Path(snapshot.__file__).read_text(encoding="utf-8")
    assert "import MetaTrader5" not in source
    assert "from MetaTrader5" not in source
    assert "order_send" not in source


def test_snapshot_contract_is_explicitly_read_only() -> None:
    assert snapshot._SCHEMA == "DAXLAB_MT5_SHADOW_RUNTIME_STATUS_V1"
    assert snapshot._OUTPUT.name == "runtime_status.json"
