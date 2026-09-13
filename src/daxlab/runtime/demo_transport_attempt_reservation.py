"""Restart-safe local reservation before any future DEMO evidence venue call.

The reservation advances the existing attempt key from PREPARED to
TRANSPORT_ATTEMPT_RESERVED. It grants no execution capability and contains no
venue adapter or order API. Callers must serialize access to the same StateStorePort
key because the port provides atomic replacement, not compare-and-swap.

A restored reservation means reconcile/query first. It must never be interpreted as
permission to blindly resubmit an order.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Mapping

from daxlab.domain.ports import StateStorePort
from daxlab.runtime.broker_reconciliation import (
    BrokerReconciliationVerdict,
    VenueOrderObservation,
    reconcile_broker_order,
)
from daxlab.runtime.demo_evidence_authorization import (
    DemoEvidenceAction,
    DemoEvidenceAuthorization,
    DemoEvidenceAuthorizationStatus,
    DemoEvidenceAuthorizationVerdict,
    evaluate_demo_evidence_authorization,
)
from daxlab.runtime.mt5_demo_account_context import (
    Mt5DemoAccountContextEvidence,
    parse_mt5_demo_account_context_payload,
)
from daxlab.runtime.mt5_windows_bundle import WindowsMt5Bundle, parse_windows_mt5_bundle
from daxlab.runtime.nextgen_prepared_checkpoint import (
    NextgenPreparedCheckpoint,
    nextgen_prepared_checkpoint_from_bytes,
    nextgen_prepared_checkpoint_to_bytes,
)

SCHEMA = "DAXLAB_DEMO_TRANSPORT_ATTEMPT_RESERVATION_V1"
STATUS = "TRANSPORT_ATTEMPT_RESERVED"


@dataclass(frozen=True, slots=True)
class DemoTransportAttemptReservation:
    prepared: NextgenPreparedCheckpoint
    prepared_fingerprint: str
    authorization: DemoEvidenceAuthorization
    authorization_verdict: DemoEvidenceAuthorizationVerdict
    authorization_fingerprint: str
    account_context: Mt5DemoAccountContextEvidence
    account_context_fingerprint: str
    bundle_fingerprint: str
    host_observed_at: datetime
    feed_observed_at: datetime
    feed_latest_closed_fingerprint: str
    evaluated_at: datetime
    max_host_age_seconds: float
    submission_ordinal: int
    status: str = STATUS
    schema_version: str = SCHEMA
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA or self.status != STATUS:
            raise ValueError("demo transport reservation schema/status mismatch")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("demo transport reservation cannot grant execution")

        # Existing owners remain authoritative and validate their own nested evidence.
        self.prepared.__post_init__()
        self.authorization.__post_init__()
        self.account_context.__post_init__()
        if self.prepared_fingerprint != self.prepared.fingerprint:
            raise ValueError("demo transport reservation PREPARED fingerprint mismatch")
        if self.authorization_fingerprint != self.authorization.fingerprint:
            raise ValueError("demo transport reservation authorization fingerprint mismatch")
        if self.account_context_fingerprint != self.account_context.fingerprint:
            raise ValueError("demo transport reservation account-context fingerprint mismatch")
        for value, field in (
            (self.prepared_fingerprint, "prepared_fingerprint"),
            (self.authorization_fingerprint, "authorization_fingerprint"),
            (self.account_context_fingerprint, "account_context_fingerprint"),
            (self.bundle_fingerprint, "bundle_fingerprint"),
            (self.feed_latest_closed_fingerprint, "feed_latest_closed_fingerprint"),
        ):
            _sha(value, field)

        _aware(self.host_observed_at, "host_observed_at")
        _aware(self.feed_observed_at, "feed_observed_at")
        _aware(self.evaluated_at, "evaluated_at")
        if self.feed_observed_at != self.host_observed_at:
            raise ValueError("demo transport reservation host/feed observation mismatch")
        if self.evaluated_at < self.host_observed_at:
            raise ValueError("demo transport reservation cannot use future host evidence")
        if (
            not isinstance(self.max_host_age_seconds, (int, float))
            or isinstance(self.max_host_age_seconds, bool)
            or not isfinite(float(self.max_host_age_seconds))
            or self.max_host_age_seconds < 0
        ):
            raise ValueError("max_host_age_seconds must be finite and non-negative")
        host_age_seconds = (self.evaluated_at - self.host_observed_at).total_seconds()
        if host_age_seconds > self.max_host_age_seconds:
            raise ValueError("demo transport reservation host evidence is stale")
        if type(self.submission_ordinal) is not int or self.submission_ordinal < 1:
            raise ValueError("submission_ordinal must be an integer >= 1")

        if (
            self.authorization_verdict.status
            is not DemoEvidenceAuthorizationStatus.SCOPE_VALID
            or self.authorization_verdict.blockers
            or self.authorization_verdict.requested_action
            is not DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER
        ):
            raise ValueError("demo transport reservation requires scope-valid SUBMIT evidence")
        if (
            self.authorization_verdict.authorization_fingerprint
            != self.authorization.fingerprint
        ):
            raise ValueError("demo transport reservation authorization verdict mismatch")
        if (
            self.authorization_verdict.execution_capability != "NONE"
            or self.authorization_verdict.order_execution_enabled
        ):
            raise ValueError("demo transport reservation verdict cannot grant execution")

        expected_verdict = evaluate_demo_evidence_authorization(
            authorization=self.authorization,
            observed=self.account_context.to_observed_context(),
            requested_action=DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,
            evaluated_at=self.evaluated_at,
            submissions_already_attempted=self.submission_ordinal - 1,
        )
        if expected_verdict != self.authorization_verdict:
            raise ValueError("demo transport reservation authorization evidence mismatch")

    @property
    def fingerprint(self) -> str:
        return _fingerprint(_payload(self))


def build_demo_transport_attempt_reservation(
    *,
    prepared: NextgenPreparedCheckpoint,
    authorization: DemoEvidenceAuthorization,
    bundle: WindowsMt5Bundle,
    evaluated_at: datetime,
    max_host_age_seconds: float,
    submission_ordinal: int,
) -> DemoTransportAttemptReservation:
    """Compose already-validated evidence only; perform no I/O and no venue action."""
    account_context = _validated_demo_bundle_context(bundle)

    verdict = evaluate_demo_evidence_authorization(
        authorization=authorization,
        observed=account_context.to_observed_context(),
        requested_action=DemoEvidenceAction.SUBMIT_EVIDENCE_ORDER,
        evaluated_at=evaluated_at,
        submissions_already_attempted=submission_ordinal - 1,
    )
    if not verdict.scope_valid:
        raise ValueError(
            "demo transport reservation authorization blocked: "
            + ",".join(verdict.blockers)
        )

    return DemoTransportAttemptReservation(
        prepared=prepared,
        prepared_fingerprint=prepared.fingerprint,
        authorization=authorization,
        authorization_verdict=verdict,
        authorization_fingerprint=authorization.fingerprint,
        account_context=account_context,
        account_context_fingerprint=account_context.fingerprint,
        bundle_fingerprint=bundle.fingerprint,
        host_observed_at=bundle.host.observed_at,
        feed_observed_at=bundle.feed.observed_at,
        feed_latest_closed_fingerprint=bundle.feed.latest_closed_fingerprint,
        evaluated_at=evaluated_at,
        max_host_age_seconds=float(max_host_age_seconds),
        submission_ordinal=submission_ordinal,
    )


def _validated_demo_bundle_context(
    bundle: WindowsMt5Bundle,
) -> Mt5DemoAccountContextEvidence:
    """Share the existing reservation host/account vetoes with read-only query."""
    if not bundle.green:
        raise ValueError("demo transport reservation requires GREEN Windows MT5 bundle")
    if bundle.demo_account_context is None:
        raise ValueError("demo transport reservation requires DEMO account context")
    if bundle.feed is None:
        raise ValueError("demo transport reservation requires CLOSED-M5 feed evidence")
    if bundle.feed.observed_at != bundle.host.observed_at:
        raise ValueError("demo transport reservation requires one host/feed observation cycle")
    if bundle.demo_account_context.trade_allowed != bundle.host.account_trade_allowed:
        raise ValueError("demo transport reservation account trade-allowed mismatch")
    if bundle.demo_account_context.symbol not in {
        symbol.name for symbol in bundle.host.symbols
    }:
        raise ValueError("demo transport reservation account symbol is not in host bundle")

    return bundle.demo_account_context


def reserve_demo_transport_attempt(
    *,
    store: StateStorePort,
    key: str,
    prepared: NextgenPreparedCheckpoint,
    authorization: DemoEvidenceAuthorization,
    bundle: WindowsMt5Bundle,
    evaluated_at: datetime,
    max_host_age_seconds: float,
    submission_ordinal: int,
) -> DemoTransportAttemptReservation:
    """Advance one existing PREPARED attempt key exactly once, before transport."""
    existing = store.load(key)
    if existing is None:
        raise ValueError("demo transport reservation requires existing PREPARED state")

    schema = _schema(existing)
    if schema == SCHEMA:
        reservation = demo_transport_attempt_reservation_from_bytes(existing)
        candidate = build_demo_transport_attempt_reservation(
            prepared=prepared,
            authorization=authorization,
            bundle=bundle,
            evaluated_at=evaluated_at,
            max_host_age_seconds=max_host_age_seconds,
            submission_ordinal=submission_ordinal,
        )
        if reservation != candidate:
            raise ValueError("demo transport reservation attempt/provenance collision")
        return reservation

    prepared_on_disk = nextgen_prepared_checkpoint_from_bytes(existing)
    if prepared_on_disk != prepared:
        raise ValueError("demo transport reservation PREPARED attempt/provenance collision")

    reservation = build_demo_transport_attempt_reservation(
        prepared=prepared,
        authorization=authorization,
        bundle=bundle,
        evaluated_at=evaluated_at,
        max_host_age_seconds=max_host_age_seconds,
        submission_ordinal=submission_ordinal,
    )
    store.save(key, demo_transport_attempt_reservation_to_bytes(reservation))
    return reservation


def demo_transport_attempt_reservation_to_bytes(
    reservation: DemoTransportAttemptReservation,
) -> bytes:
    reservation.__post_init__()
    payload = _payload(reservation)
    return _bytes(payload | {"reservation_fingerprint": _fingerprint(payload)})


def load_reserved_demo_transport_attempt(
    *,
    store: StateStorePort,
    key: str,
    expected_reservation_fingerprint: str,
) -> DemoTransportAttemptReservation:
    """Load a pinned attempt without reserving, refreshing or writing anything.

    The caller retains the original fingerprint as its attempt/provenance pin.
    Missing, PREPARED, corrupt and differently wired keys all fail closed. An
    expired original scope remains historical evidence, never current authority.
    """
    _sha(expected_reservation_fingerprint, "expected_reservation_fingerprint")
    payload = store.load(key)
    if payload is None:
        raise ValueError("reserved demo transport attempt is missing")
    reservation = demo_transport_attempt_reservation_from_bytes(payload)
    if reservation.fingerprint != expected_reservation_fingerprint:
        raise ValueError("reserved demo transport attempt/provenance collision")
    return reservation


def demo_transport_restart_status(
    reservation: DemoTransportAttemptReservation,
) -> dict[str, Any]:
    """Project local operator evidence; do not fabricate venue or fill truth.

    This is a read model of the existing checkpoint, not another journal. Even a
    reservation created immediately before a crash cannot prove whether a later
    transport call reached the venue. No projection permits retry or slot release.
    """
    reservation.__post_init__()
    return {
        "status": reservation.status,
        "reservation_fingerprint": reservation.fingerprint,
        "intent_id": reservation.prepared.intent.intent_id,
        "client_order_id": reservation.prepared.broker.lifecycle.client_order_id,
        "submission_ordinal": reservation.submission_ordinal,
        "local_order_state": reservation.prepared.broker.lifecycle.state.value,
        "venue_state": "UNKNOWN",
        "required_next_action": "QUERY_RECONCILE_REQUIRED",
        "resubmit_allowed": False,
        "session_slot_release_allowed": False,
        "execution_capability": "NONE",
        "order_execution_enabled": False,
    }


def reconcile_reserved_demo_transport_query(
    *,
    reservation: DemoTransportAttemptReservation,
    bundle_payload: Mapping[str, Any],
    venue: VenueOrderObservation | None,
    evaluated_at: datetime,
) -> BrokerReconciliationVerdict:
    """Veto current query evidence, then delegate comparison to its existing owner.

    No broker query is performed here. Supplied observations remain external
    evidence; an empty/missing observation never proves non-execution. Neither
    CONSISTENT nor BLOCKED permits submission, repair, slot release or promotion.
    Callers reuse telemetry_from_reconciliation and the existing broker journal.
    """
    bundle, _ = _reserved_demo_query_context(
        reservation=reservation, bundle_payload=bundle_payload, evaluated_at=evaluated_at,
    )
    if venue is not None:
        venue.__post_init__()
        if not bundle.host.observed_at <= venue.observed_at <= evaluated_at:
            raise ValueError("demo query venue observation is future or stale")
    return reconcile_broker_order(local=reservation.prepared.broker.lifecycle, venue=venue)


def validate_reserved_demo_transport_query(
    *,
    reservation: DemoTransportAttemptReservation,
    bundle_payload: Mapping[str, Any],
    evaluated_at: datetime,
) -> DemoEvidenceAuthorizationVerdict:
    """Preflight a future read-only query before it runs; grant no execution.

    The query adapter remains external. It must use the pinned reservation's
    client identity and exact account/server/symbol; recheck returned evidence
    through reconcile_reserved_demo_transport_query. Never reuse SUBMIT scope as
    QUERY scope or reuse this preflight as submission/recovery authorization.
    """
    _, scope = _reserved_demo_query_context(
        reservation=reservation, bundle_payload=bundle_payload, evaluated_at=evaluated_at,
    )
    return scope


def _reserved_demo_query_context(
    *,
    reservation: DemoTransportAttemptReservation,
    bundle_payload: Mapping[str, Any],
    evaluated_at: datetime,
) -> tuple[WindowsMt5Bundle, DemoEvidenceAuthorizationVerdict]:
    """One shared current-context veto for pre-query and returned-query evidence."""
    reservation.__post_init__()
    _aware(evaluated_at, "evaluated_at")
    if evaluated_at < reservation.evaluated_at:
        raise ValueError("demo query cannot precede reservation")
    # Parse the actual current envelope, not a caller-forged GREEN summary.
    bundle = parse_windows_mt5_bundle(bundle_payload)
    context = _validated_demo_bundle_context(bundle)
    if context.fingerprint != reservation.account_context_fingerprint:
        raise ValueError("demo query account context cross-wiring")
    if bundle.host.observed_at < reservation.evaluated_at:
        raise ValueError("demo query host observation precedes reservation")
    host_age = (evaluated_at - bundle.host.observed_at).total_seconds()
    if host_age < 0 or host_age > reservation.max_host_age_seconds:
        raise ValueError("demo query host observation is future or stale")
    feed_limit = bundle_payload["closed_m5_feed"]["max_age_seconds"]
    if bundle.feed.age_seconds + host_age > feed_limit:
        raise ValueError("demo query feed evidence is stale at evaluation")

    scope = evaluate_demo_evidence_authorization(
        authorization=reservation.authorization,
        observed=context.to_observed_context(),
        requested_action=DemoEvidenceAction.QUERY_EVIDENCE_ORDER,
        evaluated_at=evaluated_at,
        submissions_already_attempted=reservation.submission_ordinal,
    )
    if not scope.scope_valid:
        raise ValueError("demo query authorization blocked: " + ",".join(scope.blockers))
    return bundle, scope


def demo_transport_attempt_reservation_from_bytes(
    payload: bytes,
) -> DemoTransportAttemptReservation:
    """Restore original reservation evidence without refreshing time or authority."""
    raw = json.loads(payload, object_pairs_hook=_unique, parse_constant=_reject_constant)
    expected_keys = {
        f.name for f in fields(DemoTransportAttemptReservation)
    } | {"reservation_fingerprint"}
    if not isinstance(raw, dict) or raw.keys() != expected_keys:
        raise ValueError("demo transport reservation field set mismatch")
    observed_fingerprint = raw.pop("reservation_fingerprint")
    if observed_fingerprint != _fingerprint(raw):
        raise ValueError("demo transport reservation fingerprint mismatch")

    prepared = nextgen_prepared_checkpoint_from_bytes(_bytes(raw["prepared"]))
    authorization = _authorization_from_payload(raw["authorization"])
    verdict = _verdict_from_payload(raw["authorization_verdict"])
    account_context = parse_mt5_demo_account_context_payload(raw["account_context"])
    reservation = DemoTransportAttemptReservation(
        prepared=prepared,
        prepared_fingerprint=raw["prepared_fingerprint"],
        authorization=authorization,
        authorization_verdict=verdict,
        authorization_fingerprint=raw["authorization_fingerprint"],
        account_context=account_context,
        account_context_fingerprint=raw["account_context_fingerprint"],
        bundle_fingerprint=raw["bundle_fingerprint"],
        host_observed_at=_timestamp(raw["host_observed_at"], "host_observed_at"),
        feed_observed_at=_timestamp(raw["feed_observed_at"], "feed_observed_at"),
        feed_latest_closed_fingerprint=raw["feed_latest_closed_fingerprint"],
        evaluated_at=_timestamp(raw["evaluated_at"], "evaluated_at"),
        max_host_age_seconds=raw["max_host_age_seconds"],
        submission_ordinal=raw["submission_ordinal"],
        status=raw["status"],
        schema_version=raw["schema_version"],
        execution_capability=raw["execution_capability"],
        order_execution_enabled=raw["order_execution_enabled"],
    )
    if demo_transport_attempt_reservation_to_bytes(reservation) != payload:
        raise ValueError("demo transport reservation payload is not canonical")
    return reservation


def _payload(reservation: DemoTransportAttemptReservation) -> dict[str, Any]:
    prepared = json.loads(nextgen_prepared_checkpoint_to_bytes(reservation.prepared))
    return {
        "prepared": prepared,
        "prepared_fingerprint": reservation.prepared_fingerprint,
        "authorization": _authorization_payload(reservation.authorization),
        "authorization_verdict": _verdict_payload(reservation.authorization_verdict),
        "authorization_fingerprint": reservation.authorization_fingerprint,
        "account_context": reservation.account_context.to_payload(),
        "account_context_fingerprint": reservation.account_context_fingerprint,
        "bundle_fingerprint": reservation.bundle_fingerprint,
        "host_observed_at": _iso(reservation.host_observed_at),
        "feed_observed_at": _iso(reservation.feed_observed_at),
        "feed_latest_closed_fingerprint": reservation.feed_latest_closed_fingerprint,
        "evaluated_at": _iso(reservation.evaluated_at),
        "max_host_age_seconds": reservation.max_host_age_seconds,
        "submission_ordinal": reservation.submission_ordinal,
        "status": reservation.status,
        "schema_version": reservation.schema_version,
        "execution_capability": reservation.execution_capability,
        "order_execution_enabled": reservation.order_execution_enabled,
    }


def _authorization_payload(value: DemoEvidenceAuthorization) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "authorization_id": value.authorization_id,
        "account_id": value.account_id,
        "server": value.server,
        "symbol": value.symbol,
        "valid_from": _iso(value.valid_from),
        "expires_at": _iso(value.expires_at),
        "allowed_actions": [action.value for action in value.allowed_actions],
        "max_submissions": value.max_submissions,
        "purpose": value.purpose,
        "execution_capability": value.execution_capability,
        "order_execution_enabled": value.order_execution_enabled,
    }


def _authorization_from_payload(payload: Any) -> DemoEvidenceAuthorization:
    if not isinstance(payload, dict):
        raise ValueError("demo transport reservation authorization must be an object")
    required = {
        "schema_version",
        "authorization_id",
        "account_id",
        "server",
        "symbol",
        "valid_from",
        "expires_at",
        "allowed_actions",
        "max_submissions",
        "purpose",
        "execution_capability",
        "order_execution_enabled",
    }
    if payload.keys() != required:
        raise ValueError("demo transport reservation authorization field set mismatch")
    actions_raw = payload["allowed_actions"]
    if not isinstance(actions_raw, list):
        raise ValueError("demo transport reservation allowed_actions must be a list")
    return DemoEvidenceAuthorization(
        schema_version=payload["schema_version"],
        authorization_id=payload["authorization_id"],
        account_id=payload["account_id"],
        server=payload["server"],
        symbol=payload["symbol"],
        valid_from=_timestamp(payload["valid_from"], "valid_from"),
        expires_at=_timestamp(payload["expires_at"], "expires_at"),
        allowed_actions=tuple(DemoEvidenceAction(item) for item in actions_raw),
        max_submissions=payload["max_submissions"],
        purpose=payload["purpose"],
        execution_capability=payload["execution_capability"],
        order_execution_enabled=payload["order_execution_enabled"],
    )


def _verdict_payload(value: DemoEvidenceAuthorizationVerdict) -> dict[str, Any]:
    return {
        "status": value.status.value,
        "blockers": list(value.blockers),
        "authorization_fingerprint": value.authorization_fingerprint,
        "requested_action": value.requested_action.value,
        "execution_capability": value.execution_capability,
        "order_execution_enabled": value.order_execution_enabled,
    }


def _verdict_from_payload(payload: Any) -> DemoEvidenceAuthorizationVerdict:
    if not isinstance(payload, dict):
        raise ValueError("demo transport reservation verdict must be an object")
    required = {
        "status",
        "blockers",
        "authorization_fingerprint",
        "requested_action",
        "execution_capability",
        "order_execution_enabled",
    }
    if payload.keys() != required:
        raise ValueError("demo transport reservation verdict field set mismatch")
    blockers = payload["blockers"]
    if not isinstance(blockers, list):
        raise ValueError("demo transport reservation verdict blockers must be a list")
    return DemoEvidenceAuthorizationVerdict(
        status=DemoEvidenceAuthorizationStatus(payload["status"]),
        blockers=tuple(blockers),
        authorization_fingerprint=payload["authorization_fingerprint"],
        requested_action=DemoEvidenceAction(payload["requested_action"]),
        execution_capability=payload["execution_capability"],
        order_execution_enabled=payload["order_execution_enabled"],
    )


def _schema(payload: bytes) -> str | None:
    try:
        raw = json.loads(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("demo transport attempt state is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise ValueError("demo transport attempt state must be an object")
    schema = raw.get("schema_version")
    if schema is not None and not isinstance(schema, str):
        raise ValueError("demo transport attempt schema_version must be a string")
    return schema


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be valid ISO-8601") from exc
    _aware(parsed, field)
    return parsed


def _aware(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


def _iso(value: datetime) -> str:
    _aware(value, "timestamp")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be a 64-character SHA-256 hex string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be hexadecimal") from exc


def _bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return sha256(_bytes(payload)).hexdigest()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate demo transport reservation JSON field")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite demo transport reservation JSON value: {value}")
