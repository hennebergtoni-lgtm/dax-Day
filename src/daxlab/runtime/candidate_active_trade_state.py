"""Restart-safe evidence bundle for one active CAND-001 SHADOW trade.

The virtual lifecycle already persists price-path state. A later costed outcome
also needs the originating TRADE DecisionRecord, including its deterministic
identity inputs. This module binds those two existing owners without creating a
second recovery or execution architecture.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from daxlab.runtime.candidate_state import (
    candidate_virtual_lifecycle_payload,
    parse_candidate_virtual_lifecycle_payload,
)
from daxlab.runtime.candidate_virtual_lifecycle import Cand001VirtualLifecycleState
from daxlab.runtime.decision import (
    DecisionRecord,
    FinalAction,
    deterministic_decision_id,
    stable_fingerprint,
)


SCHEMA_VERSION = "DAX_BOT_CANDIDATE_ACTIVE_TRADE_V1"
_ALLOWED_FIELDS = {
    "schema_version",
    "core_version",
    "origin_decision",
    "virtual_lifecycle",
    "execution_capability",
    "order_execution_enabled",
    "payload_fingerprint",
}
_DECISION_FIELDS = {
    "event_time",
    "data_fingerprint",
    "regime",
    "structure",
    "setup",
    "filter_results",
    "blockers",
    "risk_result",
    "final_action",
    "config_fingerprint",
    "decision_id",
}


@dataclass(frozen=True, slots=True)
class Cand001ActiveTradeState:
    core_version: str
    origin_decision: DecisionRecord
    lifecycle: Cand001VirtualLifecycleState
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.core_version.strip():
            raise ValueError("active trade core_version must be non-empty")
        if self.origin_decision.event_time.tzinfo is None:
            raise ValueError("active trade decision time must be timezone-aware")
        if self.origin_decision.final_action is not FinalAction.TRADE:
            raise ValueError("active trade requires originating TRADE decision")
        if self.lifecycle.decision_id != self.origin_decision.decision_id:
            raise ValueError("active trade lifecycle decision identity drift")
        if self.lifecycle.requested_at != self.origin_decision.event_time:
            raise ValueError("active trade lifecycle request time drift")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("active trade state cannot authorize execution")
        _verify_decision_identity(self.origin_decision, self.core_version)


def candidate_active_trade_payload(state: Cand001ActiveTradeState) -> dict[str, Any]:
    """Return a JSON-safe tamper-evident active-trade persistence envelope."""
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "core_version": state.core_version,
        "origin_decision": _decision_payload(state.origin_decision),
        "virtual_lifecycle": candidate_virtual_lifecycle_payload(state.lifecycle),
        "execution_capability": state.execution_capability,
        "order_execution_enabled": state.order_execution_enabled,
    }
    payload["payload_fingerprint"] = stable_fingerprint(payload)
    return payload


def parse_candidate_active_trade_payload(
    payload: Mapping[str, Any],
) -> Cand001ActiveTradeState:
    """Fail closed on shape, identity, tamper or execution-safety drift."""
    unknown = payload.keys() - _ALLOWED_FIELDS
    missing = _ALLOWED_FIELDS - payload.keys()
    if unknown:
        raise ValueError(f"unknown active-trade fields: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing active-trade fields: {sorted(missing)}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("active-trade schema mismatch")
    if payload.get("execution_capability") != "NONE":
        raise ValueError("active-trade execution capability invalid")
    if payload.get("order_execution_enabled") is not False:
        raise ValueError("active-trade state cannot enable order execution")

    observed = payload.get("payload_fingerprint")
    _sha(observed, "payload_fingerprint")
    unhashed = dict(payload)
    unhashed.pop("payload_fingerprint", None)
    if stable_fingerprint(unhashed) != observed:
        raise ValueError("active-trade payload fingerprint mismatch")

    core_version = payload.get("core_version")
    if not isinstance(core_version, str) or not core_version.strip():
        raise ValueError("active-trade core_version invalid")
    raw_decision = payload.get("origin_decision")
    raw_lifecycle = payload.get("virtual_lifecycle")
    if not isinstance(raw_decision, Mapping):
        raise ValueError("active-trade origin_decision missing")
    if not isinstance(raw_lifecycle, Mapping):
        raise ValueError("active-trade virtual_lifecycle missing")

    decision = _parse_decision(raw_decision, core_version=core_version)
    lifecycle = parse_candidate_virtual_lifecycle_payload(raw_lifecycle)
    return Cand001ActiveTradeState(
        core_version=core_version,
        origin_decision=decision,
        lifecycle=lifecycle,
    )


def _decision_payload(decision: DecisionRecord) -> dict[str, Any]:
    return {
        "event_time": decision.event_time.isoformat(),
        "data_fingerprint": decision.data_fingerprint,
        "regime": decision.regime,
        "structure": decision.structure,
        "setup": decision.setup,
        "filter_results": dict(decision.filter_results),
        "blockers": list(decision.blockers),
        "risk_result": decision.risk_result,
        "final_action": decision.final_action.value,
        "config_fingerprint": decision.config_fingerprint,
        "decision_id": decision.decision_id,
    }


def _parse_decision(raw: Mapping[str, Any], *, core_version: str) -> DecisionRecord:
    if set(raw) != _DECISION_FIELDS:
        raise ValueError("active-trade origin decision shape invalid")
    event_time = _datetime(raw.get("event_time"), "origin_decision.event_time")
    data_fingerprint = _sha(raw.get("data_fingerprint"), "data_fingerprint")
    config_fingerprint = _sha(raw.get("config_fingerprint"), "config_fingerprint")
    decision_id = _sha(raw.get("decision_id"), "decision_id")

    filter_results = raw.get("filter_results")
    if not isinstance(filter_results, Mapping) or not all(
        isinstance(key, str) and type(value) is bool
        for key, value in filter_results.items()
    ):
        raise ValueError("active-trade filter_results invalid")
    blockers = raw.get("blockers")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        raise ValueError("active-trade blockers invalid")

    try:
        final_action = FinalAction(str(raw.get("final_action")))
    except ValueError as exc:
        raise ValueError("active-trade final_action invalid") from exc

    decision = DecisionRecord(
        event_time=event_time,
        data_fingerprint=data_fingerprint,
        regime=_text(raw.get("regime"), "regime"),
        structure=_text(raw.get("structure"), "structure"),
        setup=_text(raw.get("setup"), "setup"),
        filter_results=dict(filter_results),
        blockers=tuple(blockers),
        risk_result=_text(raw.get("risk_result"), "risk_result"),
        final_action=final_action,
        config_fingerprint=config_fingerprint,
        decision_id=decision_id,
    )
    _verify_decision_identity(decision, core_version)
    return decision


def _verify_decision_identity(decision: DecisionRecord, core_version: str) -> None:
    expected = deterministic_decision_id(
        event_time=decision.event_time,
        data_fingerprint=decision.data_fingerprint,
        config_fingerprint=decision.config_fingerprint,
        core_version=core_version,
    )
    if decision.decision_id != expected:
        raise ValueError("active-trade origin decision deterministic identity drift")


def _datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be ISO-8601 string")
    try:
        result = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} invalid") from exc
    if result.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return result


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"active-trade {field} invalid")
    return value


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value
