# V12 MILESTONE 246 — isolated candidate evaluation

Status: IMPLEMENTED RESEARCH EVIDENCE / NO PROMOTION
Date: 2026-09-09

## Scope and safeguards
This document records isolated V12 research evidence for ADX001, BODY001, COMP001, and STALE001. V11.2 remains the immutable reference. No candidate is promoted to production, Paper, broker execution, or LIVE by this evidence.

Historical market-data identity is hash-verified against the frozen V11.2 session fingerprint after reproducing the historical normalization contract. Reproduced trade evidence remains classified as `REPRODUCED_CLEAN_EVIDENCE` with trade provenance `NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH`.

Frozen bindings:
- Dataset session SHA-256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`
- V11.2 engine SHA-256: `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`
- Reproduced normal trade rows: 856
- Reproduced normal trade SHA-256: `f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023`

The exact V11.2 stress path was reconstructed and validated: normal replay reproduced all 856 trades exactly, stress 1.5x reproduced aggregate `-40.92169502338484 R` versus the known `-40.921695023387514 R`, and stress 2x reproduced `-48.42461196300394 R` versus the known `-48.424611963007294 R`.

## ADX001
Predeclared semantic target: causal ADX14 at the completed signal/decision-bar close. Training-only quantile regimes are the formal research design; fixed thresholds 20 and 25 are interpretation/sensitivity checks only and are not treated as threshold discovery.

Corrected signal-bar binding is available for all 856/856 reproduced trades. The optimized ADX series was spot-checked against the repository `adx_feature` implementation at distributed trade positions with maximum observed difference `0.0`.

Diagnostic sensitivity:
| Case | Trades | Return-R | PF | Avg-R | Max DD-R | Positive WFs | Negative WFs | Median WF-R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V11.2 baseline | 856 | -31.309 | 0.939 | -0.037 | -55.808 | 37 | 44 | -0.512 |
| ADX >= 20 | 675 | -7.129 | 0.982 | -0.011 | -34.996 | 36 | 45 | -0.305 |
| ADX >= 25 | 514 | -7.102 | 0.977 | -0.014 | -27.314 | 34 | 46 | -0.253 |

Year Return-R for ADX >= 20: 2014 `-6.660`, 2015 `+16.231`, 2016 `+2.653`, 2017 `-11.005`, 2018 `-10.189`, 2019 `+1.842`.

Year Return-R for ADX >= 25: 2014 `-4.641`, 2015 `+13.409`, 2016 `-6.335`, 2017 `-7.578`, 2018 `-7.737`, 2019 `+5.780`.

Interpretation: fixed ADX sensitivity materially reduces aggregate loss and drawdown versus the baseline, but remains negative and unstable across years. This is not a robust-promotion result. Formal training-only-quantile use must not be replaced by post-hoc threshold selection.

Status: `RESEARCH / NO PROMOTION`.

## BODY001
Predeclared semantic target: real-body ratio and breakout-side close-location on the completed breakout/signal candle, with close-location mirrored for shorts so higher always means closer to the breakout-side extreme.

Corrected signal-bar binding is available for all 856/856 reproduced trades. Direction-only diagnostic:
- body direction agrees with breakout side: 855 trades, `-32.804 R`, PF `0.936`, Avg-R `-0.038`, Max DD `-57.303 R`, 37 positive / 44 negative WFs, median WF-R `-0.512`;
- body direction disagrees: 1 trade, `+1.495 R`.

Interpretation: direction agreement is effectively non-discriminating because it is already true for 855/856 trades. No new body-ratio or close-location threshold is selected post-hoc because the original V12 intake did not predeclare a numeric cutoff grid.

Status: `RESEARCH / NO PROMOTION`.

## COMP001
The original intake describes a recent completed-bar range statistic over a small predeclared window divided by causal ATR14, with training-only quantile states. The implemented engineering primitive computes current True Range divided by the mean of prior True Ranges. These definitions are not equivalent.

No repository evidence was found that predeclared the missing recent-range window length. Therefore choosing a window after observing OOS outcomes would violate the research discipline.

The existing compression primitive remains explicitly labeled `DIAGNOSTIC_PRIMITIVE_NOT_FORMAL_COMP001`. Previous exploratory compression buckets are not accepted as formal COMP001 evidence.

Status: `HELD_FOR_DEFINITION / NO FORMAL PERFORMANCE CLAIM / NO PROMOTION`.

## STALE001
Predeclared retest staleness buckets are `1`, `2`, `3-4`, and `>=5` completed M5 bars from breakout signal to retest. All 385 retest trades have exact signal- and retest-bar matches.

Exact stress replay summary:
| Bucket | Normal Return-R / PF | 1.5x Return-R / PF | 2.0x Return-R / PF |
|---|---:|---:|---:|
| 1 | -30.697 / 0.649 | -31.058 / 0.647 | -31.418 / 0.645 |
| 2 | +15.271 / 1.408 | +14.916 / 1.398 | +14.561 / 1.387 |
| 3-4 | -13.620 / 0.585 | -13.823 / 0.581 | -14.025 / 0.577 |
| >=5 | +1.378 / 1.017 | +0.794 / 1.010 | +0.212 / 1.003 |

The 2-bar bucket is the only materially positive bucket that remains clearly positive under 2x stress. However its annual normal-cost Return-R is mixed: 2014 `-6.1582`, 2015 `+4.5321`, 2016 `-3.0686`, 2017 `+10.2863`, 2018 `+9.7634`, 2019 `-0.0835`. WF summary: 32 affected WFs, 17 positive and 15 negative, median WF-R approximately `+0.40 R`.

Interpretation: stress-resilient isolated signal, but not sufficiently stable for a robust-promotion claim.

Status: `RESEARCH / NO PROMOTION`.

## Milestone 246 conclusion
- ADX001: isolated causal diagnostic completed; negative aggregate under fixed sensitivity; no promotion.
- BODY001: isolated signal-bar diagnostic completed; direction-only state does not discriminate; no promotion.
- COMP001: formal isolated performance claim withheld because the predeclared definition is incomplete and differs from the engineering primitive; no post-hoc repair.
- STALE001: isolated normal and exact-stress evidence completed; 2-bar bucket is the only stress-resilient area, but temporal stability is mixed; no promotion.

Milestone 246 is considered complete as an isolated evaluation and evidence-discipline gate. The unresolved COMP001 definition is carried into milestone 247 rejection/hold discipline rather than silently optimized.
