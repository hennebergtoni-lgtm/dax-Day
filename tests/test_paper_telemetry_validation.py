from datetime import datetime, timezone

import pytest

from daxlab.runtime.paper_contracts import PaperLifecycleState, PaperTelemetry


def kwargs() -> dict:
    aware = datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc)
    return {
        "schema_version": "DAXLAB_PAPER_TELEMETRY_V1",
        "decision_id": "1" * 64,
        "run_manifest_fingerprint": "2" * 64,
        "client_order_id": "3" * 64,
        "lifecycle_state": PaperLifecycleState.ACK,
        "requested_at": aware,
        "accepted_at": aware,
        "filled_at": None,
        "requested_price": 25000.0,
        "filled_price": None,
        "spread_points": 0.2,
        "slippage_points": 0.1,
        "commission_points": 0.1,
        "feed_age_seconds": 1.0,
        "health_state": "GREEN",
        "reconciliation_state": "SIMULATED_ACK",
    }


def test_telemetry_rejects_naive_timestamp() -> None:
    values = kwargs()
    values["requested_at"] = datetime(2026, 9, 9, 8, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        PaperTelemetry(**values)


def test_telemetry_rejects_negative_feed_age() -> None:
    values = kwargs()
    values["feed_age_seconds"] = -1.0
    with pytest.raises(ValueError, match="non-negative"):
        PaperTelemetry(**values)
