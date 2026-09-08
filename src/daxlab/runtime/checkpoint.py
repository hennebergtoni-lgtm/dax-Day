"""Checkpoint provenance for deterministic replay restart/resume."""

from __future__ import annotations

from dataclasses import dataclass

from daxlab.runtime.manifests import DecisionLogManifest, RunManifest


@dataclass(frozen=True, slots=True)
class ReplayCheckpoint:
    run_manifest_fingerprint: str
    processed_candles: int
    last_event_time_iso: str | None
    decision_log_fingerprint: str

    @classmethod
    def build(
        cls,
        *,
        run_manifest: RunManifest,
        processed_candles: int,
        last_event_time_iso: str | None,
        decision_log: DecisionLogManifest,
    ) -> ReplayCheckpoint:
        if processed_candles < 0:
            raise ValueError("processed_candles must be non-negative")
        return cls(
            run_manifest_fingerprint=run_manifest.manifest_fingerprint,
            processed_candles=processed_candles,
            last_event_time_iso=last_event_time_iso,
            decision_log_fingerprint=decision_log.decision_ids_fingerprint,
        )


def assert_resume_compatible(checkpoint: ReplayCheckpoint, run_manifest: RunManifest) -> None:
    """Prevent resumed replay from mixing data, engine, config or mode identities."""
    if checkpoint.run_manifest_fingerprint != run_manifest.manifest_fingerprint:
        raise RuntimeError("replay checkpoint run-manifest mismatch")
