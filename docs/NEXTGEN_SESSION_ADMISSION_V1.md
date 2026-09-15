# NextGen Session Admission V1

Status: **STEP-2169 PRODUCT CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Define the minimal broker-neutral product-domain evidence needed to decide whether another trade may be admitted inside an already-identified session.

## Canonical contracts

### `SessionAdmissionPolicy`

Owns only:

- explicit positive integer `max_trades_per_session`;
- deterministic `policy_fingerprint`.

There is no product default. In particular, CAND-001's value `1` is not inherited automatically.

### `SessionAdmissionObservation`

Owns only:

- caller-supplied normalized non-empty `session_key`;
- non-negative integer `trades_admitted`;
- deterministic `observation_fingerprint`.

The observation does not derive a session from a timestamp.

### `SessionAdmissionDecision`

Evaluation is deterministic:

- `trades_admitted < max_trades_per_session` → `ALLOW`;
- `trades_admitted >= max_trades_per_session` → `BLOCK` with `MAX_TRADES_PER_SESSION`.

The decision fingerprint binds policy identity, observation identity, action and reason code.

## Deliberately outside this owner

This contract does not:

- choose `Europe/Berlin` or any timezone;
- convert timestamps into dates/session keys;
- define session start/end, holidays or market calendars;
- perform session-reset state transitions;
- mutate CAND-001 state;
- access broker/account APIs;
- call MT5/order APIs;
- authorize PAPER or LIVE.

Session-key production and reset semantics require separate, explicitly verified environment/session semantics.

## Safety

Software existence is not readiness evidence. `execution_capability=NONE`, `order_execution_enabled=false`, PAPER unauthorized and LIVE unauthorized remain binding project boundaries.
