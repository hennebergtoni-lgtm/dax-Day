from datetime import datetime, timedelta, timezone
import ast
import importlib.util
import json
from pathlib import Path

from daxlab.runtime import mt5_demo_evidence_transport as owner
import test_mt5_demo_evidence_transport as evidence

prepared_attempt = evidence.prepared_attempt


def _load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "mt5_demo_evidence_lookup.py"
    spec = importlib.util.spec_from_file_location("mt5_demo_evidence_lookup", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _request(prepared_attempt):
    _, _, _, _, request = evidence._lookup(prepared_attempt)
    return request


def test_execute_readonly_lookup_emits_fail_closed_credential_free_envelope(prepared_attempt):
    script = _load_script()
    request = _request(prepared_attempt)
    mt5 = evidence.FakeMt5()
    observed_at = request.query_evaluated_at
    payload = script.execute_readonly_lookup(
        mt5=mt5,
        request_payload=owner.demo_mt5_lookup_request_to_payload(request),
        observed_at=observed_at,
    )
    assert payload["schema_version"] == script.RESULT_ENVELOPE_SCHEMA
    assert payload["request_fingerprint"] == request.fingerprint
    assert payload["result"]["status"] == "NOT_FOUND"
    assert payload["result"]["resubmit_allowed"] is False
    assert payload["result"]["session_slot_release_allowed"] is False
    assert payload["execution_capability"] == "NONE"
    assert payload["order_execution_enabled"] is False
    unsigned = dict(payload)
    observed = unsigned.pop("sha256")
    assert script._fingerprint(unsigned) == observed
    serialized = json.dumps(payload, sort_keys=True)
    assert str(evidence.LOGIN) not in serialized
    assert "password" not in serialized.lower()
    assert "token" not in serialized.lower()
    assert [call[0] for call in mt5.calls] == [
        "account_info",
        "orders_get",
        "history_orders_get",
        "history_deals_get",
        "account_info",  # Context must still match after all reads.
    ]


def test_runner_preserves_account_fail_closed_before_order_lookup(prepared_attempt):
    script = _load_script()
    request = _request(prepared_attempt)
    mt5 = evidence.FakeMt5(account_mode=evidence.FakeMt5.ACCOUNT_TRADE_MODE_REAL)
    payload = script.execute_readonly_lookup(
        mt5=mt5,
        request_payload=owner.demo_mt5_lookup_request_to_payload(request),
        observed_at=request.query_evaluated_at,
    )
    assert payload["result"]["status"] == "BLOCKED"
    assert payload["result"]["blockers"] == ["MT5_ACCOUNT_CONTEXT_MISMATCH"]
    assert mt5.calls == [("account_info",)]


def test_runner_rejects_tampered_request_before_mt5_query(prepared_attempt):
    script = _load_script()
    request = _request(prepared_attempt)
    raw = owner.demo_mt5_lookup_request_to_payload(request)
    raw["requested_quantity"] += 1
    mt5 = evidence.FakeMt5()
    try:
        script.execute_readonly_lookup(
            mt5=mt5,
            request_payload=raw,
            observed_at=datetime.now(timezone.utc),
        )
    except ValueError as exc:
        assert "fingerprint" in str(exc)
    else:
        raise AssertionError("tampered request unexpectedly accepted")
    assert mt5.calls == []


def test_runner_rejects_expired_history_window_before_mt5_query(prepared_attempt):
    script = _load_script()
    request = _request(prepared_attempt)
    mt5 = evidence.FakeMt5()
    try:
        script.execute_readonly_lookup(
            mt5=mt5,
            request_payload=owner.demo_mt5_lookup_request_to_payload(request),
            observed_at=request.history_to + timedelta(microseconds=1),
        )
    except ValueError as exc:
        assert "history window expired" in str(exc)
    else:
        raise AssertionError("expired lookup window unexpectedly accepted")
    assert mt5.calls == []


def test_windows_lookup_script_has_no_submission_cancel_or_modify_call():
    script = _load_script()
    source = Path(script.__file__).read_text()
    tree = ast.parse(source)
    forbidden = {
        "order_send",
        "order_check",
        "submit_order",
        "send_order",
        "place_order",
        "cancel_order",
        "modify_order",
    }
    seen_mt5_import = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [alias.name for alias in node.names]
            )
            if any(name.split(".")[0] == "MetaTrader5" for name in modules):
                seen_mt5_import = True
        if isinstance(node, ast.Call):
            name = (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else node.func.id
                if isinstance(node.func, ast.Name)
                else ""
            )
            assert name not in forbidden
    assert seen_mt5_import
