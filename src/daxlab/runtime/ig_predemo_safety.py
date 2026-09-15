"""IG-specific bindings for the canonical pre-DEMO safety owners.

This module is deliberately an adapter, not a second risk, session, lifecycle or
reconciliation engine.  It validates credential-free Step2238 evidence and
projects provider-specific blockers into the existing owners.  It contains no
HTTP client and can never authorize or submit an order.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping

from daxlab.domain.market import InstrumentId
from daxlab.domain.risk import InstrumentRiskInputs


IG_PREDEMO_SAFETY_SCHEMA = "DAXLAB_IG_PREDEMO_SAFETY_V1"


class GateStatus(StrEnum):
    VERIFIED = "VERIFIED"
    IMPLEMENTED = "IMPLEMENTED"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    BLOCKED = "BLOCKED"


class IgTransportObservation(StrEnum):
    PREPARED = "PREPARED"
    RESERVED = "RESERVED"
    REQUEST_SENT = "REQUEST_SENT"
    ACK = "ACK"
    REJECT = "REJECT"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"
    DUPLICATE = "DUPLICATE"
    OUT_OF_ORDER = "OUT_OF_ORDER"


@dataclass(frozen=True, slots=True)
class IgRiskSessionBinding:
    source_fingerprint: str
    instrument: InstrumentRiskInputs | None
    account_context_fingerprint: str | None
    inventory_fingerprint: str | None
    blockers: tuple[str, ...]
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        _sha(self.source_fingerprint, "source_fingerprint")
        for value, name in (
            (self.account_context_fingerprint, "account_context_fingerprint"),
            (self.inventory_fingerprint, "inventory_fingerprint"),
        ):
            if value is not None:
                _sha(value, name)
        if self.instrument is None and not self.blockers:
            raise ValueError("missing IG risk binding requires blockers")
        if self.execution_capability != "NONE" or self.order_execution_enabled is not False:
            raise ValueError("IG risk/session binding cannot authorize execution")

    @property
    def admission_inputs_complete(self) -> bool:
        return self.instrument is not None and not self.blockers


@dataclass(frozen=True, slots=True)
class IgLifecycleDirective:
    observation: IgTransportObservation
    next_action: str
    terminal_truth: bool
    resubmit_allowed: bool = False
    session_slot_release_allowed: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_capability != "NONE" or self.order_execution_enabled is not False:
            raise ValueError("IG lifecycle directive cannot authorize execution")
        if self.resubmit_allowed or self.session_slot_release_allowed:
            raise ValueError("IG lifecycle adapter cannot release or resubmit")


def bind_ig_risk_session_inputs(
    evidence: Mapping[str, Any], *, instrument_id: InstrumentId
) -> IgRiskSessionBinding:
    """Bind only externally verified IG values into canonical Risk V1 inputs.

    No default quantity step, maximum size, pip value or currency is inferred.
    A stable pair of empty inventory reads is required, but is still bound to the
    explicit read interval and history scope; an isolated negative read is never
    promoted to flatness proof.
    """
    _require_evidence_envelope(evidence)
    blockers = _v3_binding_blockers(evidence, instrument_id=instrument_id)
    market = _mapping(evidence.get("market"), "market")
    account = _mapping(evidence.get("account"), "account")
    inventory = _mapping(evidence.get("inventory"), "inventory")

    currency = account.get("currency")
    if not isinstance(currency, str) or not currency:
        blockers.append("ACCOUNT_CURRENCY_UNVERIFIED")
    account_fp = account.get("account_context_fingerprint")
    if not _is_sha(account_fp):
        account_fp = None
        blockers.append("ACCOUNT_CONTEXT_UNVERIFIED")

    inventory_fp = inventory.get("stable_inventory_fingerprint")
    if not _is_sha(inventory_fp):
        inventory_fp = None
        blockers.append("CURRENT_INVENTORY_SCOPE_UNVERIFIED")
    if inventory.get("stable_across_bracket") is not True:
        blockers.append("CURRENT_INVENTORY_CHANGED_DURING_READ")
    if inventory.get("foreign_or_manual_inventory_present") is not False:
        blockers.append("FOREIGN_OR_MANUAL_INVENTORY_NOT_CLEARED")
    history_complete = (
        _mapping(evidence.get("history_scope"), "history_scope").get("scope_complete")
        if evidence.get("schema") == "DAXLAB_IG_PREDEMO_READINESS_V3"
        else inventory.get("history_scope_complete")
    )
    if history_complete is not True:
        blockers.append("HISTORY_SCOPE_INCOMPLETE")

    numeric: dict[str, float] = {}
    for key, blocker in (
        ("quantity_min", "MIN_SIZE_UNVERIFIED"),
        ("quantity_step", "QUANTITY_INCREMENT_UNVERIFIED"),
        ("quantity_max", "MAX_SIZE_UNVERIFIED"),
        ("tick_size", "TICK_SIZE_UNVERIFIED"),
        ("cash_per_tick_per_quantity", "TICK_VALUE_UNVERIFIED"),
    ):
        value = market.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            blockers.append(blocker)
        elif not isfinite(float(value)) or float(value) <= 0:
            blockers.append(blocker)
        else:
            numeric[key] = float(value)

    if market.get("economics_verified") is not True:
        blockers.append("BROKER_ECONOMICS_UNVERIFIED")
    if market.get("native_stop_constraints_verified") is not True:
        blockers.append("STOP_CONSTRAINTS_UNVERIFIED")

    unique = tuple(dict.fromkeys(blockers))
    instrument = None
    if not unique:
        instrument = InstrumentRiskInputs(
            instrument_id=instrument_id,
            quantity_min=numeric["quantity_min"],
            quantity_step=numeric["quantity_step"],
            quantity_max=numeric["quantity_max"],
            cash_loss_per_price_unit_per_quantity=(
                numeric["cash_per_tick_per_quantity"] / numeric["tick_size"]
            ),
            currency=currency,
        )
    return IgRiskSessionBinding(
        source_fingerprint=evidence["fingerprint"],
        instrument=instrument,
        account_context_fingerprint=account_fp,
        inventory_fingerprint=inventory_fp,
        blockers=unique,
    )


def ig_lifecycle_directive(
    observation: IgTransportObservation,
    *, reservation_present: bool,
    broker_query_scope_complete: bool,
) -> IgLifecycleDirective:
    """Map IG transport observations to the existing lifecycle/recon workflow."""
    if type(reservation_present) is not bool or type(broker_query_scope_complete) is not bool:
        raise ValueError("IG lifecycle evidence flags must be boolean")
    if observation is IgTransportObservation.PREPARED:
        action, terminal = "RESERVE_ATTEMPT_BEFORE_TRANSPORT", False
    elif not reservation_present:
        action, terminal = "BLOCK_MISSING_ATTEMPT_RESERVATION", False
    elif observation in {IgTransportObservation.TIMEOUT, IgTransportObservation.UNKNOWN}:
        action, terminal = "QUERY_REQUIRED", False
    elif observation in {
        IgTransportObservation.DUPLICATE,
        IgTransportObservation.OUT_OF_ORDER,
        IgTransportObservation.PARTIAL,
    }:
        action, terminal = "RECONCILE_REQUIRED", False
    elif observation is IgTransportObservation.REQUEST_SENT:
        action, terminal = "QUERY_REQUIRED", False
    elif observation in {IgTransportObservation.ACK, IgTransportObservation.RESERVED}:
        action, terminal = "WAIT_OR_QUERY", False
    elif observation in {IgTransportObservation.REJECT, IgTransportObservation.FILLED}:
        if broker_query_scope_complete:
            action, terminal = "RECONCILE_TERMINAL_EVIDENCE", True
        else:
            action, terminal = "QUERY_REQUIRED", False
    else:  # defensive against future enum extension
        action, terminal = "QUERY_REQUIRED", False
    return IgLifecycleDirective(
        observation=observation,
        next_action=action,
        terminal_truth=terminal,
    )


def _v3_binding_blockers(
    evidence: Mapping[str, Any], *, instrument_id: InstrumentId
) -> list[str]:
    """Project V3 findings; never relabel its schema, content or source hash."""
    if evidence.get("schema") != "DAXLAB_IG_PREDEMO_READINESS_V3":
        return []
    if evidence.get("instrument_id") != instrument_id.value:
        raise ValueError("IG pre-DEMO instrument binding mismatch")
    matrix = _mapping(evidence.get("authenticated_read_matrix"), "read matrix")
    resources = (
        "ACCOUNTS", "POSITIONS_A", "WORKING_ORDERS_A", "MARKET_V4",
        "ACTIVITY_HISTORY", "M5_PRICES", "POSITIONS_B", "WORKING_ORDERS_B",
    )
    rows = matrix.get("resources")
    if not isinstance(rows, list) or len(rows) != 8 or tuple(
        row.get("resource") if isinstance(row, Mapping) else None for row in rows
    ) != resources:
        raise ValueError("IG pre-DEMO V3 read matrix contract mismatch")
    endpoints = (
        "ACCOUNTS_V1", "POSITIONS_V2", "WORKING_ORDERS_V2", "MARKET_V4",
        "ACTIVITY_HISTORY_V3", "PRICES_V3", "POSITIONS_V2", "WORKING_ORDERS_V2",
    )
    if tuple(row.get("endpoint_family") for row in rows) != endpoints:
        raise ValueError("IG pre-DEMO V3 endpoint contract mismatch")
    if any(row.get("status") not in ("PASS", "FAIL", "BLOCKED", "UNKNOWN") for row in rows):
        raise ValueError("IG pre-DEMO V3 row status invalid")
    blockers = [
        f"IG_READ_{resource}_UNVERIFIED" for resource, row in zip(resources, rows)
        if row.get("status") != "PASS"
    ]
    if matrix.get("status") != "PASS" or matrix.get("row_count") != 8:
        blockers.append("IG_READ_MATRIX_INCOMPLETE")
    derived = _mapping(evidence.get("derived_processing"), "derived processing")
    required_stages = (
        "MATRIX_CONSTRUCTION", "LOGIN_CONTEXT", "INVENTORY", "HISTORY",
        "MARKET_ECONOMICS", "M5", "CLOCK", "DEPENDENT_CONCLUSIONS",
        "EVIDENCE_ENRICHMENT", "COMPONENT_CONSTRUCTION",
    )
    if evidence.get("derived_processing_complete") is not True or any(
        not isinstance(derived.get(stage), Mapping) or derived[stage].get("status") != "PASS"
        for stage in required_stages
    ):
        blockers.append("IG_READ_DERIVATION_INCOMPLETE")
    if evidence.get("single_authenticated_session") is not True:
        blockers.append("IG_SESSION_CONTEXT_UNVERIFIED")
    account = _mapping(evidence.get("account"), "account")
    if account.get("environment") != "IG_DEMO":
        blockers.append("IG_ACCOUNT_ENVIRONMENT_UNVERIFIED")
    return blockers


def _require_evidence_envelope(evidence: Mapping[str, Any]) -> None:
    if evidence.get("schema") not in {
        "DAXLAB_IG_PREDEMO_READINESS_V1", "DAXLAB_IG_PREDEMO_READINESS_V3"
    }:
        raise ValueError("IG pre-DEMO evidence schema mismatch")
    if evidence.get("environment") != "IG_DEMO":
        raise ValueError("IG pre-DEMO evidence environment mismatch")
    if evidence.get("execution_capability") != "NONE":
        raise ValueError("IG pre-DEMO evidence execution capability invalid")
    if evidence.get("order_execution_enabled") is not False:
        raise ValueError("IG pre-DEMO evidence cannot enable execution")
    fingerprint = evidence.get("fingerprint")
    _sha(fingerprint, "fingerprint")
    unhashed = dict(evidence)
    unhashed.pop("fingerprint", None)
    if _fingerprint(unhashed) != fingerprint:
        raise ValueError("IG pre-DEMO evidence fingerprint mismatch")


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"IG pre-DEMO evidence requires {name}")
    return value


def _is_sha(value: object) -> bool:
    try:
        _sha(value, "value")
    except ValueError:
        return False
    return True


def _sha(value: object, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc


def _fingerprint(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )
    return sha256(canonical.encode()).hexdigest()
