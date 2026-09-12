from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/NEXTGEN_SESSION_ADMISSION_CONSUMPTION_AUDIT_V1.md"
CANDIDATE_ADMISSION = ROOT / "src/daxlab/runtime/candidate_admission.py"
DOMAIN_SESSION = ROOT / "src/daxlab/domain/session_admission.py"


def test_audit_requires_restart_idempotent_consumption_identity() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "ADAPT_CANONICALLY" in text
    assert "do not implement a naive counter increment" in text
    assert "deterministic `consumption_id`" in text
    assert "replaying the same consumption ID is idempotent" in text
    assert "state remembers applied consumption IDs" in text
    assert "StateStorePort" in text


def test_audit_does_not_promote_candidate_session_reset_semantics() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    candidate = CANDIDATE_ADMISSION.read_text(encoding="utf-8")

    assert "ZoneInfo" in candidate
    assert "session_date" in candidate
    assert "trades_admitted=working.trades_admitted + 1" in candidate
    assert "CAND-001" in text
    assert "Candidate-specific" in text
    assert "no timezone/date/calendar/session-reset inference" in text


def test_current_canonical_domain_has_evaluation_but_no_consumption_transition() -> None:
    source = DOMAIN_SESSION.read_text(encoding="utf-8")

    assert "def evaluate_session_admission" in source
    assert "consumption_id" not in source
    assert "consume_session" not in source


def test_audit_preserves_explicit_consumption_boundary_and_safety() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "must **not infer consumption merely from a strategy signal" in text
    assert "SessionAdmissionDecision ALLOW" in text
    assert "blocked protection verdicts" in text
    assert "no broker submission path" in text
    assert "PAPER remains unauthorized" in text
    assert "LIVE remains unauthorized" in text
    assert "Implementation is a separate next whole-number step" in text
