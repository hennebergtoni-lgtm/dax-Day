# LIQ001 — Descriptive Run 2026-09-08

Status: RESEARCH ONLY / OOS_DIAGNOSTIC_DERIVED / NOT PROMOTION PROOF.

## Causal alignment
Raw M5 timestamps are bar-open timestamps. For this run, LIQ001 receives completed-bar availability timestamps (`raw_open + 5 minutes`) and only bars with availability strictly before frozen `entry_time`.

Coverage on 856 reproduced normal-cost OOS trades:
- trades with >=1 confirmed level before entry: 404
- trades with >=1 confirmed wick-rejection sweep: 181
- sweep state-time violations: 0

Latest sweep side descriptive results:
- HIGH_SIDE: 85 trades, -9.1484R, PF 0.8211
- LOW_SIDE: 96 trades, -15.7671R, PF 0.7169
- NONE: 675 trades, -6.3938R, PF 0.9844

## Session confounder
Sweep presence is highly dependent on elapsed session time:
- EARLY: 89/762 trades had a sweep (~11.7%)
- MIDDLE: 71/73 (~97.3%)
- LATE: 21/21 (100%)

Within EARLY, sweep presence was approximately neutral: 89 trades, -0.0483R, PF 0.9990. Therefore the strongly negative aggregate sweep groups are largely explained by later-session exposure rather than clear incremental sweep information.

## Binding interpretation
No LIQ001 selector is retained from this descriptive run. The sweep signal is heavily confounded with SESSION001 and does not establish independent value. Variant A remains a causal research primitive for future fresh/prospective testing, not a deployable filter.
