# NextGen Session Admission Consumption Persistence V1

Status: IMPLEMENTED / RESTART-SAFE STATE CONTRACT
Step: 2176

## Purpose

Persist the exact Step-2175 `SessionAdmissionConsumptionState` so deterministic consumption IDs and their bound admission-decision provenance survive restart without creating a second storage service.

## Persistence boundary

`SessionAdmissionConsumptionStateCheckpoint` stores:

- the exact canonical consumption state;
- every ordered unique consumption record;
- each record's deterministic identity and admission-decision provenance;
- the canonical state fingerprint;
- a deterministic checkpoint fingerprint;
- disabled execution-safety flags.

The bytes representation is canonical UTF-8 JSON with a trailing newline. Restore is strict and fail-closed on unknown or missing fields, schema drift, malformed records, duplicate consumption IDs, record/state/checkpoint fingerprint drift and execution-safety drift.

## Storage ownership

Save/load helpers use the existing `StateStorePort`. `AtomicFileStateStore` remains the file-backed implementation used by tests. No second file store, database or persistence service is introduced.

## Restart semantics

After restore, replaying an already-recorded `consumption_id` with the same bound `SessionAdmissionDecision` remains `IDEMPOTENT_REPLAY` and does not increment the session count.

The persistence owner does not:

- derive or change a session key;
- infer dates, timezones or reset boundaries;
- create a new admission decision;
- submit an order or access a broker;
- authorize PAPER or LIVE.

The Step-2172 observation checkpoint remains a separate freshness/protection evidence surface. This step does not silently replace or merge that contract.

## Safety

- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- CAND-001 compatibility behavior remains unchanged;
- frozen V11.2 evidence remains unchanged.
