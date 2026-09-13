"""Technical MT5 DEMO-evidence transport/lookup boundary with no submission API.

This module derives deterministic local correlation metadata from the canonical
client identity, projects a non-executable transport draft, and performs only
read-only lookup through an injected MetaTrader5-compatible object. It never
imports MetaTrader5 and never submits, changes or cancels an order.

The shortened MT5 tag is local correlation metadata, not broker proof. A real
DEMO host still has to prove that the venue preserves enough metadata for exact
lookup. Zero, ambiguous, incomplete or failed lookup always stays fail-closed and
never permits retry, resubmit or session-slot release.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
from math import isclose, isfinite
from typing import Any, Mapping

from daxlab.runtime.broker_order_lifecycle import BrokerOrderState
from daxlab.runtime.broker_reconciliation import (
    VENUE_ORDER_OBSERVATION_SCHEMA,
    VenueOrderObservation,
)
from daxlab.domain.ports import ClockPort, StateStorePort
from daxlab.runtime.demo_transport_attempt_reservation import (
    DemoTransportAttemptReservation,
    load_reserved_demo_transport_attempt,
    validate_reserved_demo_transport_query,
)
from daxlab.runtime.mt5_demo_account_context import (
    Mt5DemoAccountContextEvidence,
    normalize_mt5_demo_account_context,
    parse_mt5_demo_account_context_payload,
)


MT5_DEMO_TRANSPORT_IDENTITY_SCHEMA = "DAXLAB_MT5_DEMO_TRANSPORT_IDENTITY_V1"
MT5_DEMO_TRANSPORT_DRAFT_SCHEMA = "DAXLAB_MT5_DEMO_TRANSPORT_DRAFT_V1"
MT5_DEMO_LOOKUP_REQUEST_SCHEMA = "DAXLAB_MT5_DEMO_LOOKUP_REQUEST_V1"
MT5_DEMO_LOOKUP_RESULT_SCHEMA = "DAXLAB_MT5_DEMO_LOOKUP_RESULT_V1"
_MAGIC_NAMESPACE = "DAXLAB:MT5:DEMO:MAGIC:V1"
_COMMENT_NAMESPACE = "DAXLAB:MT5:DEMO:COMMENT:V1"
_COMMENT_PREFIX = "DXE1-"
_COMMENT_HEX_CHARS = 20
_MAX_MAGIC = 2_147_483_647


class DemoMt5LookupStatus(StrEnum):
    MATCHED = "MATCHED"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class DemoMt5TransportIdentity:
    schema_version: str
    client_order_id: str
    symbol: str
    magic: int
    comment: str
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != MT5_DEMO_TRANSPORT_IDENTITY_SCHEMA:
            raise ValueError("MT5 DEMO transport identity schema mismatch")
        _sha(self.client_order_id, "client_order_id")
        _nonempty(self.symbol, "symbol")
        if type(self.magic) is not int or not 1 <= self.magic <= _MAX_MAGIC:
            raise ValueError("MT5 DEMO transport magic must be positive signed-31-bit")
        expected_magic, expected_comment = _derive_tag(self.client_order_id)
        if self.magic != expected_magic or self.comment != expected_comment:
            raise ValueError("MT5 DEMO transport identity derivation mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("MT5 DEMO transport identity cannot grant execution")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "magic": self.magic,
            "comment": self.comment,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


@dataclass(frozen=True, slots=True)
class DemoMt5TransportDraft:
    schema_version: str
    identity: DemoMt5TransportIdentity
    reservation_fingerprint: str
    prepared_fingerprint: str
    authorization_fingerprint: str
    account_context_fingerprint: str
    submission_ordinal: int
    side: str
    quantity: float
    requested_price: float
    stop_price: float
    target_price: float
    broker_submission_authorized: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != MT5_DEMO_TRANSPORT_DRAFT_SCHEMA:
            raise ValueError("MT5 DEMO transport draft schema mismatch")
        self.identity.__post_init__()
        for value, field in (
            (self.reservation_fingerprint, "reservation_fingerprint"),
            (self.prepared_fingerprint, "prepared_fingerprint"),
            (self.authorization_fingerprint, "authorization_fingerprint"),
            (self.account_context_fingerprint, "account_context_fingerprint"),
        ):
            _sha(value, field)
        if type(self.submission_ordinal) is not int or self.submission_ordinal < 1:
            raise ValueError("submission_ordinal must be integer >= 1")
        if self.side not in {"BUY", "SELL"}:
            raise ValueError("MT5 DEMO transport draft side must be BUY or SELL")
        if not _positive(self.quantity):
            raise ValueError("MT5 DEMO transport draft quantity must be positive")
        for value, field in (
            (self.requested_price, "requested_price"),
            (self.stop_price, "stop_price"),
            (self.target_price, "target_price"),
        ):
            if not _positive(value):
                raise ValueError(f"MT5 DEMO transport draft {field} must be positive")
        if self.broker_submission_authorized:
            raise ValueError("Step 2200 transport draft cannot authorize submission")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("MT5 DEMO transport draft cannot grant execution")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "identity": self.identity.to_payload(),
            "reservation_fingerprint": self.reservation_fingerprint,
            "prepared_fingerprint": self.prepared_fingerprint,
            "authorization_fingerprint": self.authorization_fingerprint,
            "account_context_fingerprint": self.account_context_fingerprint,
            "submission_ordinal": self.submission_ordinal,
            "side": self.side,
            "quantity": float(self.quantity),
            "requested_price": float(self.requested_price),
            "stop_price": float(self.stop_price),
            "target_price": float(self.target_price),
            "broker_submission_authorized": self.broker_submission_authorized,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


@dataclass(frozen=True, slots=True)
class DemoMt5LookupRequest:
    schema_version: str
    identity: DemoMt5TransportIdentity
    reservation_fingerprint: str
    query_request_fingerprint: str
    account_context: Mt5DemoAccountContextEvidence
    account_context_fingerprint: str
    requested_quantity: float
    history_from: datetime
    history_to: datetime
    query_evaluated_at: datetime
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != MT5_DEMO_LOOKUP_REQUEST_SCHEMA:
            raise ValueError("MT5 DEMO lookup request schema mismatch")
        self.identity.__post_init__()
        self.account_context.__post_init__()
        for value, field in (
            (self.reservation_fingerprint, "reservation_fingerprint"),
            (self.query_request_fingerprint, "query_request_fingerprint"),
            (self.account_context_fingerprint, "account_context_fingerprint"),
        ):
            _sha(value, field)
        if self.account_context.fingerprint != self.account_context_fingerprint:
            raise ValueError("MT5 DEMO lookup account fingerprint mismatch")
        if self.account_context.symbol != self.identity.symbol:
            raise ValueError("MT5 DEMO lookup symbol cross-wiring")
        if not _positive(self.requested_quantity):
            raise ValueError("MT5 DEMO lookup requested quantity must be positive")
        _aware(self.history_from, "history_from")
        _aware(self.history_to, "history_to")
        _aware(self.query_evaluated_at, "query_evaluated_at")
        if self.history_to <= self.history_from:
            raise ValueError("MT5 DEMO lookup history_to must be after history_from")
        if not self.history_from <= self.query_evaluated_at <= self.history_to:
            raise ValueError("MT5 DEMO lookup history window must contain query evaluation")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("MT5 DEMO lookup request cannot grant execution")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "identity": self.identity.to_payload(),
            "reservation_fingerprint": self.reservation_fingerprint,
            "query_request_fingerprint": self.query_request_fingerprint,
            "account_context": self.account_context.to_payload(),
            "account_context_fingerprint": self.account_context_fingerprint,
            "requested_quantity": float(self.requested_quantity),
            "history_from": _iso(self.history_from),
            "history_to": _iso(self.history_to),
            "query_evaluated_at": _iso(self.query_evaluated_at),
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


@dataclass(frozen=True, slots=True)
class DemoMt5LookupResult:
    schema_version: str
    status: DemoMt5LookupStatus
    blockers: tuple[str, ...]
    request_fingerprint: str
    observed_at: datetime
    matching_order_tickets: tuple[str, ...]
    matching_deal_tickets: tuple[str, ...]
    open_order_count: int
    history_order_count: int
    history_deal_count: int
    venue_observation: VenueOrderObservation | None
    resubmit_allowed: bool = False
    session_slot_release_allowed: bool = False
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != MT5_DEMO_LOOKUP_RESULT_SCHEMA:
            raise ValueError("MT5 DEMO lookup result schema mismatch")
        if not isinstance(self.status, DemoMt5LookupStatus):
            raise ValueError("MT5 DEMO lookup status mismatch")
        _sha(self.request_fingerprint, "request_fingerprint")
        _aware(self.observed_at, "observed_at")
        counts = (
            self.open_order_count,
            self.history_order_count,
            self.history_deal_count,
        )
        if any(type(value) is not int or value < 0 for value in counts):
            raise ValueError("MT5 DEMO lookup source counts must be non-negative integers")
        if self.status is DemoMt5LookupStatus.MATCHED:
            if self.blockers or self.venue_observation is None:
                raise ValueError("matched lookup requires one clean venue observation")
            if len(self.matching_order_tickets) != 1:
                raise ValueError("matched lookup requires exactly one order ticket")
        elif not self.blockers or self.venue_observation is not None:
            raise ValueError("non-matched lookup must be blocked without venue truth")
        if self.venue_observation is not None:
            self.venue_observation.__post_init__()
        if self.resubmit_allowed or self.session_slot_release_allowed:
            raise ValueError("MT5 DEMO lookup cannot authorize retry or slot release")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("MT5 DEMO lookup result cannot grant execution")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        observation = None
        if self.venue_observation is not None:
            observation = {
                "schema_version": self.venue_observation.schema_version,
                "observed_at": _iso(self.venue_observation.observed_at),
                "client_order_id": self.venue_observation.client_order_id,
                "venue_order_id": self.venue_observation.venue_order_id,
                "venue_state": self.venue_observation.venue_state,
                "requested_quantity": float(self.venue_observation.requested_quantity),
                "cumulative_filled_quantity": float(
                    self.venue_observation.cumulative_filled_quantity
                ),
                "average_fill_price": self.venue_observation.average_fill_price,
                "execution_capability": self.venue_observation.execution_capability,
                "order_execution_enabled": self.venue_observation.order_execution_enabled,
            }
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "blockers": list(self.blockers),
            "request_fingerprint": self.request_fingerprint,
            "observed_at": _iso(self.observed_at),
            "matching_order_tickets": list(self.matching_order_tickets),
            "matching_deal_tickets": list(self.matching_deal_tickets),
            "open_order_count": self.open_order_count,
            "history_order_count": self.history_order_count,
            "history_deal_count": self.history_deal_count,
            "venue_observation": observation,
            "resubmit_allowed": self.resubmit_allowed,
            "session_slot_release_allowed": self.session_slot_release_allowed,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def derive_demo_mt5_transport_identity(
    *, client_order_id: str, symbol: str
) -> DemoMt5TransportIdentity:
    """Derive stable local MT5 correlation metadata from the full identity."""
    _sha(client_order_id, "client_order_id")
    symbol = _nonempty(symbol, "symbol")
    magic, comment = _derive_tag(client_order_id)
    return DemoMt5TransportIdentity(
        schema_version=MT5_DEMO_TRANSPORT_IDENTITY_SCHEMA,
        client_order_id=client_order_id,
        symbol=symbol,
        magic=magic,
        comment=comment,
    )


def build_demo_mt5_transport_draft(
    reservation: DemoTransportAttemptReservation,
) -> DemoMt5TransportDraft:
    """Project technical metadata without producing an executable MT5 request."""
    reservation.__post_init__()
    intent = reservation.prepared.intent
    identity = derive_demo_mt5_transport_identity(
        client_order_id=intent.intent_id,
        symbol=reservation.account_context.symbol,
    )
    return DemoMt5TransportDraft(
        schema_version=MT5_DEMO_TRANSPORT_DRAFT_SCHEMA,
        identity=identity,
        reservation_fingerprint=reservation.fingerprint,
        prepared_fingerprint=reservation.prepared_fingerprint,
        authorization_fingerprint=reservation.authorization_fingerprint,
        account_context_fingerprint=reservation.account_context_fingerprint,
        submission_ordinal=reservation.submission_ordinal,
        side=intent.side.value,
        quantity=intent.quantity,
        requested_price=intent.requested_price,
        stop_price=intent.stop_price,
        target_price=intent.target_price,
    )


def build_demo_mt5_lookup_request(
    *,
    reservation: DemoTransportAttemptReservation,
    query_request: Mapping[str, Any],
    history_from: datetime,
    history_to: datetime,
) -> DemoMt5LookupRequest:
    """Bind the pinned Step-2198 query projection to an explicit history window."""
    reservation.__post_init__()
    if not isinstance(query_request, Mapping):
        raise ValueError("query_request must be a mapping")
    unsigned = dict(query_request)
    observed_fingerprint = unsigned.pop("query_request_fingerprint", None)
    if not isinstance(observed_fingerprint, str) or observed_fingerprint != _fingerprint(
        unsigned
    ):
        raise ValueError("MT5 DEMO lookup query request fingerprint mismatch")
    if query_request.get("requested_action") != "QUERY_EVIDENCE_ORDER":
        raise ValueError("MT5 DEMO lookup requires QUERY_EVIDENCE_ORDER")
    if query_request.get("execution_capability") != "NONE" or query_request.get(
        "order_execution_enabled"
    ) is not False:
        raise ValueError("MT5 DEMO lookup query request cannot grant execution")
    if query_request.get("resubmit_allowed") is not False or query_request.get(
        "session_slot_release_allowed"
    ) is not False:
        raise ValueError("MT5 DEMO lookup cannot grant retry or slot release")
    checks = (
        ("reservation_fingerprint", reservation.fingerprint),
        ("prepared_fingerprint", reservation.prepared_fingerprint),
        ("authorization_fingerprint", reservation.authorization_fingerprint),
        ("account_context_fingerprint", reservation.account_context_fingerprint),
        ("client_order_id", reservation.prepared.intent.intent_id),
        ("submission_ordinal", reservation.submission_ordinal),
    )
    for field, expected in checks:
        if query_request.get(field) != expected:
            raise ValueError(f"MT5 DEMO lookup {field} cross-wiring")
    account_context = parse_mt5_demo_account_context_payload(
        query_request.get("account_context")
    )
    if account_context != reservation.account_context:
        raise ValueError("MT5 DEMO lookup account payload cross-wiring")
    query_evaluated_at = _timestamp(
        query_request.get("query_evaluated_at"), "query_evaluated_at"
    )
    return DemoMt5LookupRequest(
        schema_version=MT5_DEMO_LOOKUP_REQUEST_SCHEMA,
        identity=derive_demo_mt5_transport_identity(
            client_order_id=reservation.prepared.intent.intent_id,
            symbol=reservation.account_context.symbol,
        ),
        reservation_fingerprint=reservation.fingerprint,
        query_request_fingerprint=observed_fingerprint,
        account_context=account_context,
        account_context_fingerprint=reservation.account_context_fingerprint,
        requested_quantity=reservation.prepared.broker.lifecycle.requested_quantity,
        history_from=history_from,
        history_to=history_to,
        query_evaluated_at=query_evaluated_at,
    )


def validate_reserved_demo_mt5_lookup(
    *,
    store: StateStorePort,
    key: str,
    expected_reservation_fingerprint: str,
    request_payload: Mapping[str, Any],
    bundle_payload: Mapping[str, Any],
    evaluated_at: datetime,
) -> DemoMt5LookupRequest:
    """Bind operational lookup to durable identity and current QUERY scope.

    A history window is not an authorization/freshness window. Reuse the existing
    reservation/query owner immediately before SDK reads. No state is saved or
    reset; original preparation/request evidence and codecs remain unchanged.
    """
    request = demo_mt5_lookup_request_from_payload(request_payload)
    reservation = load_reserved_demo_transport_attempt(
        store=store, key=key,
        expected_reservation_fingerprint=expected_reservation_fingerprint,
    )
    expected_identity = derive_demo_mt5_transport_identity(
        client_order_id=reservation.prepared.intent.intent_id,
        symbol=reservation.account_context.symbol,
    )
    if (
        request.reservation_fingerprint != reservation.fingerprint
        or request.identity != expected_identity
        or request.account_context != reservation.account_context
        or request.requested_quantity != reservation.prepared.broker.lifecycle.requested_quantity
    ):
        raise ValueError("MT5 reserved lookup request cross-wiring")
    _aware(evaluated_at, "evaluated_at")
    if evaluated_at < request.query_evaluated_at or evaluated_at > request.history_to:
        raise ValueError("MT5 reserved lookup outside request history/evaluation window")
    validate_reserved_demo_transport_query(
        reservation=reservation, bundle_payload=bundle_payload, evaluated_at=evaluated_at,
    )
    return request


def query_mt5_demo_evidence(
    *, mt5: Any, request: DemoMt5LookupRequest, observed_at: datetime
) -> DemoMt5LookupResult:
    """Call only read-only MT5 account/order/history/deal query methods."""
    request.__post_init__()
    _aware(observed_at, "observed_at")
    if observed_at < request.query_evaluated_at:
        return _blocked(request, observed_at, "LOOKUP_PRECEDES_QUERY_EVALUATION")

    try:
        account = mt5.account_info()
    except Exception:
        return _blocked(request, observed_at, "MT5_ACCOUNT_INFO_QUERY_FAILED")
    if account is None:
        return _blocked(request, observed_at, "MT5_ACCOUNT_INFO_UNAVAILABLE")
    try:
        current_account = _normalized_account(mt5, account, request.identity.symbol)
    except (TypeError, ValueError):
        return _blocked(request, observed_at, "MT5_ACCOUNT_CONTEXT_INVALID")
    if current_account != request.account_context:
        return _blocked(request, observed_at, "MT5_ACCOUNT_CONTEXT_MISMATCH")

    open_orders = _query(mt5, "orders_get", symbol=request.identity.symbol)
    if open_orders is _QUERY_ERROR:
        return _blocked(request, observed_at, "MT5_OPEN_ORDERS_QUERY_FAILED")
    history_orders = _query(
        mt5,
        "history_orders_get",
        request.history_from,
        request.history_to,
        group=request.identity.symbol,
    )
    if history_orders is _QUERY_ERROR:
        return _blocked(request, observed_at, "MT5_ORDER_HISTORY_QUERY_FAILED")
    history_deals = _query(
        mt5,
        "history_deals_get",
        request.history_from,
        request.history_to,
        group=request.identity.symbol,
    )
    if history_deals is _QUERY_ERROR:
        return _blocked(request, observed_at, "MT5_DEAL_HISTORY_QUERY_FAILED")

    # SDK queries are not a broker transaction. Never label another account's
    # rows with the initially observed DEMO context after a terminal switch.
    after = _query(mt5, "account_info")
    if after is _QUERY_ERROR:
        return _blocked(request, observed_at, "MT5_ACCOUNT_RECHECK_UNAVAILABLE")
    try:
        final_account = _normalized_account(mt5, after, request.identity.symbol)
    except (TypeError, ValueError):
        return _blocked(request, observed_at, "MT5_ACCOUNT_RECHECK_INVALID")
    if final_account != current_account:
        return _blocked(request, observed_at, "MT5_ACCOUNT_CONTEXT_CHANGED_DURING_QUERY")

    open_rows = tuple(open_orders)
    history_rows = tuple(history_orders)
    deal_rows = tuple(history_deals)
    matched: dict[str, Any] = {}
    for row in open_rows + history_rows:
        if not _matches_identity(row, request.identity):
            continue
        ticket = _positive_ticket(row, "ticket")
        if ticket is None:
            return _blocked(
                request,
                observed_at,
                "MT5_MATCHED_ORDER_TICKET_INVALID",
                counts=(len(open_rows), len(history_rows), len(deal_rows)),
            )
        previous = matched.get(ticket)
        if previous is not None and not _same_order_evidence(previous, row):
            return _blocked(
                request,
                observed_at,
                "MT5_DUPLICATE_ORDER_TICKET_CONTRADICTION",
                order_tickets=tuple(sorted(matched | {ticket: row})),
                counts=(len(open_rows), len(history_rows), len(deal_rows)),
            )
        matched[ticket] = row

    tickets = tuple(sorted(matched))
    counts = (len(open_rows), len(history_rows), len(deal_rows))
    if not tickets:
        return DemoMt5LookupResult(
            schema_version=MT5_DEMO_LOOKUP_RESULT_SCHEMA,
            status=DemoMt5LookupStatus.NOT_FOUND,
            blockers=("VENUE_ORDER_NOT_FOUND_ACROSS_OPEN_AND_HISTORY",),
            request_fingerprint=request.fingerprint,
            observed_at=observed_at,
            matching_order_tickets=(),
            matching_deal_tickets=(),
            open_order_count=counts[0],
            history_order_count=counts[1],
            history_deal_count=counts[2],
            venue_observation=None,
        )
    if len(tickets) != 1:
        return DemoMt5LookupResult(
            schema_version=MT5_DEMO_LOOKUP_RESULT_SCHEMA,
            status=DemoMt5LookupStatus.AMBIGUOUS,
            blockers=("VENUE_IDENTITY_TAG_MATCHED_MULTIPLE_ORDERS",),
            request_fingerprint=request.fingerprint,
            observed_at=observed_at,
            matching_order_tickets=tickets,
            matching_deal_tickets=(),
            open_order_count=counts[0],
            history_order_count=counts[1],
            history_deal_count=counts[2],
            venue_observation=None,
        )

    ticket = tickets[0]
    order = matched[ticket]
    requested_quantity = _float_field(order, "volume_initial")
    if requested_quantity is None or not _positive(requested_quantity):
        return _blocked(
            request,
            observed_at,
            "MT5_MATCHED_ORDER_QUANTITY_INVALID",
            order_tickets=tickets,
            counts=counts,
        )
    if not isclose(
        requested_quantity, request.requested_quantity, rel_tol=1e-12, abs_tol=1e-12
    ):
        return _blocked(
            request,
            observed_at,
            "MT5_MATCHED_ORDER_QUANTITY_MISMATCH",
            order_tickets=tickets,
            counts=counts,
        )
    venue_state = _map_state(mt5, _field(order, "state"))
    if venue_state is None:
        return _blocked(
            request,
            observed_at,
            "MT5_ORDER_STATE_UNSUPPORTED",
            order_tickets=tickets,
            counts=counts,
        )

    matched_deals: dict[str, Any] = {}
    for deal in deal_rows:
        if _positive_ticket(deal, "order") != ticket:
            continue
        if not _deal_identity_compatible(deal, request.identity):
            return _blocked(
                request,
                observed_at,
                "MT5_DEAL_IDENTITY_MISMATCH",
                order_tickets=tickets,
                counts=counts,
            )
        deal_ticket = _positive_ticket(deal, "ticket")
        if deal_ticket is None:
            return _blocked(request, observed_at, "MT5_MATCHED_DEAL_TICKET_INVALID",
                            order_tickets=tickets, counts=counts)
        previous = matched_deals.get(deal_ticket)
        if previous is not None and not _same_deal_evidence(previous, deal):
            return _blocked(request, observed_at, "MT5_DUPLICATE_DEAL_TICKET_CONTRADICTION",
                            order_tickets=tickets, deal_tickets=tuple(sorted(matched_deals)), counts=counts)
        matched_deals[deal_ticket] = deal

    cumulative_fill = 0.0
    weighted_price = 0.0
    deal_tickets: list[str] = []
    for deal_ticket in sorted(matched_deals):
        deal = matched_deals[deal_ticket]
        volume = _float_field(deal, "volume")
        price = _float_field(deal, "price")
        if volume is None or volume < 0:
            return _blocked(
                request,
                observed_at,
                "MT5_DEAL_VOLUME_INVALID",
                order_tickets=tickets,
                counts=counts,
            )
        if volume == 0:
            continue
        if price is None or not _positive(price):
            return _blocked(
                request,
                observed_at,
                "MT5_DEAL_PRICE_INVALID",
                order_tickets=tickets,
                counts=counts,
            )
        cumulative_fill += volume
        weighted_price += volume * price
        deal_tickets.append(deal_ticket)
    deal_ids = tuple(sorted(set(deal_tickets)))

    if cumulative_fill > requested_quantity and not isclose(
        cumulative_fill, requested_quantity, rel_tol=1e-12, abs_tol=1e-12
    ):
        return _blocked(
            request,
            observed_at,
            "MT5_DEAL_FILL_EXCEEDS_REQUESTED_QUANTITY",
            order_tickets=tickets,
            deal_tickets=deal_ids,
            counts=counts,
        )
    remaining = _float_field(order, "volume_current")
    if remaining is not None and remaining >= 0:
        implied_fill = requested_quantity - remaining
        if implied_fill < -1e-12 or not isclose(
            implied_fill, cumulative_fill, rel_tol=1e-9, abs_tol=1e-9
        ):
            return _blocked(
                request,
                observed_at,
                "MT5_ORDER_DEAL_FILL_EVIDENCE_MISMATCH",
                order_tickets=tickets,
                deal_tickets=deal_ids,
                counts=counts,
            )
    if venue_state is BrokerOrderState.PARTIAL and not 0 < cumulative_fill < requested_quantity:
        return _blocked(
            request,
            observed_at,
            "MT5_PARTIAL_STATE_WITHOUT_PARTIAL_FILL_EVIDENCE",
            order_tickets=tickets,
            deal_tickets=deal_ids,
            counts=counts,
        )
    if venue_state is BrokerOrderState.FILLED and not isclose(
        cumulative_fill, requested_quantity, rel_tol=1e-9, abs_tol=1e-9
    ):
        return _blocked(
            request,
            observed_at,
            "MT5_FILLED_STATE_WITHOUT_COMPLETE_FILL_EVIDENCE",
            order_tickets=tickets,
            deal_tickets=deal_ids,
            counts=counts,
        )

    observation = VenueOrderObservation(
        schema_version=VENUE_ORDER_OBSERVATION_SCHEMA,
        observed_at=observed_at,
        client_order_id=request.identity.client_order_id,
        venue_order_id=ticket,
        venue_state=venue_state.value,
        requested_quantity=requested_quantity,
        cumulative_filled_quantity=cumulative_fill,
        average_fill_price=(
            None if cumulative_fill == 0 else weighted_price / cumulative_fill
        ),
    )
    return DemoMt5LookupResult(
        schema_version=MT5_DEMO_LOOKUP_RESULT_SCHEMA,
        status=DemoMt5LookupStatus.MATCHED,
        blockers=(),
        request_fingerprint=request.fingerprint,
        observed_at=observed_at,
        matching_order_tickets=tickets,
        matching_deal_tickets=deal_ids,
        open_order_count=counts[0],
        history_order_count=counts[1],
        history_deal_count=counts[2],
        venue_observation=observation,
    )


def demo_mt5_lookup_request_to_payload(request: DemoMt5LookupRequest) -> dict[str, Any]:
    request.__post_init__()
    payload = request.to_payload()
    return payload | {"request_fingerprint": _fingerprint(payload)}


def demo_mt5_lookup_request_from_payload(payload: Mapping[str, Any]) -> DemoMt5LookupRequest:
    if not isinstance(payload, Mapping):
        raise ValueError("MT5 DEMO lookup request payload must be a mapping")
    raw = dict(payload)
    observed = raw.pop("request_fingerprint", None)
    if not isinstance(observed, str) or observed != _fingerprint(raw):
        raise ValueError("MT5 DEMO lookup request payload fingerprint mismatch")
    required = {
        "schema_version",
        "identity",
        "reservation_fingerprint",
        "query_request_fingerprint",
        "account_context",
        "account_context_fingerprint",
        "requested_quantity",
        "history_from",
        "history_to",
        "query_evaluated_at",
        "execution_capability",
        "order_execution_enabled",
    }
    if raw.keys() != required:
        raise ValueError("MT5 DEMO lookup request payload field set mismatch")
    identity_payload = raw["identity"]
    if not isinstance(identity_payload, Mapping):
        raise ValueError("MT5 DEMO transport identity payload must be mapping")
    identity = DemoMt5TransportIdentity(
        schema_version=identity_payload.get("schema_version"),
        client_order_id=identity_payload.get("client_order_id"),
        symbol=identity_payload.get("symbol"),
        magic=identity_payload.get("magic"),
        comment=identity_payload.get("comment"),
        execution_capability=identity_payload.get("execution_capability"),
        order_execution_enabled=identity_payload.get("order_execution_enabled"),
    )
    return DemoMt5LookupRequest(
        schema_version=raw["schema_version"],
        identity=identity,
        reservation_fingerprint=raw["reservation_fingerprint"],
        query_request_fingerprint=raw["query_request_fingerprint"],
        account_context=parse_mt5_demo_account_context_payload(raw["account_context"]),
        account_context_fingerprint=raw["account_context_fingerprint"],
        requested_quantity=raw["requested_quantity"],
        history_from=_timestamp(raw["history_from"], "history_from"),
        history_to=_timestamp(raw["history_to"], "history_to"),
        query_evaluated_at=_timestamp(raw["query_evaluated_at"], "query_evaluated_at"),
        execution_capability=raw["execution_capability"],
        order_execution_enabled=raw["order_execution_enabled"],
    )


_QUERY_ERROR = object()


def _normalized_account(mt5: Any, account: Any, symbol: str) -> Mt5DemoAccountContextEvidence:
    return normalize_mt5_demo_account_context(
        raw_login=getattr(account, "login", None),
        raw_server=getattr(account, "server", None),
        raw_trade_mode=getattr(account, "trade_mode", None),
        trade_allowed=getattr(account, "trade_allowed", None),
        resolved_symbol=symbol,
        demo_trade_mode=getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", None),
        contest_trade_mode=getattr(mt5, "ACCOUNT_TRADE_MODE_CONTEST", None),
        real_trade_mode=getattr(mt5, "ACCOUNT_TRADE_MODE_REAL", None),
    )


def _query(mt5: Any, name: str, *args: Any, **kwargs: Any) -> Any:
    method = getattr(mt5, name, None)
    if not callable(method):
        return _QUERY_ERROR
    try:
        value = method(*args, **kwargs)
    except Exception:
        return _QUERY_ERROR
    return _QUERY_ERROR if value is None else value


def _derive_tag(client_order_id: str) -> tuple[int, str]:
    magic_bytes = sha256(f"{_MAGIC_NAMESPACE}:{client_order_id}".encode()).digest()
    magic = int.from_bytes(magic_bytes[:4], "big") & _MAX_MAGIC
    if magic == 0:
        magic = 1
    comment_hex = sha256(f"{_COMMENT_NAMESPACE}:{client_order_id}".encode()).hexdigest()
    return magic, _COMMENT_PREFIX + comment_hex[:_COMMENT_HEX_CHARS]


def _matches_identity(row: Any, identity: DemoMt5TransportIdentity) -> bool:
    return (
        str(_field(row, "symbol") or "") == identity.symbol
        and _int_field(row, "magic") == identity.magic
        and str(_field(row, "comment") or "") == identity.comment
    )


def _deal_identity_compatible(row: Any, identity: DemoMt5TransportIdentity) -> bool:
    symbol = _field(row, "symbol")
    magic = _field(row, "magic")
    comment = _field(row, "comment")
    if symbol not in (None, "") and str(symbol) != identity.symbol:
        return False
    if magic is not None and _int_field(row, "magic") != identity.magic:
        return False
    if comment not in (None, "") and str(comment) != identity.comment:
        return False
    return True


def _same_deal_evidence(left: Any, right: Any) -> bool:
    # One immutable venue deal per ticket; transport replays never add fills.
    fields = ("ticket", "order", "symbol", "magic", "comment", "volume", "price",
              "time", "time_msc", "type", "entry", "position_id")
    return all(_field(left, field) == _field(right, field) for field in fields)


def _same_order_evidence(left: Any, right: Any) -> bool:
    fields = (
        "ticket",
        "symbol",
        "magic",
        "comment",
        "state",
        "volume_initial",
        "volume_current",
    )
    return all(_field(left, field) == _field(right, field) for field in fields)


def _map_state(mt5: Any, value: Any) -> BrokerOrderState | None:
    mapping = {
        getattr(mt5, "ORDER_STATE_STARTED", object()): BrokerOrderState.REQUESTED,
        getattr(mt5, "ORDER_STATE_REQUEST_ADD", object()): BrokerOrderState.REQUESTED,
        getattr(mt5, "ORDER_STATE_PLACED", object()): BrokerOrderState.ACK,
        getattr(mt5, "ORDER_STATE_PARTIAL", object()): BrokerOrderState.PARTIAL,
        getattr(mt5, "ORDER_STATE_FILLED", object()): BrokerOrderState.FILLED,
        getattr(mt5, "ORDER_STATE_CANCELED", object()): BrokerOrderState.CANCELLED,
        getattr(mt5, "ORDER_STATE_REJECTED", object()): BrokerOrderState.REJECT,
        getattr(mt5, "ORDER_STATE_EXPIRED", object()): BrokerOrderState.EXPIRED,
    }
    return mapping.get(value)


def _blocked(
    request: DemoMt5LookupRequest,
    observed_at: datetime,
    *blockers: str,
    order_tickets: tuple[str, ...] = (),
    deal_tickets: tuple[str, ...] = (),
    counts: tuple[int, int, int] = (0, 0, 0),
) -> DemoMt5LookupResult:
    return DemoMt5LookupResult(
        schema_version=MT5_DEMO_LOOKUP_RESULT_SCHEMA,
        status=DemoMt5LookupStatus.BLOCKED,
        blockers=tuple(blockers),
        request_fingerprint=request.fingerprint,
        observed_at=observed_at,
        matching_order_tickets=order_tickets,
        matching_deal_tickets=deal_tickets,
        open_order_count=counts[0],
        history_order_count=counts[1],
        history_deal_count=counts[2],
        venue_observation=None,
    )


def _field(row: Any, name: str) -> Any:
    if isinstance(row, Mapping):
        return row.get(name)
    return getattr(row, name, None)


def _int_field(row: Any, name: str) -> int | None:
    value = _field(row, name)
    return value if type(value) is int else None


def _float_field(row: Any, name: str) -> float | None:
    value = _field(row, name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if isfinite(result) else None


def _positive_ticket(row: Any, name: str) -> str | None:
    value = _field(row, name)
    if type(value) is not int or value <= 0:
        return None
    return str(value)


def _positive(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(float(value))
        and float(value) > 0
    )


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc
    return value


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")
    return value.strip()


def _aware(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field}") from exc
    return _aware(parsed, field)


def _iso(value: datetime) -> str:
    _aware(value, "datetime")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


OPEN_INVENTORY_SCHEMA = 'DAXLAB_MT5_DEMO_OPEN_INVENTORY_V1'


@dataclass(frozen=True, slots=True)
class DemoMt5OpenInventoryRow:
    kind: str
    ticket: str
    symbol: str
    side: str
    native_volume: float
    observed_open_price: float
    transport_tag_matches_attempt: bool

    def __post_init__(self) -> None:
        if self.kind not in ('ORDER', 'POSITION') or self.side not in ('BUY', 'SELL'):
            raise ValueError('inventory kind/side invalid')
        if not isinstance(self.ticket, str) or not self.ticket.isascii() or not self.ticket.isdecimal() or int(self.ticket) <= 0:
            raise ValueError('inventory ticket invalid')
        _nonempty(self.symbol, 'inventory symbol')
        if not _positive(self.native_volume) or not _positive(self.observed_open_price):
            raise ValueError('inventory native volume/open price must be finite and positive')
        if type(self.transport_tag_matches_attempt) is not bool:
            raise ValueError('inventory tag match must be bool')

    def to_payload(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass(frozen=True, slots=True)
class DemoMt5OpenInventoryObservation:
    request_fingerprint: str
    client_order_id: str
    account_context: Mt5DemoAccountContextEvidence
    collection_started_at: datetime
    collection_completed_at: datetime
    status: str
    blockers: tuple[str, ...]
    rows: tuple[DemoMt5OpenInventoryRow, ...]

    def __post_init__(self) -> None:
        _sha(self.request_fingerprint, 'inventory request fingerprint')
        _sha(self.client_order_id, 'inventory client order id')
        self.account_context.__post_init__()
        if self.account_context.account_mode.value != 'DEMO':
            raise ValueError('inventory requires bound DEMO account')
        _aware(self.collection_started_at, 'collection_started_at')
        _aware(self.collection_completed_at, 'collection_completed_at')
        if self.collection_completed_at < self.collection_started_at:
            raise ValueError('inventory collection clock regressed')
        if not isinstance(self.rows, tuple) or not isinstance(self.blockers, tuple) or any(not isinstance(b, str) or not b for b in self.blockers):
            raise ValueError('inventory rows/blockers must be immutable typed evidence')
        if self.status not in ('OBSERVED', 'BLOCKED'):
            raise ValueError('inventory status invalid')
        for row in self.rows:
            row.__post_init__()
        keys = tuple((r.kind, r.ticket) for r in self.rows)
        if keys != tuple(sorted(set(keys))):
            raise ValueError('inventory rows must have unique ordered identities')
        if self.status == 'BLOCKED' and (not self.blockers or self.rows):
            raise ValueError('blocked inventory cannot imply partial/empty account truth')
        if self.status == 'OBSERVED':
            expected = tuple(f'ACCOUNT_HAS_OPEN_{kind}' for kind in ('ORDERS', 'POSITIONS')
                             if any(r.kind == kind[:-1] for r in self.rows))
            if self.blockers != expected:
                raise ValueError('inventory blocker/row mismatch')

    def to_payload(self) -> dict[str, Any]:
        body = {
            'schema_version': OPEN_INVENTORY_SCHEMA,
            'request_fingerprint': self.request_fingerprint, 'client_order_id': self.client_order_id,
            'account_context': self.account_context.to_payload(),
            'account_context_fingerprint': self.account_context.fingerprint,
            'collection_started_at': _iso(self.collection_started_at),
            'collection_completed_at': _iso(self.collection_completed_at),
            'time_source': 'LOCAL_OBSERVATION_CLOCK_NOT_BROKER_CLOCK',
            'collection_is_atomic': False,
            'scope': 'ACCOUNT_OPEN_ORDERS_AND_POSITIONS_ONLY',
            'status': self.status, 'blockers': list(self.blockers),
            'rows': [r.to_payload() for r in self.rows],
            'open_queries_completed': self.status == 'OBSERVED',
            'broker_reconciliation_complete': False, 'history_completeness': 'UNKNOWN',
            'risk_loss_values': None, 'execution_capability': 'NONE', 'order_execution_enabled': False,
        }
        return body | {'observation_fingerprint': _fingerprint(body)}


def parse_demo_mt5_open_inventory(payload: Mapping[str, Any]) -> DemoMt5OpenInventoryObservation:
    if not isinstance(payload, Mapping):
        raise ValueError('inventory payload must be mapping')
    for name in ('open_queries_completed', 'broker_reconciliation_complete', 'collection_is_atomic', 'order_execution_enabled'):
        if type(payload.get(name)) is not bool:
            raise ValueError('inventory flags must be bool')
    unsigned = dict(payload)
    digest = unsigned.pop('observation_fingerprint', None)
    if digest != _fingerprint(unsigned):
        raise ValueError('inventory fingerprint mismatch')
    try:
        observation = DemoMt5OpenInventoryObservation(
            request_fingerprint=payload['request_fingerprint'], client_order_id=payload['client_order_id'],
            account_context=parse_mt5_demo_account_context_payload(payload['account_context']),
            collection_started_at=_timestamp(payload['collection_started_at'], 'collection_started_at'),
            collection_completed_at=_timestamp(payload['collection_completed_at'], 'collection_completed_at'),
            status=payload['status'], blockers=tuple(payload['blockers']),
            rows=tuple(DemoMt5OpenInventoryRow(**row) for row in payload['rows']),
        )
    except (KeyError, TypeError) as exc:
        raise ValueError('inventory payload fields invalid') from exc
    if observation.to_payload() != dict(payload):
        raise ValueError('inventory contract/provenance mismatch')
    return observation


def query_mt5_demo_open_inventory(
    *, mt5: Any, request: DemoMt5LookupRequest, clock: ClockPort,
) -> DemoMt5OpenInventoryObservation:
    """Observe full-account open objects; never claim ownership or compute PnL.

    Multiple SDK reads are non-atomic. Even an empty successful observation is
    not complete historical/account reconciliation and cannot authorize execution.
    Raw comments/login and margin/profit values never enter this read model.
    """
    request.__post_init__()
    started = _aware(clock.now(), 'inventory clock')

    def finish(reason: str | None, rows: tuple[DemoMt5OpenInventoryRow, ...] = ()):
        completed = _aware(clock.now(), 'inventory clock')
        if completed < started:
            raise ValueError('inventory collection clock regressed')
        if not request.query_evaluated_at <= started <= completed <= request.history_to:
            reason, rows = 'INVENTORY_OUTSIDE_QUERY_WINDOW', ()
        blockers = (reason,) if reason else tuple(
            f'ACCOUNT_HAS_OPEN_{kind}' for kind in ('ORDERS', 'POSITIONS')
            if any(r.kind == kind[:-1] for r in rows)
        )
        return DemoMt5OpenInventoryObservation(
            request.fingerprint, request.identity.client_order_id, request.account_context,
            started, completed, 'BLOCKED' if reason else 'OBSERVED', blockers, rows,
        )

    if request.account_context.account_mode.value != 'DEMO':
        raise ValueError('inventory requires DEMO request')
    if started < request.query_evaluated_at or started > request.history_to:
        return finish('INVENTORY_OUTSIDE_QUERY_WINDOW')
    account = _query(mt5, 'account_info')
    try:
        if account is _QUERY_ERROR or _normalized_account(mt5, account, request.identity.symbol) != request.account_context:
            return finish('INVENTORY_ACCOUNT_CONTEXT_UNAVAILABLE_OR_MISMATCH')
    except (TypeError, ValueError):
        return finish('INVENTORY_ACCOUNT_CONTEXT_INVALID')
    orders = _query(mt5, 'orders_get')
    positions = _query(mt5, 'positions_get')
    after = _query(mt5, 'account_info')
    try:
        if after is _QUERY_ERROR or _normalized_account(mt5, after, request.identity.symbol) != request.account_context:
            return finish('INVENTORY_ACCOUNT_CONTEXT_CHANGED_OR_UNAVAILABLE')
    except (TypeError, ValueError):
        return finish('INVENTORY_ACCOUNT_CONTEXT_INVALID')
    if orders is _QUERY_ERROR or positions is _QUERY_ERROR:
        return finish('INVENTORY_OPEN_QUERY_FAILED')
    parsed: dict[tuple[str, str], DemoMt5OpenInventoryRow] = {}
    try:
        for kind, objects in (('ORDER', orders), ('POSITION', positions)):
            for raw in objects:
                row = DemoMt5OpenInventoryRow(
                    kind=kind, ticket=_positive_ticket(raw, 'ticket'), symbol=_field(raw, 'symbol'),
                    side=_inventory_side(mt5, raw, kind),
                    native_volume=_float_field(raw, 'volume_current' if kind == 'ORDER' else 'volume'),
                    observed_open_price=_float_field(raw, 'price_open'),
                    transport_tag_matches_attempt=_matches_identity(raw, request.identity),
                )
                key = (row.kind, row.ticket)
                if key in parsed and parsed[key] != row:
                    return finish('INVENTORY_DUPLICATE_OBJECT_CONTRADICTION')
                parsed[key] = row
    except (TypeError, ValueError):
        return finish('INVENTORY_OBJECT_INVALID')
    return finish(None, tuple(parsed[key] for key in sorted(parsed)))


def _inventory_side(mt5: Any, row: Any, kind: str) -> str:
    names = ('BUY', 'SELL') if kind == 'POSITION' else (
        'BUY', 'SELL', 'BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP', 'BUY_STOP_LIMIT', 'SELL_STOP_LIMIT',
    )
    prefix = 'POSITION_TYPE_' if kind == 'POSITION' else 'ORDER_TYPE_'
    constants = tuple(getattr(mt5, prefix + name, None) for name in names)
    if any(type(c) is not int for c in constants) or len(set(constants)) != len(constants):
        raise ValueError('inventory side constants invalid')
    value = _int_field(row, 'type')
    if value not in constants:
        raise ValueError('inventory side unsupported')
    return 'BUY' if names[constants.index(value)].startswith('BUY') else 'SELL'
