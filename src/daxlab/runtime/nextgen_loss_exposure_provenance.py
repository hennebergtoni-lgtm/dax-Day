"""Narrow source provenance adapter over the existing loss checkpoint owner.

No loss calculation, policy selection, broker API, store or journal.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from math import isfinite

from daxlab.domain.loss_admission import LossExposurePolicy
from daxlab.runtime.demo_evidence_authorization import DemoAccountMode
from daxlab.runtime.mt5_demo_account_context import (
    Mt5DemoAccountContextEvidence, parse_mt5_demo_account_context_payload,
)
from daxlab.state.loss_exposure import (
    LossExposureObservationCheckpoint,
    assert_loss_exposure_checkpoint_compatible,
    loss_exposure_checkpoint_from_bytes,
    _fingerprint, _require_aware, _require_sha256, _text,
)

@dataclass(frozen=True, slots=True)
class LossExposureObservationProvenance:
    """Binding evidence for an independently reviewed, already-computed snapshot.

    Source/review/definition digests are not authentication or proof of broker
    origin. Their content and policy approval require independent review. This
    adapter does not calculate loss, interpret margin, or choose/reset periods.
    No additional store or journal is introduced; the legacy checkpoint is intact.
    """

    checkpoint: LossExposureObservationCheckpoint
    account_context: Mt5DemoAccountContextEvidence
    source_fingerprint: str
    calculation_contract_fingerprint: str
    policy_review_record_fingerprint: str
    daily_period_start: datetime
    daily_period_end: datetime
    weekly_period_start: datetime
    weekly_period_end: datetime
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        self.checkpoint.__post_init__()
        self.checkpoint.observation.__post_init__()
        self.account_context.__post_init__()
        if self.account_context.account_mode is not DemoAccountMode.DEMO:
            raise ValueError("loss provenance requires DEMO account context")
        for field in (
            "source_fingerprint", "calculation_contract_fingerprint",
            "policy_review_record_fingerprint",
        ):
            _require_sha256(getattr(self, field), field)
        for field in (
            "daily_period_start", "daily_period_end",
            "weekly_period_start", "weekly_period_end",
        ):
            value = getattr(self, field)
            _require_aware(value, field)
            if value.utcoffset() is None:
                raise ValueError(f"{field} must have a UTC offset")
        if not (
            self.weekly_period_start <= self.daily_period_start
            <= self.checkpoint.observed_at < self.daily_period_end
            <= self.weekly_period_end
        ):
            raise ValueError("loss provenance periods must contain observation and daily scope")
        if self.execution_capability != "NONE" or self.order_execution_enabled is not False:
            raise ValueError("loss provenance cannot authorize execution")

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": "DAXLAB_LOSS_EXPOSURE_OBSERVATION_PROVENANCE_V1",
            "checkpoint": self.checkpoint.to_dict(),
            "account_context": self.account_context.to_payload(),
            "source_fingerprint": self.source_fingerprint,
            "calculation_contract_fingerprint": self.calculation_contract_fingerprint,
            "policy_review_record_fingerprint": self.policy_review_record_fingerprint,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }
        for field in (
            "daily_period_start", "daily_period_end",
            "weekly_period_start", "weekly_period_end",
        ):
            payload[field] = getattr(self, field).astimezone(timezone.utc).isoformat()
        return payload

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.to_dict())


def loss_exposure_provenance_to_bytes(provenance: LossExposureObservationProvenance) -> bytes:
    provenance.__post_init__()
    payload = provenance.to_dict() | {"provenance_fingerprint": provenance.fingerprint}
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def loss_exposure_provenance_from_bytes(payload: bytes) -> LossExposureObservationProvenance:
    """Strict source-binding codec reusing the original checkpoint/account parsers."""
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite provenance JSON: {value}")

    def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate loss provenance JSON key")
            result[key] = value
        return result

    if not isinstance(payload, bytes):
        raise TypeError("loss provenance payload must be bytes")
    raw = json.loads(payload.decode(), parse_constant=reject_constant, object_pairs_hook=unique_pairs)
    required = {
        "schema_version", "checkpoint", "account_context", "source_fingerprint",
        "calculation_contract_fingerprint", "policy_review_record_fingerprint",
        "daily_period_start", "daily_period_end", "weekly_period_start", "weekly_period_end",
        "execution_capability", "order_execution_enabled", "provenance_fingerprint",
    }
    if not isinstance(raw, dict) or raw.keys() != required:
        raise ValueError("loss provenance field set mismatch")
    observed = raw.pop("provenance_fingerprint")
    if observed != _fingerprint(raw):
        raise ValueError("loss provenance fingerprint mismatch")
    if raw.pop("schema_version") != "DAXLAB_LOSS_EXPOSURE_OBSERVATION_PROVENANCE_V1":
        raise ValueError("loss provenance schema mismatch")
    checkpoint = loss_exposure_checkpoint_from_bytes(json.dumps(raw.pop("checkpoint")).encode())
    context = parse_mt5_demo_account_context_payload(raw.pop("account_context"))
    for field in (
        "daily_period_start", "daily_period_end", "weekly_period_start", "weekly_period_end",
    ):
        raw[field] = datetime.fromisoformat(_text(raw, field))
    provenance = LossExposureObservationProvenance(checkpoint=checkpoint, account_context=context, **raw)
    if loss_exposure_provenance_to_bytes(provenance) != payload:
        raise ValueError("loss provenance payload is not canonical")
    return provenance


def assert_loss_exposure_provenance_compatible(
    provenance: LossExposureObservationProvenance,
    *,
    checkpoint: LossExposureObservationCheckpoint,
    policy: LossExposurePolicy,
    account_context: Mt5DemoAccountContextEvidence,
    expected_source_fingerprint: str,
    evaluated_at: datetime,
    max_age_seconds: float,
) -> None:
    """Check pinned source/account/policy/freshness before existing protection.

    This check authenticates neither the source packet nor product policy review
    and never changes readiness. The external review must validate those records.
    """
    provenance.__post_init__()
    policy.__post_init__()
    account_context.__post_init__()
    _require_sha256(expected_source_fingerprint, "expected_source_fingerprint")
    assert_loss_exposure_checkpoint_compatible(checkpoint, policy_fingerprint=policy.policy_fingerprint)
    if provenance.checkpoint != checkpoint or provenance.account_context != account_context:
        raise ValueError("loss provenance checkpoint/account cross-wiring")
    if provenance.source_fingerprint != expected_source_fingerprint:
        raise ValueError("loss provenance source cross-wiring")
    if checkpoint.observation.currency != policy.currency:
        raise ValueError("loss provenance policy currency mismatch")
    _require_aware(evaluated_at, "evaluated_at")
    if (
        isinstance(max_age_seconds, bool) or not isinstance(max_age_seconds, (int, float))
        or not isfinite(max_age_seconds) or max_age_seconds < 0
    ):
        raise ValueError("loss provenance max age must be finite and non-negative")
    age = (evaluated_at - checkpoint.observed_at).total_seconds()
    if age < 0 or age > max_age_seconds or evaluated_at >= provenance.daily_period_end:
        raise ValueError("loss provenance future-dated, stale or outside explicit period")
