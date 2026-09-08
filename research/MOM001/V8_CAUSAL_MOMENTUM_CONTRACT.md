# MOM001 — V8 Causal Momentum Contract

Status: RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Purpose
Test whether a very small set of causally available short-horizon momentum descriptors adds information beyond V11.2, BB001, ATR001 and STRUCT001.

## Public-donor boundary
Public repositories are architecture/testing donors only. Useful patterns are truncation/future-pollution tests, explicit execution lag, fixed predeclared hypotheses, and reporting failed OOS results without post-hoc parameter changes. No public strategy performance, thresholds or trading rules are imported. GPL-licensed donor code is not copied.

## Timestamp contract
`MomentumBar.time` is the time at which that bar is fully known. For an entry at `entry_time`, only bars with `bar.time < entry_time` are eligible. Same-entry-time bar information is forbidden.

When adapting raw DAX M5 data, whose stored timestamp is bar-open time, the adapter must convert it to completion/availability time (`open_time + 5 minutes`) before constructing `MomentumBar` objects. This preserves the global DAXLAB rule `state_time < entry_time`.

## Fixed pilot descriptors
The existing implementation is the pilot surface:
1. `return_1`: close-to-close return over one completed bar;
2. `return_3`: close-to-close return over three completed bars;
3. `directional_closes_3`: +3 only when the last three completed candle bodies are all positive, -3 only when all are negative, otherwise 0;
4. `body_fraction`: absolute body divided by the latest completed candle range, with zero-range guarded;
5. `range_points`: latest completed candle high-low range.

No oscillator zoo, dense horizon sweep or post-OOS feature addition is allowed inside this pilot.

## First-stage use
Descriptive feature attachment only. MOM001 must not filter, rank, resize, enter or exit V11.2 trades at this stage.

## Mandatory causality tests
- same-entry-time bar exclusion;
- future-suffix pollution / prefix invariance;
- fixed-horizon calculation;
- OHLC validation and zero-range handling before descriptive evidence is upgraded.

## Later evaluation discipline
If a selector is tested later, thresholds/normalization must be predeclared or learned from each WF training slice only. OOS-derived cutoffs are diagnostic evidence and cannot count as independent promotion proof.

Required reporting: trade count, Return-R, PF, drawdown, WF/broad-era stability, overlap with BB001/ATR001/STRUCT001, cost stress when selection changes, and no-trade increase.
