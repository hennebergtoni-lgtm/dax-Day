from datetime import date

import pandas as pd

from daxlab.research.atr_wf import apply_frozen_regimes, fit_train_only_regimes


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"date": "2026-01-01", "atr14_points": 10.0, "or_atr_ratio": 1.0, "feature_eligible": True},
            {"date": "2026-01-02", "atr14_points": 20.0, "or_atr_ratio": 2.0, "feature_eligible": True},
            {"date": "2026-01-03", "atr14_points": 30.0, "or_atr_ratio": 3.0, "feature_eligible": True},
            {"date": "2026-01-04", "atr14_points": 9999.0, "or_atr_ratio": 9999.0, "feature_eligible": True},
        ]
    )


def test_future_oos_pollution_cannot_change_training_boundaries():
    features = _features()
    train = [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]
    before = fit_train_only_regimes(features, wf=1, train_days=train)
    polluted = features.copy()
    polluted.loc[polluted["date"] == "2026-01-04", ["atr14_points", "or_atr_ratio"]] = [-9999.0, -9999.0]
    after = fit_train_only_regimes(polluted, wf=1, train_days=train)
    assert after == before
    assert before.train_rows == 3


def test_frozen_boundaries_classify_oos_without_refit():
    features = _features()
    bounds = fit_train_only_regimes(
        features,
        wf=7,
        train_days=[date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
    )
    out = apply_frozen_regimes(features, bounds, oos_days=[date(2026, 1, 4)])
    assert len(out) == 1
    assert out.iloc[0]["atr_regime"] == "HIGH"
    assert out.iloc[0]["or_atr_regime"] == "HIGH"
    assert out.iloc[0]["regime_fit_wf"] == 7


def test_train_days_are_mandatory():
    try:
        fit_train_only_regimes(_features(), wf=1, train_days=[])
    except ValueError as exc:
        assert "train_days" in str(exc)
    else:
        raise AssertionError("expected empty training days to fail closed")
