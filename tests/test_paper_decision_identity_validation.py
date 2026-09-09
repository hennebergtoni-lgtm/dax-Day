from datetime import datetime, timezone

import pytest

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def values() -> dict:
    return {
        "decision_id": "1" * 64,
        "run_manifest_fingerprint": "2" * 64,
        "created_at": datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        "symbol": "DE40",
        "side": Side.BUY,
        "quantity": 1.0,
        "requested_price": 25000.0,
        "stop_price": 24950.0,
        "target_price": 25100.0,
    }


def test_invalid_decision_or_run_hash_is_rejected() -> None:
    with pytest.raises(ValueError, match="decision_id"):
        ExecutionIntent.build(**{**values(), "decision_id": "bad"})
    with pytest.raises(ValueError, match="run_manifest_fingerprint"):
        ExecutionIntent.build(**{**values(), "run_manifest_fingerprint": "bad"})
