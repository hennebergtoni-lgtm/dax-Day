from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/NEXTGEN_SESSION_GUARD_CRASH_COHERENCE_AUDIT_V1.md"


def test_audit_requires_one_combined_atomic_session_guard_snapshot() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "ADAPT_CANONICALLY" in text
    assert "one combined atomic session-guard snapshot" in text
    assert "single-key" in text
    assert "There is no transaction, compare-and-swap or multi-key atomic-write contract" in text
    assert "as **one payload under one key**" in text


def test_audit_identifies_torn_state_false_allow_risk() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "consumption ledger advances from count 0 to count 1" in text
    assert "old observation checkpoint still says count 0" in text
    assert "may still be within its max-age window" in text
    assert "old ALLOW decision" in text
    assert "must not depend on an unstated ordering assumption" in text


def test_audit_preserves_freshness_semantics_and_compatibility() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "Loading a persisted snapshot must never refresh `observed_at`" in text
    assert "Step-2172 `SessionAdmissionObservationCheckpoint` remains valid" in text
    assert "compatibility/diagnostic evidence type" in text
    assert "authoritative product evidence" in text


def test_audit_preserves_session_and_execution_safety_boundaries() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "must not:" in text
    assert "derive a date, timezone, calendar or session key" in text
    assert "silently reset a ledger on session mismatch" in text
    assert "no broker/account API" in text
    assert "no order submission path" in text
    assert "PAPER remains unauthorized" in text
    assert "LIVE remains unauthorized" in text
    assert "Implementation of the combined atomic session-guard snapshot is a separate next whole-number step" in text
