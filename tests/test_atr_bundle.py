from datetime import datetime, timedelta, timezone

import pandas as pd

from daxlab.research.atr_bundle import build_atr001_bundle


def _bars() -> pd.DataFrame:
    start = datetime(2026, 9, 8, 6, 30, tzinfo=timezone.utc)
    rows = []
    close = 100.0
    for i in range(60):
        open_ = close
        close = open_ + (0.4 if i % 2 == 0 else -0.1)
        rows.append(
            {
                "datetime": start + timedelta(minutes=5 * i),
                "open": open_,
                "high": max(open_, close) + 1.0,
                "low": min(open_, close) - 1.0,
                "close": close,
            }
        )
    return pd.DataFrame(rows)


def _trade(entry: datetime) -> pd.DataFrame:
    return pd.DataFrame(
        [{
            "wf": 1,
            "date": "2026-09-08",
            "entry_time": entry,
            "orb_min": 15,
            "entry_mode": "retest",
            "side": "long",
            "r": 1.5,
        }]
    )


def test_bundle_is_descriptive_and_causal():
    bars = _bars()
    entry = datetime(2026, 9, 8, 8, 30, tzinfo=timezone.utc)
    out = build_atr001_bundle(bars, _trade(entry))
    assert len(out) == 1
    assert bool(out.iloc[0]["feature_eligible"])
    assert out.iloc[0]["atr_observation_time"] < entry
    assert out.iloc[0]["or_confirmation_time"] < entry
    assert out.iloc[0]["or_atr_ratio"] > 0
    assert out.iloc[0]["r"] == 1.5


def test_entry_bar_pollution_does_not_change_feature():
    bars = _bars()
    entry = datetime(2026, 9, 8, 8, 30, tzinfo=timezone.utc)
    before = build_atr001_bundle(bars, _trade(entry)).iloc[0]
    polluted = bars.copy()
    polluted.loc[polluted["datetime"] >= entry, ["high", "low", "close"]] = [9999.0, 1.0, 5000.0]
    after = build_atr001_bundle(polluted, _trade(entry)).iloc[0]
    assert after["atr14_points"] == before["atr14_points"]
    assert after["or_atr_ratio"] == before["or_atr_ratio"]


def test_or_must_be_complete_before_entry():
    bars = _bars()
    # 09:10 Berlin = 07:10 UTC, before an OR15 can be complete at 09:15.
    entry = datetime(2026, 9, 8, 7, 10, tzinfo=timezone.utc)
    out = build_atr001_bundle(bars, _trade(entry))
    assert not bool(out.iloc[0]["feature_eligible"])
