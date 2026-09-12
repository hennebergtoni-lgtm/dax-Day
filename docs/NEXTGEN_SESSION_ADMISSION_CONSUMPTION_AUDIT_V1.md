# NextGen Session Admission Consumption Audit V1

Status: IMPLEMENTATION AUDIT / ADAPT_CANONICALLY
Step: 2174
Branch: `nextgen-bot-line-v1`

## Decision

**ADAPT_CANONICALLY, but do not implement a naive counter increment.**

NextGen has a canonical SessionAdmissionPolicy/Observation/Decision, a restart-safe observation checkpoint and freshness enforcement, but it does **not** yet have a canonical owner for consuming one admitted trade slot after downstream acceptance.

The existing CAND-001 owner is not that owner. `candidate_admission.py` derives its own Europe/Berlin session date and increments `trades_admitted` inside the strategy pipeline as soon as a CAND-001 trade plan is admitted. That behavior remains Candidate-specific and must not be promoted as the canonical product transition.

## Why observation-only increment is unsafe

A function that accepts only `SessionAdmissionObservation` and returns `trades_admitted + 1` cannot be restart-idempotent. After a crash or retry, the same downstream trade/admission consumption could be applied twice because the observation contains only a count and no identity of already-consumed events.

The canonical product transition therefore needs explicit consumption identity in addition to the visible observation count.

## Required canonical boundary

The next implementation should introduce one broker-neutral deterministic consumption state/transition with these properties:

1. caller supplies an already-derived normalized `session_key`;
2. caller supplies a deterministic `consumption_id` tied to the exact downstream trade-slot consumption event;
3. state remembers applied consumption IDs for the current session;
4. applying a new consumption ID increments the admitted count exactly once;
5. replaying the same consumption ID is idempotent and does not increment again;
6. a mismatched session key fails closed rather than silently resetting state;
7. transition output deterministically exposes the canonical `SessionAdmissionObservation` derived from the state;
8. strategy signals, proposed plans, denied risk decisions, blocked protection verdicts, duplicate publications and retries do not automatically count;
9. no timezone/date/calendar/session-reset inference is added;
10. no broker API, order submission, PAPER or LIVE authorization is added.

## Exact consumption event boundary

The canonical transition must **not infer consumption merely from a strategy signal, TradePlan, or SessionAdmissionDecision ALLOW**. `ALLOW` means a slot is available; it does not prove the slot was consumed.

A caller must explicitly present a deterministic consumption event only after its downstream product stage has committed to consuming that trade slot. The transition owner validates and records that explicit event; it does not decide when a broker order was submitted or filled.

This keeps the domain reusable across SHADOW, future PAPER and future LIVE without coupling session accounting to a broker SDK.

## Restart and persistence implication

Step 2172's `SessionAdmissionObservationCheckpoint` remains valid as freshness/protection evidence, but the count alone is insufficient to guarantee duplicate-safe consumption across restart.

A future implementation must persist the deterministic consumption state/IDs through the existing `StateStorePort` infrastructure. It may compose with the Step-2172 observation checkpoint, but it must not introduce a second storage implementation or silently reinterpret the V1 observation checkpoint as an idempotency ledger.

## CAND-001 compatibility

CAND-001's existing `Cand001AdmissionState` / `admit_cand001_trade()` behavior remains unchanged. Its session-date derivation, automatic reset and strategy-stage increment are Candidate-specific compatibility behavior, not the canonical NextGen owner.

## Safety

- `execution_capability=NONE` remains binding where applicable.
- `order_execution_enabled=false` remains binding.
- no broker submission path is introduced.
- PAPER remains unauthorized.
- LIVE remains unauthorized.
- frozen V11.2 evidence remains unchanged.

## Next step

Implementation is a separate next whole-number step. Step 2174 itself is audit/evidence only.
