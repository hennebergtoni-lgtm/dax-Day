"""Pure CAND-001 trade-price geometry derived from a confirmed signal.

This module does not size positions, create paper intents, submit orders, or
persist state. It only converts a CAND-001 directional signal into deterministic
entry/stop/target geometry.
"""
from __future__ import annotations

from dataclasses import dataclass

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection
from daxlab.runtime.decision import stable_fingerprint


@dataclass(frozen=True, slots=True)
class Cand001TradePlan:
    candidate_id: str
    ruleset_version: str
    direction: SignalDirection
    entry_price: float
    stop_price: float
    target_price: float
    risk_points: float
    reward_risk: float
    signal_data_fingerprint: str
    plan_fingerprint: str

    def __post_init__(self) -> None:
        if self.direction not in {SignalDirection.LONG, SignalDirection.SHORT}:
            raise ValueError("trade plan requires LONG or SHORT direction")
        if min(self.entry_price, self.stop_price, self.target_price, self.risk_points) <= 0:
            raise ValueError("trade-plan prices and risk_points must be positive")
        if self.reward_risk <= 0:
            raise ValueError("reward_risk must be positive")
        if len(self.signal_data_fingerprint) != 64:
            raise ValueError("signal_data_fingerprint must be sha256 hex")
        int(self.signal_data_fingerprint, 16)
        if len(self.plan_fingerprint) != 64:
            raise ValueError("plan_fingerprint must be sha256 hex")
        int(self.plan_fingerprint, 16)
        if self.direction is SignalDirection.LONG and not (
            self.stop_price < self.entry_price < self.target_price
        ):
            raise ValueError("LONG trade-plan geometry is invalid")
        if self.direction is SignalDirection.SHORT and not (
            self.target_price < self.entry_price < self.stop_price
        ):
            raise ValueError("SHORT trade-plan geometry is invalid")


def build_cand001_trade_plan(
    signal: Cand001Signal,
    *,
    config: Cand001Config | None = None,
) -> Cand001TradePlan | None:
    """Return deterministic CAND-001 price geometry, or None for no-signal bars."""
    cfg = config or Cand001Config()
    if signal.direction is SignalDirection.NONE:
        return None
    if signal.trigger_price is None or signal.or_high is None or signal.or_low is None:
        raise ValueError("directional signal requires trigger price and completed opening range")

    entry = float(signal.trigger_price)
    if signal.direction is SignalDirection.LONG:
        stop = float(signal.or_low)
        risk = entry - stop
        if risk <= 0:
            raise ValueError("LONG signal must enter above OR-opposite stop")
        target = entry + cfg.reward_risk * risk
    elif signal.direction is SignalDirection.SHORT:
        stop = float(signal.or_high)
        risk = stop - entry
        if risk <= 0:
            raise ValueError("SHORT signal must enter below OR-opposite stop")
        target = entry - cfg.reward_risk * risk
        if target <= 0:
            raise ValueError("SHORT target must remain positive")
    else:  # pragma: no cover - enum exhaustiveness guard
        raise ValueError("unsupported signal direction")

    payload = {
        "candidate_id": cfg.candidate_id,
        "ruleset_version": cfg.ruleset_version,
        "direction": signal.direction.value,
        "entry_price": entry,
        "stop_price": stop,
        "target_price": target,
        "risk_points": risk,
        "reward_risk": cfg.reward_risk,
        "signal_data_fingerprint": signal.data_fingerprint,
    }
    return Cand001TradePlan(
        candidate_id=cfg.candidate_id,
        ruleset_version=cfg.ruleset_version,
        direction=signal.direction,
        entry_price=entry,
        stop_price=stop,
        target_price=target,
        risk_points=risk,
        reward_risk=cfg.reward_risk,
        signal_data_fingerprint=signal.data_fingerprint,
        plan_fingerprint=stable_fingerprint(payload),
    )
