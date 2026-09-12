from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/NEXTGEN_SESSION_OBSERVATION_RESTART_FRESHNESS_AUDIT_V1.md"
STATE_DIR = ROOT / "src/daxlab/state"
CANDIDATE_STATE = ROOT / "src/daxlab/runtime/candidate_state.py"


def test_audit_classifies_restart_and_freshness_as_canonical_adaptation() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "ADAPT_CANONICALLY" in text
    assert "SessionAdmissionObservationCheckpoint" in text
    assert "StateStorePort" in text
    assert "caller-supplied timezone-aware `observed_at`" in text
    assert "future-dated checkpoint evidence to fail closed" in text
    assert "stale checkpoint evidence to block new admission" in text
    assert "does **not** determine when a session changes" in text
    assert "Implementation is a separate next whole-number step" in text


def test_no_canonical_session_checkpoint_exists_before_implementation_step() -> None:
    assert not (STATE_DIR / "session_admission.py").exists()


def test_candidate_restart_provenance_remains_candidate_specific() -> None:
    source = CANDIDATE_STATE.read_text(encoding="utf-8")

    assert '"session_date": state.admission.session_date' in source
    assert '"trades_admitted": state.admission.trades_admitted' in source


def test_audit_preserves_safety_and_defers_session_derivation() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "session-key derivation" in text
    assert "timezone selection" in text
    assert "session reset transitions" in text
    assert "no broker submission path" in text
    assert "`execution_capability=NONE` remains binding" in text
    assert "PAPER and LIVE remain unauthorized" in text
