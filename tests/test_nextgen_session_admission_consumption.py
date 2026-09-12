from __future__ import annotations

import pytest

from daxlab.domain.session_admission import (
    SessionAdmissionConsumptionAction,
    SessionAdmissionConsumptionRecord,
    SessionAdmissionConsumptionState,
    SessionAdmissionPolicy,
    consume_session_admission,
    evaluate_session_admission,
)


SESSION_KEY = "2026-09-12-DE40-DAY"
CONSUMPTION_A = "a" * 64
CONSUMPTION_B = "b" * 64


def _initial(*, max_trades: int = 2):
    policy = SessionAdmissionPolicy.build(max_trades_per_session=max_trades)
    state = SessionAdmissionConsumptionState.build(session_key=SESSION_KEY)
    decision = evaluate_session_admission(
        policy=policy,
        observation=state.observation,
    )
    return policy, state, decision


def test_initial_state_derives_zero_count_observation() -> None:
    _, state, _ = _initial()

    assert state.session_key == SESSION_KEY
    assert state.records == ()
    assert state.trades_admitted == 0
    assert state.observation.session_key == SESSION_KEY
    assert state.observation.trades_admitted == 0


def test_new_consumption_increments_exactly_once_and_binds_provenance() -> None:
    policy, state, decision = _initial()

    transition = consume_session_admission(
        state=state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )

    assert transition.action is SessionAdmissionConsumptionAction.CONSUMED
    assert transition.consumed is True
    assert transition.idempotent_replay is False
    assert transition.state.trades_admitted == 1
    assert transition.observation.trades_admitted == 1
    assert transition.state.records[0].consumption_id == CONSUMPTION_A
    assert (
        transition.state.records[0].admission_decision_fingerprint
        == decision.decision_fingerprint
    )
    assert transition.execution_capability == "NONE"
    assert transition.order_execution_enabled is False


def test_same_consumption_id_is_idempotent_on_retry() -> None:
    policy, state, decision = _initial()
    first = consume_session_admission(
        state=state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )

    replay = consume_session_admission(
        state=first.state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )

    assert replay.action is SessionAdmissionConsumptionAction.IDEMPOTENT_REPLAY
    assert replay.consumed is False
    assert replay.idempotent_replay is True
    assert replay.state == first.state
    assert replay.state.trades_admitted == 1
    assert len(replay.state.records) == 1


def test_second_unique_consumption_uses_current_canonical_decision() -> None:
    policy, state, decision = _initial(max_trades=2)
    first = consume_session_admission(
        state=state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )
    second_decision = evaluate_session_admission(
        policy=policy,
        observation=first.state.observation,
    )

    second = consume_session_admission(
        state=first.state,
        policy=policy,
        decision=second_decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_B,
    )

    assert second.consumed is True
    assert second.state.trades_admitted == 2
    assert tuple(record.consumption_id for record in second.state.records) == (
        CONSUMPTION_A,
        CONSUMPTION_B,
    )


def test_new_consumption_is_rejected_after_session_limit() -> None:
    policy, state, decision = _initial(max_trades=1)
    first = consume_session_admission(
        state=state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )
    blocked = evaluate_session_admission(
        policy=policy,
        observation=first.state.observation,
    )
    assert blocked.allowed is False

    with pytest.raises(ValueError, match="blocked session admission cannot be consumed"):
        consume_session_admission(
            state=first.state,
            policy=policy,
            decision=blocked,
            session_key=SESSION_KEY,
            consumption_id=CONSUMPTION_B,
        )


def test_same_consumption_id_with_conflicting_decision_provenance_fails_closed() -> None:
    policy, state, decision = _initial(max_trades=3)
    first = consume_session_admission(
        state=state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )
    different_decision = evaluate_session_admission(
        policy=policy,
        observation=first.state.observation,
    )
    assert different_decision.allowed is True
    assert different_decision.decision_fingerprint != decision.decision_fingerprint

    with pytest.raises(ValueError, match="consumption provenance conflict"):
        consume_session_admission(
            state=first.state,
            policy=policy,
            decision=different_decision,
            session_key=SESSION_KEY,
            consumption_id=CONSUMPTION_A,
        )


def test_session_key_mismatch_never_resets_state() -> None:
    policy, state, decision = _initial()

    with pytest.raises(ValueError, match="consumption session key mismatch"):
        consume_session_admission(
            state=state,
            policy=policy,
            decision=decision,
            session_key="2026-09-13-DE40-DAY",
            consumption_id=CONSUMPTION_A,
        )


def test_stale_allow_decision_cannot_consume_new_unique_id() -> None:
    policy, state, decision = _initial(max_trades=3)
    first = consume_session_admission(
        state=state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )

    with pytest.raises(ValueError, match="current consumption state"):
        consume_session_admission(
            state=first.state,
            policy=policy,
            decision=decision,
            session_key=SESSION_KEY,
            consumption_id=CONSUMPTION_B,
        )


def test_state_rejects_duplicate_consumption_ids() -> None:
    record = SessionAdmissionConsumptionRecord.build(
        consumption_id=CONSUMPTION_A,
        admission_decision_fingerprint="c" * 64,
    )

    with pytest.raises(ValueError, match="consumption IDs must be unique"):
        SessionAdmissionConsumptionState.build(
            session_key=SESSION_KEY,
            records=(record, record),
        )


def test_consumption_transition_is_deterministic() -> None:
    policy, state, decision = _initial()

    first = consume_session_admission(
        state=state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )
    second = consume_session_admission(
        state=state,
        policy=policy,
        decision=decision,
        session_key=SESSION_KEY,
        consumption_id=CONSUMPTION_A,
    )

    assert first == second
    assert first.transition_fingerprint == second.transition_fingerprint
    assert first.state.state_fingerprint == second.state.state_fingerprint


def test_consumption_id_must_be_sha256_hex() -> None:
    policy, state, decision = _initial()

    with pytest.raises(ValueError, match="consumption_id must be sha256 hex"):
        consume_session_admission(
            state=state,
            policy=policy,
            decision=decision,
            session_key=SESSION_KEY,
            consumption_id="not-a-sha",
        )
