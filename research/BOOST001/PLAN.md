# BOOST001 — Bounded high-risk capital sleeve

Status: RESEARCH_ONLY

## Purpose
Study whether a deliberately isolated, expendable capital sleeve can support higher-risk sizing without contaminating the validated core strategy, changing setup quality, or creating loss-chasing behaviour.

BOOST001 is not permission to risk an entire sleeve on one trade. It is a research object for bounded sizing and risk-of-ruin analysis.

## Non-negotiable gates
A booster-eligible observation must pass, in order:
1. DATA_GATE — clean, causal, replayable data.
2. REGIME — recognized and validated market regime.
3. STRUCTURE — eligible DAX structure.
4. SETUP — independently validated deployable setup.
5. EXECUTION_GATE — broker/execution state healthy.
6. RISK_GATE — daily, trade and sleeve limits all green.
7. BOOST_GATE — booster-specific criteria green.

Failure at any stage means NO_TRADE or normal-risk handling. BOOST may never make an invalid setup valid.

## Research sleeve example
The initial research scenario uses a hypothetical EUR 200 fully expendable sleeve because this is the proposed Phase-1 booster budget. This is a simulation parameter, not a live allocation instruction.

## Forbidden behaviour
- martingale or loss-triggered size increases
- revenge trades
- averaging down because a trade lost
- bypassing daily loss limits
- borrowing/margin escalation to restore losses
- changing thresholds from recent P&L
- mixing booster P&L with core validation evidence

## Candidate sizing questions
Compare fixed fractional sleeve risk levels and hard euro caps under the exact same validated signals. Evaluate probability of sleeve ruin, maximum drawdown, loss streaks, recovery time, expected R, cost stress and sensitivity to execution degradation.

No candidate sizing level may be promoted from return alone. Survival and tail-loss behaviour are primary metrics.

## Relationship to FAIL001
BOOST001 consumes FAIL001 guardrails. In particular, revenge/risk escalation, overconfidence, excess leverage, forced trading and rule changes after losing streaks are explicit blockers.

## Separation from strategy research
BOOST001 changes sizing only. It must not alter entry, exit, regime, filter, OR, RR, stop or signal definitions. Strategy evidence is measured first at normalized R; booster simulations are downstream.

## Promotion path
RESEARCH -> SIMULATION -> PAPER_ONLY -> restricted pilot only after independent approval.

There is no direct path from BOOST001 research to live execution.
