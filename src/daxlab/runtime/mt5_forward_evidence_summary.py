"""Credential-free summary for MT5 read-only SHADOW forward evidence."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

_FORBIDDEN_KEYS = frozenset({"login", "password", "token", "secret", "email", "phone", "account_id"})


@dataclass(frozen=True, slots=True)
class ForwardEvidenceSummary:
    status: str
    heartbeat_count: int
    green_count: int
    blocked_count: int
    error_count: int
    stopped_count: int
    max_processed_total: int | None
    total_new_decisions: int
    total_duplicates_suppressed: int
    blocker_counts: tuple[tuple[str, int], ...]
    gap_reports_with_review_required: int
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def summarize_forward_evidence(
    heartbeats: Iterable[Mapping[str, Any]],
    *,
    gap_reports: Iterable[Any] = (),
) -> ForwardEvidenceSummary:
    items = tuple(heartbeats)
    blocker_counts: dict[str, int] = {}
    green = blocked = error = stopped = 0
    max_processed: int | None = None
    new_decisions = 0
    duplicates = 0

    for heartbeat in items:
        _assert_credential_free(heartbeat)
        if heartbeat.get("execution_capability") != "NONE":
            raise ValueError("heartbeat execution_capability must be NONE")
        if heartbeat.get("order_execution_enabled") is not False:
            raise ValueError("heartbeat order_execution_enabled must be false")

        status = heartbeat.get("status")
        if status == "GREEN":
            green += 1
        elif status == "BLOCKED":
            blocked += 1
        elif status == "ERROR":
            error += 1
        elif status == "STOPPED":
            stopped += 1
        else:
            raise ValueError("unsupported heartbeat status")

        processed = heartbeat.get("processed_total")
        if processed is not None:
            if type(processed) is not int or processed < 0:
                raise ValueError("processed_total must be non-negative integer or null")
            max_processed = processed if max_processed is None else max(max_processed, processed)

        nd = heartbeat.get("new_decisions", 0)
        ds = heartbeat.get("duplicates_suppressed", 0)
        if type(nd) is not int or nd < 0 or type(ds) is not int or ds < 0:
            raise ValueError("decision counters must be non-negative integers")
        new_decisions += nd
        duplicates += ds

        blockers = heartbeat.get("blockers", [])
        if not isinstance(blockers, list):
            raise ValueError("heartbeat blockers must be a list")
        for blocker in blockers:
            if not isinstance(blocker, str) or not blocker.strip():
                raise ValueError("heartbeat blocker must be non-empty string")
            blocker_counts[blocker] = blocker_counts.get(blocker, 0) + 1

    review_required = 0
    for report in gap_reports:
        if getattr(report, "execution_capability", None) != "NONE":
            raise ValueError("gap report execution_capability must be NONE")
        if getattr(report, "order_execution_enabled", None) is not False:
            raise ValueError("gap report order_execution_enabled must be false")
        if bool(getattr(report, "requires_human_review", False)):
            review_required += 1

    if error:
        overall = "ERROR_PRESENT"
    elif blocked:
        overall = "BLOCKED_PRESENT"
    elif review_required:
        overall = "REVIEW_REQUIRED"
    elif items and green == len(items):
        overall = "GREEN_ONLY"
    elif items:
        overall = "MIXED_NON_ERROR"
    else:
        overall = "NO_EVIDENCE"

    return ForwardEvidenceSummary(
        status=overall,
        heartbeat_count=len(items),
        green_count=green,
        blocked_count=blocked,
        error_count=error,
        stopped_count=stopped,
        max_processed_total=max_processed,
        total_new_decisions=new_decisions,
        total_duplicates_suppressed=duplicates,
        blocker_counts=tuple(sorted(blocker_counts.items())),
        gap_reports_with_review_required=review_required,
    )


def _assert_credential_free(payload: Mapping[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if str(key).lower() in _FORBIDDEN_KEYS:
                    raise ValueError(f"forbidden evidence key: {key}")
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    walk(payload)
