from datetime import datetime, timezone

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def build(price: float) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=price,
        stop_price=24950.0,
        target_price=25100.0,
    )


def test_client_order_identity_binds_price_inputs() -> None:
    assert build(25000.0).client_order_id != build(25000.5).client_order_id
