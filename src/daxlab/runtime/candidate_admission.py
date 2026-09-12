"""Pure per-session trade admission for DAX-BOT CAND-001."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from zoneinfo import ZoneInfo

from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_signal import Cand001Signal, SignalDirection
from daxlab.runtime.candidate_trade_plan import Cand001TradePlan


class AdmissionStatus(StrEnum):
    NO_SIGNAL = "NO_SIGNAL"
    ALLOWED = "ALLOWED"
    SESSION_LIMIT = "SESSION_LIMIT"


@dataclass(frozen=True, slots=True)
class Cand001AdmissionState:
    session_date: str | None = None
    trades_admitted: int = 0

    def __post_init__(self) -> None:
        if self.trades_admitted < 0:
            raise ValueError("trades_admitted cannot be negative")
        if self.trades_admitted and self.session_date is None:
            raise ValueError("admitted trades require session_date")


@dataclass(frozen=True, slots=True)
class Cand001AdmissionResult:
    state: Cand001AdmissionState
    status: AdmissionStatus
    admitted_plan: Cand001TradePlan | None


def admit_cand001_trade(
    state: Cand001AdmissionState,
    signal: Cand001Signal,
    trade_plan: Cand001TradePlan | None,
    *,
    config: Cand001Config | None = None,
) -> Cand001AdmissionResult:
    """Apply the one-trade-per-session rule without hiding later market signals."""
    cfg = config or Cand001Config()
    session_date = signal.close_time.astimezone(ZoneInfo(cfg.session_timezone)).date().isoformat()
    working = state
    if working.session_date != session_date:
        working = Cand001AdmissionState(session_date=session_date)

    directional = signal.direction in {SignalDirection.LONG, SignalDirection.SHORT}
    if not directional:
        if trade_plan is not None:
            raise ValueError("non-directional signal cannot carry a trade plan")
        return Cand001AdmissionResult(
            state=working,
            status=AdmissionStatus.NO_SIGNAL,
            admitted_plan=None,
        )
    if trade_plan is None:
        raise ValueError("directional signal requires a trade plan before admission")
    if trade_plan.direction is not signal.direction:
        raise ValueError("trade-plan direction must match signal direction")
    if trade_plan.signal_data_fingerprint != signal.data_fingerprint:
        raise ValueError("trade-plan provenance must match signal data fingerprint")

    if working.trades_admitted >= cfg.max_trades_per_session:
        return Cand001AdmissionResult(
            state=working,
            status=AdmissionStatus.SESSION_LIMIT,
            admitted_plan=None,
        )

    next_state = Cand001AdmissionState(
        session_date=session_date,
        trades_admitted=working.trades_admitted + 1,
    )
    return Cand001AdmissionResult(
        state=next_state,
        status=AdmissionStatus.ALLOWED,
        admitted_plan=trade_plan,
    )
