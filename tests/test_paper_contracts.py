from datetime import datetime, timezone

import pytest

from daxlab.runtime.paper_contracts import (
    ExecutionIntent,
    IntentDeduplicator,
    PaperFillModelConfig,
    PaperLifecycleState,
    PaperTelemetry,
    Side,
)


def intent() -> ExecutionIntent:
    return ExecutionIntent.build(
        decision_id="1" * 64,
        run_manifest_fingerprint="2" * 64,
        created_at=datetime(2026, 9, 9, 8, 0, tzinfo=timezone.utc),
        symbol="DE40",
        side=Side.BUY,
        quantity=1.0,
        requested_price=25000.0,
        stop_price=24950.0,
        target_price=25100.0,
    )


def test_execution_intent_identity_is_deterministic() -> None:
    assert intent() == intent()
    assert len(intent().client_order_id) == 64
    assert intent().schema_version == "DAXLAB_EXECUTION_INTENT_V1"


def test_duplicate_intent_is_rejected() -> None:
    dedupe = IntentDeduplicator()
    value = intent()
    assert dedupe.accept(value)
    assert not dedupe.accept(value)


def test_fill_model_is_versioned_fingerprinted_and_conservative() -> None:
    model = PaperFillModelConfig()
    assert model.schema_version == "DAXLAB_PAPER_FILL_MODEL_V1"
    assert len(model.fingerprint) == 64
    assert model.same_bar_policy.value == "CONSERVATIVE_STOP_FIRST"
    assert model.gap_policy.value == "FILL_AT_FIRST_AVAILABLE"
    assert model.partial_fill_policy.value == "DISABLED"
    assert model.spread_points == 0.20
    assert model.slippage_points == 0.10
    assert model.commission_points == 0.10


def test_paper_telemetry_has_simulation_only_capability() -> None:
    value = intent()
    telemetry = PaperTelemetry(
        schema_version="DAXLAB_PAPER_TELEMETRY_V1",
        decision_id=value.decision_id,
        run_manifest_fingerprint=value.run_manifest_fingerprint,
        client_order_id=value.client_order_id,
        lifecycle_state=PaperLifecycleState.ACK,
        requested_at=value.created_at,
        accepted_at=value.created_at,
        filled_at=None,
        requested_price=value.requested_price,
        filled_price=None,
        spread_points=0.2,
        slippage_points=0.1,
        commission_points=0.1,
        feed_age_seconds=1.0,
        health_state="GREEN",
        reconciliation_state="SIMULATED_ACK",
    )
    assert telemetry.execution_capability == "SIMULATION_ONLY"


def test_paper_telemetry_rejects_execution_capability_escalation() -> None:
    value = intent()
    with pytest.raises(ValueError, match="cannot carry broker execution"):
        PaperTelemetry(
            schema_version="DAXLAB_PAPER_TELEMETRY_V1",
            decision_id=value.decision_id,
            run_manifest_fingerprint=value.run_manifest_fingerprint,
            client_order_id=value.client_order_id,
            lifecycle_state=PaperLifecycleState.ACK,
            requested_at=value.created_at,
            accepted_at=None,
            filled_at=None,
            requested_price=value.requested_price,
            filled_price=None,
            spread_points=0.2,
            slippage_points=0.1,
            commission_points=0.1,
            feed_age_seconds=1.0,
            health_state="GREEN",
            reconciliation_state="SIMULATED_ACK",
            execution_capability="BROKER",
        )
