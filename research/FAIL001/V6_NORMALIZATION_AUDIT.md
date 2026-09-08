# FAIL001 V6 Normalization Audit

Status: RETAINED GUARDRAIL FAMILY / NOT A STRATEGY

## Role
FAIL001 remains a research-and-safety taxonomy. It does not create DAX entries, exits, thresholds or promotion decisions directly.

## Canonical translation
Accepted findings may map only to:
- DATA_GATE
- RESEARCH_GATE
- SETUP_GATE
- RISK_GATE
- EXECUTION_GATE
- MONITORING_GATE
- UI_GUARDRAIL

## Anti-duplication rule
FAIL001 must not duplicate lower-level implementation checks. It defines the failure mechanism and required control objective; the actual enforcement belongs to one canonical runtime/research component.

Examples:
- lookahead/repainting -> one causality contract + its tests, not a second parallel causality engine;
- data quality failure -> runtime data-quality gate, not a separate FAIL001 data validator;
- strategy drift -> canonical drift monitor, not duplicated rule logic;
- overtrading -> setup/no-trade policy, not a separate trade counter that independently blocks entries.

## Retained failure families
Overtrading, forced trades, overconfidence, revenge/risk escalation, cost neglect, leverage/ruin, lookahead/repainting, overfitting, parameter proliferation, regime blindness, data quality, unrealistic fills, drift, short-streak rule changes, selection bias and no-trade blindness.

## Evidence interpretation
Literature, public projects and operator observations may motivate a control but are not DAX strategy evidence. Any guardrail that changes execution semantics requires its own validation.

## V6 state
- family: FAIL001
- status: RETAINED
- evidence maturity: DESCRIPTIVE
- causality: NOT_APPLICABLE
- promotion_allowed: false
- implementation rule: control objective here; enforcement in canonical subsystem only.
