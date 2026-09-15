from pathlib import Path

import pandas as pd
import pytest

import daxlab.data.legacy_dataset as legacy_dataset
from daxlab.data.fingerprint import fingerprint_ohlc
from daxlab.research.cand001_historical_replay import EVIDENCE_CLASS
from daxlab.research.cand001_recovered_m5_replay import (
    run_audited_recovered_m5_cand001_replay,
)


def _daily_frame(day: str) -> pd.DataFrame:
    index = pd.date_range(day, periods=288, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp_utc": index,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
        }
    )


def _small_audited_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(legacy_dataset, "EXPECTED_DAILY_FILES", 1)
    monkeypatch.setattr(legacy_dataset, "EXPECTED_SESSION_ROWS", 103)

    raw = _daily_frame("2019-12-30")
    raw.to_csv(tmp_path / "2019-12-30.csv", index=False)
    expected_session = legacy_dataset.berlin_session(raw)
    assert len(expected_session) == 103
    return fingerprint_ohlc(expected_session)


def test_recovered_loader_to_session_to_cand001_replay_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_fingerprint = _small_audited_fixture(tmp_path, monkeypatch)

    evidence = run_audited_recovered_m5_cand001_replay(
        tmp_path,
        expected_dataset_fingerprint=expected_fingerprint,
    )

    report = evidence.report
    assert report.evidence_class == EVIDENCE_CLASS == "HISTORICAL_DESCRIPTIVE"
    assert report.dataset_fingerprint == expected_fingerprint
    assert report.processed_bars == 103
    assert report.processed_sessions == 1
    assert report.execution_capability == "NONE"
    assert report.order_execution_enabled is False


def test_recovered_replay_fails_closed_on_audited_fingerprint_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_fingerprint = _small_audited_fixture(tmp_path, monkeypatch)
    wrong = "0" * 64
    assert wrong != expected_fingerprint

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        run_audited_recovered_m5_cand001_replay(
            tmp_path,
            expected_dataset_fingerprint=wrong,
        )


def test_recovered_replay_rejects_invalid_expected_identity_without_loading(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="64-character sha256"):
        run_audited_recovered_m5_cand001_replay(
            tmp_path,
            expected_dataset_fingerprint="not-a-sha",
        )
