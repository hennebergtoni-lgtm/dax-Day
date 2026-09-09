# V12 Public Research Intake — bounded pre-Paper candidates

Date: 2026-09-09
Status: RESEARCH INTAKE ONLY

## Guardrails
This intake records external ideas as provenance. It does not promote any public strategy, threshold, or filter into frozen V11.2. No external code is copied. Every candidate must be causal on closed M5 bars, tested in isolation first, and rejected if it relies on future data, unavailable historical volume, fragile tuning, or trade-count collapse.

## Public ideas reviewed
The intake sampled recent public GitHub ORB/breakout projects and noted recurring engineering ideas:

- `reselbob/orbilicious`: confirmation retest plus explicit retest-age/staleness guard and ATR-aware stop viability.
- `sarthak070707/Regime-trading-engine`: ADX trend-strength, ATR/price regime, candle-body quality and session/regime gating.
- `OVVAR/xauusd-research`: closed-bar ORB, rolling volatility regime built only from past bars, explicit anti-lookahead rules.
- `abhidp/orb-strategy`: breakout confirmation requiring a candle-body close beyond the range.
- `Smashthehedgehog/break-retest-daytrader`: first-range break/retest state machine and one-trade/day discipline; its volume confirmation is NOT adopted because our historical dataset has no trustworthy volume series.
- Donchian/session-breakout examples were reviewed as structural references only; no new Donchian production rule is introduced in V12.

## Selected V12 candidates
Only four compact, OHLC-only candidates enter this V12 block.

### ADX001 — causal trend-strength context
Hypothesis: V11.2 entries occurring when pre-entry directional trend strength is materially higher may have better continuation quality.

Definition discipline:
- Wilder-style ADX using completed M5 bars only.
- Default research lookback: 14 completed bars.
- Feature value is frozen at the signal decision bar close; no later bar may alter it.
- Initial isolated test uses coarse predeclared regimes rather than fine optimization: LOW / MID / HIGH based on training-only quantiles, with a fixed-threshold sensitivity check such as ADX 20/25 for interpretation only.
- Warm-up bars yield MISSING and cannot be silently treated as pass.

### BODY001 — breakout candle quality
Hypothesis: a breakout candle whose real body occupies a larger share of its high-low range and closes nearer the breakout-side extreme may distinguish committed breaks from wick-heavy noise.

Causal features on the completed breakout bar:
- `body_ratio = abs(close-open)/(high-low)` when range > 0.
- long `close_location = (close-low)/(high-low)`; short mirrored from high.
- direction agreement requires body direction to match breakout direction.
- Predeclared coarse states only; no exhaustive threshold grid.

### COMP001 — pre-break range/ATR compression-expansion context
Hypothesis: the relation between recent realized range and causal ATR before entry may identify compressed/noisy versus expansion-ready environments beyond existing ATR001.

Separation from ATR001:
- ATR001 studies volatility level/regime and OR/ATR relationships.
- COMP001 studies short-horizon compression of completed pre-entry bars relative to their own causal ATR reference.

Candidate feature:
- recent completed-bar range statistic over a small predeclared window divided by ATR14 calculated without the decision bar's future.
- Coarse training-only quantile states COMPRESSED / NORMAL / EXPANDED.
- No current-bar percentile self-inclusion.

### STALE001 — retest staleness
Hypothesis: after a confirmed breakout, retests arriving too many closed M5 bars later may lose continuation quality.

Definition:
- `bars_since_breakout = retest_bar_index - breakout_bar_index` using only already-closed bars.
- Same-bar/intrabar future knowledge is prohibited.
- Predeclared isolated buckets: 1 bar, 2 bars, 3–4 bars, >=5 bars; buckets may be combined only after isolated evidence.
- Applies only where the underlying V11.2 path has a retest concept; it must not rewrite breakout-only entries.

## Explicitly excluded from this V12 intake
- volume confirmation / VWAP requiring historical trade volume,
- ML confidence scoring,
- news/event hindsight labels,
- large indicator grids,
- strategy replacement by public GitHub code,
- any execution/broker behavior.

## Acceptance discipline
A candidate can become `ROBUST_CANDIDATE` only after isolated evidence includes Normal costs plus stress, adequate trade count, PF, Return-R, drawdown, yearly/epoch stability and WF/OOS behavior. A higher headline PF alone is insufficient. Interaction testing is allowed only for the small predeclared subset that survives isolation.
