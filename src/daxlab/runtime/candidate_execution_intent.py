"""Outer simulation boundary from admitted CAND-001 decisions to ExecutionIntent.

The pure candidate hot path remains independent of paper contracts. This adapter
is deliberately SHADOW-only in the current product state and creates no broker
capability, no order submission path, and no PAPER authorization.
"""
from __future__ import annotations

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import SignalDirection
from daxlab.runtime.candidate_sizing import Cand001SimulationSizingPolicy
from daxlab.runtime.candidate_trade_plan import Cand001TradePlan
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.decision import DecisionRecord, FinalAction, stable_fingerprint
from daxlab.runtime.manifests import RunManifest
from daxlab.runtime.paper_contracts import ExecutionIntent, Side


def build_cand001_execution_intent(
    *,
    decision: DecisionRecord,
    trade_plan: Cand001TradePlan,
    run_manifest: RunManifest,
    config: Cand001Config | None = None,
    sizing: Cand001SimulationSizingPolicy | None = None,
) -> ExecutionIntent:
    """Map one admitted CAND-001 trade into the existing simulation intent contract."""
    cfg = config or Cand001Config()
    size = sizing or Cand001SimulationSizingPolicy()

    if run_manifest.mode is not RuntimeMode.SHADOW:
        raise ValueError("current CAND-001 execution-intent adapter requires SHADOW mode")
    if decision.final_action is not FinalAction.TRADE:
        raise ValueError("ExecutionIntent requires an admitted TRADE decision")
    if decision.blockers:
        raise ValueError("ExecutionIntent cannot be created from a blocked decision")
    if decision.config_fingerprint != stable_fingerprint(cfg):
        raise ValueError("decision config fingerprint does not match CAND-001 config")

    expected_manifest_config = stable_fingerprint({"candidate": cfg, "sizing": size})
    if run_manifest.config_fingerprint != expected_manifest_config:
        raise ValueError("run manifest config fingerprint must bind candidate and sizing policy")

    if trade_plan.candidate_id != cfg.candidate_id:
        raise ValueError("trade-plan candidate_id must match CAND-001 config")
    if trade_plan.ruleset_version != cfg.ruleset_version:
        raise ValueError("trade-plan ruleset_version must match CAND-001 config")
    if trade_plan.signal_data_fingerprint != decision.data_fingerprint:
        raise ValueError("trade-plan provenance must match decision data fingerprint")

    if trade_plan.direction is SignalDirection.LONG:
        side = Side.BUY
    elif trade_plan.direction is SignalDirection.SHORT:
        side = Side.SELL
    else:  # pragma: no cover - Cand001TradePlan already forbids NONE
        raise ValueError("trade plan must be LONG or SHORT")

    return ExecutionIntent.build(
        decision_id=decision.decision_id,
        run_manifest_fingerprint=run_manifest.manifest_fingerprint,
        created_at=decision.event_time,
        symbol=cfg.symbol,
        side=side,
        quantity=size.quantity,
        requested_price=trade_plan.entry_price,
        stop_price=trade_plan.stop_price,
        target_price=trade_plan.target_price,
    )
