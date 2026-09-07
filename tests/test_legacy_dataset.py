from pathlib import Path

import pandas as pd
import pytest

from daxlab.data.legacy_dataset import (
    EXPECTED_M5_ROWS_PER_FILE,
    _read_daily_m5,
    berlin_session,
)


def _daily_frame(day: str) -> pd.DataFrame:
    idx = pd.date_range(day, periods=EXPECTED_M5_ROWS_PER_FILE, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp_utc": idx,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1.0,
        }
    )


def test_read_daily_m5_accepts_exact_288_rows(tmp_path: Path):
    path = tmp_path / "2019-12-30.csv"
    _daily_frame("2019-12-30").to_csv(path, index=False)

    loaded = _read_daily_m5(path)

    assert len(loaded) == 288
    assert list(loaded.columns) == ["timestamp_utc", "open", "high", "low", "close"]


def test_read_daily_m5_rejects_row_drift(tmp_path: Path):
    path = tmp_path / "bad.csv"
    _daily_frame("2019-12-30").iloc[:-1].to_csv(path, index=False)

    with pytest.raises(ValueError, match="expected 288 rows"):
        _read_daily_m5(path)


def test_berlin_session_has_103_inclusive_m5_bars_in_winter():
    raw = _daily_frame("2019-12-30")

    session = berlin_session(raw)

    assert len(session) == 103
    local = session.index.tz_convert("Europe/Berlin")
    assert local[0].strftime("%H:%M") == "09:00"
    assert local[-1].strftime("%H:%M") == "17:30"
