from datetime import datetime, timezone

from daxlab.runtime.paper_contracts import PaperLifecycleState, PaperTelemetry


def test_paper_telemetry_default_is_simulation_only() -> None:
    at = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    value = PaperTelemetry(
        schema_version="DAXLAB_PAPER_TELEMETRY_V1",
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        client_order_id="3" * 64,
        lifecycle_state=PaperLifecycleState.REJECT,
        requested_at=at,
        accepted_at=None,
        filled_at=None,
        requested_price=25000.0,
        filled_price=None,
        spread_points=0.2,
        slippage_points=0.0,
        commission_points=0.0,
        feed_age_seconds=2.0,
        health_state="RED",
        reconciliation_state="SIMULATED_REJECT",
    )
    assert value.execution_capability == "SIMULATION_ONLY"
