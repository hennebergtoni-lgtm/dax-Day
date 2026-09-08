# ATR001 Research Contract

Status: RESEARCH / PROMOTION BLOCKED
Date: 2026-09-08
Baseline: V112_REFERENCE_V1 (immutable)

## Purpose
Re-test the retained legacy clue that opening-range size relative to pre-entry volatility may identify useful DAX intraday regimes. This contract does not modify V11.2 and does not treat any historical OR/ATR threshold as validated.

## Milestone position
ATR001 is the next regime-layer research family after the clean V11.2 reference reproduction and the descriptive FIB001 work. Decision order remains DATA SAFE -> REGIME -> STRUCTURE -> ENTRY -> RISK -> SIGNAL.

## Predeclared causal feature
For each candidate decision time, compute:

`or_atr_ratio = opening_range_points / atr14_points`

where:
- `opening_range_points` is the completed OR high minus completed OR low for the variant's OR length (5m or 15m),
- `atr14_points` is Wilder-style ATR(14) from completed M5 candles only,
- the ATR observation must be available strictly before the V11.2 entry time,
- no entry-bar high/low/close or later candle may contribute,
- all timestamps are timezone-aware and preserve Europe/Berlin session semantics.

The implementation must expose the exact ATR observation timestamp so causality can be audited.

## Legacy thresholds are not proof
V11.2 contains historical OR/ATR grid states `none`, `above0.20`, and `between0.20-0.60`. These are retained as LEGACY_OBSERVATION only. They may be measured for reproduction/diagnostics but cannot count as independent promotion evidence.

No new threshold may be selected from full OOS performance and then relabelled as predeclared.

## Stage plan
1. CAUSALITY_TESTED: implement ATR/OR feature with timestamp invariants, future-pollution tests, DST coverage and zero/invalid ATR fail-closed behavior.
2. DESCRIPTIVE: measure coverage/distribution on frozen reference trades without filtering or changing trades.
3. TRAIN_DERIVED hypotheses: any threshold discovery must use training data only and record provenance.
4. OOS/WF: evaluate predeclared/train-derived regimes on untouched OOS windows using the canonical rolling 45/20/20 schedule.
5. COST_STRESSED: normal, 1.5x and 2x costs.
6. STABILITY: year/WF coverage, parameter-neighborhood sensitivity, minimum sample requirements and no single-period dependence.
7. Only then can ATR001 be considered for VALIDATED; DEPLOYABLE additionally requires prospective evidence.

## Required comparisons
At minimum report:
- unfiltered frozen V11.2 reference,
- legacy `above0.20`,
- legacy `between0.20-0.60`,
- any independently predeclared or train-derived candidate,
- OR5 and OR15 separately,
- breakout and retest separately where sample size permits.

Report trade count, total R, AvgR, PF, max drawdown, positive/negative WF count and cost-stress behavior. Lower trade count must be shown explicitly; PF alone is insufficient.

## Fail-closed rules
Reject or mark feature unavailable when:
- fewer than 14 valid prior true-range observations exist,
- ATR is non-finite or <= 0,
- OR is incomplete,
- ATR observation timestamp is not strictly before entry time,
- bars are duplicated/out-of-order/unsafe,
- timezone/session identity is ambiguous.

Unavailable ATR001 never invents a value and never forces a trade.

## Public-project use
Public repositories may contribute architecture, test patterns and hypotheses only. Their strategy performance and thresholds are not DAX evidence. Before direct code reuse, license and provenance must be verified. Preferred donor concepts for this stage include leakage-safe walk-forward regime APIs, explicit robustness tests, event-driven/point-in-time semantics and strict separation of research features from runtime execution.

## Promotion
ATR001 starts as RESEARCH. V11.2 remains frozen. No ATR001 result can alter Paper/Live readiness until the full evidence ladder and an explicit promotion decision are complete.