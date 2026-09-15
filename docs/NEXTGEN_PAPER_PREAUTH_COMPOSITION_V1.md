# NextGen PAPER Pre-Authorization Composition V1

Status: **STEP-2158 LEAN / SAFETY CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Decision

Do **not** create another pre-submission runtime orchestrator or authorization owner before real demo-broker evidence.

The binding pre-authorization composition already exists as two independent evidence surfaces:

1. concrete execution-protection evidence from `runtime.broker_execution_protection` for the specific lifecycle/client-order identity; and
2. system-level `evaluate_run_readiness(RunKind.PAPER, snapshot)` including the explicit independent `paper_user_authorized` STOP-GATE.

A future separately authorized thin demo adapter must require **both** surfaces to be true immediately before any venue submission. Neither surface can infer or replace the other.

## Why no new gate owner

`docs/BROKER_NEUTRAL_PREAUTH_LEAN_AUDIT_V1.md` already forbids an additional broker-neutral execution orchestrator before real demo evidence and explicit PAPER authorization. Adding a second verdict would duplicate current readiness/protection semantics without creating new evidence.

Therefore Step 2158 adds conformance proof, not production orchestration.

## Conformance proof

`tests/test_nextgen_paper_preauth_conformance.py` proves:

- a canonical NextGen `ExecutionIntent` retains identity through existing lifecycle and protection evidence;
- complete technical protection evidence cannot infer `paper_user_authorized=True`;
- even with every technical PAPER readiness flag true, `paper_user_authorized=False` blocks with `PAPER_USER_AUTHORIZATION_REQUIRED`;
- user authorization in a fixture cannot override a blocked concrete protection verdict;
- only the conjunction of specific protection evidence and system PAPER readiness can be true in a hypothetical fully-ready fixture;
- protection evidence remains `execution_capability=NONE` and `order_execution_enabled=false`.

A test fixture with `paper_user_authorized=True` is proof of gate behavior only. It does not change repository/runtime authorization state.

## Current authorization truth

Repository/project truth remains:

- SHADOW authorized;
- PAPER/demo broker execution **not authorized**;
- LIVE **not authorized**;
- `execution_capability=NONE`;
- `order_execution_enabled=false`.

The manual MetaQuotes-Demo plumbing test performed outside the bot does not change this authorization state.

## Next implication

The remaining path to a controlled bot demo is not another synthetic execution framework. It is evidence and thin-adapter work: read-only broker economics/instrument mapping, market-open host evidence, promoted broker-aware risk/loss-cap policy, and only later an explicitly authorized venue submission adapter.
