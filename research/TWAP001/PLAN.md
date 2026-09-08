# TWAP001 — Session-Reset Anchored Price Reference

Status: PLANNED / RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Why TWAP, not VWAP
The audited 2014–2019 DAX source contains OHLC but no trustworthy volume field. Therefore a true volume-weighted average price cannot be reconstructed from this evidence. TWAP001 must never be labeled VWAP.

## Public idea boundary
Current public projects motivate session-reset VWAP/TWAP references, walk-forward evaluation, no-lookahead replay and live MT5 monitoring as architecture/research ideas only. No public strategy rule, threshold or performance is imported.

## Predeclared research question
Does the location and distance of a frozen V11.2 entry relative to a causal session-reset average-price reference provide incremental context beyond BB001, ATR001, MOM001, STRUCT001 and SESSION001?

## Fixed first implementation
Use only completed Berlin-session M5 bars whose close is known strictly before `entry_time`.

Primary reference:
- `session_twap_close`: arithmetic mean of completed M5 closes from the 09:00 Berlin session open through the latest bar available strictly before entry.

Primary descriptors:
- signed entry distance from session TWAP in points;
- signed distance normalized by causal ATR14 already defined by ATR001;
- entry side aligned/opposed with price position relative to TWAP;
- completed-bar count contributing to the reference.

## Causality
Raw M5 timestamps are bar-open timestamps. A bar contributes only at `open_time + 5 minutes`, and only when that availability time is strictly earlier than `entry_time`. The entry candle itself is forbidden.

## Parameter discipline
- no volume reconstruction or proxy volume;
- no band multiplier sweep;
- no minute-by-minute anchor search;
- no alternate session starts after outcome inspection;
- first pass is descriptive attachment only;
- any selector threshold must later be predeclared or train-only per WF.

## Required controls
- same-entry-bar pollution test;
- future-suffix pollution test;
- Europe/Berlin DST handling;
- minimum completed-bar count reported, not optimized;
- overlap/incremental checks versus BB001/ATR001/MOM001/SESSION001 before stacking.

## Promotion
TWAP001 starts PLAN_ONLY and `promotion_allowed=false`. Full-sample descriptive thresholds cannot be used as trading rules.
