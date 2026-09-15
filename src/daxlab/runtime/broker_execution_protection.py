"""Broker-neutral pre-submission protection evidence with no submission API.

The verdict here is deliberately NOT an execution authorization. It combines
already-owned safety evidence into one fail-closed classification that a future,
separately authorized PAPER adapter could require before submission.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
from math import isfinite
from typing import Any

from daxlab.domain.loss_admission import (
    LossExposureAdmissionDecision,
    LossExposureObservation,
    LossExposurePolicy,
    evaluate_loss_exposure_admission,
)
from daxlab.domain.risk import RiskDecision, RiskRequest, evaluate_fixed_cash_risk
from daxlab.domain.risk_policy import FixedCashRiskPolicy
from daxlab.domain.session_admission import (
    SessionAdmissionDecision,
    SessionAdmissionPolicy,
    evaluate_session_admission,
)
from daxlab.runtime.broker_reconciliation import BrokerReconciliationVerdict
from daxlab.state.loss_exposure import LossExposureObservationCheckpoint
from daxlab.state.session_admission import SessionAdmissionGuardCheckpoint


BROKER_EXECUTION_PROTECTION_SCHEMA = "DAXLAB_BROKER_EXECUTION_PROTECTION_V1"


class ExecutionProtectionStatus(StrEnum):
    ALLOW_EVIDENCE = "ALLOW_EVIDENCE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class BrokerExecutionProtectionVerdict:
    schema_version: str
    status: ExecutionProtectionStatus
    blockers: tuple[str, ...]
    client_order_id: str
    reconciliation_fingerprints: tuple[str, ...]
    sizing_evidence_fingerprint: str | None
    risk_policy_fingerprint: str | None
    feed_age_seconds: float
    observed_spread_points: float | None
    loss_admission_evidence_fingerprint: str | None = None
    loss_observation_checkpoint_fingerprint: str | None = None
    loss_observation_age_seconds: float | None = None
    session_policy_fingerprint: str | None = None
    session_observation_fingerprint: str | None = None
    session_admission_evidence_fingerprint: str | None = None
    session_observation_checkpoint_fingerprint: str | None = None
    session_guard_checkpoint_fingerprint: str | None = None
    session_observation_age_seconds: float | None = None
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != BROKER_EXECUTION_PROTECTION_SCHEMA:
            raise ValueError("execution protection schema mismatch")
        _sha(self.client_order_id, "client_order_id")
        for value in self.reconciliation_fingerprints:
            _sha(value, "reconciliation_fingerprint")
        for value, field in (
            (self.sizing_evidence_fingerprint, "sizing_evidence_fingerprint"),
            (self.risk_policy_fingerprint, "risk_policy_fingerprint"),
            (
                self.loss_admission_evidence_fingerprint,
                "loss_admission_evidence_fingerprint",
            ),
            (
                self.loss_observation_checkpoint_fingerprint,
                "loss_observation_checkpoint_fingerprint",
            ),
            (self.session_policy_fingerprint, "session_policy_fingerprint"),
            (
                self.session_observation_fingerprint,
                "session_observation_fingerprint",
            ),
            (
                self.session_admission_evidence_fingerprint,
                "session_admission_evidence_fingerprint",
            ),
            (
                self.session_observation_checkpoint_fingerprint,
                "session_observation_checkpoint_fingerprint",
            ),
            (
                self.session_guard_checkpoint_fingerprint,
                "session_guard_checkpoint_fingerprint",
            ),
        ):
            if value is not None:
                _sha(value, field)
        _validate_max_age(self.feed_age_seconds, "feed_age_seconds")
        _validate_optional_age(self.observed_spread_points, "observed_spread_points")
        _validate_optional_age(
            self.loss_observation_age_seconds,
            "loss_observation_age_seconds",
        )
        _validate_optional_age(
            self.session_observation_age_seconds,
            "session_observation_age_seconds",
        )
        if (self.loss_observation_checkpoint_fingerprint is None) != (
            self.loss_observation_age_seconds is None
        ):
            raise ValueError("loss observation checkpoint identity and age must appear together")
        _validate_session_checkpoint_identity_and_age(
            observation_checkpoint_fingerprint=(
                self.session_observation_checkpoint_fingerprint
            ),
            guard_checkpoint_fingerprint=self.session_guard_checkpoint_fingerprint,
            age_seconds=self.session_observation_age_seconds,
        )
        session_identity = (
            self.session_policy_fingerprint,
            self.session_observation_fingerprint,
            self.session_admission_evidence_fingerprint,
        )
        if any(value is not None for value in session_identity) and any(
            value is None for value in session_identity
        ):
            raise ValueError("session admission identity evidence must be complete")
        if self.execution_capability != "NONE" or self.order_execution_enabled is not False:
            raise ValueError("execution protection verdict cannot authorize execution")
        if self.status is ExecutionProtectionStatus.ALLOW_EVIDENCE and self.blockers:
            raise ValueError("allow evidence cannot carry blockers")
        if self.status is ExecutionProtectionStatus.BLOCKED and not self.blockers:
            raise ValueError("blocked protection verdict requires blockers")

    @property
    def allow_evidence(self) -> bool:
        return self.status is ExecutionProtectionStatus.ALLOW_EVIDENCE

    @property
    def fingerprint(self) -> str:
        return _fingerprint(
            {
                "schema_version": self.schema_version,
                "status": self.status.value,
                "blockers": list(self.blockers),
                "client_order_id": self.client_order_id,
                "reconciliation_fingerprints": list(self.reconciliation_fingerprints),
                "sizing_evidence_fingerprint": self.sizing_evidence_fingerprint,
                "risk_policy_fingerprint": self.risk_policy_fingerprint,
                "loss_admission_evidence_fingerprint": (
                    self.loss_admission_evidence_fingerprint
                ),
                "loss_observation_checkpoint_fingerprint": (
                    self.loss_observation_checkpoint_fingerprint
                ),
                "loss_observation_age_seconds": self.loss_observation_age_seconds,
                "session_policy_fingerprint": self.session_policy_fingerprint,
                "session_observation_fingerprint": (
                    self.session_observation_fingerprint
                ),
                "session_admission_evidence_fingerprint": (
                    self.session_admission_evidence_fingerprint
                ),
                "session_observation_checkpoint_fingerprint": (
                    self.session_observation_checkpoint_fingerprint
                ),
                "session_guard_checkpoint_fingerprint": (
                    self.session_guard_checkpoint_fingerprint
                ),
                "session_observation_age_seconds": self.session_observation_age_seconds,
                "feed_age_seconds": float(self.feed_age_seconds),
                "observed_spread_points": (
                    None
                    if self.observed_spread_points is None
                    else float(self.observed_spread_points)
                ),
                "execution_capability": self.execution_capability,
                "order_execution_enabled": self.order_execution_enabled,
            }
        )


def evaluate_execution_protection(
    *,
    client_order_id: str,
    host_health_green: bool,
    broker_account_trade_allowed: bool,
    feed_age_seconds: float,
    max_feed_age_seconds: float,
    observed_spread_points: float | None,
    max_spread_points: float,
    reconciliation_inventory_complete: bool,
    reconciliations: tuple[BrokerReconciliationVerdict, ...],
    duplicate_client_order_id: bool,
    sizing_allowed: bool,
    sizing_evidence_fingerprint: str | None,
    loss_cap_allowed: bool,
    risk_policy_fingerprint: str | None,
    session_admission_allowed: bool,
    loss_admission_evidence_fingerprint: str | None = None,
    loss_observation_checkpoint_fingerprint: str | None = None,
    loss_observation_age_seconds: float | None = None,
    loss_observation_fresh: bool | None = None,
    session_policy_fingerprint: str | None = None,
    session_observation_fingerprint: str | None = None,
    session_admission_evidence_fingerprint: str | None = None,
    session_observation_checkpoint_fingerprint: str | None = None,
    session_guard_checkpoint_fingerprint: str | None = None,
    session_observation_age_seconds: float | None = None,
    session_observation_fresh: bool | None = None,
) -> BrokerExecutionProtectionVerdict:
    """Combine normalized protection evidence; submit and authorize nothing."""
    for value, label in (
        (host_health_green, "host_health_green"),
        (broker_account_trade_allowed, "broker_account_trade_allowed"),
        (reconciliation_inventory_complete, "reconciliation_inventory_complete"),
        (duplicate_client_order_id, "duplicate_client_order_id"),
        (sizing_allowed, "sizing_allowed"), (loss_cap_allowed, "loss_cap_allowed"),
        (session_admission_allowed, "session_admission_allowed"),
    ):
        if type(value) is not bool:
            raise ValueError(label + " must be boolean")
    _sha(client_order_id, "client_order_id")
    _validate_max_age(feed_age_seconds, "feed_age_seconds")
    _validate_max_age(max_feed_age_seconds, "max_feed_age_seconds")
    _validate_max_age(max_spread_points, "max_spread_points")
    _validate_optional_age(observed_spread_points, "observed_spread_points")
    for value, field in (
        (sizing_evidence_fingerprint, "sizing_evidence_fingerprint"),
        (risk_policy_fingerprint, "risk_policy_fingerprint"),
        (
            loss_admission_evidence_fingerprint,
            "loss_admission_evidence_fingerprint",
        ),
        (
            loss_observation_checkpoint_fingerprint,
            "loss_observation_checkpoint_fingerprint",
        ),
        (session_policy_fingerprint, "session_policy_fingerprint"),
        (session_observation_fingerprint, "session_observation_fingerprint"),
        (
            session_admission_evidence_fingerprint,
            "session_admission_evidence_fingerprint",
        ),
        (
            session_observation_checkpoint_fingerprint,
            "session_observation_checkpoint_fingerprint",
        ),
        (
            session_guard_checkpoint_fingerprint,
            "session_guard_checkpoint_fingerprint",
        ),
    ):
        if value is not None:
            _sha(value, field)

    _validate_freshness_bundle(
        checkpoint_fingerprint=loss_observation_checkpoint_fingerprint,
        age_seconds=loss_observation_age_seconds,
        fresh=loss_observation_fresh,
        label="loss observation",
    )
    session_checkpoint_fingerprint = _select_session_checkpoint_fingerprint(
        observation_checkpoint_fingerprint=session_observation_checkpoint_fingerprint,
        guard_checkpoint_fingerprint=session_guard_checkpoint_fingerprint,
    )
    _validate_freshness_bundle(
        checkpoint_fingerprint=session_checkpoint_fingerprint,
        age_seconds=session_observation_age_seconds,
        fresh=session_observation_fresh,
        label="session observation",
    )

    session_identity = (
        session_policy_fingerprint,
        session_observation_fingerprint,
        session_admission_evidence_fingerprint,
    )
    if any(value is not None for value in session_identity) and any(
        value is None for value in session_identity
    ):
        raise ValueError("session admission identity evidence must be complete")

    blockers: list[str] = []
    if not host_health_green:
        blockers.append("HOST_HEALTH_NOT_GREEN")
    if not broker_account_trade_allowed:
        blockers.append("BROKER_ACCOUNT_TRADING_NOT_ALLOWED")
    if feed_age_seconds > max_feed_age_seconds:
        blockers.append("STALE_FEED")
    if observed_spread_points is None:
        blockers.append("SPREAD_UNAVAILABLE")
    elif observed_spread_points > max_spread_points:
        blockers.append("EXTREME_SPREAD")

    if not reconciliation_inventory_complete:
        blockers.append("RECONCILIATION_INVENTORY_INCOMPLETE")
    if any(not verdict.consistent for verdict in reconciliations):
        blockers.append("BROKER_RECONCILIATION_BLOCKED")

    if duplicate_client_order_id:
        blockers.append("DUPLICATE_CLIENT_ORDER_ID")
    if sizing_evidence_fingerprint is None:
        blockers.append("SIZING_EVIDENCE_MISSING")
    if not sizing_allowed:
        blockers.append("SIZING_BLOCKED")
    if risk_policy_fingerprint is None:
        blockers.append("RISK_POLICY_EVIDENCE_MISSING")
    if not loss_cap_allowed:
        blockers.append("LOSS_CAP_BLOCKED")
    if loss_observation_fresh is False:
        blockers.append("LOSS_EXPOSURE_OBSERVATION_STALE")
    if not session_admission_allowed:
        blockers.append("SESSION_ADMISSION_BLOCKED")
    if session_observation_fresh is False:
        blockers.append("SESSION_ADMISSION_OBSERVATION_STALE")

    unique = tuple(dict.fromkeys(blockers))
    status = (
        ExecutionProtectionStatus.ALLOW_EVIDENCE
        if not unique
        else ExecutionProtectionStatus.BLOCKED
    )
    return BrokerExecutionProtectionVerdict(
        schema_version=BROKER_EXECUTION_PROTECTION_SCHEMA,
        status=status,
        blockers=unique,
        client_order_id=client_order_id,
        reconciliation_fingerprints=tuple(
            verdict.fingerprint for verdict in reconciliations
        ),
        sizing_evidence_fingerprint=sizing_evidence_fingerprint,
        risk_policy_fingerprint=risk_policy_fingerprint,
        feed_age_seconds=float(feed_age_seconds),
        observed_spread_points=(
            None if observed_spread_points is None else float(observed_spread_points)
        ),
        loss_admission_evidence_fingerprint=loss_admission_evidence_fingerprint,
        loss_observation_checkpoint_fingerprint=(
            loss_observation_checkpoint_fingerprint
        ),
        loss_observation_age_seconds=(
            None
            if loss_observation_age_seconds is None
            else float(loss_observation_age_seconds)
        ),
        session_policy_fingerprint=session_policy_fingerprint,
        session_observation_fingerprint=session_observation_fingerprint,
        session_admission_evidence_fingerprint=(
            session_admission_evidence_fingerprint
        ),
        session_observation_checkpoint_fingerprint=(
            session_observation_checkpoint_fingerprint
        ),
        session_guard_checkpoint_fingerprint=session_guard_checkpoint_fingerprint,
        session_observation_age_seconds=(
            None
            if session_observation_age_seconds is None
            else float(session_observation_age_seconds)
        ),
    )


def evaluate_nextgen_execution_protection(
    *,
    client_order_id: str,
    host_health_green: bool,
    broker_account_trade_allowed: bool,
    feed_age_seconds: float,
    max_feed_age_seconds: float,
    observed_spread_points: float | None,
    max_spread_points: float,
    reconciliation_inventory_complete: bool,
    reconciliations: tuple[BrokerReconciliationVerdict, ...],
    duplicate_client_order_id: bool,
    risk_policy: FixedCashRiskPolicy,
    risk_request: RiskRequest,
    risk_decision: RiskDecision,
    loss_policy: LossExposurePolicy,
    loss_observation: LossExposureObservation,
    loss_observation_checkpoint: LossExposureObservationCheckpoint,
    loss_admission_decision: LossExposureAdmissionDecision,
    evaluated_at: datetime,
    max_loss_observation_age_seconds: float,
    session_policy: SessionAdmissionPolicy,
    session_guard_checkpoint: SessionAdmissionGuardCheckpoint,
    session_admission_decision: SessionAdmissionDecision,
    max_session_observation_age_seconds: float,
) -> BrokerExecutionProtectionVerdict:
    """Bind canonical product risk/admission evidence into existing protection."""
    canonical_request = RiskRequest.build(
        strategy_decision_id=risk_request.strategy_decision_id,
        trade_plan=risk_request.trade_plan,
        max_loss_cash=risk_request.max_loss_cash,
        loss_currency=risk_request.loss_currency,
        instrument=risk_request.instrument,
    )
    if canonical_request != risk_request:
        raise ValueError("risk request identity does not match canonical request")
    if (
        risk_request.loss_currency != risk_policy.currency
        or risk_request.max_loss_cash != risk_policy.max_loss_cash
    ):
        raise ValueError("risk request does not match fixed-cash risk policy")

    expected_risk_decision = evaluate_fixed_cash_risk(canonical_request)
    if expected_risk_decision != risk_decision:
        raise ValueError("risk decision does not match canonical risk evaluation")

    expected_loss_admission = evaluate_loss_exposure_admission(
        policy=loss_policy,
        observation=loss_observation,
    )
    if expected_loss_admission != loss_admission_decision:
        raise ValueError(
            "loss admission decision does not match canonical admission evaluation"
        )
    if risk_policy.currency != loss_policy.currency:
        raise ValueError("risk and loss/admission policy currencies must match")
    if loss_observation_checkpoint.policy_fingerprint != loss_policy.policy_fingerprint:
        raise ValueError("loss observation checkpoint policy mismatch")
    if loss_observation_checkpoint.observation != loss_observation:
        raise ValueError("loss observation checkpoint observation mismatch")

    if not isinstance(evaluated_at, datetime) or evaluated_at.tzinfo is None:
        raise ValueError("evaluated_at must be timezone-aware")
    _validate_max_age(
        max_loss_observation_age_seconds,
        "max_loss_observation_age_seconds",
    )
    loss_observation_age_seconds = _observation_age_seconds(
        evaluated_at=evaluated_at,
        observed_at=loss_observation_checkpoint.observed_at,
        future_error="loss observation checkpoint cannot be future-dated",
    )
    loss_observation_fresh = (
        loss_observation_age_seconds <= max_loss_observation_age_seconds
    )

    if session_guard_checkpoint.policy_fingerprint != session_policy.policy_fingerprint:
        raise ValueError("session guard checkpoint policy mismatch")
    session_observation = session_guard_checkpoint.observation
    expected_session_admission = evaluate_session_admission(
        policy=session_policy,
        observation=session_observation,
    )
    if expected_session_admission != session_admission_decision:
        raise ValueError(
            "session admission decision does not match canonical session evaluation"
        )
    _validate_max_age(
        max_session_observation_age_seconds,
        "max_session_observation_age_seconds",
    )
    session_observation_age_seconds = _observation_age_seconds(
        evaluated_at=evaluated_at,
        observed_at=session_guard_checkpoint.observed_at,
        future_error="session guard checkpoint cannot be future-dated",
    )
    session_observation_fresh = (
        session_observation_age_seconds <= max_session_observation_age_seconds
    )

    return evaluate_execution_protection(
        client_order_id=client_order_id,
        host_health_green=host_health_green,
        broker_account_trade_allowed=broker_account_trade_allowed,
        feed_age_seconds=feed_age_seconds,
        max_feed_age_seconds=max_feed_age_seconds,
        observed_spread_points=observed_spread_points,
        max_spread_points=max_spread_points,
        reconciliation_inventory_complete=reconciliation_inventory_complete,
        reconciliations=reconciliations,
        duplicate_client_order_id=duplicate_client_order_id,
        sizing_allowed=risk_decision.allowed,
        sizing_evidence_fingerprint=risk_decision.decision_id,
        loss_cap_allowed=loss_admission_decision.allowed,
        risk_policy_fingerprint=risk_policy.policy_fingerprint,
        session_admission_allowed=session_admission_decision.allowed,
        loss_admission_evidence_fingerprint=(
            loss_admission_decision.decision_fingerprint
        ),
        loss_observation_checkpoint_fingerprint=(
            loss_observation_checkpoint.checkpoint_fingerprint
        ),
        loss_observation_age_seconds=loss_observation_age_seconds,
        loss_observation_fresh=loss_observation_fresh,
        session_policy_fingerprint=session_policy.policy_fingerprint,
        session_observation_fingerprint=(
            session_observation.observation_fingerprint
        ),
        session_admission_evidence_fingerprint=(
            session_admission_decision.decision_fingerprint
        ),
        session_guard_checkpoint_fingerprint=(
            session_guard_checkpoint.checkpoint_fingerprint
        ),
        session_observation_age_seconds=session_observation_age_seconds,
        session_observation_fresh=session_observation_fresh,
    )


def _select_session_checkpoint_fingerprint(
    *,
    observation_checkpoint_fingerprint: str | None,
    guard_checkpoint_fingerprint: str | None,
) -> str | None:
    if (
        observation_checkpoint_fingerprint is not None
        and guard_checkpoint_fingerprint is not None
    ):
        raise ValueError("session freshness evidence cannot use two checkpoint identities")
    return (
        guard_checkpoint_fingerprint
        if guard_checkpoint_fingerprint is not None
        else observation_checkpoint_fingerprint
    )


def _validate_session_checkpoint_identity_and_age(
    *,
    observation_checkpoint_fingerprint: str | None,
    guard_checkpoint_fingerprint: str | None,
    age_seconds: float | None,
) -> None:
    checkpoint_fingerprint = _select_session_checkpoint_fingerprint(
        observation_checkpoint_fingerprint=observation_checkpoint_fingerprint,
        guard_checkpoint_fingerprint=guard_checkpoint_fingerprint,
    )
    if (checkpoint_fingerprint is None) != (age_seconds is None):
        raise ValueError("session checkpoint identity and age must appear together")


def _validate_freshness_bundle(
    *,
    checkpoint_fingerprint: str | None,
    age_seconds: float | None,
    fresh: bool | None,
    label: str,
) -> None:
    values = (checkpoint_fingerprint, age_seconds, fresh)
    if any(value is not None for value in values) and any(
        value is None for value in values
    ):
        raise ValueError(f"{label} freshness evidence must be complete")
    _validate_optional_age(age_seconds, f"{label.replace(' ', '_')}_age_seconds")
    if fresh is not None and type(fresh) is not bool:
        raise ValueError(f"{label.replace(' ', '_')}_fresh must be boolean")


def _finite_nonnegative(value) -> bool:
    try:
        return type(value) in (int, float) and isfinite(value) and value >= 0
    except OverflowError:
        return False


def _validate_max_age(value: float, field_name: str) -> None:
    if not _finite_nonnegative(value):
        raise ValueError(f"{field_name} must be finite and non-negative")


def _validate_optional_age(value: float | None, field_name: str) -> None:
    if value is not None and (
        not _finite_nonnegative(value)
    ):
        raise ValueError(f"{field_name} must be finite and non-negative")


def _observation_age_seconds(
    *,
    evaluated_at: datetime,
    observed_at: datetime,
    future_error: str,
) -> float:
    age = (
        evaluated_at.astimezone(timezone.utc)
        - observed_at.astimezone(timezone.utc)
    ).total_seconds()
    if age < 0:
        raise ValueError(future_error)
    return float(age)


def _sha(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256 hex") from exc


def _fingerprint(value: dict[str, Any]) -> str:
    canonical = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def evaluate_independent_pretrade_controls(*, policy, observation, protection):
    """Independent PTC diagnostic in this protection owner; never submit/unlock.

    Explicit caller-pinned DEMO policy, native price/quantity grids and cash point
    value are required. Strategy risk cannot supply an execution authorization.
    Future bounded transport must revalidate this evidence at request time.
    """
    from decimal import Decimal, InvalidOperation, localcontext
    import re

    policy_fields = {"account_identity_sha256", "instrument_identity_sha256",
                     "min_quantity", "max_quantity", "quantity_increment", "tick_size",
                     "max_notional_cash", "max_price_deviation_points",
                     "max_quote_age_seconds", "max_attempts"}
    observation_fields = {"source_sha256", "account_identity_sha256", "instrument_identity_sha256",
                          "environment", "quantity", "request_price", "reference_price",
                          "cash_per_point_per_unit", "quote_age_seconds", "attempts_used",
                          "duplicate", "inventory_clear", "session_allowed",
                          "reservation_unknown", "emergency_latched"}
    if (not isinstance(policy, dict) or set(policy) != policy_fields
            or not isinstance(observation, dict) or set(observation) != observation_fields):
        raise ValueError("closed independent PTC evidence schema required")
    if not isinstance(protection, BrokerExecutionProtectionVerdict):
        raise ValueError("canonical existing protection verdict required")
    for mapping, fields in ((policy, ("account_identity_sha256", "instrument_identity_sha256")),
                            (observation, ("source_sha256", "account_identity_sha256", "instrument_identity_sha256"))):
        for field in fields:
            if not isinstance(mapping[field], str) or re.fullmatch(r"[0-9a-f]{64}", mapping[field]) is None:
                raise ValueError("PTC semantic/source SHA256 pins required")

    def number(mapping, field, *, nonnegative=False):
        value = mapping[field]
        if not isinstance(value, str) or len(value) > 40 or re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value) is None:
            raise ValueError("PTC native finite decimal string required")
        try:
            result = Decimal(value)
        except InvalidOperation:
            raise ValueError("PTC invalid native decimal") from None
        if result < 0 or (not nonnegative and result == 0):
            raise ValueError("PTC positive bound/observation required")
        return result

    values = {field: number(policy, field, nonnegative=field == "max_price_deviation_points")
              for field in ("min_quantity", "max_quantity", "quantity_increment", "tick_size",
                            "max_notional_cash", "max_price_deviation_points")}
    quantities = {field: number(observation, field)
                  for field in ("quantity", "request_price", "reference_price", "cash_per_point_per_unit")}
    if values["min_quantity"] > values["max_quantity"]:
        raise ValueError("PTC inverted quantity bounds")
    for mapping, field, positive in ((policy, "max_attempts", True), (observation, "attempts_used", False)):
        if type(mapping[field]) is not int or mapping[field] < (1 if positive else 0):
            raise ValueError("PTC integer attempt bound required")
    for field in ("duplicate", "inventory_clear", "session_allowed", "reservation_unknown", "emergency_latched"):
        if type(observation[field]) is not bool:
            raise ValueError("PTC boolean observation required")
    _validate_max_age(policy["max_quote_age_seconds"], "max_quote_age_seconds")
    _validate_max_age(observation["quote_age_seconds"], "quote_age_seconds")
    blockers = []
    if observation["environment"] != "DEMO":
        blockers.append("PTC_HARD_LIVE_OR_UNKNOWN_ENVIRONMENT_BLOCK")
    for field, blocker in (("account_identity_sha256", "PTC_ACCOUNT_VETO"),
                           ("instrument_identity_sha256", "PTC_INSTRUMENT_VETO")):
        if observation[field] != policy[field]:
            blockers.append(blocker)
    if not protection.allow_evidence:
        blockers.append("PTC_EXISTING_PROTECTION_BLOCKED")
    with localcontext() as context:
        context.prec = 160
        qty = quantities["quantity"]
        if not values["min_quantity"] <= qty <= values["max_quantity"]:
            blockers.append("PTC_QUANTITY_BOUND_VETO")
        if qty % values["quantity_increment"] != 0:
            blockers.append("PTC_NATIVE_QUANTITY_GRID_VETO")
        if quantities["request_price"] % values["tick_size"] != 0:
            blockers.append("PTC_NATIVE_PRICE_GRID_VETO")
        if abs(quantities["request_price"] - quantities["reference_price"]) > values["max_price_deviation_points"]:
            blockers.append("PTC_PRICE_COLLAR_VETO")
        notional = qty * quantities["request_price"] * quantities["cash_per_point_per_unit"]
        if notional > values["max_notional_cash"]:
            blockers.append("PTC_NOTIONAL_BOUND_VETO")
    if observation["quote_age_seconds"] > policy["max_quote_age_seconds"]:
        blockers.append("PTC_STALE_PRICE_VETO")
    if observation["attempts_used"] >= policy["max_attempts"]:
        blockers.append("PTC_ATTEMPT_BOUND_VETO")
    for condition, blocker in (
        (observation["duplicate"], "PTC_DUPLICATE_VETO"),
        (not observation["inventory_clear"], "PTC_INVENTORY_VETO"),
        (not observation["session_allowed"], "PTC_SESSION_VETO"),
        (observation["reservation_unknown"], "PTC_UNKNOWN_RESERVATION_QUERY_REQUIRED"),
        (observation["emergency_latched"], "PTC_EMERGENCY_AUTHORITY_LATCHED"),
    ):
        if condition:
            blockers.append(blocker)
    payload = {"schema": "DAX_INDEPENDENT_PTC_DIAGNOSTIC_V1",
               "policy_fingerprint": _fingerprint(policy),
               "observation_fingerprint": _fingerprint(observation),
               "protection_fingerprint": protection.fingerprint,
               "source_sha256": observation["source_sha256"], "blockers": blockers,
               "status": "BLOCKED" if blockers else "ALLOW_EVIDENCE",
               "notional_cash_proxy": str(notional),
               "notional_definition": "NATIVE_QTY_X_PRICE_X_CASH_POINT_VALUE",
               "runtime_integration": "BOUNDED_TRANSPORT_NOT_YET_VERIFIED",
               "execution_capability": "NONE", "order_execution_enabled": False}
    return payload | {"fingerprint": _fingerprint(payload)}
