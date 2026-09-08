# FAIL001 — NO_TRADE taxonomy

Status: RESEARCH CONTROL

A valid `NO_TRADE` is not missing activity. It is an auditable system outcome.

## Primary classes
- `DATA_UNSAFE`: stale, gap, duplicate, out-of-order, clock skew, source disagreement or other unsafe feed state.
- `SESSION_BLOCKED`: outside the validated trading session or invalid trading-state window.
- `REGIME_UNKNOWN`: the system cannot assign an eligible validated regime with sufficient evidence.
- `STRUCTURE_MISSING`: no validated market structure/setup context is present.
- `SETUP_INVALID`: a candidate structure exists but the exact entry conditions are not satisfied.
- `FILTER_BLOCKED`: an eligible validated filter blocks the candidate setup.
- `RISK_BLOCKED`: per-trade, daily, exposure or emergency risk controls prohibit a trade.
- `EXECUTION_BLOCKED`: spread, feed, broker/execution health or contradictory state makes execution unsafe.
- `EVIDENCE_BLOCKED`: a research-only tool is visible but not permitted to change trade eligibility.
- `COOLDOWN_BLOCKED`: session/day trade limit or validated cooldown prevents an additional trade.

## Required analysis dimensions
Every NO_TRADE research record should retain when available:
- event/session time;
- data-quality state;
- regime and structure state;
- candidate setup;
- blocker class and detailed blocker reasons;
- filters evaluated and their evidence state;
- risk-gate result;
- execution-health result;
- final deterministic decision ID/config fingerprint.

## Opportunity-cost analysis
NO_TRADE decisions may later be evaluated against subsequent market movement, but this must remain diagnostic only. Future movement must never be fed back into the original historical decision or used to relabel a causal blocker as an error.

Useful diagnostics include:
- avoided loss rate;
- missed positive-R opportunity rate;
- distribution of hypothetical MFE/MAE after blocked decisions;
- blocker concentration by regime/session/volatility;
- overlap between multiple blockers.

## Promotion rule
A blocker may be weakened, removed or converted into a softer annotation only after independent OOS/WF evidence. A handful of missed winners is not evidence to relax a gate.
