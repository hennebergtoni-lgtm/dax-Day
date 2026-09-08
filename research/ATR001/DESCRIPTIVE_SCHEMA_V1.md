# ATR001 — Descriptive Measurement Schema V1

Status: RESEARCH ONLY. No V11.2 mutation. No threshold promotion.

## Purpose
Measure volatility context on the reproduced V11.2 normal-cost trade ledger before any new selector is tested.

## Per-trade fields
- wf
- date
- entry_time
- orb_min
- entry_mode
- side
- r
- atr14_points
- atr_observation_time
- or_points
- or_atr_ratio
- feature_eligible
- rejection_reason

## Causal cutoff
ATR must be the latest observation derived from completed M5 bars strictly before `entry_time`. OR/ATR is eligible only when the selected OR is already complete before entry. No entry-bar OHLC is used.

## Descriptive summaries
Report only distributions and coverage at this stage:
- eligible / rejected trade counts and rejection reasons
- ATR14 median and broad quantiles by calendar year
- OR/ATR median and broad quantiles by calendar year
- same summaries by OR5/OR15 and breakout/retest
- coarse WF-era coverage

Any full-sample quantile is DESCRIPTIVE_ONLY and may not become a trading threshold. If train-derived bins are later tested, boundaries are recomputed independently inside every WF training slice.

## Promotion
Blocked. Descriptive statistics do not modify the reference, registry deployment state, Paper, or Live eligibility.
