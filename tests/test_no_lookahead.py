import pandas as pd
import pytest

from daxlab.research.no_lookahead import assert_prefix_stable


def _data() -> pd.DataFrame:
    index = pd.date_range("2026-01-01 09:00", periods=6, freq="min")
    return pd.DataFrame({"close": [100, 101, 99, 102, 103, 104]}, index=index)


def test_causal_rolling_feature_passes() -> None:
    def feature(df: pd.DataFrame) -> pd.Series:
        return df["close"].rolling(3).mean()

    assert_prefix_stable(feature, _data())


def test_future_dependent_feature_fails() -> None:
    def leaked_feature(df: pd.DataFrame) -> pd.Series:
        return df["close"].shift(-1)

    with pytest.raises(AssertionError):
        assert_prefix_stable(leaked_feature, _data())
