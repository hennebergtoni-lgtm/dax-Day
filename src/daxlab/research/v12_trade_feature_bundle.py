"""Causal trade-feature bundle for V12 isolated research candidates.

The bundle is intentionally input-bound: callers must provide a verified full
2014-2019 session OHLC sequence and reproduced clean trade rows. This module
never loads arbitrary external data and cannot execute orders.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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


@dataclass(frozen=True, slots=True)
class V12TradeFeatures:
    wf: int
    entry_time: str
    entry_mode: str
    r: float
    asof_bar_open_time: str
    adx: float | None
    plus_di: float | None
    minus_di: float | None
    body_fraction: float
    close_location: float
    body_direction: int
    compression_ratio: float | None
    bars_since_breakout: int | None


def build_trade_feature_bundle(
    bars: Sequence[TimedClosedBar],
    trades: Iterable[ReproducedTrade],
    *,
    ohlc_identity: OhlcEvidenceIdentity,
    trade_identity: TradeEvidenceIdentity,
) -> tuple[V12TradeFeatures, ...]:
    """Attach causal V12 features to reproduced trades using only closed bars before entry."""
    verify_ohlc_evidence(ohlc_identity)
    verify_reproduced_trade_evidence(trade_identity)
    if not bars:
        raise ValueError("verified OHLC evidence cannot be empty")

    times = [bar.open_time for bar in bars]
    if times != sorted(times) or len(times) != len(set(times)):
        raise ValueError("OHLC bars must be unique and chronological")

    closed = tuple(ClosedBar(bar.open, bar.high, bar.low, bar.close) for bar in bars)
    index_by_time = {bar.open_time: index for index, bar in enumerate(bars)}
    output: list[V12TradeFeatures] = []

    for trade in trades:
        asof_time = trade.entry_time
        eligible = [time for time in times if time < asof_time]
        if not eligible:
            raise ValueError("trade has no completed M5 bar before entry")
        last_time = eligible[-1]
        asof_index = index_by_time[last_time]

        adx = adx_feature(closed, asof_index)
        body = body_quality(closed, asof_index)
        compression = range_compression(closed, asof_index)

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
                entry_mode=trade.entry_mode,
                r=trade.r,
                asof_bar_open_time=last_time.isoformat(),
                adx=None if adx is None else adx.adx,
                plus_di=None if adx is None else adx.plus_di,
                minus_di=None if adx is None else adx.minus_di,
                body_fraction=body.body_fraction,
                close_location=body.close_location,
                body_direction=body.direction,
                compression_ratio=None if compression is None else compression.tr_ratio,
                bars_since_breakout=stale,
            )
        )
    return tuple(output)
