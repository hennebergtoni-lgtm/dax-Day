# NextGen Session Admission Promotion Audit V1

Status: **STEP-2168 AUDIT — ADAPT_CANONICALLY**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Question

Can the remaining coarse `session_admission_allowed` boolean in the typed NextGen execution-protection path be replaced by deterministic canonical evidence without silently promoting CAND-001-specific session/timezone behavior?

## Evidence audited

### Existing CAND-001 behavior

`src/daxlab/runtime/candidate_admission.py` owns CAND-001 per-session admission. It:

- derives `session_date` from `signal.close_time` using `Cand001Config.session_timezone`;
- resets admission state when that derived date changes;
- blocks when `trades_admitted >= max_trades_per_session`;
- increments the count only for an admitted directional trade.

`src/daxlab/runtime/candidate_config.py` fixes CAND-001 to:

- `session_timezone = Europe/Berlin`;
- `max_trades_per_session = 1`.

Those values are explicit CAND-001 `NEW_1X_SELECTION` choices, not generic product defaults.

`src/daxlab/runtime/candidate_state.py` persists `admission.session_date` plus `admission.trades_admitted`, proving that the already-derived session identity and count are restart-relevant state.

`tests/test_candidate_admission.py` proves first-trade allow, second-trade same-session block, new-session reset and no-slot consumption for no-signal events.

### Existing NextGen protection behavior

`src/daxlab/runtime/broker_execution_protection.py` still accepts a coarse `session_admission_allowed` boolean even though risk, loss/exposure admission and observation freshness now have typed deterministic evidence.

The boolean is protection evidence only. It does not itself derive session identity, count trades or persist state.

## Decision

**ADAPT_CANONICALLY.**

A broker-neutral canonical session-admission owner is justified **only** if it receives already-derived explicit inputs and does not own timezone/calendar derivation.

The minimal product contract may own:

1. `SessionAdmissionPolicy(max_trades_per_session)` with positive integer validation and deterministic fingerprint;
2. `SessionAdmissionObservation(session_key, trades_admitted)` with normalized non-empty session key, non-negative integer count and deterministic fingerprint;
3. deterministic `ALLOW` / `BLOCK` evaluation where equality at the configured limit blocks;
4. deterministic decision fingerprint binding policy and observation identity.

## Explicitly not promoted

The canonical owner must **not**:

- default to `Europe/Berlin`;
- derive a date/session key from timestamps;
- define market-session start/end;
- define holiday/weekend/calendar semantics;
- silently inherit CAND-001's `max_trades_per_session = 1` as a product default;
- mutate CAND-001 admission behavior or state;
- access broker/account APIs;
- authorize broker submission, PAPER or LIVE.

Session-key production remains caller/environment responsibility until separately verified semantics exist.

## Consumer / migration conclusion

The typed NextGen protection path can later replace its coarse boolean with exact canonical session-admission evidence. Generic legacy protection callers may retain the compatibility boolean until their own provenance is explicitly migrated.

Implementation belongs to the next independent whole-number step. Step 2168 is classification/audit only.

## Safety

- `execution_capability=NONE` remains binding;
- `order_execution_enabled=false` remains binding;
- PAPER remains unauthorized;
- LIVE remains unauthorized;
- frozen V11.2 evidence remains unchanged.
