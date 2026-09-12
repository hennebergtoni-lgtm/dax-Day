"""Bind the audited recovered DE40 M5 dataset owner to CAND-001 replay.

This module does not implement a second loader, session filter or strategy engine.
It composes the canonical recovered-data owner with the descriptive CAND-001
historical replay and fails closed if the freshly audited dataset fingerprint does
not match the explicitly expected audited identity.
"""
from __future__ import annotations

from pathlib import Path

from daxlab.data.legacy_dataset import load_audited_recovered_session
from daxlab.research.cand001_historical_replay import (
    Cand001HistoricalReplayEvidence,
    candles_from_legacy_session,
    run_cand001_historical_descriptive_replay,
)
from daxlab.runtime.candidate_config import Cand001Config


def run_audited_recovered_m5_cand001_replay(
    directory: str | Path,
    *,
    expected_dataset_fingerprint: str,
    config: Cand001Config | None = None,
) -> Cand001HistoricalReplayEvidence:
    """Replay the freshly audited recovered Berlin-session M5 surface.

    ``expected_dataset_fingerprint`` must come from an authoritative audited
    manifest/evidence source. This function intentionally does not guess or
    silently substitute a dataset identity.
    """
    if not isinstance(expected_dataset_fingerprint, str) or len(expected_dataset_fingerprint) != 64:
        raise ValueError("expected_dataset_fingerprint must be a 64-character sha256")
    try:
        int(expected_dataset_fingerprint, 16)
    except ValueError as exc:
        raise ValueError("expected_dataset_fingerprint must be hexadecimal") from exc

    session, dataset_report = load_audited_recovered_session(directory)
    if dataset_report.fingerprint != expected_dataset_fingerprint:
        raise ValueError(
            "audited recovered M5 fingerprint mismatch: "
            f"expected={expected_dataset_fingerprint} observed={dataset_report.fingerprint}"
        )

    candles = candles_from_legacy_session(session)
    evidence = run_cand001_historical_descriptive_replay(
        candles,
        dataset_fingerprint=dataset_report.fingerprint,
        config=config,
    )
    if evidence.report.processed_bars != dataset_report.session_rows:
        raise RuntimeError("historical replay bar count drift from audited session report")
    if evidence.report.processed_sessions != dataset_report.session_days:
        raise RuntimeError("historical replay session count drift from audited session report")
    return evidence
