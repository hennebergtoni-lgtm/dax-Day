"""Common contract for causal research feature bundles."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class FeatureBundleContract:
    family_id: str
    entry_time_col: str
    state_time_cols: tuple[str, ...]
    expected_rows: int | None = None
    strict_before_entry: bool = True


def validate_feature_bundle(bundle: pd.DataFrame, contract: FeatureBundleContract) -> None:
    """Fail closed on missing rows/columns or causal timestamp violations."""
    required = {contract.entry_time_col, *contract.state_time_cols}
    missing = sorted(required - set(bundle.columns))
    if missing:
        raise ValueError(f"feature bundle missing required columns: {missing}")
    if contract.expected_rows is not None and len(bundle) != contract.expected_rows:
        raise ValueError(
            f"feature bundle row-count mismatch: expected={contract.expected_rows} observed={len(bundle)}"
        )
    if bundle[contract.entry_time_col].isna().any():
        raise ValueError("feature bundle contains missing entry times")

    entry = pd.to_datetime(bundle[contract.entry_time_col], utc=True)
    for column in contract.state_time_cols:
        if bundle[column].isna().any():
            raise ValueError(f"feature bundle contains missing state times: {column}")
        state = pd.to_datetime(bundle[column], utc=True)
        invalid = state >= entry if contract.strict_before_entry else state > entry
        if bool(invalid.any()):
            raise ValueError(f"feature bundle causality violation in {column}")
