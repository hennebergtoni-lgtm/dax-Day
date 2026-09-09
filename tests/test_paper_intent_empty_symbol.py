from datetime import datetime, timezone

import pytest

from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def test_execution_intent_rejects_empty_symbol() -> None:
    with pytest.raises(ValueError, match="symbol"):
        ExecutionIntent.build(
            decision_id="1" * 64,
            run_manifest_fingerprint="2" * 64,
            created_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
            symbol=" ",
            side=Side.BUY,
            quantity=1.0,
            requested_price=25000.0,
            stop_price=24950.0,
            target_price=25100.0,
        )
