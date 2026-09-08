
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from daxlab.research.bollinger_filter import (
    add_bollinger_state,
    align_last_completed_state,
    classify_htf_regime,
    resample_completed_htf,
)


def build_bundle(
    bars: pd.DataFrame,
    trades: pd.DataFrame,
    *,
    time_col: str = "datetime",
    entry_time_col: str = "entry_time",
    htf_minutes: tuple[int, ...] = (15, 30, 60),
) -> pd.DataFrame:
    """Attach causal M5 BB state plus optional completed-HTF BB regimes to trades."""
    m5 = add_bollinger_state(bars, time_col=time_col)
    state_cols = [
        time_col,
        "bb_mid",
        "bb_upper",
        "bb_lower",
        "bb_bandwidth",
        "bb_position",
    ]
    out = align_last_completed_state(
        trades,
        m5[state_cols],
        entry_time_col=entry_time_col,
        state_time_col=time_col,
    ).rename(
        columns={
            time_col: "bb_m5_state_time",
            "bb_mid": "bb_m5_mid",
            "bb_upper": "bb_m5_upper",
            "bb_lower": "bb_m5_lower",
            "bb_bandwidth": "bb_m5_bandwidth",
            "bb_position": "bb_m5_position",
        }
    )

    for minutes in htf_minutes:
        htf = resample_completed_htf(
            bars[[time_col, "close"]],
            time_col=time_col,
            minutes=minutes,
        )
        htf[f"bb_{minutes}m_regime"] = classify_htf_regime(htf, lookback=3)
        keep = htf[
            [time_col, "bb_bandwidth", "bb_position", f"bb_{minutes}m_regime"]
        ].rename(
            columns={
                time_col: f"bb_{minutes}m_state_time",
                "bb_bandwidth": f"bb_{minutes}m_bandwidth",
                "bb_position": f"bb_{minutes}m_position",
            }
        )
        out = pd.merge_asof(
            out.sort_values(entry_time_col),
            keep.sort_values(f"bb_{minutes}m_state_time"),
            left_on=entry_time_col,
            right_on=f"bb_{minutes}m_state_time",
            direction="backward",
            allow_exact_matches=True,
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build causal BB001 feature bundle.")
    parser.add_argument("--bars", required=True, help="CSV with datetime/OHLC columns.")
    parser.add_argument("--trades", required=True, help="CSV with entry_time column.")
    parser.add_argument("--out", required=True, help="Output CSV path.")
    args = parser.parse_args()

    bars = pd.read_csv(args.bars)
    trades = pd.read_csv(args.trades)
    bars["datetime"] = pd.to_datetime(bars["datetime"])
    trades["entry_time"] = pd.to_datetime(trades["entry_time"])
    bundle = build_bundle(bars, trades)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    bundle.to_csv(args.out, index=False)
    print(f"[BB001] wrote {len(bundle)} rows -> {args.out}")


if __name__ == "__main__":
    main()
