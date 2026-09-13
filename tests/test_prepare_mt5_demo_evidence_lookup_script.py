from datetime import timedelta
import ast
import importlib.util
from pathlib import Path

import pytest

from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.runtime import demo_transport_attempt_reservation as reservation_owner
from daxlab.runtime import mt5_demo_evidence_transport as transport_owner
import test_mt5_demo_evidence_transport as evidence

prepared_attempt = evidence.prepared_attempt


def _load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "prepare_mt5_demo_evidence_lookup.py"
    spec = importlib.util.spec_from_file_location("prepare_mt5_demo_evidence_lookup", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _file_reservation(tmp_path, prepared_attempt):
    _, _, reservation = evidence._reservation(prepared_attempt)
    store = AtomicFileStateStore(tmp_path)
    store.save(
        "attempt",
        reservation_owner.demo_transport_attempt_reservation_to_bytes(reservation),
    )
    return store, reservation


def test_prepare_uses_exact_file_state_and_does_not_mutate_it(tmp_path, prepared_attempt):
    script = _load_script()
    store, reservation = _file_reservation(tmp_path, prepared_attempt)
    before = store.load("attempt")
    history_from = reservation.prepared.broker.lifecycle.last_event_time - timedelta(minutes=1)
    history_to = reservation.evaluated_at + timedelta(minutes=1)
    payload = script.prepare_lookup_request(
        state_dir=tmp_path,
        attempt_key="attempt",
        expected_reservation_fingerprint=reservation.fingerprint,
        bundle_payload=evidence.evidence._raw_bundle(
            account_fingerprint=evidence.ACCOUNT_FINGERPRINT
        ),
        history_from=history_from,
        history_to=history_to,
        evaluated_at=reservation.evaluated_at,
    )
    request = transport_owner.demo_mt5_lookup_request_from_payload(payload)
    assert request.reservation_fingerprint == reservation.fingerprint
    assert request.identity.client_order_id == reservation.prepared.intent.intent_id
    assert request.account_context_fingerprint == reservation.account_context_fingerprint
    assert request.execution_capability == "NONE"
    assert request.order_execution_enabled is False
    assert store.load("attempt") == before


def test_prepare_wrong_pin_and_stale_bundle_fail_without_state_change(tmp_path, prepared_attempt):
    script = _load_script()
    store, reservation = _file_reservation(tmp_path, prepared_attempt)
    before = store.load("attempt")
    common = dict(
        state_dir=tmp_path,
        attempt_key="attempt",
        bundle_payload=evidence.evidence._raw_bundle(
            account_fingerprint=evidence.ACCOUNT_FINGERPRINT
        ),
        history_from=reservation.prepared.broker.lifecycle.last_event_time
        - timedelta(minutes=1),
        history_to=reservation.evaluated_at + timedelta(minutes=2),
    )
    with pytest.raises(ValueError, match="collision"):
        script.prepare_lookup_request(
            expected_reservation_fingerprint="d" * 64,
            evaluated_at=reservation.evaluated_at,
            **common,
        )
    with pytest.raises(ValueError, match="stale"):
        script.prepare_lookup_request(
            expected_reservation_fingerprint=reservation.fingerprint,
            evaluated_at=reservation.evaluated_at + timedelta(seconds=31),
            **common,
        )
    assert store.load("attempt") == before


def test_prepare_script_has_no_mt5_or_broker_side_effect_surface():
    script = _load_script()
    source = Path(script.__file__).read_text()
    tree = ast.parse(source)
    forbidden = {
        "order_send",
        "order_check",
        "orders_get",
        "history_orders_get",
        "history_deals_get",
        "cancel_order",
        "modify_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [alias.name for alias in node.names]
            )
            assert all(name.split(".")[0] != "MetaTrader5" for name in modules)
        if isinstance(node, ast.Call):
            name = (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else node.func.id
                if isinstance(node.func, ast.Name)
                else ""
            )
            assert name not in forbidden
