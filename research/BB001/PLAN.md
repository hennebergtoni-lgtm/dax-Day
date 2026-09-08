# BB001 — Clean Bollinger Research Plan

Status: RESEARCH

## Baseline
BB001 is measured against the active reproducible `V112_REFERENCE_V1`, not the historical Colab aggregate. V11.2 remains frozen and unchanged.

## Primary question
Can Bollinger-derived market state improve OOS trade selection or robustness without changing V11.2 execution semantics?

## Causal state rule — binding
The first alignment pass matched Bollinger state to the same `entry_time` M5 bar. That pass remains useful as descriptive/diagnostic evidence, but the entry bar close is not known at the entry open and therefore **same-entry-bar Bollinger state is not promotion-eligible**.

Exact V11.2 semantics are:
- breakout: signal is confirmed on a completed bar close; entry is the next M5 bar open;
- retest: retest is confirmed on a completed bar close; entry is the next M5 bar open.

Therefore all promotion-eligible BB001 performance tests must use the **last fully completed M5 bar strictly before `entry_time`**. Current audited reconstruction gives 856/856 prior-bar matches, zero missing/ambiguous matches, and a 5-minute lag for every baseline trade.

The prior same-entry-bar artifacts are retained for provenance and hypothesis generation only; they do not validate a strategy.

## Indicator definition
Fixed first measurement definition:
- source: M5 close
- center: rolling SMA(20)
- standard deviation: rolling population standard deviation over 20 M5 closes
- upper/lower: SMA20 ± 2 × SD20
- bandwidth: (upper - lower) / center
- position: (close - lower) / (upper - lower)

No claim is made that 20/2 is optimal. It is fixed to reduce parameter fishing.

## Isolated hypotheses
1. `bandwidth_volatility`
2. `price_position`
3. `band_breakout`
4. `pullback_mean_reversion`
5. `or_interaction`

## Current causal evidence
Causal prior-bar descriptive buckets materially weaken the same-bar effects, which is expected and preferable to look-ahead contamination.

Current research-only candidate, generated from previously observed hypotheses:
- side: long
- entry mode: retest
- prior-bar Bollinger position >= 0.75
- prior-bar bandwidth above the global causal OOS median
- 37 trades
- normal: +8.6499R, PF 1.4609
- stress 1.5x: +8.4995R, PF 1.4513
- stress 2x: +8.3505R, PF 1.4418
- 14 positive vs 9 negative active WFs under all three cost surfaces

This is **RESEARCH_EVIDENCE only**, not a pilot/validated tool, because the global OOS bandwidth median is a descriptive threshold derived from the evaluation sample. Promotion requires a threshold that is fixed ex ante or estimated only from each WF training window, plus neighbourhood and trade-count stability.

## Controls
- active `V112_REFERENCE_V1`
- same audited DAX M5 dataset/fingerprint
- fixed rolling 45/20/20 WF schedule
- same V11.2 execution semantics
- same normal / stress_1.5x / stress_2x costs
- no Bollinger filter control

## Research discipline
- BB001 cannot modify or promote V11.2.
- Causality is tested before profitability.
- Same-entry-bar state is diagnostic only.
- Start with descriptive buckets and fixed/natural thresholds; no large parameter grid.
- Any promising threshold must survive OOS/WF distribution, exact costs, sufficient trade count and neighbourhood stability.
- Any data-derived threshold intended for a deployable candidate must be estimated from training data only inside each WF.
- A negative result is retained as evidence.

## Next executable block
Replace the global OOS bandwidth-median research threshold with a causally valid deployment-style rule:
1. preserve natural directional position threshold(s) as fixed hypotheses;
2. derive any bandwidth cut only from each WF training window, or use a fixed ex-ante economic/indicator definition;
3. apply it unchanged to that WF OOS block;
4. run normal / 1.5x / 2x costs;
5. report total trades, positive/negative WFs, median WF result, broad-era stability and threshold neighbourhood without selecting the best neighbour after the fact.

Only if that survives does BB001 advance to PILOT consideration.
