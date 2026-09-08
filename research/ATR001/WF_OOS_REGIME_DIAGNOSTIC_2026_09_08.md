# ATR001 — Train-only WF/OOS Regime Diagnostic — 2026-09-08

Status: RESEARCH ONLY. Evidence class: OOS_DIAGNOSTIC_DERIVED. No promotion.

## Method
For each of the canonical 81 V11.2 walk-forward windows, ATR14 and OR/ATR tertile boundaries were fitted using only that window's 45 training days. OR5 and OR15 were fitted separately. Boundaries were frozen before applying them to the corresponding 20 OOS days. No OOS refit and no full-sample threshold was used.

## Coverage
- WF windows: 81
- OR families per WF: 2
- train-only boundary rows: 162 / 162
- reproduced normal-cost OOS trades classified: 856 / 856
- missing classifications: 0

Boundary artifact SHA256: `e1f7654bf30cdad8fecdc093d0093598cb3e2078832b32ddecccba2ef5430eed`
Classified-trade artifact SHA256: `66a8f7056c228a279078d6256accf6733427e7bdb95471031550d2a60238d508`

## Aggregate descriptive OOS association
### ATR regimes
- HIGH: 340 trades, +7.3244R, avgR +0.0215
- MID: 219 trades, -13.7459R, avgR -0.0628
- LOW: 297 trades, -24.8877R, avgR -0.0838

### OR/ATR regimes
- HIGH: 355 trades, -6.5001R, avgR -0.0183
- MID: 267 trades, -10.6299R, avgR -0.0398
- LOW: 234 trades, -14.1792R, avgR -0.0606

## Stability check for ATR HIGH
Aggregate ATR HIGH looked superficially positive, but stability failed:
- active WFs with HIGH trades: 68
- positive HIGH WFs: 34
- negative HIGH WFs: 34
- median HIGH R per active WF: approximately -0.0074R

Broad WF eras:
- WF1-27: 134 trades, +17.1591R, PF 1.2234
- WF28-54: 93 trades, -1.7911R, PF 0.9656
- WF55-81: 113 trades, -8.0436R, PF 0.8822

Calendar-year HIGH evidence also decays materially after the early period, including negative aggregate R in 2016, 2018 and 2019.

## Interpretation
The apparent aggregate ATR-HIGH advantage is not temporally stable. It is therefore retained as negative/diagnostic evidence against promotion. OR/ATR tertiles are also unstable across WF eras and do not support a standalone selector.

## Public-project comparison
Public robustness-first quant research projects reinforce the same discipline: walk-forward isolation, strict no-lookahead tests, parity/invariant gates and explicit overfitting diagnostics. These are used here only as research-method donors. No external strategy performance is imported.

## Decision
- ATR001 remains RESEARCH.
- Causality remains PASS.
- Evidence advances to OOS_TESTED because train-only boundaries were frozen and applied to OOS.
- `promotion_allowed=false` remains binding.
- ATR HIGH is NOT a validated filter.
- OR/ATR tertiles are NOT a validated filter.
- Next useful work should test only small, predeclared robustness checks or move to another research family rather than threshold-mining ATR001.
