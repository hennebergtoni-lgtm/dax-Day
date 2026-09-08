# V6 Causal Timestamp Contract

Status: BINDING RESEARCH CONTRACT

## Core rule
Every research feature used to qualify, reject, classify or manage a V11.2 setup must be timestamped by the latest market information required to compute it.

For entry-eligibility use, `feature_state_time < entry_time` is mandatory.

If a feature depends on a completed bar, the state becomes available only after that bar is closed. If a higher-timeframe feature is used, only a fully completed HTF bar may contribute unless a separate intrabar hypothesis is explicitly declared and tested.

## Required fields for feature evidence
Each material feature family must be able to expose or reconstruct:
- `feature_id`
- `source_timeframe`
- `state_time`
- `entry_time` or decision time being evaluated
- `causality_pass`
- `lookahead_reason` when blocked
- source observations/bars required to compute the feature

## V11.2 binding
The frozen execution semantics remain authoritative:
- breakout/retest confirmation is based on completed candles;
- entry occurs at the next candle open;
- an entry filter may only use information strictly known before that `entry_time`.

## Higher-timeframe rule
A 15m/30m/60m state can only be used once the corresponding HTF candle is complete. Partial HTF aggregation is not equivalent to a completed HTF state and must not be silently substituted.

## Structural / swing rule
Pivots, impulses, Fibonacci anchors, liquidity sweeps and structure labels must not be confirmed by future bars unless their state time is moved forward to the actual confirmation time. A hindsight label cannot be attached retrospectively to an earlier decision.

## Session / previous-day rule
Previous-day or completed-session statistics are eligible from the next session onward. Same-day statistics must respect the exact information cutoff at decision time.

## Failure policy
Any feature row with unknown, equal-to-entry, future, repainting or otherwise ambiguous state timing fails closed for eligibility testing. It may remain as descriptive diagnostics but cannot be counted as causal strategy evidence.

## Accelerator parity
Accelerated/vectorized feature generation must preserve the exact same timestamp contract. Speed never relaxes causality. Each accelerated family requires exact spot checks before its results may be treated as research evidence.
