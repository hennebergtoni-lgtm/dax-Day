# STRUCT001 — Descriptive Run 2026-09-08

Status: RESEARCH ONLY / OOS_DIAGNOSTIC_DERIVED / NOT PROMOTION PROOF.

## Causal alignment
STRUCT001 reuses LIQ001 confirmed levels. Raw M5 bar-open timestamps were shifted to completed-bar availability (`+5 minutes`) before structure extraction, and only bars strictly before frozen entry were eligible.

Coverage on 856 reproduced normal-cost OOS trades:
- trades with >=1 BOS before entry: 171
- BOS state-time violations: 0

Latest BOS descriptive results:
- DOWN: 99 trades, -22.1436R, PF 0.6420
- UP: 72 trades, -6.4131R, PF 0.8414
- NONE: 685 trades, -2.7525R, PF 0.9933

## Session overlap
BOS presence is strongly related to session age:
- EARLY: 81/762 trades (~10.6%)
- MIDDLE: 69/73 (~94.5%)
- LATE: 21/21 (100%)

The initial EARLY-BOS diagnostic looked negative (81 trades, -8.7383R, PF 0.8227), but stability failed:
- WF1-27: -11.1741R
- WF28-54: +0.9334R
- WF55-81: +1.5024R
- calendar years 2017 and 2018 were positive
- 41 active WFs: 12 positive / 29 negative, median -1.0029R

## Binding interpretation
No STRUCT001 selector is retained. Aggregate BOS weakness is heavily confounded with later-session timing, while the EARLY-only effect does not remain stable across eras. STRUCT001 stays as a causal descriptive research tool, not a deployable regime or exclusion rule.
