# NextGen Session Consumption Commit-Boundary Audit V1

Status: STEP 2182 AUDIT / BINDING PRODUCT-ARCHITECTURE DECISION

## Purpose

Define the exact local commit boundary after typed NextGen execution protection returns `ALLOW_EVIDENCE`, before any future external broker submission capability exists. This audit closes the interrupted Step 2180 scope under monotonic Step 2182 and preserves the existing execution-safety boundary: no broker order submission, no PAPER authorization and no LIVE authorization are introduced here.

## Audited owners

The current repository already owns the required primitives:

- canonical `ExecutionIntent.intent_id`;
- NextGen lifecycle adaptation with `client_order_id = intent.intent_id`;
- canonical `BrokerOrderLifecycleState` and `REQUESTED` lifecycle state;
- deterministic `consume_session_admission(...)` and `SessionAdmissionConsumptionState`;
- atomic `SessionAdmissionGuardCheckpoint` binding policy, full consumption ledger, policy-derived observation and caller-supplied `observed_at`;
- `StateStorePort` / `AtomicFileStateStore` with atomic replacement for one key/file;
- `BrokerExecutionCheckpoint` as an existing atomic broker-execution checkpoint owner;
- fail-closed broker reconciliation keyed by the same `client_order_id` identity;
- typed NextGen execution protection whose session evidence is the authoritative `SessionAdmissionGuardCheckpoint`.

No second lifecycle, state-store, journal or identifier stack is justified.

## Crash-window finding

The external broker and the local `StateStorePort` do not share one transaction. Therefore a purely local implementation cannot make both external submission and local session consumption atomically commit together.

Two unsafe orderings must be distinguished:

### Submit before consume

If an external order is accepted and the process crashes before session consumption is durably committed, restart can observe the old session count and silently allow an additional order. This is the unacceptable `submit-before-consume` window because it can create duplicate exposure or an extra session allowance.

### Consume before an unrecorded submission attempt

If session consumption is durably committed before an external submission and the process then fails before the broker receives an order, the system can conservatively lose one session slot. This is under-trading, not duplicate exposure. The slot must not be silently released or reconstructed without explicit later evidence and policy.

The product therefore chooses the conservative local write-ahead boundary: durable local preparation must precede any future external broker call.

## Binding identity

One logical attempt must use one deterministic identity across all involved owners:

`ExecutionIntent.intent_id == BrokerOrderLifecycleState.client_order_id == session consumption_id`

The existing `intent_id` / `client_order_id` mapping is REUSED. No new broker-attempt identity is introduced.

## Required PREPARED commit sequence

A future execution-capable composition must follow this ordering:

1. Evaluate typed NextGen execution protection against the current authoritative `SessionAdmissionGuardCheckpoint`.
2. Continue only when protection returns the canonical allow evidence; retain its provenance/fingerprint.
3. Apply `consume_session_admission(...)` using `consumption_id = intent.intent_id`.
4. Build the updated `SessionAdmissionGuardCheckpoint` from the resulting consumption state. The guard observation must remain derived from that state.
5. Build the existing NextGen `REQUESTED` broker lifecycle for the same `intent_id` / `client_order_id`.
6. Persist one higher-level local `PREPARED` checkpoint that atomically binds, in one `StateStorePort` key/payload:
   - the updated authoritative session guard;
   - the `REQUESTED` lifecycle / existing broker-execution checkpoint semantics;
   - the protection provenance/fingerprint that allowed preparation;
   - the shared `intent_id == client_order_id == consumption_id` identity;
   - deterministic checkpoint provenance sufficient to reject cross-wiring or tampering.
7. Only after that single local PREPARED checkpoint is durably stored may a later, separately authorized execution layer be permitted to attempt an external broker submission.
8. After restart, a PREPARED-but-unresolved attempt must never be blindly submitted again. The runtime must first reconcile using the same `client_order_id` and existing reconciliation owner/evidence.

Step 2182 is audit-only. It does not implement step 7 or any broker call.

## REUSE / ADAPT / DEFER

### REUSE

- `ExecutionIntent.intent_id` as the canonical attempt identity.
- Existing NextGen mapping `client_order_id = intent.intent_id`.
- The same identity as deterministic session `consumption_id`.
- `consume_session_admission(...)` and its retry-idempotent consumption ledger.
- `SessionAdmissionGuardCheckpoint` as authoritative session truth.
- `BrokerOrderLifecycleState` and existing NextGen `REQUESTED` lifecycle construction.
- Existing `BrokerExecutionCheckpoint` validation/checkpoint semantics where embedded by the composition.
- Existing `StateStorePort` / `AtomicFileStateStore` single-key atomic persistence.
- Existing broker reconciliation keyed by `client_order_id`.
- Existing typed protection and its provenance/fingerprint.

### ADAPT

Add exactly one higher-level, evidence-neutral local PREPARED checkpoint/composition owner that binds the updated session guard, REQUESTED lifecycle/broker-execution checkpoint semantics, protection provenance and shared attempt identity into one atomic payload under one existing StateStore key.

This adaptation must not create a second lifecycle, second state store, second reconciliation system or second session-admission owner.

### DEFER

The following remain outside Step 2182 and are not authorized by this audit:

- any real or demo broker order submission/API call;
- PAPER authorization;
- LIVE authorization;
- automatic rollback/release of a consumed session slot;
- blind re-submission after restart or ambiguous external outcome;
- broker-specific idempotency guarantees beyond evidence actually verified for the connected venue;
- session-key, date, timezone or reset derivation;
- mutation of CAND-001 defaults.

## Recovery rule

A durable PREPARED record means the local system has reserved/consumed the session slot for that deterministic attempt and recorded a REQUESTED lifecycle, but it does not prove the external broker received or accepted anything.

After restart or ambiguous failure, the next safe action is reconciliation/evidence gathering by the existing `client_order_id` identity. Lack of a broker observation must not be silently converted into permission to re-submit or release the slot. Such release/retry semantics require a separate explicit product decision with evidence.

## Safety consequence

The chosen boundary prefers conservative under-trading over duplicate exposure. A crash after local PREPARED persistence but before a future broker call can consume a session slot without an order. A crash must not create the opposite failure mode in which an accepted external order exists while local session truth still silently permits another slot.

## Minimal next product step

The smallest evidence-neutral implementation after this audit is a single atomic NextGen PREPARED checkpoint owner over the existing primitives. It should build/validate/persist/load the combined local state and prove restart/tamper/idempotency behavior. It must stop before any external broker submission.

That implementation belongs to the next whole-number work unit after Step 2182, subject to the Step-Close-Gate and pointer synchronization.

## Unchanged safety boundary

- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- no broker order submission path is authorized by this audit;
- PAPER remains unauthorized;
- LIVE remains unauthorized;
- `NO_STRATEGY_AUTO_PROMOTION` remains unchanged;
- frozen V11.2 evidence and verified historical fingerprints remain unchanged.
