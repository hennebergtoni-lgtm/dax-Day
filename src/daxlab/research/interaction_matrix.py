from collections.abc import Callable, Mapping
from dataclasses import dataclass

import pandas as pd


MaskFn = Callable[[pd.DataFrame], pd.Series]


@dataclass(frozen=True)
class InteractionResult:
    name: str
    trades: int
    return_r: float
    win_rate: float | None


def compose_masks(frame: pd.DataFrame, masks: Mapping[str, MaskFn]) -> pd.DataFrame:
    """Return one boolean column per research component plus a combined mask.

    This helper is research-only. It does not mutate strategy parameters, perform
    optimization, or promote any component to live execution.
    """
    out = pd.DataFrame(index=frame.index)
    combined = pd.Series(True, index=frame.index)
    for name, fn in masks.items():
        mask = fn(frame).reindex(frame.index).fillna(False).astype(bool)
        out[name] = mask
        combined &= mask
    out["combined"] = combined
    return out


def summarize_mask(frame: pd.DataFrame, mask: pd.Series, *, name: str, r_col: str = "r") -> InteractionResult:
    selected = frame.loc[mask.fillna(False).astype(bool)]
    if selected.empty:
        return InteractionResult(name=name, trades=0, return_r=0.0, win_rate=None)
    r = pd.to_numeric(selected[r_col], errors="raise").astype(float)
    return InteractionResult(
        name=name,
        trades=len(selected),
        return_r=float(r.sum()),
        win_rate=float((r > 0).mean()),
    )
