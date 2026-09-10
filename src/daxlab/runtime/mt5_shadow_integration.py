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
    build_counters,
    build_shadow_decision,
    recovery_payload,
    verify_recovery_payload,
)
from daxlab.runtime.shadow_resume_anchor import (
    bars_after_resume_anchor,
    reconcile_shadow_resume_anchor,
)
from daxlab.runtime.shadow_soak import (
    MT5_READONLY_EVIDENCE_STATE,
    SoakCheckpoint as ShadowSoakCheckpoint,
    SoakResult,
    run_shadow_soak,
    verify_soak_checkpoint,
)

_MT5_RESUME_SCHEMA = "DAXLAB_MT5_SHADOW_RESUME_V1"


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


@dataclass(frozen=True, slots=True)
class Mt5ShadowResumeState:
    """Hashed provenance envelope for an MT5 read-only SHADOW checkpoint."""

    schema_version: str
    evidence_state: str
    symbol: str
    checkpoint: ShadowSoakCheckpoint
    payload_sha256: str


def build_mt5_shadow_resume_state(
    *,
    symbol: str,
    checkpoint: ShadowSoakCheckpoint,
) -> Mt5ShadowResumeState:
    """Bind a verified soak checkpoint to MT5 read-only provenance and symbol."""
    clean_symbol = symbol.strip()
    if not clean_symbol:
        raise ValueError("MT5 SHADOW resume symbol must be non-empty")
    verify_soak_checkpoint(checkpoint)
    payload = _mt5_resume_payload(
        schema_version=_MT5_RESUME_SCHEMA,
        evidence_state=MT5_READONLY_EVIDENCE_STATE,
        symbol=clean_symbol,
        checkpoint=checkpoint,
    )
    return Mt5ShadowResumeState(
        schema_version=_MT5_RESUME_SCHEMA,
        evidence_state=MT5_READONLY_EVIDENCE_STATE,
        symbol=clean_symbol,
        checkpoint=checkpoint,
        payload_sha256=_hash(payload),
    )


def verify_mt5_shadow_resume_state(
    state: Mt5ShadowResumeState,
    *,
    expected_symbol: str,
) -> None:
    """Fail closed if resume provenance, symbol, checkpoint or hash is invalid."""
    if not isinstance(state, Mt5ShadowResumeState):
        raise ValueError("MT5 SHADOW resume state type mismatch")
    if state.schema_version != _MT5_RESUME_SCHEMA:
        raise ValueError("MT5 SHADOW resume schema mismatch")
    if state.evidence_state != MT5_READONLY_EVIDENCE_STATE:
        raise ValueError("MT5 SHADOW resume evidence state mismatch")
    clean_expected = expected_symbol.strip()
    if not clean_expected or state.symbol != clean_expected:
        raise ValueError("MT5 SHADOW resume symbol mismatch")
    verify_soak_checkpoint(state.checkpoint)
    expected_hash = _hash(
        _mt5_resume_payload(
            schema_version=state.schema_version,
            evidence_state=state.evidence_state,
            symbol=state.symbol,
            checkpoint=state.checkpoint,
        )
    )
    if state.payload_sha256 != expected_hash:
        raise ValueError("MT5 SHADOW resume hash mismatch")


def mt5_shadow_resume_payload(state: Mt5ShadowResumeState) -> dict[str, Any]:
    """Return a JSON-safe persistence payload after validating the envelope."""
    verify_mt5_shadow_resume_state(state, expected_symbol=state.symbol)
    return {
        "schema_version": state.schema_version,
        "evidence_state": state.evidence_state,
        "symbol": state.symbol,
        "checkpoint": asdict(state.checkpoint),
        "payload_sha256": state.payload_sha256,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def parse_mt5_shadow_resume_payload(payload: Mapping[str, Any]) -> Mt5ShadowResumeState:
    """Reconstruct and verify a persisted credential-free MT5 resume envelope."""
    allowed = {
        "schema_version",
        "evidence_state",
        "symbol",
        "checkpoint",
        "payload_sha256",
        "execution_capability",
        "order_execution_enabled",
    }
    unknown = payload.keys() - allowed
    if unknown:
        raise ValueError(f"unknown MT5 SHADOW resume fields: {sorted(unknown)}")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("MT5 SHADOW resume execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("MT5 SHADOW resume must keep order execution disabled")
    checkpoint_raw = payload.get("checkpoint")
    if not isinstance(checkpoint_raw, Mapping):
        raise ValueError("MT5 SHADOW resume checkpoint missing")
    checkpoint_values = dict(checkpoint_raw)
    for field in ("seen_decision_ids", "seen_bar_fingerprints"):
        values = checkpoint_values.get(field)
        if not isinstance(values, (list, tuple)) or not all(
            isinstance(item, str) for item in values
        ):
            raise ValueError("MT5 SHADOW resume checkpoint invalid")
        checkpoint_values[field] = tuple(values)
    try:
        checkpoint = ShadowSoakCheckpoint(**checkpoint_values)
    except TypeError as exc:
        raise ValueError("MT5 SHADOW resume checkpoint invalid") from exc
    state = Mt5ShadowResumeState(
        schema_version=str(payload.get("schema_version", "")),
        evidence_state=str(payload.get("evidence_state", "")),
        symbol=str(payload.get("symbol", "")),
        checkpoint=checkpoint,
        payload_sha256=str(payload.get("payload_sha256", "")),
    )
    verify_mt5_shadow_resume_state(state, expected_symbol=state.symbol)
    return state


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


def evaluate_shadow_soak_from_bundle(
    bundle: WindowsMt5Bundle,
    *,
    authorization: ProspectiveAuthorization,
    single_instance_lock_held: bool,
    resume_state: Mt5ShadowResumeState | None = None,
) -> tuple[ProspectiveGateResult, SoakResult | None, HostShadowStatus]:
    """Process validated closed M5 bars with provenance-bound resume semantics."""
    gate, _, status = evaluate_shadow_from_bundle(
        bundle,
        authorization=authorization,
        single_instance_lock_held=single_instance_lock_held,
    )
    if not gate.allowed or bundle.feed is None or status.symbol is None:
        return gate, None, status

    checkpoint: ShadowSoakCheckpoint | None = None
    bars = bundle.feed.bars
    if resume_state is not None:
        verify_mt5_shadow_resume_state(resume_state, expected_symbol=status.symbol)
        checkpoint = resume_state.checkpoint
        anchor = reconcile_shadow_resume_anchor(bars, checkpoint=checkpoint)
        bars = bars_after_resume_anchor(bars, result=anchor)

    result = run_shadow_soak(
        bars,
        symbol=status.symbol,
        checkpoint=checkpoint,
        evidence_state=MT5_READONLY_EVIDENCE_STATE,
    )
    if result.execution_capability != "NONE":
        raise RuntimeError("MT5 SHADOW soak unexpectedly gained execution capability")
    if result.order_execution_enabled is not False:
        raise RuntimeError("MT5 SHADOW soak unexpectedly enabled order execution")
    if any(item.action != "NO_ORDER" for item in result.decisions):
        raise RuntimeError("MT5 SHADOW soak emitted an order-capable action")
    return gate, result, status


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
        counters=build_counters((decision,)),
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
    verify_recovery_payload(shadow)


def _mt5_resume_payload(
    *,
    schema_version: str,
    evidence_state: str,
    symbol: str,
    checkpoint: ShadowSoakCheckpoint,
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "evidence_state": evidence_state,
        "symbol": symbol,
        "checkpoint": asdict(checkpoint),
    }


def _hash(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
