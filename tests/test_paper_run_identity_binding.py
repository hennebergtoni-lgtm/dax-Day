from datetime import datetime, timezone

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def build(run_hash: str) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint=run_hash,
        created_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=25000.0,
        stop_price=24950.0,
        target_price=25100.0,
    )


def test_client_order_identity_binds_run_manifest() -> None:
    assert build("2" * 64).client_order_id != build("3" * 64).client_order_id
