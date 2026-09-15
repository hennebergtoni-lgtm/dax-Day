"""One tamper-evident persistence envelope for complete CAND-001 SHADOW state.

Nested state semantics remain owned by the existing candidate, active-trade and
publication modules. This envelope only binds them to one SHADOW RunManifest so
callers can persist the whole state with one existing ``atomic_write_json`` call.
"""
from __future__ import annotations

from typing import Any, Mapping

from daxlab.runtime.candidate_active_trade_state import (
    candidate_active_trade_payload,
    parse_candidate_active_trade_payload,
)
from daxlab.runtime.candidate_config import Cand001Config
from daxlab.runtime.candidate_publication_state import (
    candidate_publication_state_payload,
    parse_candidate_publication_state_payload,
)
from daxlab.runtime.candidate_shadow_orchestrator import Cand001ShadowState
from daxlab.runtime.candidate_state import candidate_state_payload, parse_candidate_state_payload
from daxlab.runtime.contracts import RuntimeMode
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.manifests import RunManifest


SCHEMA_VERSION = "DAX_BOT_CANDIDATE_SHADOW_CHECKPOINT_V1"
_ALLOWED_FIELDS = {
    "schema_version",
    "run_manifest_fingerprint",
    "pipeline_state",
    "active_trade",
    "publication_state",
    "execution_capability",
    "order_execution_enabled",
    "payload_fingerprint",
}


def candidate_shadow_checkpoint_payload(
    state: Cand001ShadowState,
    *,
    run_manifest: RunManifest,
    config: Cand001Config | None = None,
) -> dict[str, Any]:
    """Bind complete CAND-001 SHADOW state to one deterministic run identity."""
    cfg = config or Cand001Config()
    _require_shadow_manifest(run_manifest)
    _validate_state_relationships(state, run_manifest=run_manifest, config=cfg)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_manifest_fingerprint": run_manifest.manifest_fingerprint,
        "pipeline_state": candidate_state_payload(state.pipeline, config=cfg),
        "active_trade": (
            candidate_active_trade_payload(state.active_trade)
            if state.active_trade is not None
            else None
        ),
        "publication_state": candidate_publication_state_payload(state.publication),
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }
    payload["payload_fingerprint"] = stable_fingerprint(payload)
    return payload


def parse_candidate_shadow_checkpoint_payload(
    payload: Mapping[str, Any],
    *,
    run_manifest: RunManifest,
    config: Cand001Config | None = None,
) -> Cand001ShadowState:
    """Restore one complete SHADOW state and fail closed on any provenance drift."""
    cfg = config or Cand001Config()
    _require_shadow_manifest(run_manifest)
    unknown = payload.keys() - _ALLOWED_FIELDS
    missing = _ALLOWED_FIELDS - payload.keys()
    if unknown:
        raise ValueError(f"unknown candidate SHADOW checkpoint fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing candidate SHADOW checkpoint fields: {sorted(missing)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("candidate SHADOW checkpoint schema mismatch")
    if payload.get("run_manifest_fingerprint") != run_manifest.manifest_fingerprint:
        raise ValueError("candidate SHADOW checkpoint run-manifest drift")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("candidate SHADOW checkpoint execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("candidate SHADOW checkpoint cannot enable order execution")

    observed = payload.get("payload_fingerprint")
    _sha(observed, "payload_fingerprint")
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    if stable_fingerprint(unhashed) != observed:
        raise ValueError("candidate SHADOW checkpoint payload fingerprint mismatch")

    raw_pipeline = payload.get("pipeline_state")
    raw_publication = payload.get("publication_state")
    raw_active = payload.get("active_trade")
    if not isinstance(raw_pipeline, Mapping):
        raise ValueError("candidate SHADOW checkpoint pipeline_state missing")
    if not isinstance(raw_publication, Mapping):
        raise ValueError("candidate SHADOW checkpoint publication_state missing")
    if raw_active is not None and not isinstance(raw_active, Mapping):
        raise ValueError("candidate SHADOW checkpoint active_trade invalid")

    state = Cand001ShadowState(
        pipeline=parse_candidate_state_payload(raw_pipeline, config=cfg),
        active_trade=(
            parse_candidate_active_trade_payload(raw_active)
            if raw_active is not None
            else None
        ),
        publication=parse_candidate_publication_state_payload(raw_publication),
    )
    _validate_state_relationships(state, run_manifest=run_manifest, config=cfg)
    return state


def _validate_state_relationships(
    state: Cand001ShadowState,
    *,
    run_manifest: RunManifest,
    config: Cand001Config,
) -> None:
    active = state.active_trade
    if active is None:
        return
    if active.core_version != config.product_identity().core_version:
        raise ValueError("candidate SHADOW active-trade core-version drift")
    if active.lifecycle.run_manifest_fingerprint != run_manifest.manifest_fingerprint:
        raise ValueError("candidate SHADOW active-trade run-manifest drift")
    if active.origin_decision.config_fingerprint != stable_fingerprint(config):
        raise ValueError("candidate SHADOW active-trade config drift")
    if state.pipeline.admission.trades_admitted < 1:
        raise ValueError("candidate SHADOW active trade requires admitted session trade state")


def _require_shadow_manifest(run_manifest: RunManifest) -> None:
    if run_manifest.mode is not RuntimeMode.SHADOW:
        raise ValueError("candidate SHADOW checkpoint requires SHADOW RunManifest")
    _sha(run_manifest.manifest_fingerprint, "run_manifest_fingerprint")


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value
