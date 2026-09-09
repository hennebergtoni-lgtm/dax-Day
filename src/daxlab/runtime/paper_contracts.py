"""Paper-execution contracts with no broker adapter and no order submission API.

These types prepare a deterministic execution boundary without starting Paper or
creating any venue capability.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class PaperLifecycleState(StrEnum):
    ACK = "ACK"
    REJECT = "REJECT"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


class SameBarPolicy(StrEnum):
    CONSERVATIVE_STOP_FIRST = "CONSERVATIVE_STOP_FIRST"


class GapPolicy(StrEnum):
    FILL_AT_FIRST_AVAILABLE = "FILL_AT_FIRST_AVAILABLE"


class PartialFillPolicy(StrEnum):
    DISABLED = "DISABLED"
    PRO_RATA = "PRO_RATA"


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    schema_version: str
    decision_id: str
    run_manifest_fingerprint: str
    created_at: datetime
    symbol: str
    side: Side
    quantity: float
    requested_price: float
    stop_price: float
    target_price: float
    client_order_id: str

    @classmethod
    def build(
        cls,
        *,
        decision_id: str,
        run_manifest_fingerprint: str,
        created_at: datetime,
        symbol: str,
        side: Side,
        quantity: float,
        requested_price: float,
        stop_price: float,
        target_price: float,
    ) -> "ExecutionIntent":
        _sha(decision_id, "decision_id")
        _sha(run_manifest_fingerprint, "run_manifest_fingerprint")
        if created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if not symbol.strip():
            raise ValueError("symbol must be non-empty")
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        for name, value in (
            ("requested_price", requested_price),
            ("stop_price", stop_price),
            ("target_price", target_price),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        identity = {
            "schema_version": "DAXLAB_EXECUTION_INTENT_V1",
            "decision_id": decision_id,
            "run_manifest_fingerprint": run_manifest_fingerprint,
            "created_at": created_at.isoformat(),
            "symbol": symbol,
            "side": side.value,
            "quantity": float(quantity),
            "requested_price": float(requested_price),
            "stop_price": float(stop_price),
            "target_price": float(target_price),
        }
        return cls(
            schema_version="DAXLAB_EXECUTION_INTENT_V1",
            decision_id=decision_id,
            run_manifest_fingerprint=run_manifest_fingerprint,
            created_at=created_at,
            symbol=symbol,
            side=side,
            quantity=float(quantity),
            requested_price=float(requested_price),
            stop_price=float(stop_price),
            target_price=float(target_price),
            client_order_id=_hash(identity),
        )


@dataclass(frozen=True, slots=True)
class PaperFillModelConfig:
    schema_version: str = "DAXLAB_PAPER_FILL_MODEL_V1"
    spread_points: float = 0.20
    slippage_points: float = 0.10
    commission_points: float = 0.10
    latency_ms: int = 250
    same_bar_policy: SameBarPolicy = SameBarPolicy.CONSERVATIVE_STOP_FIRST
    gap_policy: GapPolicy = GapPolicy.FILL_AT_FIRST_AVAILABLE
    partial_fill_policy: PartialFillPolicy = PartialFillPolicy.DISABLED

    def __post_init__(self) -> None:
        if min(self.spread_points, self.slippage_points, self.commission_points) < 0:
            raise ValueError("paper cost assumptions must be non-negative")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")

    @property
    def fingerprint(self) -> str:
        return _hash(
            {
                "schema_version": self.schema_version,
                "spread_points": self.spread_points,
                "slippage_points": self.slippage_points,
                "commission_points": self.commission_points,
                "latency_ms": self.latency_ms,
                "same_bar_policy": self.same_bar_policy.value,
                "gap_policy": self.gap_policy.value,
                "partial_fill_policy": self.partial_fill_policy.value,
            }
        )


@dataclass(frozen=True, slots=True)
class PaperTelemetry:
    schema_version: str
    decision_id: str
    run_manifest_fingerprint: str
    client_order_id: str
    lifecycle_state: PaperLifecycleState
    requested_at: datetime
    accepted_at: datetime | None
    filled_at: datetime | None
    requested_price: float
    filled_price: float | None
    spread_points: float
    slippage_points: float
    commission_points: float
    feed_age_seconds: float
    health_state: str
    reconciliation_state: str
    execution_capability: str = "SIMULATION_ONLY"

    def __post_init__(self) -> None:
        for value in (self.requested_at, self.accepted_at, self.filled_at):
            if value is not None and value.tzinfo is None:
                raise ValueError("paper telemetry timestamps must be timezone-aware")
        if min(
            self.requested_price,
            self.spread_points,
            self.slippage_points,
            self.commission_points,
            self.feed_age_seconds,
        ) < 0:
            raise ValueError("paper telemetry numeric fields must be non-negative")
        if self.execution_capability != "SIMULATION_ONLY":
            raise ValueError("paper telemetry cannot carry broker execution capability")


class IntentDeduplicator:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def accept(self, intent: ExecutionIntent) -> bool:
        if intent.client_order_id in self._seen:
            return False
        self._seen.add(intent.client_order_id)
        return True


def _sha(value: str, field: str) -> None:
    if len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    int(value, 16)


def _hash(value: dict[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
