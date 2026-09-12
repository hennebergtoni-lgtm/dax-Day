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
    SessionAdmissionObservation,
    SessionAdmissionPolicy,
    evaluate_session_admission,
)
from daxlab.runtime.broker_reconciliation import BrokerReconciliationVerdict
from daxlab.state.loss_exposure import LossExposureObservationCheckpoint


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
        ):
            if value is not None:
                _sha(value, field)
        if self.feed_age_seconds < 0:
            raise ValueError("feed_age_seconds must be non-negative")
        if self.observed_spread_points is not None and self.observed_spread_points < 0:
            raise ValueError("observed_spread_points must be non-negative")
        if self.loss_observation_age_seconds is not None and (
            not isfinite(self.loss_observation_age_seconds)
            or self.loss_observation_age_seconds < 0
        ):
            raise ValueError("loss_observation_age_seconds must be finite and non-negative")
        if (
            self.loss_observation_checkpoint_fingerprint is None
        ) != (self.loss_observation_age_seconds is None):
            raise ValueError("loss observation checkpoint identity and age must appear together")
        session_values = (
            self.session_policy_fingerprint,
            self.session_observation_fingerprint,
            self.session_admission_evidence_fingerprint,
        )
        if any(value is not None for value in session_values) and any(
            value is None for value in session_values
        ):
            raise ValueError("session admission identity evidence must be complete")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
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
) -> BrokerExecutionProtectionVerdict:
    """Combine normalized protection evidence; submit and authorize nothing."""
    _sha(client_order_id, "client_order_id")
    if feed_age_seconds < 0 or max_feed_age_seconds < 0:
        raise ValueError("feed ages must be non-negative")
    if max_spread_points < 0:
        raise ValueError("max_spread_points must be non-negative")
    if observed_spread_points is not None and observed_spread_points < 0:
        raise ValueError("observed_spread_points must be non-negative")
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
    ):
        if value is not None:
            _sha(value, field)

    freshness_values = (
        loss_observation_checkpoint_fingerprint,
        loss_observation_age_seconds,
        loss_observation_fresh,
    )
    if any(value is not None for value in freshness_values) and any(
        value is None for value in freshness_values
    ):
        raise ValueError("loss observation freshness evidence must be complete")
    if loss_observation_age_seconds is not None and (
        isinstance(loss_observation_age_seconds, bool)
        or not isfinite(loss_observation_age_seconds)
        or loss_observation_age_seconds < 0
    ):
        raise ValueError("loss_observation_age_seconds must be finite and non-negative")
    if loss_observation_fresh is not None and type(loss_observation_fresh) is not bool:
        raise ValueError("loss_observation_fresh must be boolean")

    session_values = (
        session_policy_fingerprint,
        session_observation_fingerprint,
        session_admission_evidence_fingerprint,
    )
    if any(value is not None for value in session_values) and any(
        value is None for value in session_values
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
    session_observation: SessionAdmissionObservation,
    session_admission_decision: SessionAdmissionDecision,
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
    if (
        isinstance(max_loss_observation_age_seconds, bool)
        or not isfinite(max_loss_observation_age_seconds)
        or max_loss_observation_age_seconds < 0
    ):
        raise ValueError(
            "max_loss_observation_age_seconds must be finite and non-negative"
        )
    observation_age_seconds = (
        evaluated_at.astimezone(timezone.utc)
        - loss_observation_checkpoint.observed_at.astimezone(timezone.utc)
    ).total_seconds()
    if observation_age_seconds < 0:
        raise ValueError("loss observation checkpoint cannot be future-dated")
    observation_fresh = observation_age_seconds <= max_loss_observation_age_seconds

    expected_session_admission = evaluate_session_admission(
        policy=session_policy,
        observation=session_observation,
    )
    if expected_session_admission != session_admission_decision:
        raise ValueError(
            "session admission decision does not match canonical session evaluation"
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
        loss_observation_age_seconds=observation_age_seconds,
        loss_observation_fresh=observation_fresh,
        session_policy_fingerprint=session_policy.policy_fingerprint,
        session_observation_fingerprint=(
            session_observation.observation_fingerprint
        ),
        session_admission_evidence_fingerprint=(
            session_admission_decision.decision_fingerprint
        ),
    )


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
