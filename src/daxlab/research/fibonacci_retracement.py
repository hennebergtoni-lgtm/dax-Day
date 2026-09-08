from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


ALLOWED_ANCHOR_RULES = frozenset(
    {
        "OR_COMPLETED_IMPULSE",
        "CONFIRMED_BREAKOUT_IMPULSE",
        "STRUCTURE_CONFIRMED_IMPULSE",
    }
)


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


@dataclass(frozen=True)
class CausalImpulseAnchor:
    rule_id: str
    start_price: float
    start_time: datetime
    end_price: float
    end_time: datetime
    confirmation_time: datetime

    def __post_init__(self) -> None:
        if self.rule_id not in ALLOWED_ANCHOR_RULES:
            raise ValueError("unknown Fibonacci anchor rule")
        if self.start_price == self.end_price:
            raise ValueError("impulse start and end must differ")
        timestamps = (self.start_time, self.end_time, self.confirmation_time)
        if any(value.tzinfo is None for value in timestamps):
            raise ValueError("Fibonacci anchor timestamps must be timezone-aware")
        if self.start_time > self.end_time or self.end_time > self.confirmation_time:
            raise ValueError("invalid Fibonacci anchor timestamp ordering")


def validate_retracement_observation(
    anchor: CausalImpulseAnchor,
    *,
    observation_time: datetime,
    entry_time: datetime | None = None,
) -> None:
    """Fail closed unless a retracement observation is causally usable."""
    if observation_time.tzinfo is None:
        raise ValueError("retracement observation time must be timezone-aware")
    if observation_time <= anchor.confirmation_time:
        raise ValueError("retracement observation must follow anchor confirmation")
    if entry_time is not None and entry_time.tzinfo is None:
        raise ValueError("entry time must be timezone-aware")
    if entry_time is not None and observation_time > entry_time:
        raise ValueError("retracement observation cannot occur after entry")


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
