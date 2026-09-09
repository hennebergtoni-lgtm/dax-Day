# V12 STALE001 — isolated evidence, normal costs only

Status: PARTIAL ISOLATED EVIDENCE / NOT PROMOTED
Date: 2026-09-09

## Provenance
- Evidence classification: `REPRODUCED_CLEAN_EVIDENCE`
- Trade artifact: `trades_normal.csv`
- Rows: 856
- SHA-256: `f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023`
- Trade provenance: `NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH`
- Frozen dataset SHA-256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`
- Frozen V11.2 engine SHA-256: `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`

This evidence is newly reproducible clean evidence. It is not claimed to be the historical original trade-file identity.

## Candidate definition
STALE001 applies only to V11.2 retest entries. `bars_since_breakout` is computed causally as the elapsed closed M5 bars from `signal_time` to `retest_time`. Predeclared buckets: `1`, `2`, `3-4`, `>=5`. Breakout-only entries are not rewritten.

The reproduced normal-cost trade artifact contains 385 retest trades, all with `signal_time` and `retest_time` available.

## Normal-cost isolated results
| Bucket | Trades | Return-R | PF | Avg-R | Max DD-R | Positive WFs | Negative WFs | Median WF-R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 129 | -30.6955 | 0.6477 | -0.2379 | -43.9417 | 12 | 28 | -1.0068 |
| 2 | 72 | +15.2715 | 1.4135 | +0.2121 | -7.0901 | 17 | 15 | +0.4028 |
| 3-4 | 51 | -13.6208 | 0.5888 | -0.2671 | -18.3042 | 10 | 18 | -0.4447 |
| >=5 | 133 | +1.3805 | 1.0186 | +0.0104 | -9.4696 | 19 | 23 | -0.3436 |

## Year stability
Bucket `2` annual Return-R by signal year:
- 2014: -6.1582 R
- 2015: +4.5321 R
- 2016: -3.0686 R
- 2017: +10.2863 R
- 2018: +9.7634 R
- 2019: -0.0835 R

Therefore the strongest normal-cost bucket is not positive across all years and is not yet a robust candidate.

## Gate state
- Normal-cost isolated evidence: COMPLETE for STALE001 buckets.
- Stress 1.5x / 2x trade-level evidence: `PENDING_EXACT_COST_REPLAY`.
- ADX001 / BODY001 / COMP001 isolated historical evaluation: `BLOCKED_PENDING_VERIFIED_FULL_OHLC_SEQUENCE`.
- Candidate status remains `RESEARCH`.
- No interaction test is authorized from this partial evidence.
- No production promotion, Paper start, broker execution, or LIVE implication.
