# DEMO evidence local forward boundary — V1

Scope: Step 2199 integrated local proof and stop-boundary audit. This is not
Acceptance, a PAPER/LIVE grant, a transport authorization or broker evidence.
Repository: `hennebergtoni-lgtm/dax-Day`, PR #109, `nextgen-bot-line-v1`.
Work start: `9a07f679f10a4cae29083456b2930aba967fb919`.

## REUSE before BUILD

The Step-2182 and Step-2194 decisions remain binding. No second lifecycle,
identity, store, session owner, reconciliation engine or telemetry journal was
introduced. The higher reservation owner composes these existing contracts:

| Concern | Authoritative owner | Local forward use |
| --- | --- | --- |
| Shared attempt identity | `ExecutionIntent`, `NextgenPreparedCheckpoint` | Original intent/client/consumption identity is unchanged. |
| Consumed session slot | `SessionAdmissionGuardCheckpoint` | Original authoritative post-consumption guard remains bound. |
| REQUESTED evidence | `begin_nextgen_order_lifecycle`, `BrokerExecutionCheckpointState` | Original REQUESTED lifecycle/journal remain unchanged inside PREPARED. |
| Protection provenance | `BrokerExecutionProtectionVerdict` | Original ALLOW_EVIDENCE is historical preparation evidence, never execution authority. |
| Durable reservation | `DemoTransportAttemptReservation`, `StateStorePort` | Exactly the existing PREPARED attempt key is replaced once with RESERVED. |
| Account/host/feed | `parse_windows_mt5_bundle`, MT5 account-context/feed/host owners | DEMO context mandatory for reservation/query; absent context remains valid for legacy SHADOW. |
| Read-only query scope | `evaluate_demo_evidence_authorization` | QUERY is evaluated explicitly; SUBMIT scope does not imply QUERY scope. |
| Environment clock | `ClockPort` | Current query evaluation time is explicit and separate from original reservation/host timestamps. |
| Venue comparison | `reconcile_broker_order` | Exact supplied normalized agreement only; missing/unknown/contradictory truth blocks. |
| Telemetry/idempotency | `telemetry_from_reconciliation`, `admit_broker_execution_telemetry` | Existing typed records and journal reused; no new persistence or invented venue facts. |

## Local path and provenance

All additions live in `runtime/demo_transport_attempt_reservation.py`:

1. `reserve_demo_transport_attempt` durably reserves the existing attempt key.
   Its exact replay returns original evidence without another save, ordinal or
   session consumption. Callers serialize the key; the port is not CAS.
2. `load_reserved_demo_transport_attempt` loads exact original bytes through the
   existing strict codec and requires the caller's original reservation-fingerprint
   pin. Missing/PREPARED/corrupt/colliding state fails closed. An original expired
   scope can be restored as historical evidence; it is never renewed.
3. `demo_transport_restart_status` reports local RESERVED / REQUESTED and venue
   UNKNOWN / QUERY_RECONCILE_REQUIRED. It never permits resubmit or slot release.
4. `validate_reserved_demo_transport_query` checks a real supplied current bundle
   through its strict owner, exact account-context binding, healthy host/feed,
   causal/fresh observation time and current QUERY action scope. Invalid evidence
   fails before any future query adapter may be invoked. This is read-only scope
   preflight, not a submission or recovery grant.
5. `build_reserved_demo_transport_query_request` composes the pinned load, existing
   ClockPort and that same preflight into an ephemeral JSON-safe work item. Its
   deterministic fingerprint binds the same key/client identity, original
   reservation/PREPARED/authorization/account/ordinal and supplied current bundle,
   host/feed timestamps/fingerprint. It does not persist or create a new identity.
6. `reconcile_reserved_demo_transport_query` rechecks the current context/scope and
   returned observation time, then delegates to the existing reconciliation owner.
   A supplied ACK/fill contradicting local REQUESTED blocks; it is not silently
   ingested, promoted or used to repair local state.
7. Callers reuse the existing telemetry projection and broker journal. Current
   local/query work does not write a second journal or modify immutable PREPARED.
   A future authorized venue-event ingestion must use the existing lifecycle and
   broker checkpoint, atomically within the same attempt key; it is not added here.

New evaluation time never upgrades old host/feed evidence. Host age is limited by
original reservation policy; feed freshness is checked at evaluation as well as
at its supplied observation. Future/preceding observations fail closed. QUERY
remains possible after the submission budget is exhausted when explicitly scoped;
this does not return a slot or allow another submission.

## Integrated failure proof

`tests/test_demo_pretransport_boundary.py` exercises full local restart, pinned
QUERY work item, supplied observation, reconciliation, existing telemetry/journal
and replay under seven cases: normalized fixture agreement, missing venue,
UNKNOWN venue, unexpected ACK, unexpected fill, stale clock and wrong pin.

Every case preserves exact reservation bytes, one attempt key, one consumed slot,
original REQUESTED lifecycle with no venue ID/fill and NONE/false safety. Invalid
preflight never reaches the stand-in query. Telemetry replay is deduplicated by
the existing journal. An AST regression rejects SDK imports, submission calls and
literal execution activation in the reservation owner.

Other new tests prove keyword/positional legacy SHADOW compatibility, reservation
write interruption before/after persistence, real local file-store restart,
current-account/host/feed/time/scope cross-wiring and deterministic work-item
projection. These are Linux/offline/fixture proofs, not external broker proof.

## First external boundary / next step

The local handoff ends before a venue adapter is activated. No SDK query or order
API is implemented/called by the new owner. It accepts externally supplied
`VenueOrderObservation`; the read-only producer, lookup coverage and venue support
for the existing full deterministic client identity need real-host verification.
An empty open-order list alone never proves non-execution; history/fills and
ambiguous lookup remain necessary external evidence, not permission to retry.

The first actual progress from local REQUESTED toward qualifying broker lifecycle
and bootstrap evidence requires a separately reviewed, narrowly authorized DEMO
transport and the first real demo evidence order. That is the work-package stop
boundary. Another local mock/derived ACK cannot replace that external fact.

**Step 2200: PLANNED / REQUIRES EXPLICIT AUTHORIZATION.** No Step-2200 technical
implementation starts here. Before any future venue side effect, the main chat
must approve the bounded DEMO-only adapter/activation and establish:

- current Windows/MT5 host lane 2122, market-open feed and explicitly evidenced
  broker clock/timezone; no inferred session key/reset/timezone;
- exact observed DEMO account/server/symbol with current scope and budget;
- verified deterministic client-identity transport/lookup, open/history/fill
  coverage and query/reconcile-first restart/reconnect; no blind resubmit;
- current broker economics, explicit promoted risk/loss-cap policy, sizing,
  fresh feed/spread/protection and no contradictory local/venue evidence;
- same-key durable persistence before side effects and conservative ambiguity
  handling; never automatically free the consumed slot;
- no automatic normal PAPER or LIVE promotion. SCOPE_VALID and ALLOW_EVIDENCE
  remain evidence classifications, never grants.

Read-only lookup verification remains an external prerequisite and does not
itself authorize the first demo order. This work grants neither action.

## External evidence / governance

Both required PR checks are preserved: `dax-bot-1x-ci`, `research-lab-ci`. Actual
run/head/test evidence is recorded in `CURRENT_WORK_STEP.md`; later green checks
are required before closing this step. No ruleset/workflow/Acceptance/main/merge
change is made.

Local environment is Linux, without `pwsh`, MetaTrader5 or NEON_DATABASE_URL.
Six PowerShell tests are skipped locally. CI PowerShell fixtures do not establish
Windows/MT5 real-host evidence. Host lane 2122 remains WAITING_EXTERNAL.

A separate connected-Neon read-only SELECT on 2026-09-13 confirmed project
`dax-research-lab`, production default branch, database `neondb`, migrations
0001–0009, `cand001_operator_current`, zero unsafe Candidate rows and frozen engine
SHA `9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887`.
This is a limited direct connectivity/structural snapshot, not execution of the
full repository DB gate. No database writes or restore/import drills occurred.
All five main-only DB CI steps remain skipped on the PR; their fresh full-run
validation remains WAITING_EXTERNAL. Step-2189 verified history is not rewritten.

Safety remains: SHADOW authorized; DEMO/PAPER broker execution and LIVE not
authorized; execution_capability=NONE; order_execution_enabled=false; broker
orders NONE; frozen REF-V11.2, CAND-001 parameters and costs unchanged. No venue,
acceptance or fill facts and no profitability are asserted.
