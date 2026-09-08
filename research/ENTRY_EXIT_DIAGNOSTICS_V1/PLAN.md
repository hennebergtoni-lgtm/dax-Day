# ENTRY001 / EXIT001 — Execution Diagnostics Plan

Status: RESEARCH DIAGNOSTICS ONLY. Frozen V11.2 execution semantics remain unchanged.

## Purpose
Measure where current entries and exits behave well or poorly before proposing any execution change.

## ENTRY001 diagnostics
Initial fields may include:
- distance from confirmation level to next-bar open
- entry gap/slippage relative to signal close
- bars from breakout to retest
- bars from retest confirmation to entry
- entry location relative to OR / ATR / BB / structure context
- immediate adverse/favourable excursion after entry

These are diagnostics first. A discovered timing or distance threshold is a new hypothesis and cannot be validated on the same evidence that generated it.

## EXIT001 diagnostics
Initial fields may include:
- MFE / MAE in R
- time-to-MFE / time-to-MAE
- whether target/stop ordering is ambiguous within OHLC
- residual MFE after exit
- excursion by regime/family
- holding time

## Frozen execution boundary
No V6 diagnostic may silently alter:
- next-candle-open entry semantics
- current stop definition
- current RR target
- conservative same-bar OHLC handling
- cost model

Any proposed new execution rule becomes a separate future research hypothesis with its own version, causality test, exact replay and evidence path.

## Required provenance
Every derived suggestion must state whether it came from:
- predeclared execution hypothesis
- train-only analysis
- OOS diagnostic observation
- public idea

OOS diagnostic suggestions require fresh validation.

## Non-goals
- no adaptive exits based on hindsight MFE
- no cherry-picked entry delay
- no immediate trailing-stop implementation
- no bot mutation
