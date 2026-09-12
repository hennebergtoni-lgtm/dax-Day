from dataclasses import replace
from pathlib import Path

import pytest

from daxlab.domain.session_admission import (
    SessionAdmissionAction,
    SessionAdmissionObservation,
    SessionAdmissionPolicy,
    evaluate_session_admission,
)


def test_below_limit_allows_deterministically() -> None:
    policy = SessionAdmissionPolicy.build(max_trades_per_session=2)
    observation = SessionAdmissionObservation.build(
        session_key="2026-09-12-DE40-DAY",
        trades_admitted=1,
    )

    first = evaluate_session_admission(policy=policy, observation=observation)
    second = evaluate_session_admission(policy=policy, observation=observation)

    assert first == second
    assert first.action is SessionAdmissionAction.ALLOW
    assert first.allowed is True
    assert first.reason_codes == ("WITHIN_SESSION_TRADE_LIMIT",)
    assert first.policy_fingerprint == policy.policy_fingerprint
    assert first.observation_fingerprint == observation.observation_fingerprint
    assert len(first.decision_fingerprint) == 64


@pytest.mark.parametrize("trades_admitted", [2, 3])
def test_equal_or_above_limit_blocks(trades_admitted: int) -> None:
    policy = SessionAdmissionPolicy.build(max_trades_per_session=2)
    observation = SessionAdmissionObservation.build(
        session_key="session-A",
        trades_admitted=trades_admitted,
    )

    decision = evaluate_session_admission(policy=policy, observation=observation)

    assert decision.action is SessionAdmissionAction.BLOCK
    assert decision.allowed is False
    assert decision.reason_codes == ("MAX_TRADES_PER_SESSION",)


@pytest.mark.parametrize("value", [0, -1, True])
def test_policy_requires_explicit_positive_integer_limit(value) -> None:
    with pytest.raises(ValueError, match="integer >= 1"):
        SessionAdmissionPolicy.build(max_trades_per_session=value)


@pytest.mark.parametrize(
    ("session_key", "trades_admitted", "match"),
    [
        ("", 0, "session_key"),
        (" session-A", 0, "session_key"),
        ("session-A ", 0, "session_key"),
        ("session-A", -1, "non-negative integer"),
        ("session-A", True, "non-negative integer"),
    ],
)
def test_observation_rejects_invalid_explicit_state(
    session_key: str,
    trades_admitted,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        SessionAdmissionObservation.build(
            session_key=session_key,
            trades_admitted=trades_admitted,
        )


def test_policy_and_observation_identity_tampering_fails_closed() -> None:
    policy = SessionAdmissionPolicy.build(max_trades_per_session=2)
    observation = SessionAdmissionObservation.build(
        session_key="session-A",
        trades_admitted=1,
    )

    with pytest.raises(ValueError, match="policy fingerprint mismatch"):
        replace(policy, max_trades_per_session=3)
    with pytest.raises(ValueError, match="observation fingerprint mismatch"):
        replace(observation, trades_admitted=0)


def test_decision_identity_tampering_fails_closed() -> None:
    policy = SessionAdmissionPolicy.build(max_trades_per_session=2)
    observation = SessionAdmissionObservation.build(
        session_key="session-A",
        trades_admitted=1,
    )
    decision = evaluate_session_admission(policy=policy, observation=observation)

    with pytest.raises(ValueError, match="decision fingerprint mismatch"):
        replace(decision, decision_fingerprint="f" * 64)


def test_canonical_owner_contains_no_session_derivation_or_execution_api() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src/daxlab/domain/session_admission.py"
    ).read_text(encoding="utf-8").lower()

    assert "zoneinfo" not in source
    assert "datetime" not in source
    assert "europe/berlin" not in source
    assert "metatrader5" not in source
    assert "order_send(" not in source
    assert "max_trades_per_session: int = 1" not in source
