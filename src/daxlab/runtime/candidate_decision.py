"""Pure CAND-001 adapter into the canonical DecisionRecord contract."""
from __future__ import annotations

from daxlab.runtime.candidate_admission import AdmissionStatus, Cand001AdmissionResult
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection, SignalReason
from daxlab.runtime.decision import DecisionRecord, FinalAction

_HARD_BLOCKERS = {
    SignalReason.DATA_UNSAFE: "DATA_UNSAFE",
    SignalReason.OR_INCOMPLETE: "OR_INCOMPLETE",
    SignalReason.DUPLICATE_BAR: "DUPLICATE_BAR",
    SignalReason.OUT_OF_ORDER_BAR: "OUT_OF_ORDER_BAR",
}


def build_cand001_decision(
    signal: Cand001Signal,
    admission: Cand001AdmissionResult,
    *,
    config: Cand001Config | None = None,
) -> DecisionRecord:
    """Bind one causal CAND-001 signal and admission result to DecisionRecord."""
    cfg = config or Cand001Config()
    directional = signal.direction in {SignalDirection.LONG, SignalDirection.SHORT}

    if admission.status is AdmissionStatus.ALLOWED:
        if not directional or admission.admitted_plan is None:
            raise ValueError("ALLOWED admission requires directional signal and trade plan")
        plan = admission.admitted_plan
        if plan.direction is not signal.direction:
            raise ValueError("trade-plan direction must match signal direction")
        if plan.signal_data_fingerprint != signal.data_fingerprint:
            raise ValueError("trade-plan provenance must match signal data fingerprint")
        if plan.candidate_id != cfg.candidate_id:
            raise ValueError("trade-plan candidate_id must match config")
        if plan.ruleset_version != cfg.ruleset_version:
            raise ValueError("trade-plan ruleset_version must match config")
    elif admission.admitted_plan is not None:
        raise ValueError("non-ALLOWED admission cannot carry an admitted trade plan")

    blockers: list[str] = []
    signal_blocker = _HARD_BLOCKERS.get(signal.reason)
    if signal_blocker is not None:
        blockers.append(signal_blocker)
    if admission.status is AdmissionStatus.SESSION_LIMIT:
        blockers.append("SESSION_TRADE_LIMIT")

    allowed = admission.status is AdmissionStatus.ALLOWED
    final_action = FinalAction.TRADE if allowed else FinalAction.NO_TRADE
    if allowed:
        risk_result = "ADMITTED"
    elif admission.status is AdmissionStatus.SESSION_LIMIT:
        risk_result = "SESSION_LIMIT"
    else:
        risk_result = "NOT_APPLICABLE"

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
            "session_trade_slot_available": admission.status is not AdmissionStatus.SESSION_LIMIT,
        },
        blockers=tuple(blockers),
        risk_result=risk_result,
        config=cfg,
        core_version=cfg.product_identity().core_version,
        final_action=final_action,
    )
