"""Bounded drift checks that can warn or block but never self-optimize."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DriftState(StrEnum):
    OK = "OK"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass(frozen=True, slots=True)
class ReferenceBand:
    lower: float
    upper: float
    block_margin: float = 0.25

    def __post_init__(self) -> None:
        if self.lower >= self.upper:
            raise ValueError("lower must be below upper")
        if self.block_margin < 0:
            raise ValueError("block_margin must be non-negative")

    def classify(self, value: float) -> DriftState:
        if self.lower <= value <= self.upper:
            return DriftState.OK
        width = self.upper - self.lower
        block_low = self.lower - width * self.block_margin
        block_high = self.upper + width * self.block_margin
        if block_low <= value <= block_high:
            return DriftState.WARN
        return DriftState.BLOCK
