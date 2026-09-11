"""Pure CAND-001 adapter into the canonical DecisionRecord contract."""
from __future__ import annotations

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.candidate_trade_plan import Cand001TradePlan
from daxlab.runtime.decision import DecisionRecord, FinalAction

_HARD_BLOCKERS = {
    SignalReason.DATA_UNSAFE: "DATA_UNSAFE",
    SignalReason.OR_INCOMPLETE: "OR_INCOMPLETE",
    SignalReason.DUPLICATE_BAR: "DUPLICATE_BAR",
    SignalReason.OUT_OF_ORDER_BAR: "OUT_OF_ORDER_BAR",
}


def build_cand001_decision(
    signal: Cand001Signal,
    trade_plan: Cand001TradePlan | None,
    *,
    config: Cand001Config | None = None,
) -> DecisionRecord:
    """Bind one causal CAND-001 signal to the shared deterministic decision log."""
    cfg = config or Cand001Config()
    directional = signal.direction in {SignalDirection.LONG, SignalDirection.SHORT}
    if directional and trade_plan is None:
        raise ValueError("directional CAND-001 signal requires a trade plan")
    if not directional and trade_plan is not None:
        raise ValueError("non-directional CAND-001 signal cannot carry a trade plan")
    if trade_plan is not None:
        if trade_plan.direction is not signal.direction:
            raise ValueError("trade-plan direction must match signal direction")
        if trade_plan.signal_data_fingerprint != signal.data_fingerprint:
            raise ValueError("trade-plan provenance must match signal data fingerprint")
        if trade_plan.candidate_id != cfg.candidate_id:
            raise ValueError("trade-plan candidate_id must match config")
        if trade_plan.ruleset_version != cfg.ruleset_version:
            raise ValueError("trade-plan ruleset_version must match config")

    blocker = _HARD_BLOCKERS.get(signal.reason)
    blockers = (blocker,) if blocker is not None else ()
    final_action = FinalAction.TRADE if trade_plan is not None else FinalAction.NO_TRADE
    return DecisionRecord.build(
        event_time=signal.close_time,
        data_fingerprint=signal.data_fingerprint,
        regime=cfg.regime_policy.value,
        structure=f"{cfg.structure_rule.value}/OR{cfg.or_minutes}",
        setup=signal.reason.value,
        filter_results={
            "data_safe": signal.reason is not SignalReason.DATA_UNSAFE,
            "or_complete": signal.or_high is not None and signal.or_low is not None,
            "entry_confirmed": directional,
        },
        blockers=blockers,
        risk_result="GEOMETRY_VALID" if trade_plan is not None else "NOT_APPLICABLE",
        config=cfg,
        core_version=cfg.product_identity().core_version,
        final_action=final_action,
    )
