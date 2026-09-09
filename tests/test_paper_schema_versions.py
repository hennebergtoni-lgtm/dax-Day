from datetime import datetime, timezone

from daxlab.runtime.paper_contracts import ExecutionIntent, PaperFillModelConfig, Side


def test_paper_contract_schema_versions_are_explicit() -> None:
    intent = ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=25000.0,
        stop_price=24950.0,
        target_price=25100.0,
    )
    assert intent.schema_version == "DAXLAB_EXECUTION_INTENT_V1"
    assert PaperFillModelConfig().schema_version == "DAXLAB_PAPER_FILL_MODEL_V1"
