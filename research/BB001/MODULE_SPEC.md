# BB001 — Modular Bollinger Research Filter

Status: **RESEARCH TOOL / NOT STRATEGY-PROMOTED**

## Purpose

Bollinger logic is implemented as a detachable research/filter module. It must not mutate the frozen V11.2 reference baseline. The intended architecture is:

`regime -> DAX structure / ORB -> retest -> optional quality filters (including Bollinger) -> entry -> bounded risk`

Bollinger is therefore a secondary quality/regime input, not the primary trading idea.

## Causal contract

Promotion-eligible BB state must use information fully known before entry.

For current V11.2 breakout and retest semantics, entry occurs on the open of the bar following the completed signal/confirmation bar. Therefore the BB state used at entry is the most recent completed M5 bar strictly before `entry_time`.

Same-entry-bar BB values remain diagnostic only and are not eligible for promotion.

## Implemented code building blocks

`src/daxlab/research/bollinger_filter.py` provides:

- M5 Bollinger state: SMA center, population standard deviation (`ddof=0`), +/- 2 SD by default.
- Normalized bandwidth `(upper - lower) / mid`.
- Position `(close - lower) / (upper - lower)`.
- Strict prior-bar entry alignment.
- Train-only quantile thresholds.
- Prior-day range / ATR context using prior information only.
- Completed higher-timeframe resampling with an explicit `known_time`.
- A detachable eligibility filter that can be disabled entirely.

## Current DAX evidence

The current research candidate is:

- long
- V11.2 retest entry mode
- causal BB position >= 0.75
- causal BB bandwidth > per-WF training median
- optional prior-day regime: PrevRange/ATR <= per-WF training Q75

Observed research evidence for the combined candidate on the existing 81 fixed 45/20/20 WFs:

- Normal: 38 trades, +17.3248R, PF 2.0987
- 1.5x costs: 38 trades, +17.1462R, PF 2.0828
- 2x costs: 38 trades, +16.9697R, PF 2.0673

This remains **research evidence**, not a validated production rule. Sample size is modest and the hypothesis was developed through iterative research on this historical corpus.

## Marginal interpretation

On the same research corpus:

- long + retest only: 173 trades, +1.7762R, PF 1.0183
- + train-only prior-day Q75 regime: 119 trades, +12.0458R, PF 1.1939
- + BB position >= 0.75: 51 trades, +18.7720R, PF 1.8492
- + BB bandwidth > train median: 89 trades, +15.0705R, PF 1.3282
- + both BB conditions: 38 trades, +17.3248R, PF 2.0987

This supports treating BB as a **small filter whose usefulness may depend on regime/structure context**, not as a standalone strategy.

## Public-project intelligence — idea only

### JN842/multitf-bollinger-switching

Useful engineering/research idea:

- classify context using a completed higher timeframe;
- shift/use the last fully closed HTF bar so the state does not repaint or leak future information;
- distinguish breakout-like and mean-reversion-like regimes instead of assuming one BB interpretation everywhere.

The donor project is not evidence that the logic works on DAX. Code is not copied here. License reuse was not established during the initial audit, so this remains an independent reimplementation of the idea.

### dws-data/nas-orb-backtester

Useful engineering/research idea:

- require confirmed breakout structure before a retrace;
- treat retrace/retest as a continuation structure rather than a raw indicator signal;
- precompute daily context and reuse it across experiments;
- use conservative entry-bar semantics and explicit MFE/MAE for analysis.

Again, donor performance is not evidence for DAX and code is not copied.

## Negative / non-promoted findings retained

- Same-entry-bar BB state is non-causal for the current entry semantics.
- A completed 15m BB-above-SMA requirement did not improve the present candidate.
- A 15m BB position >= 0.75 requirement reduced the present candidate's PF.
- A tight retest-time cutoff is not justified by current evidence.
- Extra OR/ATR thresholds are not stable enough to add merely to improve historical fit.

## Prepared future interfaces

The module is intentionally ready for these isolated future experiments without changing V11.2:

1. M5 BB position/bandwidth as quality filters.
2. Train-derived bandwidth regimes.
3. Completed 15m/30m/60m BB regime context.
4. Breakout-regime versus mean-reversion-regime labels on completed HTF data.
5. Interaction with prior-day extension, OR structure, gap state, Fibonacci/retracement structure, scheduled events, and later cross-market context.
6. Complete disable/remove path: `BollingerConfig()` passes all trades when no external context cap is supplied.

## Promotion rule

No BB configuration becomes candidate-bot logic merely because it ranks well. Promotion requires causal implementation, train-only or predeclared thresholds, OOS/WF stability, normal/1.5x/2x cost stress, sufficient sample size, neighbourhood robustness, and independent/prospective validation.
