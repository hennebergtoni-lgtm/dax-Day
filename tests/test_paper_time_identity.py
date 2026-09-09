from datetime import datetime, timedelta, timezone

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def build(at: datetime) -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=at,
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=25000.0,
        stop_price=24950.0,
        target_price=25100.0,
    )


def test_client_order_identity_binds_creation_time() -> None:
    at = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    assert build(at).client_order_id != build(at + timedelta(seconds=1)).client_order_id
