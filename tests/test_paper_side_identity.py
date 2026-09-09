from datetime import datetime, timezone

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def build(side: Side) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        symbol="DE40",
        side=side,
        quantity=1.0,
        requested_price=25000.0,
        stop_price=24950.0,
        target_price=25100.0,
    )


def test_client_order_identity_binds_side() -> None:
    assert build(Side.BUY).client_order_id != build(Side.SELL).client_order_id
