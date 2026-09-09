from datetime import datetime, timezone

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def build(decision_id: str) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id=decision_id,
        run_manifest_fingerprint="2" * 64,
        created_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=25000.0,
        stop_price=24950.0,
        target_price=25100.0,
    )


def test_client_order_identity_binds_decision_id() -> None:
    assert build("1" * 64).client_order_id != build("3" * 64).client_order_id
