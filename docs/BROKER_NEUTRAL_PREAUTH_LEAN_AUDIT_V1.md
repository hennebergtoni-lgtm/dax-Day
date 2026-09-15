# Broker-Neutral Pre-Authorization LEAN Audit V1

Status: BINDING ARCHITECTURE DECISION — NO BROKER SUBMISSION AUTHORIZED
Updated: 2026-09-11
Branch: `nextgen-bot-line-v1`

## Decision

No additional broker-neutral execution orchestrator is justified before real demo-broker evidence and explicit PAPER authorization.

The repository already owns the independent broker-facing evidence semantics that can be safely implemented without creating venue capability:

- `paper_contracts.py` — canonical `ExecutionIntent`, deterministic client identity and coarse paper vocabulary;
- `broker_order_lifecycle.py` — deterministic REQUESTED/ACK/REJECT/PARTIAL/FILLED/CANCELLED evidence state;
- `broker_execution_checkpoint.py` — one tamper-evident lifecycle + telemetry-journal persistence envelope;
- `broker_reconciliation.py` — local-vs-venue truth reconciliation contract;
- `broker_execution_protection.py` — fail-closed protection verdict over health, spread, reconciliation, sizing/risk, duplicate identity and admission;
- `broker_execution_telemetry.py` — credential-free deterministic execution evidence records;
- `broker_execution_telemetry_journal.py` — restart-safe telemetry publication/idempotency identity;
- `readiness.py` — independent PAPER gates for lifecycle, checkpoint, reconciliation, protection, telemetry, broker economics/risk and user authorization.

## Why no orchestrator now

A broker execution orchestrator would only become semantically meaningful when it can consume real venue submission/ACK/fill/reject/reconnect observations. Creating it before authorization would either:

1. merely call the existing pure evidence owners in synthetic order, producing no new broker evidence; or
2. begin to encode broker API/submission behavior before the authorization boundary is crossed.

Neither improves current safety or profitability evidence.

Therefore the pre-authorization architecture stops at pure evidence owners + readiness gates. The future authorized demo runtime should be a thin adapter over these owners rather than a parallel execution framework.

## Missing evidence is external, not missing software

The remaining PAPER blockers are primarily evidence lanes:

- current-branch Windows/MT5 host verification;
- real DE40 demo-broker economics;
- validated broker-risk/risk-profile/loss-cap policy on those economics;
- real demo lifecycle/checkpoint/reconnect/reconciliation/protection/telemetry observations;
- explicit user PAPER STOP-gate authorization.

Repository fixtures and CI remain necessary software proof but cannot satisfy those broker-facing gates.

## Reuse rule

Before adding any new broker execution component, require a named capability that is not already owned above and demonstrate why it can be implemented safely without broker submission capability. Architectural symmetry is not sufficient justification.

Do not add before authorization:

- MT5 order adapter;
- `order_send` wrapper;
- generic broker execution service;
- duplicate lifecycle/reconciliation/telemetry owners;
- a second recovery/checkpoint architecture.

## Safety boundary

- SHADOW authorized.
- PAPER/demo broker execution not authorized.
- LIVE not authorized.
- `execution_capability=NONE`.
- `order_execution_enabled=false`.

This audit is an anti-overbuild decision, not a PAPER readiness claim and not a profitability claim.
