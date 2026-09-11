"""Broker-neutral pre-submission protection evidence with no submission API.

The verdict here is deliberately NOT an execution authorization. It combines
already-owned safety evidence into one fail-closed classification that a future,
separately authorized PAPER adapter could require before submission.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any

from daxlab.runtime.broker_reconciliation import BrokerReconciliationVerdict


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
        ):
            if value is not None:
                _sha(value, field)
        if self.feed_age_seconds < 0:
            raise ValueError("feed_age_seconds must be non-negative")
        if self.observed_spread_points is not None and self.observed_spread_points < 0:
            raise ValueError("observed_spread_points must be non-negative")
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
) -> BrokerExecutionProtectionVerdict:
    """Combine normalized protection evidence; submit and authorize nothing."""
    _sha(client_order_id, "client_order_id")
    if feed_age_seconds < 0 or max_feed_age_seconds < 0:
        raise ValueError("feed ages must be non-negative")
    if max_spread_points < 0:
        raise ValueError("max_spread_points must be non-negative")
    if observed_spread_points is not None and observed_spread_points < 0:
        raise ValueError("observed_spread_points must be non-negative")
    if sizing_evidence_fingerprint is not None:
        _sha(sizing_evidence_fingerprint, "sizing_evidence_fingerprint")
    if risk_policy_fingerprint is not None:
        _sha(risk_policy_fingerprint, "risk_policy_fingerprint")

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
