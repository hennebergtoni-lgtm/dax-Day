"""Contracts for the recovered 2014-2019 DAX CSV research dataset."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from daxlab.data.fingerprint import fingerprint_ohlc
from daxlab.data.validation import validate_ohlc

EXPECTED_DAILY_FILES = 1673
EXPECTED_M5_ROWS_PER_FILE = 288
EXPECTED_SESSION_BARS_PER_DAY = 103
EXPECTED_SESSION_ROWS = EXPECTED_DAILY_FILES * EXPECTED_SESSION_BARS_PER_DAY
SESSION_START = "09:00"
SESSION_END = "17:30"
SESSION_TIMEZONE = "Europe/Berlin"
_REQUIRED_COLUMNS = ("timestamp_utc", "open", "high", "low", "close")


@dataclass(frozen=True, slots=True)
class LegacyDatasetReport:
    files: int
    raw_rows: int
    session_days: int
    session_rows: int
    fingerprint: str


def _read_daily_m5(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = [column for column in _REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    if len(frame) != EXPECTED_M5_ROWS_PER_FILE:
        raise ValueError(
            f"{path.name}: expected {EXPECTED_M5_ROWS_PER_FILE} rows, found {len(frame)}"
        )

    frame = frame.loc[:, _REQUIRED_COLUMNS].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="raise")
    return frame


def load_recovered_m5(directory: str | Path) -> pd.DataFrame:
    """Load the exact daily M5 surface used by the recovered parity notebook."""
    source = Path(directory)
    files = sorted(source.glob("*.csv"))
    if len(files) != EXPECTED_DAILY_FILES:
        raise ValueError(f"expected {EXPECTED_DAILY_FILES} M5 files, found {len(files)}")

    raw = pd.concat((_read_daily_m5(path) for path in files), ignore_index=True)
    expected_raw_rows = EXPECTED_DAILY_FILES * EXPECTED_M5_ROWS_PER_FILE
    if len(raw) != expected_raw_rows:
        raise ValueError(f"expected {expected_raw_rows} raw M5 rows, found {len(raw)}")
    if raw["timestamp_utc"].duplicated().any():
        raise ValueError("duplicate UTC timestamps in recovered M5 dataset")
    return raw


def berlin_session(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the 09:00-17:30 Europe/Berlin session used by V11.2 parity."""
    timestamp = pd.to_datetime(raw["timestamp_utc"], utc=True, errors="raise")
    local = timestamp.dt.tz_convert(SESSION_TIMEZONE)
    minutes = local.dt.hour * 60 + local.dt.minute
    start = 9 * 60
    end = 17 * 60 + 30
    session = raw.loc[(minutes >= start) & (minutes <= end), _REQUIRED_COLUMNS].copy()
    session.index = pd.DatetimeIndex(
        pd.to_datetime(session.pop("timestamp_utc"), utc=True), name="timestamp_utc"
    )
    return session


def _audit_loaded_session(raw: pd.DataFrame, session: pd.DataFrame) -> LegacyDatasetReport:
    validation = validate_ohlc(session)
    if not validation.valid:
        raise ValueError(f"invalid recovered session data: {validation}")

    local_dates = session.index.tz_convert(SESSION_TIMEZONE).date
    session_days = len(set(local_dates))
    if session_days != EXPECTED_DAILY_FILES:
        raise ValueError(f"expected {EXPECTED_DAILY_FILES} session days, found {session_days}")
    if len(session) != EXPECTED_SESSION_ROWS:
        raise ValueError(f"expected {EXPECTED_SESSION_ROWS} session rows, found {len(session)}")

    return LegacyDatasetReport(
        files=EXPECTED_DAILY_FILES,
        raw_rows=len(raw),
        session_days=session_days,
        session_rows=len(session),
        fingerprint=fingerprint_ohlc(session),
    )


def load_audited_recovered_session(
    directory: str | Path,
) -> tuple[pd.DataFrame, LegacyDatasetReport]:
    """Load, sessionize, validate and fingerprint the recovered M5 surface once.

    This is the canonical reusable owner for consumers that need both the audited
    Berlin-session frame and its evidence report. It avoids rereading all daily
    CSV files merely to obtain the frame after ``audit_and_fingerprint_m5``.
    """
    raw = load_recovered_m5(directory)
    session = berlin_session(raw)
    return session, _audit_loaded_session(raw, session)


def audit_and_fingerprint_m5(directory: str | Path) -> LegacyDatasetReport:
    """Validate and fingerprint the recovered M5 session dataset deterministically."""
    _, report = load_audited_recovered_session(directory)
    return report
