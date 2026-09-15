# NextGen Session Admission Consumption V1

Status: IMPLEMENTED / SHADOW-SAFE DOMAIN CONTRACT
Step: 2175

## Purpose

Provide one canonical broker-neutral owner for consuming an already-approved session trade slot exactly once.

## Contract

`SessionAdmissionConsumptionState` owns:

- caller-supplied normalized `session_key`;
- ordered unique `SessionAdmissionConsumptionRecord` values;
- deterministic state fingerprint;
- derived `SessionAdmissionObservation` where `trades_admitted == len(records)`.

Each record binds:

- deterministic sha256 `consumption_id`;
- exact `SessionAdmissionDecision.decision_fingerprint` that originally allowed the slot;
- deterministic record fingerprint.

`consume_session_admission()`:

1. never derives or resets a session;
2. requires exact session-key equality;
3. requires policy identity to match the supplied decision;
4. for a new consumption ID, requires the supplied decision to equal canonical evaluation of the current state observation and to be `ALLOW`;
5. records a new consumption ID exactly once;
6. replaying the same ID with the same decision provenance returns `IDEMPOTENT_REPLAY` without incrementing;
7. replaying the same ID with conflicting provenance fails closed;
8. a stale ALLOW decision cannot consume a different new ID after state has advanced.

## Deliberate exclusions

This V1 contract does not:

- persist the consumption state;
- derive dates, timezones, calendars or session keys;
- reset state when the session key changes;
- infer consumption from signals, trade plans or admission decisions alone;
- call broker/account APIs;
- submit orders;
- authorize PAPER or LIVE.

Persistence of the consumption ledger is a separate subsequent work step using the existing `StateStorePort` infrastructure.

## Safety

- `execution_capability=NONE` on transition evidence;
- `order_execution_enabled=false`;
- CAND-001 compatibility behavior remains unchanged;
- frozen V11.2 evidence remains unchanged.
