# V12 MILESTONE 247 — rejection and hold discipline

Status: IMPLEMENTED RESEARCH SELECTION DISCIPLINE
Date: 2026-09-09

## Rule
Milestone 247 rejects or withholds candidates that depend on one headline metric, remain unstable across time, collapse usable trade count, or cannot be evaluated against their predeclared definition. V11.2 remains frozen. No candidate is promoted by this decision.

## ADX001 — REJECTED FOR V12 CYCLE
Causal signal-bar ADX14 sensitivity at fixed interpretation thresholds materially reduces the V11.2 aggregate loss and drawdown, but does not produce positive aggregate performance:
- baseline: 856 trades, `-31.309 R`, PF `0.939`, Max DD `-55.808 R`;
- ADX >= 20: 675 trades (78.9% retention), `-7.129 R`, PF `0.982`, Max DD `-34.996 R`;
- ADX >= 25: 514 trades (60.0% retention), `-7.102 R`, PF `0.977`, Max DD `-27.314 R`.

Both sensitivity cases remain negative and show mixed annual stability. The candidate is therefore rejected for the bounded V12 cycle rather than optimized further to a favorable threshold or headline PF.

Registry decision: `REJECTED`.

## BODY001 — REJECTED FOR V12 CYCLE
The predeclared signal-candle direction state has negligible discrimination:
- direction agrees with breakout side: 855/856 trades, `-32.804 R`, PF `0.936`;
- direction disagrees: 1 trade, `+1.495 R`.

No post-hoc body-ratio or close-location cutoff is selected because the V12 intake did not predeclare a numeric threshold grid. The observed state is not useful as an isolated filter.

Registry decision: `REJECTED`.

## COMP001 — REJECTED FOR V12 CYCLE ON DEFINITION DISCIPLINE
The intake describes a recent completed-bar range statistic over a small predeclared window divided by causal ATR14. The implemented engineering primitive computes current True Range divided by the mean of prior True Ranges. These are not definition-equivalent, and no repository evidence predeclares the missing recent-range window length.

Selecting a window now would be post-hoc. Therefore no formal OOS performance claim is made and the candidate is rejected for this bounded V12 cycle. A future version may introduce a newly predeclared COMP hypothesis with an explicit window before any outcome is observed.

Registry decision: `REJECTED`.

## STALE001 — TESTED, NOT ROBUST
The predeclared 2-bar retest bucket is the only materially positive STALE001 bucket that remains clearly positive under exact 2x stress:
- Normal: 72 trades, `+15.271 R`, PF `1.408`;
- 1.5x: 72 trades, `+14.916 R`, PF `1.398`;
- 2.0x: 72 trades, `+14.561 R`, PF `1.387`.

However:
- only 72/385 retest trades survive (18.7% of retests);
- only 72/856 total V11.2 trades survive (8.4% of all trades);
- annual normal-cost returns are mixed, including negative 2014 and 2016 and approximately flat/negative 2019;
- 32 WFs are affected, with 17 positive and 15 negative.

This is enough to retain STALE001 as tested research evidence, but not enough for `ROBUST_CANDIDATE` status and not enough to authorize an interaction test under milestone 248.

Registry decision: `TESTED`.

## Milestone 247 conclusion
- `ADX001`: REJECTED
- `BODY001`: REJECTED
- `COMP001`: REJECTED
- `STALE001`: TESTED, NOT ROBUST
- `ROBUST_CANDIDATE` count among the four V12 candidates: 0

No candidate may advance merely because one bucket or one metric looks favorable. No production filter, Paper start, broker execution, or LIVE implication is created by this milestone.
