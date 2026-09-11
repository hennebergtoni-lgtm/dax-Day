# Public architecture donor rescan — V6

Updated: 2026-09-11
Purpose: architecture/research ideas only. No foreign strategy result is evidence for DAX and no foreign source is copied into the frozen V11.2 engine or DAX-BOT candidate logic.

Supersedes V5 as the latest donor rescan. V5 remains provenance.

## Rechecked donors

### QuantConnect / LEAN

Useful current patterns:
- subscribe to the lowest market-data resolution actually required, then consolidate upward to larger deterministic bars;
- keep consolidated-bar callbacks distinct by timeframe rather than silently changing one strategy's resolution;
- model scheduled events through an explicit scheduler instead of scattering wall-clock checks through strategy entry code;
- distinguish live scheduled-event timing from backtest data-loop timing and test the difference;
- keep risk/execution components separable from alpha/signal generation.

DAX-BOT V6 reuse decision:
- prefer a future canonical CLOSED-M1 stream with deterministic M1→M5 aggregation if FAST-M1 is pursued;
- keep M1 as a separate Candidate/ruleset/evidence line rather than changing CAND-001 in place;
- treat macro-event scheduling as an external context/gate owner, not entry-rule code.

### NautilusTrader

Useful current patterns:
- explicit BarType/time aggregation contracts;
- support for one-minute external bars and bar-to-bar aggregation into larger internal bars;
- explicit timestamp-on-close and partial-first-bar behavior;
- request historical bars to initialize state, then subscribe to the same bar type for live continuation;
- cache/data engine ownership remains separate from strategy callbacks.

DAX-BOT V6 reuse decision:
- one source-of-truth lower-resolution feed is preferable to independent M1/M5 truths;
- bar alignment, startup partial bars, timestamp semantics and restart reconstruction must be explicit and regression-tested before M1 promotion.

### Freqtrade

Useful current patterns:
- stake/position sizing callbacks are separate from ordinary entry-signal calculation;
- protections such as max drawdown, stoploss guards and cooldown periods are separate composable gates;
- detailed lower timeframes can be used to evaluate intra-candle/backtest behavior rather than pretending coarse bars contain exact path order;
- operational callbacks should avoid heavy work in the hot loop.

DAX-BOT V6 reuse decision:
- a future operator `Risk / Exposure profile` should request a bounded sizing profile but never bypass independent drawdown/cooldown/risk gates;
- capital allocation and actual cash loss at stop remain distinct semantics;
- news/event awareness should be cached/preprocessed outside the per-bar hot path and exposed as a compact validated context.

### vectorbt

Useful donor category remains high-throughput vectorized research/screening.

V6 decision:
- IDEA ONLY for research acceleration;
- FAST screening may never independently promote M1/news/risk-control policies without causal event-driven validation.

## New V6 binding conclusions

1. **Multi-timeframe:** If FAST-M1 proceeds, prefer `validated CLOSED M1 -> deterministic M5 aggregation` so M1 and M5 share one market-data truth.
2. **Strategy identity:** NORMAL-M5 and FAST-M1 are separate candidates/profiles with separate config fingerprints and evidence; a UI toggle selects a validated profile rather than mutating rules in place.
3. **Risk control:** operator-requested exposure is separate from quantity calculation and separate again from protections such as drawdown/daily-loss/cooldown gates.
4. **Scheduled macro events:** maintain an explicit event/scheduler layer outside strategy entry logic.
5. **Breaking news:** collect/reconcile asynchronously into a validated EventRiskSnapshot; never run web/news retrieval synchronously inside the candle hot path.
6. **News response:** observation/guarding should precede any research that actively trades headline direction.
7. **Causality:** lower timeframe does not relax CLOSED-bar, duplicate, ordering, timestamp or restart-parity requirements.
8. **Costs:** small-M1 target research requires stricter spread/slippage/latency and turnover analysis than the M5 candidate.
9. **Safety:** none of these donor findings authorize PAPER, LIVE, broker sizing or order submission.
10. **Licensing:** code/dependency adoption still requires an explicit current license/dependency decision; V6 authorizes architecture ideas only.

## Project documents created from this rescan

- `docs/FAST_TRADING_M1_RESEARCH_V1.md`
- `docs/OPERATOR_RISK_PROFILE_CONTROL_V1.md`
- `docs/NEWS_EVENT_AWARENESS_RESEARCH_V1.md`
