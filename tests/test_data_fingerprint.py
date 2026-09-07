import pandas as pd

from daxlab.data.fingerprint import fingerprint_ohlc


def _sample() -> pd.DataFrame:
    index = pd.date_range("2026-01-01 09:00", periods=3, freq="min")
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0],
            "close": [101.0, 102.0, 103.0],
        },
        index=index,
    )


def test_fingerprint_is_deterministic() -> None:
    data = _sample()
    assert fingerprint_ohlc(data) == fingerprint_ohlc(data.copy())


def test_fingerprint_changes_when_price_changes() -> None:
    original = _sample()
    changed = _sample()
    changed.loc[changed.index[-1], "close"] = 103.5
    assert fingerprint_ohlc(original) != fingerprint_ohlc(changed)
