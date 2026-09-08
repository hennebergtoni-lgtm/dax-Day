# ATR001 — OR15 × ATR HIGH × OR/ATR MID diagnostic — 2026-09-08

Status: OOS_DIAGNOSTIC_DERIVED. Promotion blocked. V11.2 unchanged.

## Discovery context
This pattern was identified after inspecting OOS diagnostics from the reproduced V11.2 normal-cost trade ledger. It is therefore NOT independent validation and MUST NOT be promoted directly.

## Candidate definition
- existing V11.2 selected trade uses OR15
- ATR regime = HIGH, where HIGH is determined from that WF's own 45-day training-slice ATR distribution
- OR/ATR regime = MID, where MID is determined from that WF's own 45-day training-slice OR/ATR distribution
- regime boundaries are frozen before the 20-day OOS slice

## OOS diagnostic result
- trades: 74
- return: +18.8893 R
- average R: +0.2553
- PF: 1.5035
- max DD: -4.0722 R

## Stability observations
All six calendar years are positive:
- 2014: +4.4153 R / 22 trades
- 2015: +0.8965 R / 15 trades
- 2016: +0.4800 R / 5 trades
- 2017: +6.2049 R / 11 trades
- 2018: +2.8080 R / 10 trades
- 2019: +4.0845 R / 11 trades

All broad WF eras are positive:
- WF1-27: +5.3536 R / 35 trades
- WF28-54: +3.6667 R / 15 trades
- WF55-81: +9.8690 R / 24 trades

Both entry families are positive:
- breakout: +11.7919 R / 46 trades / PF 1.4822
- retest: +7.0974 R / 28 trades / PF 1.5433

Per-WF support is weaker than the aggregate presentation suggests:
- active WFs: 30
- positive WFs: 16
- negative WFs: 14
- median active-WF R: +0.3127
- median trades per active WF: 2

Every leave-one-year-out aggregate remains positive, but this is still a retrospective robustness diagnostic, not fresh OOS evidence.

## Anti-duplication observation
The candidate appears inside all three frozen V11.2 OR/ATR filter states (`none`, `above_0.2`, `between_0.2_0.6`), so it is not merely identical to the existing categorical filter. This suggests possible incremental state information, but does not prove an incremental tradable edge.

## Mandatory evidence label
`OOS_DIAGNOSTIC_DERIVED_NOT_PROMOTION_PROOF`

## Required next path
1. Freeze this exact hypothesis without changing thresholds.
2. Do not search neighbouring thresholds for a better result.
3. Re-test through a predeclared evaluation design that cannot use the discovery sample as independent proof.
4. Require cost stress, WF/stability review and prospective evidence before any promotion.
5. Paper/Live remain blocked.
