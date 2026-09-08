# ATR001 — Descriptive Reference Run — 2026-09-08

Status: DESCRIPTIVE RESEARCH ONLY. Promotion blocked. V11.2 unchanged.

## Inputs
- audited GER30 M5 raw rows: 481,824
- reproduced clean V11.2 normal-cost OOS trades: 856
- dataset session fingerprint: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`
- trade ledger historical role: newly reproduced clean evidence, not historical file identity

## Causality
M5 timestamps are treated as bar-open timestamps. ATR14 becomes available at bar-open + 5 minutes. The latest completed ATR observation strictly before entry is used. The selected OR must also be complete strictly before entry. No entry-bar OHLC is consumed.

## Coverage
- eligible: 856 / 856
- rejected: 0

## Overall descriptive distribution
ATR14 points quantiles:
- P10 6.9246
- P25 9.0250
- P50 11.4871
- P75 15.2470
- P90 19.2256

OR/ATR quantiles:
- P10 1.6071
- P25 2.0663
- P50 2.6418
- P75 3.3470
- P90 4.2166

These full-sample quantiles are DESCRIPTIVE_ONLY and are forbidden as ex-ante trading thresholds.

## Calendar-year coverage
| Year | Trades | ATR median | OR/ATR median | Existing trade R |
|---|---:|---:|---:|---:|
| 2014 | 184 | 9.3668 | 2.4407 | -15.6485 |
| 2015 | 139 | 17.0718 | 2.8159 | 4.4717 |
| 2016 | 112 | 14.1802 | 2.4602 | 3.3853 |
| 2017 | 174 | 8.9493 | 2.7868 | -12.0306 |
| 2018 | 105 | 12.4615 | 2.8824 | -16.8529 |
| 2019 | 142 | 10.8501 | 2.7054 | 5.3658 |

## Existing setup slices
| OR | Entry | Trades | ATR median | OR/ATR median | Existing trade R |
|---:|---|---:|---:|---:|---:|
| 5 | breakout | 193 | 10.6999 | 2.1642 | 4.6105 |
| 5 | retest | 175 | 10.8087 | 2.3107 | -15.1315 |
| 15 | breakout | 278 | 13.2317 | 2.8623 | -8.2553 |
| 15 | retest | 210 | 11.5114 | 3.1178 | -12.5329 |

## Broad WF eras
| WF era | Trades | ATR median | OR/ATR median | Existing trade R |
|---|---:|---:|---:|---:|
| WF1-27 | 299 | 12.3204 | 2.5246 | -9.8813 |
| WF28-54 | 296 | 10.7952 | 2.6581 | -12.6950 |
| WF55-81 | 261 | 11.6841 | 2.7927 | -8.7329 |

## Artifact
Local descriptive feature CSV SHA256:
`d1e1d472056c4f6172ac9fe649261205de74c3fe419e20bd1545f0a86d44e9c9`

## Interpretation
ATR level varies materially by year, while OR/ATR is somewhat more normalized but still shifts across periods and setup families. This supports continuing to train-only regime construction rather than using one global full-sample cutoff. Existing R values above are descriptive association only; they are not evidence for a selector.

## Next test
Construct a small number of per-WF train-only ATR/OR-ATR regime bins, freeze them before each OOS slice, then measure OOS trade count, R, PF, DD, WF stability and cost stress. No dense threshold grid.
