"""CAND-001 read-only MT5 SHADOW runtime bound to the existing host gate.

The established MT5 host/ProspectiveGate remains authoritative. Candidate logic
runs only after that gate allows SHADOW. This module has no MetaTrader5 import,
no broker adapter and no order submission capability.
"""
from __future__ import annotations

from dataclasses import dataclass

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_shadow_feed_runtime import (
    Cand001ShadowFeedResult,
    run_cand001_shadow_from_mt5_feed,
)
from daxlab.runtime.candidate_shadow_orchestrator import Cand001ShadowState
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.mt5_shadow_integration import (
    HostShadowStatus,
    evaluate_shadow_from_bundle,
)
from daxlab.runtime.mt5_windows_bundle import WindowsMt5Bundle
from daxlab.runtime.operator_runtime_bridge import build_mt5_shadow_operator_runtime_context
from daxlab.runtime.paper_contracts import PaperFillModelConfig
from daxlab.runtime.prospective_gate import ProspectiveAuthorization, ProspectiveGateResult
from daxlab.runtime.restart_reconcile import RestartReconcileResult


@dataclass(frozen=True, slots=True)
class Cand001Mt5ShadowRuntimeResult:
    state: Cand001ShadowState
    gate: ProspectiveGateResult
    host_status: HostShadowStatus
    candidate_feed_result: Cand001ShadowFeedResult | None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("candidate MT5 SHADOW runtime cannot authorize execution")
        if self.candidate_feed_result is not None and not self.gate.allowed:
            raise ValueError("blocked MT5 gate cannot carry candidate feed result")


def run_cand001_mt5_shadow(
    state: Cand001ShadowState,
    bundle: WindowsMt5Bundle,
    *,
    authorization: ProspectiveAuthorization,
    single_instance_lock_held: bool,
    run_manifest: RunManifest,
    config: Cand001Config | None = None,
    sizing: Cand001SimulationSizingPolicy | None = None,
    fill_model: PaperFillModelConfig | None = None,
    restart_reconcile: RestartReconcileResult | None = None,
) -> Cand001Mt5ShadowRuntimeResult:
    """Run CAND-001 only after the existing read-only MT5 SHADOW gate allows it."""
    gate, _, host_status = evaluate_shadow_from_bundle(
        bundle,
        authorization=authorization,
        single_instance_lock_held=single_instance_lock_held,
    )
    if not gate.allowed or bundle.feed is None or host_status.symbol is None:
        return Cand001Mt5ShadowRuntimeResult(
            state=state,
            gate=gate,
            host_status=host_status,
            candidate_feed_result=None,
        )

    runtime_context = build_mt5_shadow_operator_runtime_context(
        host_status,
        restart_reconcile=restart_reconcile,
    )
    candidate = run_cand001_shadow_from_mt5_feed(
        state,
        bundle.feed,
        broker_symbol=host_status.symbol,
        run_manifest=run_manifest,
        config=config,
        sizing=sizing,
        fill_model=fill_model,
        runtime_context=runtime_context,
    )
    return Cand001Mt5ShadowRuntimeResult(
        state=candidate.state,
        gate=gate,
        host_status=host_status,
        candidate_feed_result=candidate,
    )
