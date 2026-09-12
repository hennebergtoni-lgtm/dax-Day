# NextGen Session Admission Guard Checkpoint V1

Status: IMPLEMENTED / CRASH-ATOMIC STATE EVIDENCE
Step: 2178

## Purpose

Bind the complete canonical session-admission protection truth into one deterministic payload that can be atomically replaced under one `StateStorePort` key.

## Bound evidence

`SessionAdmissionGuardCheckpoint` contains:

- exact policy fingerprint;
- exact `SessionAdmissionConsumptionState` including all consumption IDs and decision provenance;
- exact `SessionAdmissionObservation` derived from that state;
- caller-supplied timezone-aware `observed_at`;
- deterministic checkpoint fingerprint;
- disabled execution-safety fields.

Construction and restore require `checkpoint.observation == checkpoint.state.observation`. A separately stale count therefore cannot be paired with a newer ledger inside a valid guard checkpoint.

## Crash consistency

The complete guard is serialized as one canonical UTF-8 JSON payload and saved through one existing `StateStorePort` key. `AtomicFileStateStore` can therefore use its existing single-key atomic replacement semantics for the complete guard truth instead of coordinating multiple keys.

## Freshness semantics

`observed_at` is normalized to UTC at construction and is persisted exactly. Loading or restarting never refreshes it.

Freshness evaluation remains a consumer responsibility. This checkpoint does not infer that restored state is current merely because it was successfully read.

## Compatibility

The Step-2172 `SessionAdmissionObservationCheckpoint` and Step-2176 consumption-state checkpoint remain available as compatibility/diagnostic state contracts. They are not deleted or silently rewritten by this V1 guard.

Typed NextGen execution-protection wiring to the combined guard is intentionally deferred to the next independent work step.

## Exclusions

The guard checkpoint does not:

- derive dates, timezones, calendars or session keys;
- reset state on session change;
- access broker/account APIs;
- submit orders;
- authorize PAPER or LIVE;
- mutate CAND-001 behavior.

## Safety

- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- frozen V11.2 evidence remains unchanged.
