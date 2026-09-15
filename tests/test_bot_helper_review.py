"""Independent hostile review regressions, fixed expectations beyond first pass."""
from dataclasses import replace
from datetime import timedelta

import pytest

from daxlab.domain.market import InstrumentId
from daxlab.runtime.bot_helper import coordinate, run_helper_shadow_candle
from daxlab.runtime.bot_helper_contract import observation
from daxlab.runtime.candidate_shadow_orchestrator import Cand001ShadowState
from test_bot_helper_acceptance import bar, events, manifest, subject


def test_review_expired_previous_dependency_cannot_support_current_pass():
    now = bar().received_at
    old = observation(subject(), "B", "PASS", source_time=now-timedelta(minutes=2),
                      observed_at=now-timedelta(minutes=2), valid_until=now-timedelta(minutes=1),
                      evidence_scope="SYNTHETIC", producer_epoch="e"*64)
    current = list(events(now))
    current[-1] = replace(current[-1], dependency_event_ids=(old.event_id,))
    result = coordinate(current, subject=subject(), now=now, previous=(old,))
    assert not result.shadow_allowed
    assert "SOURCE_STALE" in result.checks[-1].reason_codes


def test_review_same_cycle_sequence_reversal_is_blocked():
    now = bar().received_at
    base = events(now)
    result = coordinate((replace(base[0], source_sequence=2),
                         replace(base[0], source_sequence=1), *base[1:]),
                        subject=subject(), now=now)
    assert not result.shadow_allowed
    assert "SOURCE_ORDER" in result.blockers


def test_review_gold_subject_cannot_admit_dax_bar():
    bound = replace(subject(), instrument_id=InstrumentId("GOLD"))
    candle = bar()
    original = Cand001ShadowState()
    result = run_helper_shadow_candle(
        original, candle, observed_at=candle.received_at, run_manifest=manifest(),
        subject=bound, events=events(candle.received_at, subject_value=bound))
    assert not result.cycle.shadow_allowed
    assert "IDENTITY_MISMATCH" in result.cycle.blockers
    assert result.state == original and result.shadow_result is None


def test_review_mutated_nested_subject_cannot_bypass_constructor():
    bound = subject()
    current = events(bar().received_at, subject_value=bound)
    object.__setattr__(bound, "environment", "LIVE")
    with pytest.raises(ValueError):
        coordinate(current, subject=bound, now=bar().received_at)


@pytest.mark.parametrize("bad_subject", [None, {}, "SYNTHETIC"])
def test_review_malformed_subject_is_rejected(bad_subject):
    with pytest.raises(ValueError):
        coordinate((), subject=bad_subject, now=bar().received_at)


def test_review_dense_bounded_dag_has_deterministic_result():
    now = bar().received_at
    base = events(now)
    previous_layer = ()
    graph = []
    # 7x32 nodes, full fan-in: guard against exponential path enumeration.
    for layer in range(7):
        current_layer = tuple(replace(base[0], source_sequence=layer*32+i,
                                      dependency_event_ids=previous_layer) for i in range(32))
        graph.extend(current_layer)
        previous_layer = tuple(event.event_id for event in current_layer)
    result = coordinate((*graph, *base[1:]), subject=subject(), now=now)
    assert result.shadow_allowed
    assert len(result.event_refs) == 228
    overflow = coordinate((*graph, *base[1:], *graph[:33]), subject=subject(), now=now)
    assert not overflow.shadow_allowed
    assert "EVENT_OVERFLOW" in overflow.blockers
    assert len(overflow.checks) == 5


@pytest.mark.parametrize("fault", ["stale", "open", "wrong_instrument", "missing_identity", "foreign_window", "window_revision", "window_gap", "window_stale"])
def test_review_normal_owner_rechecks_actual_input_despite_green_helper_claim(fault):
    from daxlab.runtime.candidate_shadow_orchestrator import process_cand001_shadow_candle

    candle = bar()
    bound = subject()
    now = candle.received_at
    window = None
    if fault == "stale":
        now += timedelta(minutes=20)
    elif fault == "open":
        candle = replace(candle, is_closed=False)
    elif fault == "wrong_instrument":
        bound = replace(bound, instrument_id=InstrumentId("GOLD"))
    elif fault == "missing_identity":
        bound = replace(bound, code_head=None)
    elif fault == "foreign_window":
        window = (bar(1),)
    elif fault == "window_revision":
        window = (replace(candle, close=candle.close + 1),)
    elif fault == "window_gap":
        window = (candle, bar(2))
        now = bar(2).received_at
    elif fault == "window_stale":
        window = (candle, bar(1))
        now = bar(1).received_at + timedelta(minutes=20)
    state = Cand001ShadowState()
    with pytest.raises(ValueError, match="HELPER_ADMISSION_BLOCKED"):
        process_cand001_shadow_candle(
            state, candle, observed_at=now, run_manifest=manifest(),
            helper_events=events(now, subject_value=bound), helper_subject=bound,
            helper_window=window,
        )
    assert state == Cand001ShadowState()


def test_review_bound_fresh_window_preserves_approved_historical_catchup():
    from daxlab.runtime.candidate_shadow_orchestrator import process_cand001_shadow_candle

    window = (bar(), bar(1), bar(2))
    now = window[-1].received_at
    before = tuple((c.event_time, c.close_time, c.received_at) for c in window)
    result = process_cand001_shadow_candle(
        Cand001ShadowState(), window[0], observed_at=now, run_manifest=manifest(),
        helper_events=events(now), helper_subject=subject(), helper_window=window,
    )
    assert result.state.pipeline.signal.last_close_time == window[0].close_time
    assert tuple((c.event_time, c.close_time, c.received_at) for c in window) == before
    assert result.order_execution_enabled is False


@pytest.mark.parametrize("variant, admitted", [
    ("complete", True), ("partial_inventory", True), ("partial_prices", False),
    ("partial_market", True), ("wrong_instrument", False), ("wrong_version", False),
    ("semantics_end", False), ("basis_receipt", False),
    ("semantics_missing", False), ("basis_missing", False),
    ("semantics_unknown", False), ("basis_unknown", False),
    ("snapshot_mismatch", False), ("snapshot_missing", False), ("snapshot_offgrid", False),
])
def test_review_T14_actual_v3_to_safety_runtime_and_same_get_evidence(tmp_path, monkeypatch, variant, admitted):
    import json
    import threading
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from daxlab.adapters.ig_market_data import canonical_ig_m5_contract
    from daxlab.runtime.atomic_json import atomic_write_json
    from daxlab.runtime.bot_helper import run_ig_readiness_shadow
    from daxlab.runtime.decision import stable_fingerprint
    from daxlab.runtime import ig_predemo_safety
    from test_bot_helper_operator import console
    from test_operator_console_http import request
    from test_run_ig_predemo_readiness_2238 import MatrixClient, runner

    failed = {"partial_inventory": "POSITIONS_B", "partial_prices": "M5_PRICES",
              "partial_market": "MARKET_V4"}.get(variant)
    client = MatrixClient(raise_resource=failed)
    evidence, _ = runner.collect(client, epic="IX.D.DAX.IFMM.IP", instrument_id="DAX", bars=40)
    evidence = runner._finalize_evidence(evidence, cleanup_status="PASS", cleanup_error_code="NONE")[0]
    if variant in {"wrong_instrument", "wrong_version"}:
        evidence["instrument_id" if variant == "wrong_instrument" else "schema"] = (
            "GOLD" if variant == "wrong_instrument" else "DAXLAB_IG_PREDEMO_READINESS_V9")
        evidence.pop("fingerprint")
        evidence["fingerprint"] = runner._fingerprint(evidence)
    contract_faults = {
        "semantics_end": ("timestamp_semantics", "INTERVAL_END"),
        "basis_receipt": ("freshness_basis", "RECEIPT_TIME"),
        "semantics_missing": ("timestamp_semantics", None),
        "basis_missing": ("freshness_basis", None),
        "semantics_unknown": ("timestamp_semantics", "UNKNOWN"),
        "basis_unknown": ("freshness_basis", "UNKNOWN"),
    }
    if variant in contract_faults:
        field, value = contract_faults[variant]
        if value is None:
            evidence["market_data"].pop(field)
        else:
            evidence["market_data"][field] = value
    elif variant == "snapshot_mismatch":
        evidence["market_data"]["latest_closed_m5"]["snapshot_time_utc"] = "2026-09-15T07:00:00+00:00"
    elif variant == "snapshot_offgrid":
        row = evidence["market_data"]["latest_closed_m5"]
        for field in ("snapshot_time_utc", "event_time", "close_time"):
            row[field] = (datetime.fromisoformat(row[field]) + timedelta(minutes=1)).isoformat()
    elif variant == "snapshot_missing":
        evidence["market_data"]["latest_closed_m5"].pop("snapshot_time_utc")
    if variant in contract_faults or variant.startswith("snapshot_"):
        evidence.pop("fingerprint")
        evidence["fingerprint"] = runner._fingerprint(evidence)
    untouched = json.dumps(evidence, sort_keys=True)
    source_session = datetime.fromisoformat(evidence["collected_at_utc"]).astimezone(ZoneInfo("Europe/Berlin")).date().isoformat()
    bound = replace(subject(), provider="IG", environment="DEMO", instrument_id=InstrumentId("DAX"),
                    session_id=source_session,
                    market_contract_fingerprint=stable_fingerprint(canonical_ig_m5_contract()),
                    account_fingerprint=evidence["account"]["account_context_fingerprint"])
    binding_calls = []
    original_binding = ig_predemo_safety.bind_ig_risk_session_inputs
    def traced_binding(value, **kwargs):
        binding_calls.append(value["fingerprint"])
        return original_binding(value, **kwargs)
    monkeypatch.setattr(ig_predemo_safety, "bind_ig_risk_session_inputs", traced_binding)
    state = Cand001ShadowState()
    result = run_ig_readiness_shadow(
        state, evidence, subject=bound, observed_at=datetime.fromisoformat(evidence["collected_at_utc"]),
        run_manifest=manifest(), instrument_id=InstrumentId("DAX"), epic="IX.D.DAX.IFMM.IP")
    assert result.cycle.shadow_allowed is admitted
    assert result.cycle.as_dict()["order_execution_enabled"] is False
    if admitted:
        assert result.shadow_result is not None
        assert result.shadow_result.intent_to_publish is None
        assert "BROKER_UNKNOWN" in result.cycle.blockers
        assert evidence["market"].get("quantity_step") is None
        assert evidence["market"]["economics_verified"] is False
    else:
        assert result.shadow_result is None and result.state == state
    path = tmp_path / "READINESS.json"
    atomic_write_json(path, evidence)
    server = console.OperatorReadServer(
        state_dir=tmp_path, port=0, ig_evidence_path=path,
        ig_evidence_fingerprint=evidence["fingerprint"], ig_instrument_id="DAX")
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        code, _, body = request(server)
        view = json.loads(body)
        assert view["execution_capability"] == "NONE"
        assert view["order_execution_enabled"] is False
        if variant in {"wrong_instrument", "wrong_version"}:
            assert code == 503
        else:
            assert code == 200
            assert view["provenance"]["snapshot_fingerprint"] == evidence["fingerprint"]
            assert len(view["read_outcomes"]) == 8
            assert "BROKER_ECONOMICS_UNVERIFIED" in view["blockers"]
            assert view["system"]["EXECUTION"]["state"] == "DISABLED"
            if failed:
                assert next(row for row in view["read_outcomes"] if row["resource"] == failed)["status"] == "UNKNOWN"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    if variant == "wrong_version":
        assert binding_calls == []  # Rejected before either consumer can bind.
    else:
        assert binding_calls and all(fp == evidence["fingerprint"] for fp in binding_calls)
    assert json.dumps(evidence, sort_keys=True) == untouched
    assert client.calls == [name for name, _ in runner.READ_RESOURCE_CONTRACTS]
    assert client.login_calls == 0 and client.logout_calls == 0
