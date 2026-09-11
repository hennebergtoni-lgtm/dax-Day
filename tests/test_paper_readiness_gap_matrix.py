from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs" / "PAPER_READINESS_GAP_MATRIX_V1.md"


def test_paper_gap_matrix_preserves_execution_safety_boundary() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "PAPER/demo broker execution is **not authorized**" in text
    assert "LIVE is **not authorized**" in text
    assert "`execution_capability=NONE` / `order_execution_enabled=false`" in text
    assert "mt5.order_send" in text
    assert "USER_STOP_GATE" in text


def test_paper_gap_matrix_keeps_broker_evidence_gates_distinct() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for required in (
        "Broker order lifecycle",
        "Broker execution atomic checkpoint",
        "PAPER checkpoint readiness gate",
        "Broker reconciliation",
        "Execution protection gates",
        "Order lifecycle telemetry",
        "PAPER telemetry readiness gate",
    ):
        assert required in text


def test_shadow_simulation_does_not_count_as_broker_evidence() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "does not satisfy broker order-lifecycle evidence" in text
    assert "successful SHADOW virtual fills" in text
    assert "deterministic client IDs alone" in text
    assert "synthetic/mock broker fixtures alone" in text


def test_real_host_and_broker_economics_stay_external_evidence_lanes() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "Current Windows/MT5 read-only health" in text
    assert "Real DE40 broker economics" in text
    assert text.count("WAITING_EXTERNAL") >= 3


def test_repository_ci_never_counts_as_broker_checkpoint_evidence() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "broker_execution_checkpoint_verified" in text
    assert "repository CI alone cannot satisfy it" in text
    assert "CI success without the specific real broker evidence" in text
