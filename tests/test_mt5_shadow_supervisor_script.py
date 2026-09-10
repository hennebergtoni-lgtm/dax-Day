from __future__ import annotations

import ast
from pathlib import Path


def test_supervisor_script_has_no_order_api() -> None:
    path = Path("scripts/mt5_shadow_supervisor.py")
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    for forbidden in (
        "order_send",
        "order_check",
        "positions_get",
        "history_deals_get",
        "history_orders_get",
    ):
        assert forbidden not in attrs
    assert "from mt5_windows_probe import collect_probe" in text
    assert 'parser.add_argument("--broker-timezone", required=True)' in text
    assert 'resume_path = state_dir / "resume.json"' in text
    assert 'heartbeat_path = state_dir / "heartbeat.json"' in text
    assert 'latest_bundle_path = state_dir / "latest_bundle.json"' in text
    assert 'rejected_bundle_path = state_dir / "rejected_bundle.json"' in text
    assert "single_instance_lock_held=lock.held" in text
    assert "previous_bundle_payload=previous_bundle_payload" in text


def test_compare_happens_before_latest_bundle_replace() -> None:
    text = Path("scripts/mt5_shadow_supervisor.py").read_text(encoding="utf-8")
    process_index = text.index("cycle = process_mt5_shadow_cycle(")
    accepted_write_index = text.index("atomic_write_json(latest_bundle_path, bundle_payload)")
    assert process_index < accepted_write_index
    assert 'cycle.heartbeat.get("cross_cycle_status") == "BLOCKED"' in text
    assert "atomic_write_json(rejected_bundle_path, bundle_payload)" in text


def test_losing_second_instance_does_not_write_shared_state() -> None:
    text = Path("scripts/mt5_shadow_supervisor.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    main = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    lock_try = next(
        node
        for node in ast.walk(main)
        if isinstance(node, ast.Try)
        and any(
            isinstance(item, ast.Expr)
            and isinstance(item.value, ast.Call)
            and isinstance(item.value.func, ast.Attribute)
            and item.value.func.attr == "acquire"
            for item in node.body
        )
    )
    assert len(lock_try.handlers) == 1
    handler = lock_try.handlers[0]
    calls = [node for node in ast.walk(handler) if isinstance(node, ast.Call)]
    assert not calls
    returns = [node for node in ast.walk(handler) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    assert isinstance(returns[0].value, ast.Constant)
    assert returns[0].value.value == 4
