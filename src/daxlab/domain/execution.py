"""Canonical broker-neutral execution-domain contracts.

These types describe deterministic intent only. They do not grant broker access,
authorize order submission, or provide an execution implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from hashlib import sha256
import json
from math import isfinite

from daxlab.domain.market import InstrumentId


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    """Deterministic product intent before any simulation or broker adapter."""

    decision_id: str
    provenance_fingerprint: str
    created_at: datetime
    instrument_id: InstrumentId
    side: OrderSide
    quantity: float
    requested_price: float
    stop_price: float
    target_price: float
    intent_id: str
    schema_version: str = "DAXLAB_EXECUTION_INTENT_V2"

    @classmethod
    def build(
        cls,
        *,
        decision_id: str,
        provenance_fingerprint: str,
        created_at: datetime,
        instrument_id: InstrumentId,
        side: OrderSide,
        quantity: float,
        requested_price: float,
        stop_price: float,
        target_price: float,
    ) -> "ExecutionIntent":
        _require_sha256(decision_id, "decision_id")
        _require_sha256(provenance_fingerprint, "provenance_fingerprint")
        _require_utc(created_at, "created_at")
        if not isfinite(quantity) or quantity <= 0:
            raise ValueError("quantity must be finite and positive")
        for field_name, value in (
            ("requested_price", requested_price),
            ("stop_price", stop_price),
            ("target_price", target_price),
        ):
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{field_name} must be finite and positive")

        identity = {
            "schema_version": "DAXLAB_EXECUTION_INTENT_V2",
            "decision_id": decision_id,
            "provenance_fingerprint": provenance_fingerprint,
            "created_at": created_at.isoformat(),
            "instrument_id": instrument_id.value,
            "side": side.value,
            "quantity": float(quantity),
            "requested_price": float(requested_price),
            "stop_price": float(stop_price),
            "target_price": float(target_price),
        }
        return cls(
            decision_id=decision_id,
            provenance_fingerprint=provenance_fingerprint,
            created_at=created_at,
            instrument_id=instrument_id,
            side=side,
            quantity=float(quantity),
            requested_price=float(requested_price),
            stop_price=float(stop_price),
            target_price=float(target_price),
            intent_id=_fingerprint(identity),
        )


def _require_sha256(value: str, field_name: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def _fingerprint(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
