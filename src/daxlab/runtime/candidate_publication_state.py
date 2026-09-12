"""Restart-safe idempotency state for CAND-001 SHADOW evidence publication.

The deterministic ExecutionIntent ``client_order_id`` and virtual outcome
``outcome_id`` remain the canonical identities. This module only remembers which
identities have already crossed an outer publication boundary so replay/restart
cannot publish the same SHADOW evidence twice.

Persistence is deliberately delegated to the existing ``atomic_json`` helper.
No broker, PAPER or LIVE capability is created here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from daxlab.runtime.candidate_virtual_outcome import Cand001VirtualOutcomeEvidence
from daxlab.runtime.decision import stable_fingerprint
from daxlab.runtime.paper_contracts import ExecutionIntent


SCHEMA_VERSION = "DAX_BOT_CANDIDATE_PUBLICATION_STATE_V1"
_ALLOWED_FIELDS = {
    "schema_version",
    "published_intent_ids",
    "published_outcome_ids",
    "execution_capability",
    "order_execution_enabled",
    "payload_fingerprint",
}


@dataclass(frozen=True, slots=True)
class Cand001PublicationState:
    published_intent_ids: tuple[str, ...] = ()
    published_outcome_ids: tuple[str, ...] = ()
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        _validate_id_tuple(self.published_intent_ids, "published_intent_ids")
        _validate_id_tuple(self.published_outcome_ids, "published_outcome_ids")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("candidate publication state cannot authorize execution")


@dataclass(frozen=True, slots=True)
class PublicationAdmission:
    state: Cand001PublicationState
    accepted: bool
    publication_id: str
    publication_kind: str


def admit_cand001_intent_publication(
    state: Cand001PublicationState,
    intent: ExecutionIntent,
) -> PublicationAdmission:
    """Admit one deterministic intent identity exactly once across restarts."""
    publication_id = _sha256(intent.client_order_id, "client_order_id")
    if publication_id in state.published_intent_ids:
        return PublicationAdmission(
            state=state,
            accepted=False,
            publication_id=publication_id,
            publication_kind="INTENT",
        )
    return PublicationAdmission(
        state=Cand001PublicationState(
            published_intent_ids=_insert_id(state.published_intent_ids, publication_id),
            published_outcome_ids=state.published_outcome_ids,
        ),
        accepted=True,
        publication_id=publication_id,
        publication_kind="INTENT",
    )


def admit_cand001_outcome_publication(
    state: Cand001PublicationState,
    outcome: Cand001VirtualOutcomeEvidence,
) -> PublicationAdmission:
    """Admit one deterministic outcome identity exactly once across restarts."""
    if outcome.execution_capability != "NONE" or outcome.order_execution_enabled:
        raise ValueError("candidate outcome cannot authorize execution")
    publication_id = _sha256(outcome.outcome_id, "outcome_id")
    if publication_id in state.published_outcome_ids:
        return PublicationAdmission(
            state=state,
            accepted=False,
            publication_id=publication_id,
            publication_kind="OUTCOME",
        )
    return PublicationAdmission(
        state=Cand001PublicationState(
            published_intent_ids=state.published_intent_ids,
            published_outcome_ids=_insert_id(state.published_outcome_ids, publication_id),
        ),
        accepted=True,
        publication_id=publication_id,
        publication_kind="OUTCOME",
    )


def candidate_publication_state_payload(
    state: Cand001PublicationState,
) -> dict[str, Any]:
    """Return a JSON-safe tamper-evident publication journal envelope."""
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "published_intent_ids": list(state.published_intent_ids),
        "published_outcome_ids": list(state.published_outcome_ids),
        "execution_capability": state.execution_capability,
        "order_execution_enabled": state.order_execution_enabled,
    }
    payload["payload_fingerprint"] = stable_fingerprint(payload)
    return payload


def parse_candidate_publication_state_payload(
    payload: Mapping[str, Any],
) -> Cand001PublicationState:
    """Fail closed on schema, tamper, shape or execution-safety drift."""
    unknown = payload.keys() - _ALLOWED_FIELDS
    missing = _ALLOWED_FIELDS - payload.keys()
    if unknown:
        raise ValueError(f"unknown candidate publication-state fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing candidate publication-state fields: {sorted(missing)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("candidate publication-state schema mismatch")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("candidate publication-state execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("candidate publication-state cannot enable order execution")

    observed = payload.get("payload_fingerprint")
    if not isinstance(observed, str) or len(observed) != 64:
        raise ValueError("candidate publication-state payload fingerprint invalid")
    try:
        int(observed, 16)
    except ValueError as exc:
        raise ValueError("candidate publication-state payload fingerprint invalid") from exc
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    if stable_fingerprint(unhashed) != observed:
        raise ValueError("candidate publication-state payload fingerprint mismatch")

    intent_ids = _parse_id_list(payload.get("published_intent_ids"), "published_intent_ids")
    outcome_ids = _parse_id_list(payload.get("published_outcome_ids"), "published_outcome_ids")
    return Cand001PublicationState(
        published_intent_ids=intent_ids,
        published_outcome_ids=outcome_ids,
    )


def _insert_id(values: tuple[str, ...], value: str) -> tuple[str, ...]:
    return tuple(sorted((*values, value)))


def _parse_id_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field} must contain strings")
    parsed = tuple(value)
    _validate_id_tuple(parsed, field)
    return parsed


def _validate_id_tuple(values: tuple[str, ...], field: str) -> None:
    if values != tuple(sorted(values)):
        raise ValueError(f"{field} must be sorted")
    if len(set(values)) != len(values):
        raise ValueError(f"{field} must be unique")
    for value in values:
        _sha256(value, field)


def _sha256(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value
