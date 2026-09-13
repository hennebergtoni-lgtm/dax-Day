# MT5 DEMO Account Context REUSE Audit V1

Status: BINDING REUSE DECISION — READ-ONLY / NO BROKER SUBMISSION
Updated: 2026-09-13
Branch: `nextgen-bot-line-v1`
Step: 2192

## Decision

The existing Windows MT5 probe already owns the required read-only `mt5.account_info()` observation call. No second MT5 connection owner, account reader or host service is justified.

The Step-2191 `DemoEvidenceAuthorization` contract therefore needs only a narrow normalization extension over the existing probe evidence, not a new broker adapter.

## Current owner and gap

`scripts/mt5_windows_probe.py` already:

- initializes the existing MT5 desktop connection;
- calls `mt5.account_info()` read-only;
- observes `trade_allowed`;
- resolves the configured broker symbol;
- preserves `order_execution_enabled=false`;
- calls no order API.

However, the current serialized host payload intentionally omits the account identity, server and account trade mode. `FORBIDDEN_OUTPUT_KEYS` also prevents raw login/account identifiers from leaking into the general evidence bundle.

`src/daxlab/runtime/mt5_probe_payload.py` correspondingly parses only coarse account connectivity/trade-allowed state and has no canonical DEMO / CONTEST / REAL / UNKNOWN account-mode evidence.

Therefore Step 2191 cannot yet receive trustworthy observed `account_id`, `server` and `account_mode` values from the real-host probe.

## External API evidence

MetaQuotes documents that Python `mt5.account_info()` returns the current account information in one read-only named tuple, including at least:

- `login`;
- `trade_mode`;
- `trade_allowed`;
- `server`.

MetaQuotes also defines `ACCOUNT_TRADE_MODE_DEMO`, `ACCOUNT_TRADE_MODE_CONTEST` and `ACCOUNT_TRADE_MODE_REAL` as the account-type enumeration. Any value outside the recognized runtime constants must fail closed to `UNKNOWN`; it must never default to REAL or DEMO by positional assumption.

## Smallest safe target

REUSE the existing `mt5.account_info()` observation and existing Windows probe lifecycle.

Add only a canonical read-only account-context normalization layer with these semantics:

1. Input comes from the already-observed MT5 account object / runtime constants.
2. Raw login/account number is never serialized.
3. Canonical account identity is a deterministic SHA-256 fingerprint derived from an explicit namespace plus the exact raw login identity, suitable for equality binding but not disclosure.
4. Broker server is retained as an exact non-empty observed string.
5. Account mode is normalized by comparing the observed value against the MT5 runtime constants for DEMO, CONTEST and REAL; unrecognized/missing values become `UNKNOWN`.
6. `trade_allowed` remains an independent boolean and is never treated as proof of DEMO mode.
7. Exact resolved symbol remains separately bound by the existing symbol-resolution owner.
8. The resulting normalized evidence can construct or feed `DemoEvidenceObservedContext` but cannot itself authorize submission.
9. All outputs remain `execution_capability=NONE` / `order_execution_enabled=false` where those fields are represented.

## Preferred implementation shape

Prefer one small dependency-free normalization owner under `src/daxlab/runtime/` plus focused tests, and a minimal adaptation of the existing Windows probe to emit the normalized redacted account context.

Do not add:

- another `mt5.initialize()` owner;
- another account polling process;
- credentials/login calls;
- raw account-number output;
- `mt5.order_send` or any order API;
- broker lifecycle/reconciliation/state duplication;
- automatic DEMO/PAPER/LIVE authorization.

The existing strict probe parser may be extended only as needed to accept the explicitly versioned redacted account-context field. Backward compatibility must remain fail-closed: an old payload without account-context evidence may remain valid for SHADOW host health but must not satisfy DEMO-evidence authorization.

## Failure cases that must be tested

- recognized DEMO runtime constant -> DEMO;
- recognized CONTEST runtime constant -> CONTEST;
- recognized REAL runtime constant -> REAL;
- unknown/missing/non-integer trade mode -> UNKNOWN or validation failure, never DEMO;
- `trade_allowed=true` on REAL/CONTEST/UNKNOWN remains blocked by Step 2191;
- raw login never appears in serialized payload;
- account fingerprint changes when login changes;
- server mismatch and symbol mismatch remain blocked by Step 2191;
- malformed/empty server fails closed;
- legacy SHADOW payload without account context does not become DEMO evidence;
- no order API/import/capability is introduced.

## Safety truth

- SHADOW remains authorized with no broker orders.
- DEMO evidence transport remains NOT IMPLEMENTED / NOT AUTHORIZED.
- Normal PAPER remains NOT AUTHORIZED.
- LIVE remains NOT AUTHORIZED.
- No profitability claim is made.
- Frozen V11.2, CAND-001 strategy parameters and cost assumptions remain unchanged.
