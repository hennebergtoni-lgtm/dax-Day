"""Diagnostic-only closed-M5 gap reporting for MT5 evidence.

This module does not classify broker session gaps as acceptable. Any gap larger
than one M5 interval is reported as UNVERIFIED_SESSION_GAP until broker session
evidence is separately verified.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from daxlab.runtime.mt5_readonly import Mt5Bar


@dataclass(frozen=True, slots=True)
class GapDiagnostic:
    start: str
    end: str
    delta_seconds: int
    missing_m5_intervals: int
    classification: str = "UNVERIFIED_SESSION_GAP"


@dataclass(frozen=True, slots=True)
class GapDiagnosticReport:
    status: str
    gaps: tuple[GapDiagnostic, ...]
    auto_accepted_gap_count: int
    requires_human_review: bool
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def diagnose_m5_gaps(bars: Iterable[Mt5Bar]) -> GapDiagnosticReport:
    ordered = tuple(bars)
    for bar in ordered:
        if bar.open_time.tzinfo is None:
            raise ValueError("gap diagnostic requires timezone-aware bars")

    gaps: list[GapDiagnostic] = []
    for previous, current in zip(ordered, ordered[1:]):
        delta = int((current.open_time - previous.open_time).total_seconds())
        if delta <= 0:
            raise ValueError("gap diagnostic requires strictly increasing bar times")
        if delta == 300:
            continue
        if delta < 300 or delta % 300 != 0:
            raise ValueError("gap diagnostic encountered non-M5-aligned timestamp delta")
        gaps.append(
            GapDiagnostic(
                start=previous.open_time.isoformat(),
                end=current.open_time.isoformat(),
                delta_seconds=delta,
                missing_m5_intervals=(delta // 300) - 1,
            )
        )

    return GapDiagnosticReport(
        status="NO_GAPS" if not gaps else "DIAGNOSTIC_ONLY",
        gaps=tuple(gaps),
        auto_accepted_gap_count=0,
        requires_human_review=bool(gaps),
    )
