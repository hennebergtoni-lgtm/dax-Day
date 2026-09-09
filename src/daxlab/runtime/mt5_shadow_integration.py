"""Credential-free bridge from validated Windows MT5 evidence into SHADOW.

The bridge is deliberately observation-only. It cannot place orders and keeps
`order_execution_enabled` fail-closed for SHADOW/PAPER preparation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from daxlab.runtime.mt5_windows_bundle import WindowsMt5Bundle
from daxlab.runtime.prospective_gate import (
    ProspectiveAuthorization,
    ProspectiveGateResult,
    ProspectiveMode,
    evaluate_prospective_gate,
)
from daxlab.runtime.shadow_observation import (
    ShadowCheckpoint,
    ShadowDecision,
    ShadowObservationInput,
    build_shadow_decision,
    recovery_payload,
)


@dataclass(frozen=True, slots=True)
class HostShadowStatus:
    status: str
    blockers: tuple[str, ...]
    symbol: str | None
    closed_m5_bars: int
    latest_closed_bar_age_seconds: float | None
    single_instance_lock_held: bool
    order_execution_enabled: bool
    evidence_fingerprint: str


def evaluate_shadow_from_bundle(
    bundle: WindowsMt5Bundle,
    *,
    authorization: ProspectiveAuthorization,
    single_instance_lock_held: bool,
) -> tuple[ProspectiveGateResult, ShadowDecision | None, HostShadowStatus]:
    """Evaluate validated host evidence and, when allowed, emit a NO_ORDER decision."""
    feed = bundle.feed
    symbol = bundle.host.symbols[0].name if bundle.host.symbols else None
    feed_fresh = bool(feed and feed.fresh and not feed.discontinuities)
    exact_symbol = bundle.symbol_resolution_state not in {
        "AMBIGUOUS",
        "AMBIGUOUS_DATA_ONLY",
        "NOT_FOUND",
        "CONFIGURED_NOT_FOUND",
    }

    gate = evaluate_prospective_gate(
        mode=ProspectiveMode.SHADOW,
        authorization=authorization,
        host_read_only_healthy=bundle.green,
        exact_broker_symbol_resolved=exact_symbol,
        closed_m5_feed_fresh=feed_fresh,
        clock_ok=bundle.host.clock_ok,
        single_instance_lock_held=single_instance_lock_held,
        order_execution_enabled=bundle.host.order_execution_enabled,
    )

    blockers = list(bundle.blockers)
    blockers.extend(gate.blockers)
    blockers = list(dict.fromkeys(blockers))
    status = HostShadowStatus(
        status="GREEN" if not blockers else "BLOCKED",
        blockers=tuple(blockers),
        symbol=symbol,
        closed_m5_bars=len(feed.bars) if feed else 0,
        latest_closed_bar_age_seconds=feed.age_seconds if feed else None,
        single_instance_lock_held=single_instance_lock_held,
        order_execution_enabled=False,
        evidence_fingerprint=bundle.fingerprint,
    )

    if not gate.allowed or feed is None or symbol is None:
        return gate, None, status

    observation = ShadowObservationInput(
        observed_at=feed.observed_at,
        symbol=symbol,
        closed_bar_fingerprint=feed.latest_closed_fingerprint,
        host_read_only_healthy=True,
        feed_fresh=True,
        clock_ok=bundle.host.clock_ok,
        single_instance_lock_held=single_instance_lock_held,
    )
    return gate, build_shadow_decision(observation), status


def host_readiness_summary(status: HostShadowStatus) -> dict[str, Any]:
    """Return an iPhone/web-friendly, credential-free readiness payload."""
    return {
        "status": status.status,
        "blockers": list(status.blockers),
        "symbol": status.symbol,
        "closed_m5_bars": status.closed_m5_bars,
        "latest_closed_bar_age_seconds": status.latest_closed_bar_age_seconds,
        "single_instance_lock_held": status.single_instance_lock_held,
        "order_execution_enabled": False,
        "evidence_fingerprint": status.evidence_fingerprint,
    }


def combined_recovery_payload(
    *,
    bundle: WindowsMt5Bundle,
    checkpoint: ShadowCheckpoint,
    decision: ShadowDecision,
) -> dict[str, Any]:
    """Seal host evidence identity together with a normal SHADOW recovery payload."""
    shadow = recovery_payload(
        checkpoint=checkpoint,
        decisions=(decision,),
        counters=_one_decision_counters(decision),
    )
    payload: dict[str, Any] = {
        "schema_version": "DAXLAB_MT5_SHADOW_RECOVERY_V1",
        "host_evidence_sha256": bundle.fingerprint,
        "shadow": shadow,
        "execution_capability": "NONE",
    }
    payload["payload_sha256"] = _hash(payload)
    return payload


def verify_combined_recovery_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != "DAXLAB_MT5_SHADOW_RECOVERY_V1":
        raise ValueError("combined recovery schema mismatch")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("combined recovery must not carry execution capability")
    evidence_sha = payload.get("host_evidence_sha256")
    if not isinstance(evidence_sha, str) or len(evidence_sha) != 64:
        raise ValueError("host evidence fingerprint missing")
    int(evidence_sha, 16)
    expected = payload.get("payload_sha256")
    if not isinstance(expected, str):
        raise ValueError("combined recovery hash missing")
    unhashed = dict(payload)
    unhashed.pop("payload_sha256", None)
    if _hash(unhashed) != expected:
        raise ValueError("combined recovery hash mismatch")

    shadow = payload.get("shadow")
    if not isinstance(shadow, Mapping):
        raise ValueError("shadow recovery payload missing")
    from daxlab.runtime.shadow_observation import verify_recovery_payload

    verify_recovery_payload(shadow)


def _one_decision_counters(decision: ShadowDecision):
    from daxlab.runtime.shadow_observation import build_counters

    return build_counters((decision,))


def _hash(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
