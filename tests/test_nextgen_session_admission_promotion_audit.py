from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/NEXTGEN_SESSION_ADMISSION_PROMOTION_AUDIT_V1.md"
CONFIG = ROOT / "src/daxlab/runtime/candidate_config.py"
ADMISSION = ROOT / "src/daxlab/runtime/candidate_admission.py"
STATE = ROOT / "src/daxlab/runtime/candidate_state.py"


def test_audit_classifies_only_explicit_session_state_for_canonical_adaptation() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "ADAPT_CANONICALLY" in text
    assert "SessionAdmissionPolicy(max_trades_per_session)" in text
    assert "SessionAdmissionObservation(session_key, trades_admitted)" in text
    assert "Session-key production remains caller/environment responsibility" in text
    assert "must **not**" in text
    assert "default to `Europe/Berlin`" in text
    assert "silently inherit CAND-001's `max_trades_per_session = 1`" in text
    assert "Step 2168 is classification/audit only" in text


def test_cand001_session_semantics_remain_explicit_candidate_provenance() -> None:
    config = CONFIG.read_text(encoding="utf-8")
    admission = ADMISSION.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")

    assert 'SELECTION_PROVENANCE = "NEW_1X_SELECTION"' in config
    assert 'session_timezone: str = "Europe/Berlin"' in config
    assert "max_trades_per_session: int = 1" in config
    assert "ZoneInfo(cfg.session_timezone)" in admission
    assert "working.trades_admitted >= cfg.max_trades_per_session" in admission
    assert '"session_date": state.admission.session_date' in state
    assert '"trades_admitted": state.admission.trades_admitted' in state


def test_audit_preserves_execution_safety_boundary() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "`execution_capability=NONE` remains binding" in text
    assert "`order_execution_enabled=false` remains binding" in text
    assert "PAPER remains unauthorized" in text
    assert "LIVE remains unauthorized" in text
