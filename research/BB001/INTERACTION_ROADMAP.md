# BB001 Interaction Roadmap

Status: **binding research queue, not promoted strategy logic**

## Core principle

Bollinger is not treated as a standalone DAX strategy. It is a detachable quality/regime feature whose value must be tested conditionally on market structure.

Current conceptual order:

`regime -> DAX structure -> retest/setup -> optional BB quality -> bounded execution`

Later, if independently validated:

`regime -> DAX structure -> cross-market context -> eligible validated tools -> setup/entry -> bounded risk`

## Frozen BB findings to preserve

- Use only fully known information before entry.
- Current V11.2 entries require the last completed M5 BB state strictly before `entry_time`.
- Same-entry-bar BB values are diagnostic only.
- BB position and bandwidth show more value as filters when combined with long-retest structure and prior-day regime than as standalone logic.
- Per-WF train-only thresholds are preferred over thresholds derived globally from OOS data.
- Completed 15m BB context is supported technically but has not improved the current BB001 candidate and must not be forced into strategy logic.

## Public-project ideas preserved as hypothesis sources

### Completed HTF regime switching
Inspired by the general architecture in `JN842/multitf-bollinger-switching`:

- completed higher-timeframe bars only;
- breakout-like versus mean-reversion-like regime state;
- no repaint/look-ahead;
- independently reimplemented in `classify_htf_regime`.

### Confirmed breakout -> retrace structure
Inspired by the general architecture in `dws-data/nas-orb-backtester`:

- confirm breakout before treating a retest as continuation structure;
- retain conservative entry-bar handling;
- precompute reusable day/feature context;
- preserve MFE/MAE as later diagnostic dimensions.

### Robustness discipline
Inspired by `DaruFinance/quant-research-framework`:

- future-pollution/no-lookahead property tests;
- rolling OOS/WF evaluation;
- friction stress;
- regime segmentation;
- later overfitting diagnostics rather than selecting by headline PF alone.

Public-project performance numbers never validate DAX logic.

## Interaction queue

### BB x prior-day regime
Current strongest BB001 research interaction. Continue with train-only / predeclared context thresholds and prospective evidence. Do not promote from the present historical corpus alone.

### BB x OR / retest structure
Research:
- OR5 vs OR15;
- confirmed breakout persistence;
- retest quality/depth;
- OR range and OR/ATR state;
- stop/target interaction only after setup eligibility is fixed.

### BB x Fibonacci / retracement
Next major family after BB001 infrastructure:
- define impulse/OR leg causally;
- fixed retracement zones;
- test whether BB state improves selection within a predeclared retracement structure;
- no threshold mining across many Fibonacci variants.

### BB x gap state
Research gap size/direction/close state first in isolation, then test only a small number of BB interactions.

### BB x event context
EVENT001 remains separate. Only after event effects are measured should BB state be tested near/away from scheduled macro events.

### BB x cross-market regime
Later only, after DAX-internal evidence survives:
- Euro Stoxx / European equity context;
- US risk context when causally available;
- EUR/USD;
- Bund/rates;
- volatility index context.

No future US-session information may leak into European-morning decisions.

## Engineering contract

The reusable implementation lives in:

- `src/daxlab/research/bollinger_filter.py`
- `scripts/bb001_feature_bundle.py`
- `tests/test_bollinger_filter.py`
- `tests/test_bollinger_no_lookahead_property.py`

The module must remain detachable. An empty `BollingerConfig()` must not filter trades by itself. V11.2 remains frozen.

## Next research sequence

1. Finish BB001 infrastructure and independent validation plan.
2. Start Fibonacci/retracement family with a public-project scan before final experiment design.
3. Start gap family in isolation.
4. Compare validated isolated tools by regime.
5. Add EVENT001 interaction research.
6. Add cross-market context only after DAX-internal structure is sufficiently stable.
7. Candidate bot selection remains a later gate; no research module automatically becomes the bot.
