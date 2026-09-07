"""Causality helpers used to prevent research features from seeing future bars."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

FeatureFn = Callable[[pd.DataFrame], pd.Series]


def assert_prefix_stable(feature_fn: FeatureFn, data: pd.DataFrame) -> None:
    """Assert that extending data does not change already-known feature values.

    This catches a broad class of accidental look-ahead implementations. Feature functions
    may return NaN during warm-up; equal NaNs are treated as equal.
    """
    if len(data) < 2:
        raise ValueError("at least two rows are required for a prefix-stability test")

    full = feature_fn(data)
    if not full.index.equals(data.index):
        raise AssertionError("feature output index must equal input index")

    for end in range(1, len(data)):
        prefix = data.iloc[:end]
        prefix_feature = feature_fn(prefix)
        expected = full.iloc[:end]
        pd.testing.assert_series_equal(prefix_feature, expected, check_names=False)
