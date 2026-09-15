from dataclasses import replace
from datetime import timedelta
import hashlib
import json

import pytest

from daxlab.domain.execution import ExecutionIntent, OrderSide
from daxlab.domain.market import InstrumentId
from daxlab.runtime import demo_transport_attempt_reservation as owner
from daxlab.runtime.demo_evidence_authorization import (
    DEMO_EVIDENCE_AUTHORIZATION_SCHEMA,
    DemoEvidenceAction,
    DemoEvidenceAuthorization,
)
from daxlab.runtime.mt5_windows_bundle import parse_windows_mt5_bundle
from daxlab.runtime.nextgen_prepared_checkpoint import (
    build_nextgen_prepared_checkpoint,
    prepare_nextgen_checkpoint,
)
import test_nextgen_execution_protection_binding as evidence


class MemoryStore:
    def __init__(self):
        self.values = {}
        self.saves = 0

    def load(self, key):
        return self.values.get(key)

    def save(self, key, payload):
        self.values[key] = payload
        self.saves += 1


def _seal(payload: dict) -> dict:
    value = dict(payload)
    value.pop("sha256", None)
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    value["sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    return value


def _raw_bundle(*, account_fingerprint: str = "c" * 64, server: str = "Demo-Server") -> dict:
    observed = evidence.EVALUATED_AT
    bars = []
    for minutes in (15, 10, 5):
        t = observed - timedelta(minutes=minutes)
        bars.append(
            {
                "open_time": t.isoformat(),
                "open": 25000.0,
                "high": 25002.0,
                "low": 24999.0,
                "close": 25001.0,
            }
        )
    return _seal(
        {
            "schema": "DAXLAB_MT5_WINDOWS_BUNDLE_V1",
            "symbol_resolution_state": "AUTO_EXACT_ALIAS_DATA_ONLY",
            "host_probe": {
                "observed_at": observed.isoformat(),
                "terminal_connected": True,
                "account_connected": True,
                "account_trade_allowed": True,
                "order_execution_enabled": False,
                "engine_loop_healthy": True,
                "clock_ok": True,
                "symbols": [
                    {
                        "name": "DE40",
                        "digits": 2,
                        "point": 0.01,
                        "trade_mode": "DISABLED",
                        "contract_size": 1.0,
                        "volume_min": 0.1,
                        "volume_step": 0.1,
                    }
                ],
                "demo_account_context": {
                    "schema_version": "DAXLAB_MT5_DEMO_ACCOUNT_CONTEXT_V1",
                    "account_fingerprint": account_fingerprint,
                    "server": server,
                    "symbol": "DE40",
                    "account_mode": "DEMO",
                    "trade_allowed": True,
                    "execution_capability": "NONE",
                    "order_execution_enabled": False,
                },
            },
            "closed_m5_feed": {
                "observed_at": observed.isoformat(),
                "requested_start_pos": 1,
                "max_age_seconds": 600.0,
                "bars": bars,
            },
            "notes": [
                "READ_ONLY",
                "BAR_0_EXCLUDED",
                "NO_CREDENTIALS",
                "NO_ORDER_API",
            ],
        }
    )


def _authorization(*, authorization_id: str = "AUTH-1", max_submissions: int = 2):
    observed = evidence.EVALUATED_AT
    return DemoEvidenceAuthorization(
        schema_version=DEMO_EVIDENCE_AUTHORIZATION_SCHEMA,
        authorization_id=authorization_id,
        account_id="c" * 64,
        server="Demo-Server",
        symbol="DE40",
        valid_from=observed - timedelta(minutes=1),
        expires_at=observed + timedelta(minutes=5),
        allowed_actions=(
            DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,
            DemoEvidenceAction.QUERY_EVIDENCE_ORDER,
        ),
        max_submissions=max_submissions,
    )


@pytest.fixture
def prepared_attempt(monkeypatch):
    intent = ExecutionIntent.build(
        decision_id="a" * 64,
        provenance_fingerprint="b" * 64,
        created_at=evidence.EVALUATED_AT - timedelta(seconds=2),
        instrument_id=InstrumentId("DAX40.CFD"),
        side=OrderSide.BUY,
        quantity=2.5,
        requested_price=25000.0,
        stop_price=24900.0,
        target_price=25200.0,
    )
    policy, state, admission = evidence._session_chain()
    guard = evidence._session_guard(policy, state)
    monkeypatch.setattr(evidence, "CLIENT_ID", intent.intent_id)
    protection = evidence._evaluate(session=(policy, state, admission), session_guard=guard)
    assert protection.allow_evidence
    attempt = dict(
        intent=intent,
        policy=policy,
        admission=admission,
        pre_guard=guard,
        protection=protection,
        requested_at=intent.created_at + timedelta(seconds=1),
    )
    store = MemoryStore()
    prepared = prepare_nextgen_checkpoint(store=store, key="attempt", **attempt)
    assert store.saves == 1
    return store, prepared


def _reserve(store, prepared, **changes):
    args = dict(
        store=store,
        key="attempt",
        prepared=prepared,
        authorization=_authorization(),
        bundle=parse_windows_mt5_bundle(_raw_bundle()),
        evaluated_at=evidence.EVALUATED_AT,
        max_host_age_seconds=30.0,
        submission_ordinal=1,
    )
    args.update(changes)
    return owner.reserve_demo_transport_attempt(**args)


def test_reservation_advances_same_key_and_roundtrips(prepared_attempt):
    store, prepared = prepared_attempt
    reservation = _reserve(store, prepared)
    assert store.saves == 2
    assert list(store.values) == ["attempt"]
    assert reservation.status == owner.STATUS
    assert reservation.prepared == prepared
    assert reservation.prepared_fingerprint == prepared.fingerprint
    assert reservation.authorization_fingerprint == reservation.authorization.fingerprint
    assert reservation.account_context_fingerprint == reservation.account_context.fingerprint
    assert reservation.execution_capability == "NONE"
    assert reservation.order_execution_enabled is False
    restored = owner.demo_transport_attempt_reservation_from_bytes(store.load("attempt"))
    assert restored == reservation
    assert restored.fingerprint == reservation.fingerprint
    assert owner.demo_transport_attempt_reservation_to_bytes(restored) == store.load("attempt")


def test_exact_replay_returns_original_without_second_save(prepared_attempt):
    store, prepared = prepared_attempt
    first = _reserve(store, prepared)
    second = _reserve(store, prepared)
    third = _reserve(store, prepared)
    assert first == second == third
    assert store.saves == 2


@pytest.mark.parametrize("change", ["authorization", "bundle", "ordinal"])
def test_reserved_key_cross_wiring_fails_without_save(prepared_attempt, change):
    store, prepared = prepared_attempt
    _reserve(store, prepared)
    kwargs = {}
    if change == "authorization":
        kwargs["authorization"] = _authorization(authorization_id="AUTH-2")
    elif change == "bundle":
        raw = _raw_bundle()
        raw.pop("sha256")
        raw["closed_m5_feed"]["bars"][-1]["close"] = 25001.5
        raw["closed_m5_feed"]["bars"][-1]["high"] = 25002.5
        kwargs["bundle"] = parse_windows_mt5_bundle(_seal(raw))
    else:
        kwargs["submission_ordinal"] = 2
    with pytest.raises(ValueError, match="collision"):
        _reserve(store, prepared, **kwargs)
    assert store.saves == 2


def test_different_valid_prepared_on_reserved_key_fails_closed(prepared_attempt):
    store, prepared = prepared_attempt
    _reserve(store, prepared)
    other = build_nextgen_prepared_checkpoint(
        intent=prepared.intent,
        policy=prepared.policy,
        admission=prepared.admission,
        pre_guard=prepared.pre_guard,
        protection=prepared.protection,
        requested_at=prepared.broker.lifecycle.last_event_time + timedelta(seconds=1),
    )
    assert other.fingerprint != prepared.fingerprint
    with pytest.raises(ValueError, match="collision"):
        _reserve(store, other)
    assert store.saves == 2


def test_missing_prepared_state_never_creates_reservation(prepared_attempt):
    _, prepared = prepared_attempt
    store = MemoryStore()
    with pytest.raises(ValueError, match="existing PREPARED"):
        _reserve(store, prepared)
    assert store.saves == 0


def test_stale_host_evidence_blocks_before_save(prepared_attempt):
    store, prepared = prepared_attempt
    with pytest.raises(ValueError, match="stale"):
        _reserve(
            store,
            prepared,
            evaluated_at=evidence.EVALUATED_AT + timedelta(seconds=31),
        )
    assert store.saves == 1


def test_red_windows_bundle_blocks_before_save(prepared_attempt):
    store, prepared = prepared_attempt
    raw = _raw_bundle()
    raw.pop("sha256")
    raw["host_probe"]["terminal_connected"] = False
    bundle = parse_windows_mt5_bundle(_seal(raw))
    assert not bundle.green
    with pytest.raises(ValueError, match="GREEN"):
        _reserve(store, prepared, bundle=bundle)
    assert store.saves == 1


def test_missing_demo_context_blocks_before_save(prepared_attempt):
    store, prepared = prepared_attempt
    raw = _raw_bundle()
    raw.pop("sha256")
    raw["host_probe"].pop("demo_account_context")
    bundle = parse_windows_mt5_bundle(_seal(raw))
    with pytest.raises(ValueError, match="DEMO account context"):
        _reserve(store, prepared, bundle=bundle)
    assert store.saves == 1


def test_same_bundle_trade_allowed_cross_wiring_blocks(prepared_attempt):
    store, prepared = prepared_attempt
    raw = _raw_bundle()
    raw.pop("sha256")
    raw["host_probe"]["account_trade_allowed"] = False
    bundle = parse_windows_mt5_bundle(_seal(raw))
    with pytest.raises(ValueError, match="trade-allowed mismatch"):
        _reserve(store, prepared, bundle=bundle)
    assert store.saves == 1


def test_same_bundle_symbol_cross_wiring_blocks(prepared_attempt):
    store, prepared = prepared_attempt
    raw = _raw_bundle()
    raw.pop("sha256")
    raw["host_probe"]["demo_account_context"]["symbol"] = "DAX-DEMO-OTHER"
    bundle = parse_windows_mt5_bundle(_seal(raw))
    with pytest.raises(ValueError, match="symbol is not in host bundle"):
        _reserve(store, prepared, bundle=bundle)
    assert store.saves == 1


def test_authorization_scope_mismatch_blocks_before_save(prepared_attempt):
    store, prepared = prepared_attempt
    bad = replace(_authorization(), server="Other-Demo-Server")
    with pytest.raises(ValueError, match="authorization blocked"):
        _reserve(store, prepared, authorization=bad)
    assert store.saves == 1


def test_submission_limit_blocks_before_save(prepared_attempt):
    store, prepared = prepared_attempt
    with pytest.raises(ValueError, match="SUBMISSION_LIMIT_REACHED"):
        _reserve(
            store,
            prepared,
            authorization=_authorization(max_submissions=1),
            submission_ordinal=2,
        )
    assert store.saves == 1


def test_rehashed_outer_cross_wiring_still_fails_nested_invariants(prepared_attempt):
    store, prepared = prepared_attempt
    reservation = _reserve(store, prepared)
    raw = json.loads(owner.demo_transport_attempt_reservation_to_bytes(reservation))
    raw["prepared_fingerprint"] = "d" * 64
    raw.pop("reservation_fingerprint")
    raw["reservation_fingerprint"] = owner._fingerprint(raw)
    with pytest.raises(ValueError, match="PREPARED fingerprint mismatch"):
        owner.demo_transport_attempt_reservation_from_bytes(owner._bytes(raw))


def test_reservation_owner_exposes_no_order_submission_api():
    forbidden = {"order_send", "submit_order", "send_order", "place_order"}
    assert not forbidden.intersection(set(dir(owner)))
