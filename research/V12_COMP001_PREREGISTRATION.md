# V12 COMP001 preregistration

Date: 2026-09-09
Status: PREREGISTERED BEFORE FORMAL ISOLATED TEST
Branch: v12-prepaper-optimization

## Purpose
Resolve the definition drift detected during milestone 246 before any formal COMP001 profitability evaluation is run.

## Frozen hypothesis
Short-horizon pre-signal realized range compression or expansion relative to causal ATR14 may identify setup environments distinct from ATR001.

## Exact causal feature
For each frozen V11.2 opportunity at its `signal_time` decision bar:

1. use only fully closed M5 bars available at or before the signal decision;
2. compute True Range for each bar using the previous bar close;
3. compute `recent_tr_mean_3` as the arithmetic mean of the three most recent completed True Range observations ending on the signal bar;
4. compute Wilder ATR14 causally from completed bars only, ending on the same signal bar;
5. define `comp001_ratio = recent_tr_mean_3 / atr14`;
6. insufficient warm-up or non-positive ATR14 returns MISSING and cannot silently pass.

No future bar, entry bar information after the signal decision, MFE/MAE, exit information, or volume is allowed in the feature.

## Regime assignment
Within each walk-forward window:

- derive the 33rd and 67th percentile boundaries from TRAIN opportunities only;
- freeze those two boundaries before evaluating OOS;
- classify OOS opportunities as:
  - COMPRESSED: ratio < train q33
  - NORMAL: train q33 <= ratio < train q67
  - EXPANDED: ratio >= train q67

No global OOS quantiles and no post-hoc threshold tuning are permitted.

## Evaluation contract
Evaluate COMPRESSED / NORMAL / EXPANDED in isolation against the frozen V11.2 OOS opportunity/trade evidence. Report at minimum:

- trade count
- PF
- Return-R
- Avg-R
- Max DD-R
- yearly stability
- WF positive/negative counts
- Normal costs and exact stress replay when available

A favorable bucket is research evidence only. It does not become a production filter without fresh proof, stability review, and explicit promotion.

## Relationship to prior implementation
The existing engineering primitive `current TR / mean prior TR` is retained only as historical/diagnostic implementation evidence. It is not the formal COMP001 hypothesis test defined here.

No production promotion. No Paper start. No LIVE authorization. `order_execution_enabled=false` remains unchanged.
