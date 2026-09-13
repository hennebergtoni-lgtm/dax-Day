# DEMO Evidence Pre-Transport Composition Audit V1

Status: BINDING ARCHITECTURE DECISION — NO BROKER SUBMISSION AUTHORIZED
Updated: 2026-09-13
Branch: `nextgen-bot-line-v1`
Step: 2194

## Decision

The repository does not need a second execution orchestrator before DEMO evidence transport. Existing owners already cover intent identity, risk/loss/session protection, local PREPARED persistence, DEMO-only scope authorization, redacted account identity and read-only MT5 host observation.

The smallest remaining pre-transport capability is a **durable one-way DEMO transport-attempt checkpoint/reservation** that composes those existing owners and is persisted before any later external venue call.

No venue adapter or order API is authorized by this decision.

## Existing owners to REUSE

1. `ExecutionIntent` and canonical `intent_id`.
2. `BrokerExecutionProtectionVerdict` / typed NextGen protection for the original pre-consumption safety decision.
3. `NextgenPreparedCheckpoint` for immutable local PREPARED evidence, including post-consumption session guard and existing REQUESTED broker lifecycle/checkpoint semantics.
4. `DemoEvidenceAuthorization` and `DemoEvidenceAuthorizationVerdict` for separately granted DEMO-only account/server/symbol/time/action/submission scope.
5. `Mt5DemoAccountContextEvidence` for redacted observed account identity, exact server, exact symbol, DEMO/CONTEST/REAL/UNKNOWN mode and trade-allowed observation.
6. `Mt5HostObservation` / existing host, clock, feed and symbol-resolution owners for fresh read-only host veto evidence.
7. Existing `StateStorePort` / atomic file store; no second persistence stack.
8. Existing broker lifecycle, checkpoint, reconciliation and telemetry owners for later venue evidence.

`ExecutionIntentSinkPort` remains only a dependency boundary and is not an execution or transport authorization.

## Why PREPARED alone is insufficient

`NextgenPreparedCheckpoint` proves that the attempt was locally prepared before external submission:

- the session slot is consumed once;
- the post-consumption guard is authoritative;
- the broker lifecycle is REQUESTED;
- no venue order ID or fill exists;
- typed protection is `ALLOW_EVIDENCE`;
- exact retry loads the same local evidence without consuming or saving again.

PREPARED deliberately does **not** prove that an external submission was attempted. Its parser correctly rejects ACK/FILL/venue evidence.

Therefore using PREPARED alone as the restart marker for a future broker call leaves an ambiguity: after a process crash or transport timeout, the caller cannot distinguish “never called venue” from “venue may have accepted the request but local outcome was not persisted.” Blind resubmission would create duplicate-exposure risk.

## Why the DEMO authorization alone is insufficient

The Step-2191 authorization contract can limit `max_submissions`, but `submissions_already_attempted` is currently caller-supplied. Without durable local attempt reservation, that count cannot by itself survive crash/restart and cannot safely prevent a duplicate external attempt.

A positive `SCOPE_VALID` verdict remains non-executable (`execution_capability=NONE`, `order_execution_enabled=false`). It must never be interpreted as venue permission by itself.

## Fresh account/host evidence rule

The Step-2193 normalized account payload proves redacted account identity/mode/server/symbol but intentionally has a stable identity fingerprint. Freshness comes from the surrounding real MT5 host observation/probe cycle.

Before a future DEMO submit attempt, the pre-transport boundary must therefore bind both:

- the normalized account-context fingerprint / exact observed context; and
- a fresh host-observation identity/timestamp plus the applicable host/feed/clock/symbol veto result.

A stale historical DEMO observation must never satisfy a future submit attempt merely because account identity is unchanged.

The original protection verdict embedded in PREPARED remains immutable historical evidence. New real-host observations are additional veto evidence; they must not rewrite or “refresh” the original PREPARED protection/session evidence after session consumption.

## Smallest missing capability

Add one higher-level, deterministic, tamper-evident local owner with a one-way phase such as `TRANSPORT_ATTEMPT_RESERVED`.

It must bind at minimum:

- canonical attempt identity (`intent_id == client_order_id == consumption_id`);
- immutable `NextgenPreparedCheckpoint.fingerprint`;
- DEMO authorization fingerprint;
- requested action = `SUBMIT_EVIDENCE_ORDER`;
- redacted MT5 account-context fingerprint and exact DEMO account/server/symbol context;
- fresh host observation timestamp/identity and required host/feed/clock veto evidence;
- submission-attempt ordinal/count within the authorization scope;
- deterministic checkpoint fingerprint;
- `execution_capability=NONE` and `order_execution_enabled=false` as evidence fields.

The reservation must be durably persisted **before** a later separately authorized venue adapter is invoked.

## Storage / concurrency rule

Do not create a second store or parallel attempt journal.

The Step-2187 decision that one existing StateStore key owns the attempt remains binding. Because `StateStorePort` provides atomic replacement but no compare-and-swap, the process owner must serialize access to that attempt key.

A future implementation may evolve the higher-level payload/phase around the existing PREPARED evidence, but must not weaken the PREPARED parser by allowing venue ACK/FILL data inside the PREPARED object itself.

## Restart / ambiguous transport rule

After `TRANSPORT_ATTEMPT_RESERVED` exists, restart behavior is fail-safe:

1. never blindly submit that identity again;
2. query/reconcile the real venue first by the same deterministic client identity;
3. an empty open-order list alone is not proof of non-execution;
4. no automatic session-slot release;
5. no automatic retry unless a later separately reviewed recovery contract can prove it safe;
6. preserve original PREPARED, authorization and account/host provenance unchanged.

This intentionally prefers under-trading over duplicate exposure.

## Cross-wiring that must fail closed

A future attempt reservation must reject at least:

- PREPARED intent identity != authorization-bound attempt identity;
- authorization account/server/symbol != fresh observed DEMO context;
- account mode REAL / CONTEST / UNKNOWN;
- account trading not allowed;
- expired / not-yet-valid authorization;
- requested action out of scope;
- submission attempt ordinal above authorization limit;
- stale/unhealthy host, feed or clock evidence;
- exact symbol mismatch;
- PREPARED protection not `ALLOW_EVIDENCE`;
- PREPARED lifecycle not REQUESTED or already carrying venue/fill evidence;
- tampered PREPARED / authorization / account-context fingerprints;
- store-key collision with different attempt/provenance.

## What is explicitly deferred

Not part of Step 2194 and still unauthorized:

- MT5 `order_send` or any venue submission adapter;
- actual DEMO broker order;
- normal PAPER authorization;
- LIVE authorization;
- venue ACK/FILL/reject ingestion implementation;
- automatic cancellation/retry/slot release;
- any CAND-001, V11.2, strategy or cost mutation.

## Recommended next sequence

1. Implement and test only the durable DEMO transport-attempt reservation/checkpoint owner.
2. Red-Team its crash/restart/cross-wiring/idempotency semantics.
3. Only after that passes, audit the thinnest possible MT5 DEMO transport adapter separately.
4. Actual DEMO evidence acquisition remains a distinct user authorization/start decision and must additionally satisfy current Windows/MT5 market-open evidence and promoted economics/risk/loss policies.

## Work-credit decision

This audit itself does not justify another Work call: the missing local checkpoint is narrow and can be implemented in the main Plus chat.

A Work Red-Team becomes high-value **after** that checkpoint exists and before any venue submission adapter is enabled, because that review will span authorization, persistence, restart ambiguity, reconciliation and broker transport simultaneously.

## Safety truth

- SHADOW remains authorized with no broker orders.
- DEMO evidence submission remains NOT IMPLEMENTED / NOT AUTHORIZED.
- normal PAPER remains NOT AUTHORIZED.
- LIVE remains NOT AUTHORIZED.
- no profitability claim is made.
- frozen V11.2, CAND-001 strategy parameters and cost assumptions remain unchanged.
