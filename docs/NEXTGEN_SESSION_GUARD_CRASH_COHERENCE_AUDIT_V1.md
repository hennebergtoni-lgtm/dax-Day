# NextGen Session Guard Crash-Coherence Audit V1

Status: IMPLEMENTATION AUDIT / ADAPT_CANONICALLY
Step: 2177
Branch: `nextgen-bot-line-v1`

## Decision

**ADAPT_CANONICALLY: introduce one combined atomic session-guard snapshot before this evidence can become an authoritative future execution-protection input.**

The separate Step-2176 consumption-ledger checkpoint and Step-2172 observation-freshness checkpoint are individually valid, but saving them under independent `StateStorePort` keys cannot provide cross-key crash consistency.

## Storage truth

`StateStorePort` exposes only:

- `load(key)`;
- `save(key, payload)`.

There is no transaction, compare-and-swap or multi-key atomic-write contract.

`AtomicFileStateStore.save()` fsyncs a temporary file and atomically replaces one target path. That is a strong **single-key** guarantee only. It does not atomically commit two state keys together.

## Protection truth

Typed NextGen execution protection currently binds:

- SessionAdmissionPolicy;
- SessionAdmissionObservation;
- SessionAdmissionObservationCheckpoint;
- SessionAdmissionDecision;
- checkpoint freshness.

It does not receive or verify `SessionAdmissionConsumptionState`.

Therefore protection cannot currently prove that the separately supplied observation/count is derived from the newest persisted consumption ledger.

## Torn-state scenario

A representative crash sequence is:

1. consumption ledger advances from count 0 to count 1 and is saved successfully;
2. process crashes before the separate observation checkpoint is replaced;
3. after restart, the old observation checkpoint still says count 0 and may still be within its max-age window;
4. the old observation plus its matching old ALLOW decision can be internally self-consistent for protection even though the persisted consumption ledger has already advanced.

Step 2175's consumption transition would reject that stale ALLOW decision if a new unique consumption were later attempted against the restored ledger. That is useful defense-in-depth, but future execution safety must not depend on an unstated ordering assumption that consumption validation will always happen after protection and before any external side effect.

## Required canonical boundary

The next implementation should add one combined, single-key, tamper-evident session-guard snapshot that binds in one identity:

1. exact `SessionAdmissionConsumptionState`;
2. policy fingerprint;
3. exact `SessionAdmissionObservation` derived from that state;
4. caller-supplied timezone-aware `observed_at` representing when this state/evidence was produced or validated;
5. disabled execution-safety fields;
6. deterministic snapshot fingerprint.

The snapshot must be saved through the existing `StateStorePort` as **one payload under one key**, so `AtomicFileStateStore` can provide crash-atomic replacement for the complete protection truth.

## Freshness semantics

Loading a persisted snapshot must never refresh `observed_at`. File read time, process start time and restore time are not evidence that the underlying session state is fresh.

A new `observed_at` may only be supplied explicitly by the caller when producing/validating a new combined snapshot.

## Relationship to Step 2172

The Step-2172 `SessionAdmissionObservationCheckpoint` remains valid as a compatibility/diagnostic evidence type and should not be deleted or rewritten.

However, once the combined snapshot is implemented and wired into the typed NextGen protection path, the combined snapshot should become the authoritative product evidence because it proves that visible observation count and persisted consumption identity came from the same atomic state.

## Session ownership

The combined snapshot must not:

- derive a date, timezone, calendar or session key;
- silently reset a ledger on session mismatch;
- invent freshness on load;
- mutate CAND-001 behavior.

Session-key production/reset remains caller/environment owned and requires a separate explicit boundary if promoted later.

## Safety

- no broker/account API;
- no order submission path;
- `execution_capability=NONE` remains binding;
- `order_execution_enabled=false` remains binding;
- PAPER remains unauthorized;
- LIVE remains unauthorized;
- frozen V11.2 evidence remains unchanged.

## Next step

Implementation of the combined atomic session-guard snapshot is a separate next whole-number step. Step 2177 is audit/evidence only.
