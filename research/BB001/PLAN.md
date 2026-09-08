# BB001 — Clean Bollinger Research Plan

Status: RESEARCH

## Baseline
BB001 is measured against the active reproducible `V112_REFERENCE_V1`, not the historical Colab aggregate. V11.2 remains frozen and unchanged.

## Primary question
Can Bollinger-derived market state improve OOS trade selection or robustness without changing V11.2 execution semantics?

## Alignment gate — must pass first
The previous pilot produced zero matches because Bollinger state and trades used incompatible day/timestamp representations. The clean implementation must:

1. align primary Bollinger state to the actual V11.2 `entry_time`;
2. keep `signal_time` as a separate explicit research variant, never silently substitute it;
3. normalize day/time representation before lookup;
4. prove on a deterministic sample that every eligible baseline trade has either an exact documented Bollinger lookup or an explicitly explained missing reason;
5. stop before performance testing if alignment is not complete.

## Indicator definition
Initial neutral definition for the alignment/pilot layer:
- source: M5 close
- center: rolling SMA(20)
- standard deviation: rolling population standard deviation over 20 M5 closes
- upper/lower: SMA20 ± 2 × SD20
- bandwidth: (upper - lower) / center
- position: (close - lower) / (upper - lower)

No claim is made that 20/2 is optimal. It is the fixed first measurement definition to prevent parameter fishing.

## Isolated hypotheses
After the alignment gate passes, test separately:
1. `bandwidth_volatility` — trade quality differs across Bollinger bandwidth states.
2. `price_position` — trade quality differs by normalized position within/outside the bands.
3. `band_breakout` — entries outside a band behave differently from entries inside.
4. `pullback_mean_reversion` — post-extension return toward center/band has measurable value.
5. `or_interaction` — Bollinger state interacts with opening-range structure.

## Controls
- active `V112_REFERENCE_V1`
- same audited DAX M5 dataset/fingerprint
- fixed rolling 45/20/20 WF schedule
- same V11.2 execution semantics
- same normal / stress_1.5x / stress_2x costs
- no Bollinger filter control

## Research discipline
- BB001 cannot modify or promote V11.2.
- Alignment is tested before profitability.
- Start with descriptive buckets and fixed thresholds; no large parameter grid.
- Any promising threshold must survive OOS/WF distribution, costs, sufficient trade count and neighbourhood stability.
- Interactions with OR/ATR, retest, stop or RR are deferred until isolated BB evidence exists.
- A negative result is retained as evidence.

## First executable block
Build and test the `entry_time` alignment layer only. Required output:
- baseline trade count checked
- exact BB matches
- missing matches with reason
- duplicate/ambiguous matches
- deterministic sample rows showing date, entry_time, close, SMA20, upper, lower, bandwidth and position

Pass condition: no unexplained missing or ambiguous lookup for eligible baseline trades. Only then begin BB performance buckets.
