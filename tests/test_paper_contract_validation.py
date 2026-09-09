from datetime import datetime, timezone

import pytest

from daxlab.runtime.paper_contracts import ExecutionIntent, PaperFillModelConfig, Side


def test_execution_intent_rejects_naive_time_and_nonpositive_values() -> None:
    base = {
        "decision_id": "1" * 64,
        "run_manifest_fingerprint": "2" * 64,
        "created_at": datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        "symbol": "DE40",
        "side": Side.SELL,
        "quantity": 1.0,
        "requested_price": 25000.0,
        "stop_price": 25050.0,
        "target_price": 24900.0,
    }
    with pytest.raises(ValueError, match="timezone-aware"):
        ExecutionIntent.build(**{**base, "created_at": datetime(2026, 9, 9, 8, 0)})
    with pytest.raises(ValueError, match="quantity"):
        ExecutionIntent.build(**{**base, "quantity": 0.0})
    with pytest.raises(ValueError, match="requested_price"):
        ExecutionIntent.build(**{**base, "requested_price": 0.0})


def test_fill_model_rejects_negative_cost_or_latency() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        PaperFillModelConfig(spread_points=-0.1)
    with pytest.raises(ValueError, match="latency"):
        PaperFillModelConfig(latency_ms=-1)
