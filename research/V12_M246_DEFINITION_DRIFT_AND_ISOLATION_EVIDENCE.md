# V12 Milestone 246 — definition drift and isolated evidence

Date: 2026-09-09
Status: RESEARCH EVIDENCE — NO PRODUCTION PROMOTION
Branch: v12-prepaper-optimization

## Data identity gate
Recovered `GER30_5m.csv` was re-verified against the frozen V11.2 session identity using the historical canonical fingerprint algorithm and source-normalization semantics.

- raw rows: 481,824
- Berlin session: 09:00–17:30 inclusive
- session rows: 172,319
- session days: 1,673
- OHLC errors: 0
- canonical session OHLC SHA-256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`
- identity result: HASH_VERIFIED

The prior mismatch was representation-only: the recovered single CSV used source column `datetime`; the historical canonical fingerprint surface uses UTC index name `timestamp_utc`. No OHLC value changes were required.

## Trade evidence
The isolated evaluation uses `trades_normal.csv` from `V112_CLEAN_REFERENCE_EVIDENCE_2026_09_08.zip`.

- rows: 856
- provenance: REPRODUCED_CLEAN_EVIDENCE / NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH
- baseline Return-R: -31.309210619787684
- baseline PF: ~0.9393

All 856 `signal_time` values align exactly to historical M5 bars. All 385 non-null `retest_time` values also align exactly to historical M5 bars.

## ADX001
Predeclared hypothesis: completed-bar ADX14 trend strength may improve continuation quality.

Formal bar binding used here: ADX14 frozen at the exact `signal_time` M5 bar, matching the intake wording "signal decision bar close".

Signal-bar sensitivity diagnostics:

| slice | trades | Return-R | PF | Avg-R | Max DD-R | WF+ | WF- |
|---|---:|---:|---:|---:|---:|---:|---:|
| ADX <20 | 181 | -24.180 | 0.786 | -0.134 | -31.444 | 25 | 40 |
| ADX 20–25 | 161 | -0.028 | 1.000 | ~0.000 | -13.095 | 27 | 36 |
| ADX >=25 | 514 | -7.102 | 0.977 | -0.014 | -27.314 | 34 | 46 |
| ADX >=20 | 675 | -7.129 | 0.982 | -0.011 | -34.996 | 36 | 45 |

Interpretation: low ADX (<20) is a clearly weak historical segment. Excluding it materially improves the negative baseline, but the retained set remains negative and WF stability remains mixed. Therefore ADX001 is interesting research evidence, not a robust candidate and not production logic.

The 20/25 boundaries are sensitivity checks for interpretation only, as predeclared in the intake; they are not tuned promotion thresholds.

## BODY001
Predeclared hypothesis: the completed breakout candle's real-body ratio and breakout-side close location may separate committed breaks from wick-heavy noise.

Formal bar binding used here: exact `signal_time` bar. Short close-location is mirrored from the high. Direction agreement is checked against trade side.

- direction agreement: 855 / 856 trades

Coarse diagnostics:

### Body fraction
| slice | trades | Return-R | PF | Avg-R | Max DD-R | WF+ | WF- |
|---|---:|---:|---:|---:|---:|---:|---:|
| <0.40 | 117 | -0.347 | 0.995 | -0.003 | -12.049 | 29 | 27 |
| 0.40–0.70 | 348 | -2.798 | 0.986 | -0.008 | -26.880 | 35 | 45 |
| >=0.70 | 391 | -28.165 | 0.882 | -0.072 | -36.722 | 32 | 46 |

### Breakout-side close location
| slice | trades | Return-R | PF | Avg-R | Max DD-R | WF+ | WF- |
|---|---:|---:|---:|---:|---:|---:|---:|
| <0.67 | 187 | -4.580 | 0.960 | -0.024 | -22.679 | 28 | 36 |
| 0.67–0.85 | 289 | +13.735 | 1.085 | +0.048 | -19.197 | 33 | 41 |
| >=0.85 | 380 | -40.464 | 0.832 | -0.106 | -64.221 | 30 | 47 |

Interpretation: the simple monotonic idea "larger body / closer to extreme is better" is not supported. Extremely large bodies and extreme close-location are historically weak. The middle close-location band is positive but WF stability is mixed. Any non-linear refinement would be a new post-hoc hypothesis requiring separate preregistration; it cannot be promoted from this diagnostic.

## COMP001 definition drift
A real inconsistency was found between the original research intake and the implemented primitive.

Original intake:
- recent completed-bar range statistic over a small predeclared window
- divided by causal ATR14
- training-only quantile states COMPRESSED / NORMAL / EXPANDED
- no current-bar percentile self-inclusion

Current implementation/hardening:
- current true range divided by mean prior true range

These are not the same feature. No repository evidence was found that predeclared an exact small-window length for the intended ATR14-relative definition.

Therefore:
- current COMP001 output is engineering-causal but does not constitute the formal hypothesis test;
- prior COMP bucket results are diagnostic only and are not accepted as milestone-246 proof;
- COMP001 remains NOT TEST READY until an exact window/statistic definition is explicitly preregistered before formal evaluation.

## STALE001
STALE001's predeclared buckets match the implementation/evaluation contract:
- 1 bar
- 2 bars
- 3–4 bars
- >=5 bars

Prior isolated normal-cost evidence remains valid as diagnostic research evidence. Stress-cost completion is still required before any robust-candidate decision.

## Milestone-246 status after this audit
NOT COMPLETE.

Completed/verified components:
- frozen OHLC dataset identity recovered and hash-verified;
- reproducible 856-trade normal evidence available;
- ADX001 formal signal-bar isolated diagnostics completed;
- BODY001 formal signal-bar isolated diagnostics completed;
- STALE001 isolated normal-cost buckets completed;
- definition drift for COMP001 detected and fail-closed.

Open gates:
- exact stress-cost replay/evaluation for retained candidates;
- formal COMP001 preregistration and then isolated evaluation;
- stability review sufficient for reject/retain decisions;
- no interaction test until isolation gates are closed.

No production promotion. No Paper start. No LIVE authorization. `order_execution_enabled=false` remains unchanged.
