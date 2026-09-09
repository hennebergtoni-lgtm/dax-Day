"""Causal trade-feature bundle for V12 isolated research candidates.

The bundle is intentionally input-bound: callers must provide a verified full
2014-2019 session OHLC sequence and reproduced clean trade rows. This module
never loads arbitrary external data and cannot execute orders.

ADX001 and BODY001 are evaluated on the completed breakout/signal bar exactly
as predeclared. The current range-compression primitive is retained only as a
diagnostic engineering value; it is not treated as formal COMP001 evidence
because the intake definition requires a recent-range / causal-ATR14 contract.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Sequence

from daxlab.research.v12_evidence_gate import (
    OhlcEvidenceIdentity,
    TradeEvidenceIdentity,
    verify_ohlc_evidence,
    verify_reproduced_trade_evidence,
)
from daxlab.research.v12_prepaper_features import (
    ClosedBar,
    adx_feature,
    body_quality,
    range_compression,
    retest_staleness,
)

_M5 = timedelta(minutes=5)
_DIAGNOSTIC_COMP_STATE = "DIAGNOSTIC_PRIMITIVE_NOT_FORMAL_COMP001"


@dataclass(frozen=True, slots=True)
class TimedClosedBar:
    open_time: datetime
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        if self.open_time.tzinfo is None:
            raise ValueError("OHLC timestamps must be timezone-aware")
        ClosedBar(self.open, self.high, self.low, self.close)


@dataclass(frozen=True, slots=True)
class ReproducedTrade:
    wf: int
    entry_time: datetime
    signal_time: datetime
    retest_time: datetime | None
    entry_mode: str
    side: str
    r: float

    def __post_init__(self) -> None:
        if self.wf <= 0:
            raise ValueError("wf must be positive")
        if self.entry_time.tzinfo is None or self.signal_time.tzinfo is None:
            raise ValueError("trade timestamps must be timezone-aware")
        if self.retest_time is not None and self.retest_time.tzinfo is None:
            raise ValueError("retest_time must be timezone-aware")
        if self.entry_mode not in {"breakout", "retest"}:
            raise ValueError("unsupported entry_mode")
        if self.side not in {"long", "short"}:
            raise ValueError("unsupported side")


@dataclass(frozen=True, slots=True)
class V12TradeFeatures:
    wf: int
    entry_time: str
    signal_time: str
    entry_mode: str
    side: str
    r: float
    asof_bar_open_time: str
    adx: float | None
    plus_di: float | None
    minus_di: float | None
    body_fraction: float
    close_location: float
    breakout_side_close_location: float
    body_direction: int
    body_direction_agrees: bool
    compression_ratio: float | None
    compression_evidence_state: str
    bars_since_breakout: int | None


def last_completed_bar_index(times: Sequence[datetime], *, entry_time: datetime) -> int:
    """Return the last M5 index fully closed at entry_time; never return bar-0-in-progress."""
    if entry_time.tzinfo is None:
        raise ValueError("entry_time must be timezone-aware")
    if not times:
        raise ValueError("OHLC timeline cannot be empty")
    cutoff_open_time = entry_time - _M5
    index = bisect_right(times, cutoff_open_time) - 1
    if index < 0:
        raise ValueError("trade has no completed M5 bar before entry")
    return index


def build_trade_feature_bundle(
    bars: Sequence[TimedClosedBar],
    trades: Iterable[ReproducedTrade],
    *,
    ohlc_identity: OhlcEvidenceIdentity,
    trade_identity: TradeEvidenceIdentity,
) -> tuple[V12TradeFeatures, ...]:
    """Attach causal V12 features to reproduced trades using closed M5 bars only."""
    verify_ohlc_evidence(ohlc_identity)
    verify_reproduced_trade_evidence(trade_identity)
    if len(bars) != ohlc_identity.session_rows:
        raise ValueError("OHLC sequence length does not match verified identity")

    times = [bar.open_time for bar in bars]
    if times != sorted(times) or len(times) != len(set(times)):
        raise ValueError("OHLC bars must be unique and chronological")
    session_days = {bar.open_time.date() for bar in bars}
    if len(session_days) != ohlc_identity.session_days:
        raise ValueError("OHLC sequence day count does not match verified identity")

    closed = tuple(ClosedBar(bar.open, bar.high, bar.low, bar.close) for bar in bars)
    index_by_time = {bar.open_time: index for index, bar in enumerate(bars)}
    output: list[V12TradeFeatures] = []

    for trade in trades:
        if trade.signal_time not in index_by_time:
            raise ValueError("signal_time does not map to verified M5 bar")
        if trade.signal_time + _M5 > trade.entry_time:
            raise ValueError("signal bar is not fully closed before entry")

        signal_index = index_by_time[trade.signal_time]
        signal_bar_time = times[signal_index]

        adx = adx_feature(closed, signal_index)
        body = body_quality(closed, signal_index)
        diagnostic_compression = range_compression(closed, signal_index)

        breakout_side_location = (
            body.close_location if trade.side == "long" else 1.0 - body.close_location
        )
        expected_direction = 1 if trade.side == "long" else -1

        stale = None
        if trade.entry_mode == "retest" and trade.retest_time is not None:
            delta_seconds = (trade.retest_time - trade.signal_time).total_seconds()
            if delta_seconds <= 0 or delta_seconds % 300 != 0:
                raise ValueError("retest staleness must align to completed M5 bars")
            stale = retest_staleness(
                breakout_index=0,
                asof_index=int(delta_seconds // 300),
            )

        output.append(
            V12TradeFeatures(
                wf=trade.wf,
                entry_time=trade.entry_time.isoformat(),
                signal_time=trade.signal_time.isoformat(),
                entry_mode=trade.entry_mode,
                side=trade.side,
                r=trade.r,
                asof_bar_open_time=signal_bar_time.isoformat(),
                adx=None if adx is None else adx.adx,
                plus_di=None if adx is None else adx.plus_di,
                minus_di=None if adx is None else adx.minus_di,
                body_fraction=body.body_fraction,
                close_location=body.close_location,
                breakout_side_close_location=breakout_side_location,
                body_direction=body.direction,
                body_direction_agrees=body.direction == expected_direction,
                compression_ratio=(
                    None if diagnostic_compression is None else diagnostic_compression.tr_ratio
                ),
                compression_evidence_state=_DIAGNOSTIC_COMP_STATE,
                bars_since_breakout=stale,
            )
        )
    return tuple(output)
