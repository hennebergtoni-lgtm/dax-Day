# V12 ISOLATED SCREENING EVIDENCE — MILESTONE 246

Status: DESCRIPTIVE SCREENING ONLY — NOT PROMOTION EVIDENCE

## Purpose
This document records isolated causal screening observations for the four V12 pre-paper research families. It does not change V11.2, does not promote any family, and does not authorize Paper or LIVE execution.

## Evidence identity
- Frozen V11.2 reference unchanged.
- Audited 2014-2019 source recovered as `GER30_5m.csv`.
- Raw M5 rows: 481,824.
- Session: Europe/Berlin 09:00-17:30 inclusive.
- Session rows: 172,319.
- Session days: 1,673.
- OHLC errors: 0.
- Historical session fingerprint reproduced exactly after restoring the canonical index name `timestamp_utc` before `fingerprint_ohlc`: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`.
- Reproduced clean trade source: 856 rows, provenance `NEWLY_REPRODUCED_NO_HISTORICAL_FROZEN_HASH`, hash `f60bb5fc...` (full value remains governed by the evidence gate).

## Causality / join
- Feature inputs use only completed M5 bars.
- Closed-bar join succeeded for 856/856 reproduced trades.
- ADX implementation was cross-checked against `v12_prepaper_features.adx_feature` on real trade indices with zero sample difference.
- BODY001 and COMP001 calculations follow the repository primitives directly.

## Screening observations
These bins are descriptive diagnostics, not predeclared promotion thresholds.

### ADX001
Diagnostic buckets:
- ADX < 20: 185 trades, -22.570 R, PF 0.798.
- ADX 20-25: 161 trades, -4.739 R, PF 0.952.
- ADX 25-40: 365 trades, -6.964 R, PF 0.968.
- ADX >= 40: 145 trades, +2.964 R, PF 1.034.

A diagnostic ADX >= 20 screen leaves 671 trades at -8.7395 R and PF 0.9784 versus the frozen baseline -31.3092 R and PF 0.9393. Year effects are mixed, including deterioration in 2016 and 2019. This is not robust-candidate proof.

### BODY001
Diagnostic body-fraction buckets:
- < 0.40: 216 trades, -26.848 R, PF 0.806.
- 0.40-0.70: 333 trades, +17.950 R, PF 1.095.
- >= 0.70: 307 trades, -22.410 R, PF 0.882.

Direction agreement alone:
- disagreement: 144 trades, -16.427 R, PF 0.822.
- agreement: 712 trades, -14.882 R, PF 0.965.

A diagnostic 0.40-0.70 body fraction plus trade-direction agreement cell has 278 trades, +21.5444 R, PF 1.1401, but 2014 and 2018 remain negative. This is descriptive and was not predeclared as a promotion threshold.

### COMP001
Diagnostic TR-ratio buckets, using repository `range_compression(..., lookback=14)` semantics:
- < 0.75: 189 trades, -18.626 R, PF 0.845.
- 0.75-1.25: 337 trades, -28.994 R, PF 0.864.
- 1.25-2.00: 199 trades, +22.906 R, PF 1.213.
- >= 2.00: 131 trades, -6.596 R, PF 0.913.

The 1.25-2.00 diagnostic cell is positive overall but negative in 2017 and 2018. This is descriptive only and distinct from ATR001.

### STALE001
Previously recorded normal-cost retest-only screening remains diagnostic. The 2-bar cell was the most interesting normal-cost slice, but year/WF stability is mixed and exact stress-cost replay remains pending.

## Trial-discipline interpretation
T012-T015 were predeclared as feature hypotheses, but no numerical cutoffs were predeclared in the registry or hypothesis ledger. Therefore any promising numerical cells discovered here are OOS-diagnostic/descriptive discoveries and cannot be relabeled as independent validation.

## Milestone-246 state
PARTIAL / SCREENING COMPLETE FOR NORMAL-COST FEATURE SLICES.

Not yet sufficient to mark milestone 246 complete because:
1. exact stress 1.5x and 2x evaluation has not yet been reproduced for the filtered slices;
2. discovered numerical cells require fresh-proof discipline before any robust-candidate status;
3. no production, Paper, or LIVE promotion is allowed from these observations.
