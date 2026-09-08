# MOM001 — V8 Causal Momentum Contract

Status: RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Purpose
Test whether a very small set of causally available short-horizon momentum descriptors adds information beyond V11.2, BB001, ATR001 and STRUCT001.

## Public-donor boundary
Public repositories were used only as architecture/testing donors. In particular, truncation/future-pollution tests and explicit execution lag are retained as verification ideas. No public strategy performance, thresholds or trading rules are imported. GPL-licensed donor code is not copied.

## Timestamp contract
For an entry at `entry_time`, every momentum input must come from a fully completed M5 candle with `available_time < entry_time`.

DAXLAB M5 storage timestamps represent bar-open time. Therefore:
- `available_time = bar_open_time + 5 minutes`;
- a candle whose open equals `entry_time` is ineligible;
- same-entry-bar close/high/low/body information is forbidden.

## Fixed pilot descriptors
Only these descriptors are allowed in the first implementation:
1. `ret_1`: close-to-close return over the last 1 completed M5 bar;
2. `ret_3`: close-to-close return over the last 3 completed M5 bars;
3. `directional_closes_3`: signed count of up/down close-to-close moves over the last 3 completed bars;
4. `body_fraction_1`: absolute body divided by high-low range of the latest completed bar, with zero-range guarded;
5. `signed_body_fraction_1`: body fraction signed by close-open direction.

No oscillator zoo, no threshold sweep and no additional horizon may be added after seeing OOS results without opening a new hypothesis/version.

## First-stage use
The first stage is descriptive feature attachment only. It must not filter, rank, resize, enter or exit V11.2 trades.

## Mandatory tests before DAX descriptive run
- same-entry-bar pollution test;
- future-suffix pollution / prefix invariance test;
- insufficient-history behavior;
- zero-range candle behavior;
- exact timestamp eligibility.

## Later evaluation discipline
If a selector is tested later, thresholds/normalization must be predeclared or learned from each WF training slice only. OOS-derived cutoffs are diagnostic evidence and cannot count as independent promotion proof.

Required reporting remains trade count, Return-R, PF, drawdown, WF/broad-era stability, overlap with BB001/ATR001/STRUCT001, cost stress when selection changes, and no-trade increase.
