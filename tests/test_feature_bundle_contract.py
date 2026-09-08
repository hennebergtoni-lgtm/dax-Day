import pandas as pd
import pytest

from daxlab.research.feature_bundle import FeatureBundleContract, validate_feature_bundle


def _bundle() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time": ["2026-09-08T09:10:00+02:00", "2026-09-08T09:15:00+02:00"],
            "state_time": ["2026-09-08T09:05:00+02:00", "2026-09-08T09:10:00+02:00"],
            "feature": [1.0, 2.0],
        }
    )


def test_feature_bundle_accepts_strictly_prior_state() -> None:
    contract = FeatureBundleContract(
        family_id="TEST001",
        entry_time_col="entry_time",
        state_time_cols=("state_time",),
        expected_rows=2,
    )
    validate_feature_bundle(_bundle(), contract)


def test_feature_bundle_rejects_equal_or_future_state() -> None:
    bundle = _bundle()
    bundle.loc[0, "state_time"] = bundle.loc[0, "entry_time"]
    contract = FeatureBundleContract(
        family_id="TEST001",
        entry_time_col="entry_time",
        state_time_cols=("state_time",),
    )
    with pytest.raises(ValueError, match="causality violation"):
        validate_feature_bundle(bundle, contract)


def test_feature_bundle_rejects_row_count_drift() -> None:
    contract = FeatureBundleContract(
        family_id="TEST001",
        entry_time_col="entry_time",
        state_time_cols=("state_time",),
        expected_rows=3,
    )
    with pytest.raises(ValueError, match="row-count mismatch"):
        validate_feature_bundle(_bundle(), contract)
