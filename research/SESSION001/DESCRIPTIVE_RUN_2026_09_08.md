# SESSION001 — Corrected Descriptive Run 2026-09-08

Status: RESEARCH ONLY / OOS_DIAGNOSTIC_DERIVED / NOT PROMOTION PROOF.

## Timestamp correction
Frozen reproduced trade timestamps are Berlin-session wall-clock values stored without an offset. An initial diagnostic pass that interpreted them as UTC was rejected. The corrected pass localizes trade timestamps to `Europe/Berlin` before any UTC market-data alignment.

Corrected validation:
- trades: 856
- inside Berlin 09:00-17:30 session: 856/856
- entry range: 10 to 505 minutes after session open
- momentum state-time causality violations in paired run: 0

## Fixed coarse phases
Predeclared phases from SESSION001 code:
- EARLY: <=120 minutes after 09:00
- MIDDLE: >120 and <=300 minutes
- LATE: >300 minutes

Results:
- EARLY: 762 trades, -7.4304R, PF 0.9838
- MIDDLE: 73 trades, -23.1851R, PF 0.5164
- LATE: 21 trades, -0.6937R, PF 0.9238

MIDDLE stability diagnostics:
- negative in 2014, 2015, 2017, 2018, 2019; positive only in 2016
- WF1-27 -8.8793R
- WF28-54 -6.3900R
- WF55-81 -7.9157R
- 41 active WFs: 12 positive / 29 negative
- median active-WF R: -1.0052R
- OR5 MIDDLE: -9.1430R, PF 0.5412
- OR15 MIDDLE: -14.0421R, PF 0.4988

## Binding interpretation
The MIDDLE-session weakness is an interesting OOS diagnostic exclusion hypothesis, not independent promotion evidence. It MUST NOT be added to V11.2 or treated as validated from this ledger. Its exact coarse definition is frozen for any later fresh/prospective evaluation; minute-level refinement on the same OOS evidence is prohibited.
