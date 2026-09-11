"""Deterministic CAND-001 SHADOW coordinator with no broker execution path.

This module owns orchestration only. Strategy decisions, intent mapping, virtual
fills/exits, outcome economics, publication idempotency and operator rendering
remain owned by their existing modules.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from daxlab.runtime.bar_identity import closed_bar_identity
from daxlab.runtime.candidate_active_trade_state import Cand001ActiveTradeState
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_execution_intent import build_cand001_execution_intent
from daxlab.runtime.candidate_pipeline import (
    Cand001PipelineResult,
    Cand001PipelineState,
    process_cand001_candle,
)
from daxlab.runtime.candidate_publication_state import (
    Cand001PublicationState,
    PublicationAdmission,
    admit_cand001_intent_publication,
    admit_cand001_outcome_publication,
)
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.candidate_virtual_lifecycle import (
    VirtualPositionStatus,
    advance_cand001_virtual_lifecycle,
    start_cand001_virtual_lifecycle,
)
from daxlab.runtime.candidate_virtual_outcome import (
    Cand001VirtualOutcomeEvidence,
    build_cand001_virtual_outcome,
)
from daxlab.runtime.contracts import Candle, RuntimeMode
from daxlab.runtime.decision import FinalAction
from daxlab.runtime.health import HealthState
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.operator_runtime_bridge import OperatorRuntimeContext
from daxlab.runtime.operator_snapshot import OperatorSnapshot, build_operator_snapshot
from daxlab.runtime.paper_contracts import ExecutionIntent, PaperFillModelConfig


@dataclass(frozen=True, slots=True)
class Cand001ShadowState:
    pipeline: Cand001PipelineState = Cand001PipelineState()
    active_trade: Cand001ActiveTradeState | None = None
    publication: Cand001PublicationState = Cand001PublicationState()
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("CAND-001 SHADOW state cannot authorize execution")
        if self.active_trade is not None and (
            self.active_trade.execution_capability != "NONE"
            or self.active_trade.order_execution_enabled
        ):
            raise ValueError("active trade cannot authorize execution")


@dataclass(frozen=True, slots=True)
class Cand001ShadowStepResult:
    state: Cand001ShadowState
    pipeline_result: Cand001PipelineResult
    operator_snapshot: OperatorSnapshot
    intent_publication: PublicationAdmission | None
    outcome_publication: PublicationAdmission | None
    intent_to_publish: ExecutionIntent | None
    outcome_to_publish: Cand001VirtualOutcomeEvidence | None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("CAND-001 SHADOW result cannot authorize execution")


def process_cand001_shadow_candle(
    state: Cand001ShadowState,
    candle: Candle,
    *,
    observed_at: datetime,
    run_manifest: RunManifest,
    config: Cand001Config | None = None,
    sizing: Cand001SimulationSizingPolicy | None = None,
    fill_model: PaperFillModelConfig | None = None,
    runtime_context: OperatorRuntimeContext | None = None,
) -> Cand001ShadowStepResult:
    """Advance one CLOSED candle through strategy, virtual trade and evidence state."""
    if observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    if run_manifest.mode is not RuntimeMode.SHADOW:
        raise ValueError("CAND-001 shadow orchestrator requires SHADOW RunManifest")

    cfg = config or Cand001Config()
    size = sizing or Cand001SimulationSizingPolicy()
    model = fill_model or PaperFillModelConfig()
    core_version = cfg.product_identity().core_version

    publication = state.publication
    active_before = state.active_trade
    active_after = active_before
    display_lifecycle = active_before.lifecycle if active_before is not None else None
    display_outcome: Cand001VirtualOutcomeEvidence | None = None
    outcome_publication: PublicationAdmission | None = None
    outcome_to_publish: Cand001VirtualOutcomeEvidence | None = None
    events: list[str] = []

    if active_before is not None:
        if active_before.core_version != core_version:
            raise ValueError("active trade core-version drift")
        advanced = advance_cand001_virtual_lifecycle(
            active_before.lifecycle,
            candle,
            fill_model=model,
        )
        advanced_active = Cand001ActiveTradeState(
            core_version=active_before.core_version,
            origin_decision=active_before.origin_decision,
            lifecycle=advanced,
        )
        display_lifecycle = advanced
        if advanced.status is VirtualPositionStatus.CLOSED:
            display_outcome = build_cand001_virtual_outcome(
                decision=active_before.origin_decision,
                lifecycle=advanced,
                fill_model=model,
            )
            outcome_publication = admit_cand001_outcome_publication(
                publication,
                display_outcome,
            )
            publication = outcome_publication.state
            if outcome_publication.accepted:
                outcome_to_publish = display_outcome
                events.append("OUTCOME_PUBLICATION_ADMITTED")
            else:
                events.append("OUTCOME_PUBLICATION_DUPLICATE_SUPPRESSED")
            active_after = None
        else:
            active_after = advanced_active

    pipeline_result = process_cand001_candle(
        state.pipeline,
        candle,
        observed_at=observed_at,
        config=cfg,
    )

    intent_publication: PublicationAdmission | None = None
    intent_to_publish: ExecutionIntent | None = None
    if pipeline_result.decision.final_action is FinalAction.TRADE:
        if active_before is not None:
            raise RuntimeError("CAND-001 attempted a second admitted trade while a lifecycle existed")
        plan = pipeline_result.admission.admitted_plan
        if plan is None:
            raise RuntimeError("TRADE decision missing admitted trade plan")
        intent = build_cand001_execution_intent(
            decision=pipeline_result.decision,
            trade_plan=plan,
            run_manifest=run_manifest,
            config=cfg,
            sizing=size,
        )
        intent_publication = admit_cand001_intent_publication(publication, intent)
        publication = intent_publication.state
        if not intent_publication.accepted:
            raise RuntimeError(
                "duplicate intent publication encountered without restored active trade state"
            )
        intent_to_publish = intent
        events.append("INTENT_PUBLICATION_ADMITTED")
        lifecycle = start_cand001_virtual_lifecycle(intent, fill_model=model)
        active_after = Cand001ActiveTradeState(
            core_version=core_version,
            origin_decision=pipeline_result.decision,
            lifecycle=lifecycle,
        )
        display_lifecycle = lifecycle
        display_outcome = None

    base_snapshot = pipeline_result.operator_snapshot
    health_state, health_source, freshness_seconds, runtime_events, recovery_state, reconciliation_state = _runtime_view(
        base_snapshot=base_snapshot,
        runtime_context=runtime_context,
        extra_events=tuple(events),
    )
    bar_id = closed_bar_identity(
        canonical_symbol=candle.symbol,
        timeframe=candle.timeframe,
        close_time=candle.close_time,
    )
    operator_snapshot = build_operator_snapshot(
        generated_at=observed_at,
        config=cfg,
        signal=pipeline_result.signal,
        proposed_trade_plan=pipeline_result.proposed_trade_plan,
        admission=pipeline_result.admission,
        decision=pipeline_result.decision,
        last_bar_id=bar_id,
        last_bar_close_time=candle.close_time,
        freshness_seconds=freshness_seconds,
        health_state=health_state,
        health_source=health_source,
        runtime_events=runtime_events,
        recovery_state=recovery_state,
        reconciliation_state=reconciliation_state,
        lifecycle=display_lifecycle,
        outcome=display_outcome,
    )

    return Cand001ShadowStepResult(
        state=Cand001ShadowState(
            pipeline=pipeline_result.state,
            active_trade=active_after,
            publication=publication,
        ),
        pipeline_result=pipeline_result,
        operator_snapshot=operator_snapshot,
        intent_publication=intent_publication,
        outcome_publication=outcome_publication,
        intent_to_publish=intent_to_publish,
        outcome_to_publish=outcome_to_publish,
    )


def _runtime_view(
    *,
    base_snapshot: OperatorSnapshot,
    runtime_context: OperatorRuntimeContext | None,
    extra_events: tuple[str, ...],
) -> tuple[str, str, float, tuple[str, ...], str | None, str | None]:
    if base_snapshot.health_state is None or base_snapshot.health_source is None:
        raise ValueError("candidate pipeline snapshot must carry health context")
    if base_snapshot.freshness_seconds is None:
        raise ValueError("candidate pipeline snapshot must carry freshness")

    health_state = base_snapshot.health_state
    health_source = base_snapshot.health_source
    freshness = base_snapshot.freshness_seconds
    runtime_events = list(base_snapshot.runtime_events)
    recovery_state = base_snapshot.recovery_state
    reconciliation_state = base_snapshot.reconciliation_state

    if runtime_context is not None:
        candidate_health = HealthState(health_state)
        host_health = HealthState(runtime_context.health_state)
        if candidate_health is HealthState.GREEN:
            health_state = host_health.value
            health_source = runtime_context.health_source
        elif host_health is HealthState.RED:
            health_state = HealthState.RED.value
            health_source = f"{base_snapshot.health_source}+{runtime_context.health_source}"
        if runtime_context.freshness_seconds is not None:
            freshness = runtime_context.freshness_seconds
        runtime_events.extend(runtime_context.runtime_events)
        recovery_state = runtime_context.recovery_state
        reconciliation_state = runtime_context.reconciliation_state

    runtime_events.extend(extra_events)
    return (
        health_state,
        health_source,
        float(freshness),
        tuple(dict.fromkeys(runtime_events)),
        recovery_state,
        reconciliation_state,
    )
