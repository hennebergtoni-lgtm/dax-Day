# V12 STALE001 — isolated evidence with exact stress replay

Status: ISOLATED EVIDENCE COMPLETE / NOT PROMOTED
Date: 2026-09-09

## Provenance
- Evidence classification: `REPRODUCED_CLEAN_EVIDENCE`
- Trade artifact: `trades_normal.csv`
- Rows: 856
- SHA-256: `f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023`
- Trade provenance: `NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH`
- Frozen dataset SHA-256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`
- Frozen V11.2 engine SHA-256: `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`

The recovered `GER30_5m.csv` was re-normalized through the historical fingerprint contract and reproduced the frozen session SHA exactly. The structural source gate is therefore upgraded to hash-verified for this evaluation.

This trade evidence is newly reproducible clean evidence. It is not claimed to be the historical original trade-file identity.

## Candidate definition
STALE001 applies only to V11.2 retest entries. `bars_since_breakout` is computed causally as the elapsed closed M5 bars from `signal_time` to `retest_time`. Predeclared buckets: `1`, `2`, `3-4`, `>=5`. Breakout-only entries are not rewritten.

The reproduced normal-cost trade artifact contains 385 retest trades, all with exact `signal_time` and `retest_time` M5-bar matches.

## Normal-cost isolated results
| Bucket | Trades | Return-R | PF | Avg-R | Max DD-R | Positive WFs | Negative WFs | Median WF-R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 129 | -30.6955 | 0.6477 | -0.2379 | -43.9417 | 12 | 28 | -1.0068 |
| 2 | 72 | +15.2715 | 1.4135 | +0.2121 | -7.0901 | 17 | 15 | +0.4028 |
| 3-4 | 51 | -13.6208 | 0.5888 | -0.2671 | -18.3042 | 10 | 18 | -0.4447 |
| >=5 | 133 | +1.3805 | 1.0186 | +0.0104 | -9.4696 | 19 | 23 | -0.3436 |

## Exact stress replay
The V11.2 cost path was reconstructed from the frozen exact engine and validated before use:
- Normal replay reproduced all 856 trades exactly for entry, exit, risk, target, net points, R, exit reason, and exit time.
- Stress 1.5x aggregate reproduced the known V11.2 total to floating-point tolerance: `-40.92169502338484 R` versus `-40.921695023387514 R`.
- Stress 2x aggregate reproduced the known V11.2 total to floating-point tolerance: `-48.42461196300394 R` versus `-48.424611963007294 R`.

| Bucket | Cost | Trades | Return-R | PF | Max DD-R |
|---|---|---:|---:|---:|---:|
| 1 | Normal | 129 | -30.697 | 0.649 | -43.944 |
| 1 | 1.5x | 129 | -31.058 | 0.647 | -44.218 |
| 1 | 2.0x | 129 | -31.418 | 0.645 | -44.494 |
| 2 | Normal | 72 | +15.271 | 1.408 | -7.090 |
| 2 | 1.5x | 72 | +14.916 | 1.398 | -7.148 |
| 2 | 2.0x | 72 | +14.561 | 1.387 | -7.207 |
| 3-4 | Normal | 51 | -13.620 | 0.585 | -13.620 |
| 3-4 | 1.5x | 51 | -13.823 | 0.581 | -13.823 |
| 3-4 | 2.0x | 51 | -14.025 | 0.577 | -14.025 |
| >=5 | Normal | 133 | +1.378 | 1.017 | -18.231 |
| >=5 | 1.5x | 133 | +0.794 | 1.010 | -18.580 |
| >=5 | 2.0x | 133 | +0.212 | 1.003 | -18.927 |

The `2`-bar bucket is the only clearly positive bucket that remains materially positive under the 2x stress scenario. The `>=5` bucket nearly erodes to zero by 2x stress and is not treated as stress-robust.

## Year and WF stability
Bucket `2` annual Return-R by signal year:
- 2014: -6.1582 R
- 2015: +4.5321 R
- 2016: -3.0686 R
- 2017: +10.2863 R
- 2018: +9.7634 R
- 2019: -0.0835 R

WF summary for bucket `2`: 32 affected WFs, 17 positive and 15 negative, median WF Return-R approximately `+0.40 R` under normal costs.

Therefore the strongest bucket is stress-resilient but not positive across all years and does not satisfy a robust-promotion claim.

## Gate state
- Dataset identity: `HASH_VERIFIED` against the frozen session fingerprint.
- Normal-cost isolated STALE001 evidence: `COMPLETE`.
- Stress 1.5x / 2x replay: `EXACTLY_REPRODUCED` at the V11.2 aggregate gate and applied to STALE001.
- ADX001: signal-bar diagnostic evaluation available; no promotion claim.
- BODY001: signal-bar diagnostic evaluation available; direction-only state has negligible discrimination.
- COMP001: formal evaluation remains held because the original predeclared research description does not specify the required recent-range window and the existing engineering primitive is not definition-equivalent.
- Candidate status remains `RESEARCH`.
- No production promotion, Paper start, broker execution, or LIVE implication.
