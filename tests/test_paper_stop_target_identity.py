from datetime import datetime, timezone

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def build(stop: float, target: float) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=25000.0,
        stop_price=stop,
        target_price=target,
    )


def test_client_order_identity_binds_stop_and_target() -> None:
    base = build(24950.0, 25100.0)
    assert base.client_order_id != build(24940.0, 25100.0).client_order_id
    assert base.client_order_id != build(24950.0, 25110.0).client_order_id
