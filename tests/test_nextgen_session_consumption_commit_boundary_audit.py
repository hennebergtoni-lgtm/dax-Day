from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "NEXTGEN_SESSION_CONSUMPTION_COMMIT_BOUNDARY_AUDIT_V1.md"
NEXTGEN_LIFECYCLE = ROOT / "src" / "daxlab" / "runtime" / "nextgen_broker_lifecycle.py"


def test_commit_boundary_audit_records_fail_safe_prepared_ordering() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    required = (
        "submit-before-consume",
        "Consume before an unrecorded submission attempt",
        "PREPARED",
        "ALLOW_EVIDENCE",
        "SessionAdmissionGuardCheckpoint",
        "StateStorePort",
        "intent_id == client_order_id == consumption_id",
        "REUSE",
        "ADAPT",
        "DEFER",
        "reconcile",
    )
    for token in required:
        assert token in text

    prepared_pos = text.index("PREPARED commit sequence")
    external_pos = text.index("Only after that single local PREPARED checkpoint")
    assert prepared_pos < external_pos


def test_commit_boundary_audit_keeps_execution_unauthorized() -> None:
    text = AUDIT.read_text(encoding="utf-8")

    assert "no broker order submission" in text
    assert "PAPER remains unauthorized" in text
    assert "LIVE remains unauthorized" in text
    assert "order_execution_enabled=false" in text
    assert "NO_STRATEGY_AUTO_PROMOTION" in text


def test_existing_nextgen_lifecycle_reuses_intent_id_as_client_order_id() -> None:
    source = "".join(NEXTGEN_LIFECYCLE.read_text(encoding="utf-8").split())

    assert "client_order_id=intent.intent_id" in source
