# NextGen Session Observation Restart & Freshness Audit V1

Status: **STEP-2171 AUDIT — ADAPT_CANONICALLY**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Question

Does canonical `SessionAdmissionObservation` require restart-safe persistence and freshness evidence before typed NextGen protection can trust its admitted-trade count?

## Evidence audited

### Canonical state infrastructure

`StateStorePort` already persists opaque deterministic bytes and `AtomicFileStateStore` already provides atomic storage mechanics. A second state/recovery architecture is not justified.

`src/daxlab/state/loss_exposure.py` demonstrates the accepted pattern for safety-relevant explicit observations: policy-linked tamper-evident checkpoint, caller-supplied timezone-aware observation timestamp, deterministic bytes and explicit compatibility check.

There is currently no canonical session-admission checkpoint under `src/daxlab/state/`.

### CAND-001 provenance

CAND-001 already persists its admission state (`session_date`, `trades_admitted`) inside candidate state. This proves admitted-trade count is restart-relevant, but its `Europe/Berlin` date derivation and reset behavior remain candidate-specific and must not become generic semantics.

### Typed protection risk

Step 2170 requires exact canonical `SessionAdmissionObservation`, but without checkpoint provenance a caller could supply a structurally valid count with no restart identity or age evidence. For a safety gate, silently trusting arbitrarily old restored count evidence is weaker than the loss/exposure path.

## Decision

**ADAPT_CANONICALLY.**

The smallest justified state boundary is a tamper-evident `SessionAdmissionObservationCheckpoint` that owns only:

1. canonical `SessionAdmissionPolicy.policy_fingerprint`;
2. exact canonical `SessionAdmissionObservation`;
3. caller-supplied timezone-aware `observed_at` normalized to UTC;
4. deterministic checkpoint fingerprint;
5. disabled execution capability fields.

It should encode/decode/save/load through the existing `StateStorePort` pattern and expose an explicit policy-compatibility check.

## Freshness decision

Typed NextGen protection should later require:

- the checkpoint policy fingerprint to match the supplied canonical session policy;
- the checkpoint observation to equal the supplied canonical session observation;
- explicit timezone-aware `evaluated_at`;
- explicit non-negative finite maximum session-observation age;
- future-dated checkpoint evidence to fail closed;
- stale checkpoint evidence to block new admission;
- checkpoint identity and computed age to be included in protection provenance.

Freshness is an evidence-age guard only. It does **not** determine when a session changes or reset the admitted count.

## Explicitly deferred

This audit does not authorize or define:

- session-key derivation;
- timezone selection;
- market-session start/end;
- holiday/weekend/calendar semantics;
- session reset transitions;
- account/broker reads;
- reconciliation of a canonical count from broker positions/orders;
- PAPER or LIVE execution.

Those semantics require separate evidence and ownership.

## Safety

- reuse existing persistence infrastructure;
- no broker submission path;
- `execution_capability=NONE` remains binding;
- `order_execution_enabled=false` remains binding;
- PAPER and LIVE remain unauthorized;
- frozen V11.2 evidence remains unchanged.

Implementation is a separate next whole-number step.
