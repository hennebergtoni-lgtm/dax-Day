"""Operational read-only lookup preflight; injected SDK fixtures are not host proof."""
from dataclasses import replace
from datetime import datetime, timedelta
import json

import pytest

from daxlab.runtime.mt5_demo_evidence_transport import (
    demo_mt5_lookup_request_to_payload,
    derive_demo_mt5_transport_identity,
    validate_reserved_demo_mt5_lookup,
)
import test_mt5_demo_evidence_transport as evidence
from test_mt5_demo_evidence_lookup_script import _load_script
from test_mt5_windows_bundle import _seal

prepared_attempt = evidence.prepared_attempt


def setup(prepared_attempt):
    store, _, reservation, _, request = evidence._lookup(prepared_attempt)
    bundle = evidence.evidence._raw_bundle(account_fingerprint=evidence.ACCOUNT_FINGERPRINT)
    return dict(
        store=store, attempt_key="attempt",
        expected_reservation_fingerprint=reservation.fingerprint,
        bundle_payload=bundle,
        request_payload=demo_mt5_lookup_request_to_payload(request),
        observed_at=reservation.evaluated_at,
    ), reservation, request


def run(args, mt5):
    return _load_script().execute_reserved_readonly_lookup(mt5=mt5, **args)


def refreshed_bundle(payload, delta):
    payload = json.loads(json.dumps(payload))
    payload.pop("sha256")
    for section in ("host_probe", "closed_m5_feed"):
        payload[section]["observed_at"] = (
            datetime.fromisoformat(payload[section]["observed_at"]) + delta
        ).isoformat()
    for bar in payload["closed_m5_feed"]["bars"]:
        bar["open_time"] = (datetime.fromisoformat(bar["open_time"]) + delta).isoformat()
    return _seal(payload)


def test_valid_reserved_lookup_and_restart_leave_exact_state_unchanged(prepared_attempt):
    args, reservation, request = setup(prepared_attempt)
    store = args["store"]
    original = store.load("attempt")
    original_saves = store.saves
    results = []
    for _ in range(2):
        mt5 = evidence.FakeMt5()
        results.append(run(args, mt5))
        assert [call[0] for call in mt5.calls] == [
            "account_info", "orders_get", "history_orders_get", "history_deals_get",
        ]
    assert results[0] == results[1]
    assert results[0]["result"]["status"] == "NOT_FOUND"
    assert results[0]["result"]["resubmit_allowed"] is False
    assert results[0]["result"]["session_slot_release_allowed"] is False
    assert results[0]["reservation_fingerprint"] == reservation.fingerprint
    assert results[0]["request_fingerprint"] == request.fingerprint
    assert results[0]["execution_capability"] == "NONE"
    assert results[0]["order_execution_enabled"] is False
    assert store.load("attempt") == original
    assert store.saves == original_saves == 2


def test_wide_history_window_does_not_override_stale_host_preflight(prepared_attempt):
    args, _, request = setup(prepared_attempt)
    args["request_payload"] = demo_mt5_lookup_request_to_payload(
        replace(request, history_to=request.query_evaluated_at + timedelta(minutes=10))
    )
    args["observed_at"] += timedelta(seconds=31)
    mt5 = evidence.FakeMt5()
    with pytest.raises(ValueError, match="future or stale"):
        run(args, mt5)
    assert mt5.calls == []
    assert args["store"].saves == 2


def test_wide_history_window_and_fresh_host_do_not_override_expired_query_scope(prepared_attempt):
    args, _, request = setup(prepared_attempt)
    args["request_payload"] = demo_mt5_lookup_request_to_payload(
        replace(request, history_to=request.query_evaluated_at + timedelta(minutes=10))
    )
    delta = timedelta(minutes=6)
    args["observed_at"] += delta
    args["bundle_payload"] = refreshed_bundle(args["bundle_payload"], delta)
    mt5 = evidence.FakeMt5()
    with pytest.raises(ValueError, match="authorization blocked"):
        run(args, mt5)
    assert mt5.calls == []
    assert args["store"].saves == 2


@pytest.mark.parametrize("field", ["reservation", "identity", "account", "quantity"])
def test_rehashed_request_cross_wiring_rejects_before_sdk_reads(prepared_attempt, field):
    args, _, request = setup(prepared_attempt)
    changes = dict(reservation_fingerprint="f" * 64)
    if field == "identity":
        changes = dict(identity=derive_demo_mt5_transport_identity(client_order_id="f" * 64, symbol="DE40"))
    elif field == "account":
        changes = dict(account_context=replace(request.account_context, account_fingerprint="f" * 64))
        changes["account_context_fingerprint"] = changes["account_context"].fingerprint
    elif field == "quantity":
        changes = dict(requested_quantity=request.requested_quantity + 1)
    args["request_payload"] = demo_mt5_lookup_request_to_payload(replace(request, **changes))
    mt5 = evidence.FakeMt5()
    with pytest.raises(ValueError, match="cross-wiring"):
        run(args, mt5)
    assert mt5.calls == []


@pytest.mark.parametrize("change", ["key", "pin", "tamper", "history", "feed", "host_account"])
def test_pinned_current_evidence_failures_reject_before_sdk_reads(prepared_attempt, change):
    args, _, request = setup(prepared_attempt)
    if change == "key":
        args["attempt_key"] = "missing"
    elif change == "pin":
        args["expected_reservation_fingerprint"] = "f" * 64
    elif change == "tamper":
        args["request_payload"]["requested_quantity"] += 1
    elif change == "history":
        args["observed_at"] = request.history_to + timedelta(seconds=1)
    else:
        payload = args["bundle_payload"]
        payload.pop("sha256")
        if change == "feed":
            payload["closed_m5_feed"]["max_age_seconds"] = 0
            args["observed_at"] += timedelta(seconds=1)
        else:
            payload["host_probe"]["demo_account_context"]["account_fingerprint"] = "f" * 64
        args["bundle_payload"] = _seal(payload)
    mt5 = evidence.FakeMt5()
    with pytest.raises((ValueError, RuntimeError)):
        run(args, mt5)
    assert mt5.calls == []
    assert args["store"].saves == 2


def test_request_codec_is_unchanged_by_current_preflight(prepared_attempt):
    args, _, request = setup(prepared_attempt)
    result = validate_reserved_demo_mt5_lookup(
        store=args["store"], key=args["attempt_key"],
        expected_reservation_fingerprint=args["expected_reservation_fingerprint"],
        request_payload=args["request_payload"], bundle_payload=args["bundle_payload"],
        evaluated_at=args["observed_at"],
    )
    assert result == request
    assert demo_mt5_lookup_request_to_payload(result) == args["request_payload"]


@pytest.mark.parametrize("stale", [False, True])
def test_operational_cli_requires_current_preflight_before_sdk_initialization(
    prepared_attempt, tmp_path, monkeypatch, stale,
):
    import sys
    from daxlab.adapters.file_state_store import AtomicFileStateStore
    args, _, _ = setup(prepared_attempt)
    script = _load_script()
    store = AtomicFileStateStore(tmp_path / "state")
    original = args["store"].load("attempt")
    store.save("attempt", original)
    request_file, bundle_file, output_file = (
        tmp_path / "request.json", tmp_path / "bundle.json", tmp_path / "result.json"
    )
    request_file.write_text(json.dumps(args["request_payload"]))
    bundle_file.write_text(json.dumps(args["bundle_payload"]))
    mt5 = evidence.FakeMt5()
    sdk_lifecycle = []
    mt5.initialize = lambda: sdk_lifecycle.append("initialize") or True
    mt5.shutdown = lambda: sdk_lifecycle.append("shutdown")
    monkeypatch.setitem(sys.modules, "MetaTrader5", mt5)

    class ClockDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return args["observed_at"] + timedelta(seconds=31 if stale else 0)

    monkeypatch.setattr(script, "datetime", ClockDatetime)
    monkeypatch.setattr(sys, "argv", [
        "lookup", "--state-dir", str(tmp_path / "state"),
        "--attempt-key", "attempt", "--reservation-fingerprint",
        args["expected_reservation_fingerprint"], "--request", str(request_file),
        "--bundle", str(bundle_file), "--output", str(output_file),
    ])
    if stale:
        with pytest.raises(ValueError, match="future or stale"):
            script.main()
        assert sdk_lifecycle == []
        assert mt5.calls == []
        assert not output_file.exists()
    else:
        assert script.main() == 0
        assert sdk_lifecycle == ["initialize", "shutdown"]
        assert json.loads(output_file.read_text())["result"]["status"] == "NOT_FOUND"
    assert store.load("attempt") == original
