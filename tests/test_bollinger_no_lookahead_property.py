import numpy as np
import pandas as pd
import pandas.testing as pdt

from daxlab.research.bollinger_filter import add_bollinger_state


def test_future_price_pollution_cannot_change_past_bollinger_state():
    rng = np.random.default_rng(42)
    n = 300
    bars = pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-01 09:00", periods=n, freq="5min"),
            "close": 10000 + np.cumsum(rng.normal(0, 4, n)),
        }
    )
    cutoff = 180
    clean = add_bollinger_state(bars, window=20)

    polluted_bars = bars.copy()
    polluted_bars.loc[cutoff:, "close"] = polluted_bars.loc[cutoff:, "close"] + 5000
    polluted = add_bollinger_state(polluted_bars, window=20)

    cols = ["bb_mid", "bb_std", "bb_upper", "bb_lower", "bb_bandwidth", "bb_position"]
    pdt.assert_frame_equal(
        clean.loc[: cutoff - 1, cols].reset_index(drop=True),
        polluted.loc[: cutoff - 1, cols].reset_index(drop=True),
        check_exact=True,
    )
