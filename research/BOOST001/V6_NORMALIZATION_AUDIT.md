# BOOST001 V6 Normalization Audit

Status: RESEARCH-ONLY RISK/SIZING FAMILY

## Role
BOOST001 is downstream of strategy evidence. It may simulate bounded sleeve sizing only after a setup is independently valid under the normal research/promotion pipeline.

## Hard separation
BOOST001 must not change:
- entry logic
- exit logic
- regime definition
- filters
- OR definition
- RR
- stop logic
- signal eligibility

## Guardrails
BOOST001 consumes canonical FAIL001/risk controls instead of reimplementing them.
Explicit blockers include:
- martingale
- loss-triggered size increase
- revenge trading
- averaging down because of a loss
- bypassing daily/sleeve limits
- borrowing or leverage escalation to recover losses
- recent-P&L-driven threshold changes

## Evidence priorities
Return alone is insufficient. Required outputs include:
- sleeve survival probability
- risk of ruin
- maximum drawdown
- loss-streak distribution
- recovery time
- expected R
- cost/execution stress
- sensitivity to sizing assumptions

## V6 state
- family: BOOST001
- status: RESEARCH
- evidence maturity: PLAN_ONLY
- causality: NOT_APPLICABLE to signal timing; underlying signals must already be causal/validated
- promotion_allowed: false
- direct_live_path: false
- next valid evidence: isolated simulation using frozen signal evidence only.
