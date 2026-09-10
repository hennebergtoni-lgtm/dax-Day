"""Fail-closed anchor reconciliation for resumed MT5 SHADOW feeds."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

from daxlab.runtime.mt5_readonly import Mt5Bar
from daxlab.runtime.shadow_soak import SoakCheckpoint, bar_fingerprint, verify_soak_checkpoint


@dataclass(frozen=True, slots=True)
class ShadowResumeAnchorResult:
    fresh_start: bool
    anchor_fingerprint: str | None
    anchor_index: int | None
    feed_bar_count: int
    catchup_bar_count: int
    ordered_feed_sha256: str
    report_sha256: str
    safe_to_resume: bool = True
    execution_capability: str = "NONE"
    order_execution_enabled: bool = False


def reconcile_shadow_resume_anchor(
    bars: Iterable[Mt5Bar],
    *,
    checkpoint: SoakCheckpoint | None,
) -> ShadowResumeAnchorResult:
    """Locate the persisted last-bar identity exactly once in the current feed.

    Fresh starts require no anchor. Resumes fail closed if the persisted anchor is missing or
    ambiguous. Catch-up begins strictly after the anchor; this helper never skips evidence or
    authorizes orders.
    """
    ordered = tuple(bars)
    fingerprints = tuple(bar_fingerprint(bar) for bar in ordered)
    ordered_feed_sha256 = _hash({"ordered_bar_fingerprints": list(fingerprints)})

    if checkpoint is None:
        payload = {
            "fresh_start": True,
            "anchor_fingerprint": None,
            "anchor_index": None,
            "feed_bar_count": len(ordered),
            "catchup_bar_count": len(ordered),
            "ordered_feed_sha256": ordered_feed_sha256,
        }
        return ShadowResumeAnchorResult(
            fresh_start=True,
            anchor_fingerprint=None,
            anchor_index=None,
            feed_bar_count=len(ordered),
            catchup_bar_count=len(ordered),
            ordered_feed_sha256=ordered_feed_sha256,
            report_sha256=_hash(payload),
        )

    verify_soak_checkpoint(checkpoint)
    anchor = checkpoint.last_bar_fingerprint
    if checkpoint.processed_count == 0 and anchor is None:
        payload = {
            "fresh_start": True,
            "anchor_fingerprint": None,
            "anchor_index": None,
            "feed_bar_count": len(ordered),
            "catchup_bar_count": len(ordered),
            "ordered_feed_sha256": ordered_feed_sha256,
        }
        return ShadowResumeAnchorResult(
            fresh_start=True,
            anchor_fingerprint=None,
            anchor_index=None,
            feed_bar_count=len(ordered),
            catchup_bar_count=len(ordered),
            ordered_feed_sha256=ordered_feed_sha256,
            report_sha256=_hash(payload),
        )
    if anchor is None:
        raise RuntimeError("resume checkpoint anchor missing")

    matches = [index for index, value in enumerate(fingerprints) if value == anchor]
    if not matches:
        raise RuntimeError("resume checkpoint anchor not found in current feed")
    if len(matches) != 1:
        raise RuntimeError("resume checkpoint anchor is ambiguous in current feed")

    anchor_index = matches[0]
    catchup = len(ordered) - anchor_index - 1
    payload = {
        "fresh_start": False,
        "anchor_fingerprint": anchor,
        "anchor_index": anchor_index,
        "feed_bar_count": len(ordered),
        "catchup_bar_count": catchup,
        "ordered_feed_sha256": ordered_feed_sha256,
    }
    return ShadowResumeAnchorResult(
        fresh_start=False,
        anchor_fingerprint=anchor,
        anchor_index=anchor_index,
        feed_bar_count=len(ordered),
        catchup_bar_count=catchup,
        ordered_feed_sha256=ordered_feed_sha256,
        report_sha256=_hash(payload),
    )


def bars_after_resume_anchor(
    bars: Iterable[Mt5Bar],
    *,
    result: ShadowResumeAnchorResult,
) -> tuple[Mt5Bar, ...]:
    """Return the fresh/catch-up slice proven by a prior anchor reconciliation result."""
    if result.execution_capability != "NONE" or result.order_execution_enabled:
        raise RuntimeError("resume anchor result unexpectedly gained execution capability")
    ordered = tuple(bars)
    if result.feed_bar_count != len(ordered):
        raise RuntimeError("resume anchor feed length changed after reconciliation")
    observed_sha = _hash(
        {"ordered_bar_fingerprints": [bar_fingerprint(bar) for bar in ordered]}
    )
    if observed_sha != result.ordered_feed_sha256:
        raise RuntimeError("resume anchor feed changed after reconciliation")
    if result.fresh_start:
        return ordered
    if result.anchor_index is None:
        raise RuntimeError("resume anchor index missing")
    return ordered[result.anchor_index + 1 :]


def _hash(value: dict[str, object]) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()
