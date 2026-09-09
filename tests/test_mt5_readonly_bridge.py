from __future__ import annotations

import ast
from pathlib import Path


def test_bridge_has_no_order_api_and_excludes_bar_zero() -> None:
    path = Path("scripts/mt5_readonly_bridge.py")
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "order_send" not in attrs
    assert "order_check" not in attrs
    assert "positions_get" not in attrs
    assert "history_deals_get" not in attrs
    assert "copy_rates_from_pos" in attrs
    assert "mt5.TIMEFRAME_M5, 1, count" in text
    assert 'info.trade_mode != mt5.SYMBOL_TRADE_MODE_DISABLED' in text
    assert 'parser.add_argument("--bind", required=True' in text
    assert 'args.bind.startswith("100.")' in text


def test_bridge_only_exposes_read_endpoints() -> None:
    text = Path("scripts/mt5_readonly_bridge.py").read_text(encoding="utf-8")
    assert 'parsed.path == "/health"' in text
    assert 'parsed.path != "/v1/de40/m5"' in text
    assert "def do_POST" in text
    assert '"method_not_allowed"' in text
