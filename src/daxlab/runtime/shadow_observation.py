"""Offline-safe shadow observation primitives.

This module cannot place orders. It turns validated closed-bar observations into
credential-free NO_ORDER records with deterministic IDs, duplicate suppression,
checkpoint state, watchdog blocking, dashboard counters and recovery payloads.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

V112_EXPERIMENT_ID = "V112_REFERENCE_V1"
V112_ENGINE_SHA256 = "b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888"


@dataclass(frozen=True, slots=True)
class ShadowObservationInput:
    observed_at: datetime
    symbol: str
    closed_bar_fingerprint: str
    host_read_only_healthy: bool
    feed_fresh: bool
    clock_ok: bool
    single_instance_lock_held: bool
    reference_experiment_id: str = V112_EXPERIMENT_ID
    reference_engine_sha256: str = V112_ENGINE_SHA256

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if not self.symbol.strip():
            raise ValueError("symbol must be non-empty")
        if len(self.closed_bar_fingerprint) != 64:
            raise ValueError("closed_bar_fingerprint must be sha256 hex")
        int(self.closed_bar_fingerprint, 16)
        if self.reference_experiment_id != V112_EXPERIMENT_ID:
            raise ValueError("V11.2 reference experiment mismatch")
        if self.reference_engine_sha256 != V112_ENGINE_SHA256:
            raise ValueError("V11.2 engine fingerprint mismatch")


@dataclass(frozen=True, slots=True)
class ShadowDecision:
    decision_id: str
    observed_at: str
    symbol: str
    closed_bar_fingerprint: str
    action: str
    reason_codes: tuple[str, ...]
    reference_experiment_id: str
    reference_engine_sha256: str


@dataclass(frozen=True, slots=True)
class ShadowCheckpoint:
    schema_version: str
    last_decision_id: str | None
    processed_count: int


@dataclass(frozen=True, slots=True)
class ShadowCounters:
    observations: int
    no_order: int
    blocked: int
    duplicates_suppressed: int


def build_shadow_decision(observation: ShadowObservationInput) -> ShadowDecision:
    blockers = _watchdog_blockers(observation)
    reasons = blockers or ("OBSERVATION_ONLY_NO_ORDER",)
    identity = {
        "observed_at": observation.observed_at.isoformat(),
        "symbol": observation.symbol,
        "closed_bar_fingerprint": observation.closed_bar_fingerprint,
        "reference_experiment_id": observation.reference_experiment_id,
        "reference_engine_sha256": observation.reference_engine_sha256,
        "reason_codes": reasons,
    }
    decision_id = sha256(_canonical(identity).encode("utf-8")).hexdigest()
    return ShadowDecision(
        decision_id=decision_id,
        observed_at=observation.observed_at.isoformat(),
        symbol=observation.symbol,
        closed_bar_fingerprint=observation.closed_bar_fingerprint,
        action="NO_ORDER",
        reason_codes=reasons,
        reference_experiment_id=observation.reference_experiment_id,
        reference_engine_sha256=observation.reference_engine_sha256,
    )


def suppress_duplicate(decision: ShadowDecision, seen_ids: set[str]) -> bool:
    """Return True when duplicate was suppressed; mutate only the caller-owned ID set."""
    if decision.decision_id in seen_ids:
        return True
    seen_ids.add(decision.decision_id)
    return False


def advance_checkpoint(checkpoint: ShadowCheckpoint, decision: ShadowDecision) -> ShadowCheckpoint:
    if checkpoint.schema_version != "DAXLAB_SHADOW_CHECKPOINT_V1":
        raise ValueError("shadow checkpoint schema mismatch")
    return ShadowCheckpoint(
        schema_version=checkpoint.schema_version,
        last_decision_id=decision.decision_id,
        processed_count=checkpoint.processed_count + 1,
    )


def initial_checkpoint() -> ShadowCheckpoint:
    return ShadowCheckpoint("DAXLAB_SHADOW_CHECKPOINT_V1", None, 0)


def build_counters(
    decisions: Iterable[ShadowDecision], *, duplicates_suppressed: int = 0
) -> ShadowCounters:
    items = tuple(decisions)
    blocked = sum(1 for item in items if item.reason_codes != ("OBSERVATION_ONLY_NO_ORDER",))
    return ShadowCounters(
        observations=len(items),
        no_order=len(items),
        blocked=blocked,
        duplicates_suppressed=duplicates_suppressed,
    )


def recovery_payload(
    *, checkpoint: ShadowCheckpoint, decisions: Iterable[ShadowDecision], counters: ShadowCounters
) -> dict[str, Any]:
    payload = {
        "schema_version": "DAXLAB_SHADOW_RECOVERY_V1",
        "checkpoint": asdict(checkpoint),
        "decisions": [asdict(item) for item in decisions],
        "counters": asdict(counters),
        "execution_capability": "NONE",
    }
    payload["payload_sha256"] = sha256(_canonical(payload).encode("utf-8")).hexdigest()
    return payload


def verify_recovery_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != "DAXLAB_SHADOW_RECOVERY_V1":
        raise ValueError("shadow recovery schema mismatch")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("shadow recovery must not carry execution capability")
    if "payload_sha256" not in payload:
        raise ValueError("shadow recovery hash missing")
    expected = str(payload["payload_sha256"])
    unhashed = dict(payload)
    unhashed.pop("payload_sha256", None)
    observed = sha256(_canonical(unhashed).encode("utf-8")).hexdigest()
    if observed != expected:
        raise ValueError("shadow recovery hash mismatch")
    forbidden = ("password", "otp", "account_number", "api_key", "secret", "token")
    serialized = _canonical(unhashed).lower()
    if any(term in serialized for term in forbidden):
        raise ValueError("shadow recovery contains forbidden credential field")


def _watchdog_blockers(observation: ShadowObservationInput) -> tuple[str, ...]:
    blockers: list[str] = []
    if not observation.host_read_only_healthy:
        blockers.append("MT5_HOST_NOT_HEALTHY")
    if not observation.feed_fresh:
        blockers.append("CLOSED_M5_FEED_NOT_FRESH")
    if not observation.clock_ok:
        blockers.append("CLOCK_NOT_SAFE")
    if not observation.single_instance_lock_held:
        blockers.append("SINGLE_INSTANCE_LOCK_NOT_HELD")
    return tuple(blockers)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
