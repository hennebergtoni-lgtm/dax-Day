"""Strict parity gates for the frozen V11.2 reference.

A replacement/reconstructed engine is not V11.2 until all supplied reference surfaces match.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    trades: int
    return_r: float
    pf: float | None = None


@dataclass(frozen=True, slots=True)
class ParityResult:
    passed: bool
    mismatches: tuple[str, ...]


def compare_metrics(
    actual: MetricSnapshot,
    expected: MetricSnapshot,
    *,
    abs_tol: float = 1e-10,
) -> ParityResult:
    """Compare reference metrics without silently accepting material drift."""
    mismatches: list[str] = []
    if actual.trades != expected.trades:
        mismatches.append(f"trades: actual={actual.trades} expected={expected.trades}")
    if not isclose(actual.return_r, expected.return_r, rel_tol=0.0, abs_tol=abs_tol):
        mismatches.append(f"return_r: actual={actual.return_r} expected={expected.return_r}")

    if expected.pf is None:
        if actual.pf is not None:
            mismatches.append(f"pf: actual={actual.pf} expected=None")
    elif actual.pf is None or not isclose(actual.pf, expected.pf, rel_tol=0.0, abs_tol=abs_tol):
        mismatches.append(f"pf: actual={actual.pf} expected={expected.pf}")

    return ParityResult(passed=not mismatches, mismatches=tuple(mismatches))


PRE_GATE_REFERENCE = MetricSnapshot(
    trades=14,
    return_r=3.9351648669,
    pf=1.5556035886,
)
