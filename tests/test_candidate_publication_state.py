from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from daxlab.runtime.atomic_json import atomic_write_json, read_json_object
from daxlab.runtime.candidate_publication_state import (
    Cand001PublicationState,
    admit_cand001_intent_publication,
    admit_cand001_outcome_publication,
    candidate_publication_state_payload,
    parse_candidate_publication_state_payload,
)
from daxlab.runtime.candidate_virtual_lifecycle import (
    advance_cand001_virtual_lifecycle,
    start_cand001_virtual_lifecycle,
)
from daxlab.runtime.candidate_virtual_outcome import build_cand001_virtual_outcome
from daxlab.runtime.contracts import Candle
from daxlab.runtime.decision import DecisionRecord, FinalAction
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


UTC = timezone.utc
DECISION_TIME = datetime(2026, 9, 11, 9, 20, tzinfo=UTC)


def _decision(seed: str = "a") -> DecisionRecord:
    return DecisionRecord.build(
        event_time=DECISION_TIME,
        data_fingerprint=seed * 64,
        regime="ALL",
        structure="CONFIRMED_BREAKOUT_CLOSE/OR15",
        setup="LONG_BREAKOUT",
        filter_results={"entry_confirmed": True},
        blockers=(),
        risk_result="ADMITTED",
        config={"candidate_id": "CAND-001", "seed": seed},
        core_version="1.0-alpha",
        final_action=FinalAction.TRADE,
    )


def _intent(decision: DecisionRecord) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id=decision.decision_id,
        run_manifest_fingerprint="2" * 64,
        created_at=decision.event_time,
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=100.0,
        stop_price=90.0,
        target_price=115.0,
    )


def _outcome(decision: DecisionRecord):
    intent = _intent(decision)
    lifecycle = start_cand001_virtual_lifecycle(intent)
    candle = Candle(
        symbol="DE40",
        timeframe="M5",
        event_time=DECISION_TIME,
        close_time=DECISION_TIME + timedelta(minutes=5),
        open=100.0,
        high=116.0,
        low=95.0,
        close=114.0,
        volume=None,
        source="TEST",
        received_at=DECISION_TIME + timedelta(minutes=5, seconds=1),
        is_closed=True,
    )
    closed = advance_cand001_virtual_lifecycle(lifecycle, candle)
    return build_cand001_virtual_outcome(decision=decision, lifecycle=closed)


def test_intent_is_admitted_once_and_duplicate_is_rejected() -> None:
    intent = _intent(_decision())
    first = admit_cand001_intent_publication(Cand001PublicationState(), intent)
    duplicate = admit_cand001_intent_publication(first.state, intent)

    assert first.accepted is True
    assert duplicate.accepted is False
    assert duplicate.state == first.state
    assert first.publication_id == intent.client_order_id
    assert first.publication_kind == "INTENT"


def test_intent_duplicate_remains_rejected_after_atomic_restart(tmp_path) -> None:
    intent = _intent(_decision())
    first = admit_cand001_intent_publication(Cand001PublicationState(), intent)
    path = tmp_path / "cand001_publication_state.json"
    atomic_write_json(path, candidate_publication_state_payload(first.state))

    restored = parse_candidate_publication_state_payload(read_json_object(path))
    duplicate = admit_cand001_intent_publication(restored, intent)

    assert restored == first.state
    assert duplicate.accepted is False
    assert duplicate.state == restored


def test_outcome_duplicate_remains_rejected_after_atomic_restart(tmp_path) -> None:
    outcome = _outcome(_decision())
    first = admit_cand001_outcome_publication(Cand001PublicationState(), outcome)
    path = tmp_path / "cand001_publication_state.json"
    atomic_write_json(path, candidate_publication_state_payload(first.state))

    restored = parse_candidate_publication_state_payload(read_json_object(path))
    duplicate = admit_cand001_outcome_publication(restored, outcome)

    assert restored == first.state
    assert duplicate.accepted is False
    assert duplicate.publication_id == outcome.outcome_id
    assert duplicate.publication_kind == "OUTCOME"


def test_intent_and_outcome_namespaces_are_independent_and_persist_together() -> None:
    decision = _decision()
    intent = _intent(decision)
    outcome = _outcome(decision)

    intent_admission = admit_cand001_intent_publication(Cand001PublicationState(), intent)
    outcome_admission = admit_cand001_outcome_publication(intent_admission.state, outcome)
    restored = parse_candidate_publication_state_payload(
        candidate_publication_state_payload(outcome_admission.state)
    )

    assert intent_admission.accepted is True
    assert outcome_admission.accepted is True
    assert restored.published_intent_ids == (intent.client_order_id,)
    assert restored.published_outcome_ids == (outcome.outcome_id,)


def test_distinct_publication_ids_are_admitted() -> None:
    first_intent = _intent(_decision("a"))
    second_intent = _intent(_decision("b"))
    first = admit_cand001_intent_publication(Cand001PublicationState(), first_intent)
    second = admit_cand001_intent_publication(first.state, second_intent)

    assert first.accepted is True
    assert second.accepted is True
    assert len(second.state.published_intent_ids) == 2


def test_tampered_persisted_journal_fails_closed() -> None:
    intent = _intent(_decision())
    admitted = admit_cand001_intent_publication(Cand001PublicationState(), intent)
    payload = candidate_publication_state_payload(admitted.state)
    tampered = deepcopy(payload)
    tampered["published_intent_ids"] = []

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        parse_candidate_publication_state_payload(tampered)


def test_execution_escalation_in_persisted_journal_fails_closed() -> None:
    payload = candidate_publication_state_payload(Cand001PublicationState())
    tampered = deepcopy(payload)
    tampered["execution_capability"] = "BROKER"

    with pytest.raises(ValueError, match="execution capability"):
        parse_candidate_publication_state_payload(tampered)
