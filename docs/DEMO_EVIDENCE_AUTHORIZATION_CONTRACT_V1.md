# DEMO Evidence Authorization Contract V1

Status: IMPLEMENTED CONTRACT — NON-EXECUTABLE SCOPE EVIDENCE ONLY
Updated: 2026-09-13
Branch: `nextgen-bot-line-v1`

## Purpose

Close only the authorization-contract part of the verified demo-evidence bootstrap gap.

This contract creates a distinct, tightly scoped authorization record for a future DEMO evidence-acquisition stage. It does **not** create a broker transport, does not submit orders, does not authorize normal PAPER, and does not authorize LIVE.

The canonical runtime owner is:

- `src/daxlab/runtime/demo_evidence_authorization.py`

## Separation from existing authorization

The existing prospective/PAPER authorization remains independent.

`paper_user_authorized` and `ProspectiveAuthorization.paper_authorized` continue to mean final PAPER-stage authorization. They cannot be reused as a DEMO-evidence authorization object.

A future demo-evidence transport must therefore require its own `DemoEvidenceAuthorization` plus all other required safety/evidence gates. Passing this contract alone is never sufficient to send a broker order.

## Bound scope

`DemoEvidenceAuthorization` binds:

- explicit authorization identity;
- exact demo account identity;
- exact broker server identity;
- exact broker symbol;
- explicit validity start and expiry;
- explicit allowed evidence actions;
- explicit maximum submission-attempt count;
- fixed purpose `DEMO_EVIDENCE_ACQUISITION_ONLY`;
- `execution_capability=NONE`;
- `order_execution_enabled=false`.

No risk values are invented here. Existing broker economics, sizing/risk, loss/exposure, session admission, protection and host-health owners remain separate prerequisites for any later transport step.

## Account-mode rule

Only a separately observed `DEMO` account mode can satisfy the account-mode part of this contract.

The following fail closed:

- `REAL`;
- `CONTEST`;
- `UNKNOWN`;
- account/server/symbol mismatch;
- `trade_allowed=false`;
- expired or not-yet-valid scope;
- requested action outside the grant;
- exhausted submission-attempt scope.

`trade_allowed=true` is explicitly **not** proof that an account is DEMO.

The future MT5 adapter is responsible for translating the venue/account API into the normalized `DemoAccountMode` observation. This contract deliberately has no MT5 dependency and no venue call.

## Verdict semantics

`evaluate_demo_evidence_authorization(...)` returns a `DemoEvidenceAuthorizationVerdict`.

A positive verdict has status `SCOPE_VALID` and means only:

> the supplied DEMO-evidence authorization matches the supplied observed account context, requested action, time window and attempt scope.

It does **not** mean:

- broker submission authorized by itself;
- PAPER ready;
- PAPER user STOP-gate complete;
- broker evidence already exists;
- protection passed;
- risk/loss/session admission passed;
- broker acceptance/fill exists;
- LIVE eligible.

Every verdict preserves:

- `execution_capability=NONE`;
- `order_execution_enabled=false`.

## Fingerprint

The grant exposes a deterministic fingerprint over its complete bounded scope. This fingerprint is provenance evidence only. It proves the hashed fields are unchanged; it does not prove that the grant was issued by an authorized user or that all independent runtime gates are satisfied.

A later transport/checkpoint step must bind this fingerprint to the exact attempt it evaluates rather than accepting a cross-wired grant.

## Deferred work

Not implemented by this contract:

- MT5/demo transport adapter;
- broker-order submission API;
- account-mode integer/API mapping;
- post-PREPARED external-attempt checkpoint phase;
- broker ACK/FILL/REJECT ingestion;
- broker open-order/history recovery queries;
- restart/reconnect venue reconciliation execution;
- normal PAPER start;
- LIVE execution.

Those remain separate reviewed steps.

## Reuse requirements for later stages

A later DEMO-evidence transport must reuse, not duplicate, the existing canonical owners where applicable:

- `ExecutionIntent` and deterministic client identity;
- broker economics and broker-aware risk sizing;
- risk/loss/exposure/session admission owners;
- `SessionAdmissionGuardCheckpoint`;
- `nextgen_prepared_checkpoint.py`;
- broker order lifecycle;
- `BrokerExecutionCheckpointState`;
- broker reconciliation;
- typed broker execution protection;
- broker execution telemetry and telemetry journal;
- `StateStorePort` / `AtomicFileStateStore`;
- current Windows/MT5 host, clock and CLOSED-M5 safety gates.

No second lifecycle, store, reconciliation stack, telemetry stack or generic execution service is authorized by this contract.

## Current safety truth

- SHADOW: authorized, no broker orders;
- DEMO evidence transport: not implemented / not authorized;
- normal PAPER: not authorized;
- LIVE: not authorized;
- current execution capability: `NONE`;
- current order execution enabled: `false`;
- frozen V11.2 unchanged;
- CAND-001 strategy parameters unchanged;
- cost assumptions unchanged.
