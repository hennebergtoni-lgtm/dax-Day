from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FibonacciLevels:
    start: float
    end: float
    direction: str
    r33: float
    r382: float
    r50: float
    r618: float
    r667: float


def retracement_levels(start: float, end: float) -> FibonacciLevels:
    """Return fixed retracement levels for one already-defined impulse.

    The function deliberately does not discover swings. The caller must provide
    an impulse whose start/end were known before any subsequent retracement test.
    """
    start = float(start)
    end = float(end)
    if start == end:
        raise ValueError("impulse start and end must differ")

    move = end - start
    direction = "long" if move > 0 else "short"

    def level(frac: float) -> float:
        return end - move * frac

    return FibonacciLevels(
        start=start,
        end=end,
        direction=direction,
        r33=level(1.0 / 3.0),
        r382=level(0.382),
        r50=level(0.5),
        r618=level(0.618),
        r667=level(2.0 / 3.0),
    )


def normalized_retracement(start: float, end: float, price: float) -> float:
    """Fraction retraced from impulse end back toward impulse start."""
    start = float(start)
    end = float(end)
    price = float(price)
    move = end - start
    if move == 0:
        raise ValueError("impulse start and end must differ")
    return float((end - price) / move)


def in_zone(value: float, lower: float, upper: float) -> bool:
    lo, hi = sorted((float(lower), float(upper)))
    return lo <= float(value) <= hi
