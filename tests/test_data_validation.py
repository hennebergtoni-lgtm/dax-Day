import pandas as pd

from daxlab.data.validation import validate_ohlc


def test_clean_ohlc_is_valid() -> None:
    index = pd.date_range("2026-01-01 09:00", periods=2, freq="min")
    df = pd.DataFrame(
        {"open": [100, 101], "high": [102, 103], "low": [99, 100], "close": [101, 102]},
        index=index,
    )
    report = validate_ohlc(df)
    assert report.valid
    assert report.ohlc_errors == 0


def test_impossible_high_low_is_rejected() -> None:
    index = pd.date_range("2026-01-01 09:00", periods=1, freq="min")
    df = pd.DataFrame({"open": [100], "high": [99], "low": [101], "close": [100]}, index=index)
    report = validate_ohlc(df)
    assert not report.valid
    assert report.ohlc_errors > 0
