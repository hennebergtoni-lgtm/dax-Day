"""Semantics-aware DUAL_COMPARE evidence for the CAND-001 migration.

This module does not execute either provider and cannot place orders. It binds an
already-produced legacy SHADOW observation and an already-produced CAND-001
strategy result to the same closed-bar fingerprint while preserving their
intentionally different outcome domains.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from daxlab.runtime.candidate_pipeline import Cand001PipelineResult
from daxlab.runtime.component_transition import ComponentRoute, ProviderSlot, TransitionMode
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.shadow_observation import ShadowDecision


SCHEMA_VERSION = "DAX_BOT_CAND001_DUAL_COMPARE_V1"


class OutcomeDomain(StrEnum):
    SHADOW_ORDER_SAFETY = "SHADOW_ORDER_SAFETY"
    STRATEGY_DECISION = "STRATEGY_DECISION"


class StrategyParityStatus(StrEnum):
    UNAVAILABLE_DOMAIN_MISMATCH = "UNAVAILABLE_DOMAIN_MISMATCH"


@dataclass(frozen=True, slots=True)
class ProviderObservation:
    provider_id: str
    domain: OutcomeDomain
    outcome: str
    outcome_identity: str

    def __post_init__(self) -> None:
        if not self.provider_id.strip():
            raise ValueError("provider_id must not be empty")
        if not self.outcome.strip():
            raise ValueError("outcome must not be empty")
        _require_sha256(self.outcome_identity, "outcome_identity")


@dataclass(frozen=True, slots=True)
class Cand001DualCompareRecord:
    schema_version: str
    route_fingerprint: str
    component_id: str
    comparison_policy_version: str
    bar_fingerprint: str
    authoritative_slot: str
    authoritative_provider_id: str
    legacy: ProviderObservation
    bot_1x: ProviderObservation
    strategy_parity_status: StrategyParityStatus
    execution_capability: str
    order_execution_enabled: bool
    comparison_fingerprint: str


def build_cand001_shadow_dual_compare(
    *,
    route: ComponentRoute,
    legacy_decision: ShadowDecision,
    candidate_result: Cand001PipelineResult,
    candidate_bar_fingerprint: str,
) -> Cand001DualCompareRecord:
    """Bind legacy SHADOW safety and CAND-001 strategy evidence without promotion."""
    if route.mode is not TransitionMode.DUAL_COMPARE:
        raise ValueError("CAND-001 compare requires DUAL_COMPARE mode")
    if route.authoritative_slot is not ProviderSlot.LEGACY:
        raise ValueError("CAND-001 compare requires LEGACY to remain authoritative")
    if route.comparison_policy_version == "none":
        raise ValueError("CAND-001 compare requires a versioned comparison policy")

    _require_sha256(candidate_bar_fingerprint, "candidate_bar_fingerprint")
    if legacy_decision.closed_bar_fingerprint != candidate_bar_fingerprint:
        raise ValueError("legacy and CAND-001 evidence must reference the same closed bar")
    if legacy_decision.action != "NO_ORDER":
        raise ValueError("legacy SHADOW evidence must remain NO_ORDER")

    snapshot = candidate_result.operator_snapshot
    if snapshot.execution_capability != "NONE":
        raise ValueError("CAND-001 compare cannot carry execution capability")
    if snapshot.order_execution_enabled is not False:
        raise ValueError("CAND-001 compare requires order execution disabled")
    if snapshot.decision_id != candidate_result.decision.decision_id:
        raise ValueError("CAND-001 snapshot/decision identity mismatch")
    _require_sha256(snapshot.snapshot_fingerprint, "candidate snapshot fingerprint")

    legacy = ProviderObservation(
        provider_id=route.legacy_provider_id,
        domain=OutcomeDomain.SHADOW_ORDER_SAFETY,
        outcome=legacy_decision.action,
        outcome_identity=stable_fingerprint(legacy_decision),
    )
    bot_1x = ProviderObservation(
        provider_id=route.bot_1x_provider_id,
        domain=OutcomeDomain.STRATEGY_DECISION,
        outcome=candidate_result.decision.final_action.value,
        outcome_identity=snapshot.snapshot_fingerprint,
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "route_fingerprint": route.fingerprint(),
        "component_id": route.component_id,
        "comparison_policy_version": route.comparison_policy_version,
        "bar_fingerprint": candidate_bar_fingerprint,
        "authoritative_slot": route.authoritative_slot.value,
        "authoritative_provider_id": route.authoritative_provider_id(),
        "legacy": legacy,
        "bot_1x": bot_1x,
        "strategy_parity_status": StrategyParityStatus.UNAVAILABLE_DOMAIN_MISMATCH,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    return Cand001DualCompareRecord(
        **payload,
        comparison_fingerprint=stable_fingerprint(payload),
    )


def _require_sha256(value: str, field: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
