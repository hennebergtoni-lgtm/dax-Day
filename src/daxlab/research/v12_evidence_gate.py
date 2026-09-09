"""Fail-closed evidence gates for V12 isolated candidate evaluation.

These gates prevent research from silently substituting a different OHLC sample
or legacy trade artifact for the frozen/reproduced V11.2 evidence surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass

VERIFIED_SESSION_ROWS = 172_319
VERIFIED_SESSION_DAYS = 1_673
VERIFIED_DATASET_SHA256 = "e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2"
REPRODUCED_TRADE_ROWS = 856
REPRODUCED_TRADES_SHA256 = "f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023"
REPRODUCED_TRADE_PROVENANCE = "NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH"


@dataclass(frozen=True, slots=True)
class OhlcEvidenceIdentity:
    session_rows: int
    session_days: int
    sha256: str


@dataclass(frozen=True, slots=True)
class TradeEvidenceIdentity:
    rows: int
    sha256: str
    provenance: str


def verify_ohlc_evidence(identity: OhlcEvidenceIdentity) -> None:
    if identity.session_rows != VERIFIED_SESSION_ROWS:
        raise ValueError("V12 OHLC evidence row-count mismatch")
    if identity.session_days != VERIFIED_SESSION_DAYS:
        raise ValueError("V12 OHLC evidence session-day mismatch")
    if identity.sha256 != VERIFIED_DATASET_SHA256:
        raise ValueError("V12 OHLC evidence fingerprint mismatch")


def verify_reproduced_trade_evidence(identity: TradeEvidenceIdentity) -> None:
    if identity.rows != REPRODUCED_TRADE_ROWS:
        raise ValueError("V12 reproduced trade row-count mismatch")
    if identity.sha256 != REPRODUCED_TRADES_SHA256:
        raise ValueError("V12 reproduced trade fingerprint mismatch")
    if identity.provenance != REPRODUCED_TRADE_PROVENANCE:
        raise ValueError("V12 reproduced trade provenance mismatch")
