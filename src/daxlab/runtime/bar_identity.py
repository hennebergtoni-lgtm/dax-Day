"""Deterministic identity for one-action-per-closed-bar protection."""

from __future__ import annotations

import hashlib
from datetime import datetime


def closed_bar_identity(*, canonical_symbol: str, timeframe: str, close_time: datetime) -> str:
    if close_time.tzinfo is None:
        raise ValueError("close_time must be timezone-aware")
    payload = f"{canonical_symbol}|{timeframe}|{close_time.isoformat()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
