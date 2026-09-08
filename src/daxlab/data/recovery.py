"""Classify recovered historical datasets without overstating identity."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RecoveryIdentity(StrEnum):
    MISMATCH = "MISMATCH"
    STRUCTURAL_MATCH = "STRUCTURAL_MATCH"
    HASH_VERIFIED = "HASH_VERIFIED"


@dataclass(frozen=True, slots=True)
class RecoveryEvidence:
    raw_rows: int
    session_days: int
    session_rows: int
    bars_per_day: int
    invalid_ohlc_rows: int
    expected_raw_rows: int
    expected_session_days: int
    expected_session_rows: int
    expected_bars_per_day: int
    expected_session_sha256: str
    observed_session_sha256: str | None = None

    @property
    def structural_match(self) -> bool:
        return (
            self.raw_rows == self.expected_raw_rows
            and self.session_days == self.expected_session_days
            and self.session_rows == self.expected_session_rows
            and self.bars_per_day == self.expected_bars_per_day
            and self.invalid_ohlc_rows == 0
        )

    @property
    def identity(self) -> RecoveryIdentity:
        if not self.structural_match:
            return RecoveryIdentity.MISMATCH
        if self.observed_session_sha256 == self.expected_session_sha256:
            return RecoveryIdentity.HASH_VERIFIED
        return RecoveryIdentity.STRUCTURAL_MATCH

    @property
    def clean_reference_eligible(self) -> bool:
        return self.identity is RecoveryIdentity.HASH_VERIFIED


def classify_recovery(evidence: RecoveryEvidence) -> RecoveryIdentity:
    """Return the strongest evidence level justified by the observed dataset."""
    return evidence.identity
