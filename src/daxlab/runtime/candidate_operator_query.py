"""Pure read model for the latest CAND-001 operator telemetry snapshot.

The database/view is only a storage owner. Consumers receive a freshly validated,
credential-free envelope and a query-time bar-age observation. This module has no
DB, MT5, web-server or execution dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from daxlab.runtime.candidate_operator_telemetry import validate_candidate_operator_snapshot

_SCHEMA = "DAXLAB_CAND001_OPERATOR_CURRENT_V1"


@dataclass(frozen=True, slots=True)
class CandidateOperatorCurrent:
    schema_version: str
    queried_at_utc: str
    source: str
    snapshot_fingerprint: str
    snapshot_generated_at: str
    current_bar_age_seconds: float | None
    payload: dict[str, Any]
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA:
            raise ValueError("unsupported Candidate current-view schema")
        if self.source != "cand001_operator_current":
            raise ValueError("Candidate current-view source drift")
        if self.execution_capability != "NONE" or self.order_execution_enabled:
            raise ValueError("Candidate current-view cannot authorize execution")
        if self.current_bar_age_seconds is not None and self.current_bar_age_seconds < 0:
            raise ValueError("current_bar_age_seconds must be non-negative")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "queried_at_utc": self.queried_at_utc,
            "source": self.source,
            "snapshot_fingerprint": self.snapshot_fingerprint,
            "snapshot_generated_at": self.snapshot_generated_at,
            "current_bar_age_seconds": self.current_bar_age_seconds,
            "payload": self.payload,
            "execution_capability": self.execution_capability,
            "order_execution_enabled": self.order_execution_enabled,
        }


def build_candidate_operator_current(
    payload: Mapping[str, Any],
    *,
    queried_at: datetime,
) -> CandidateOperatorCurrent:
    """Validate one stored snapshot and derive query-time freshness evidence."""
    if queried_at.tzinfo is None:
        raise ValueError("queried_at must be timezone-aware")
    validate_candidate_operator_snapshot(payload)

    runtime = payload["runtime"]
    last_bar_close_time = runtime.get("last_bar_close_time")
    current_age: float | None = None
    if last_bar_close_time is not None:
        close_time = datetime.fromisoformat(str(last_bar_close_time))
        if close_time.tzinfo is None:
            raise ValueError("stored last_bar_close_time must be timezone-aware")
        delta = (queried_at.astimezone(timezone.utc) - close_time.astimezone(timezone.utc)).total_seconds()
        if delta < 0:
            raise ValueError("stored last_bar_close_time is in the future")
        current_age = float(delta)

    return CandidateOperatorCurrent(
        schema_version=_SCHEMA,
        queried_at_utc=queried_at.astimezone(timezone.utc).isoformat(),
        source="cand001_operator_current",
        snapshot_fingerprint=str(payload["snapshot_fingerprint"]),
        snapshot_generated_at=str(payload["generated_at"]),
        current_bar_age_seconds=current_age,
        payload=dict(payload),
    )
