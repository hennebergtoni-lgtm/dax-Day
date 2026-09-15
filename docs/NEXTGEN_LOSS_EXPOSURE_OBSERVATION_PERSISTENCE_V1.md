# NextGen Loss / Exposure Observation Persistence V1

Status: **STEP-2166 PRODUCT / RESTART-SAFE PERSISTENCE CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Decision

Reuse the existing `StateStorePort` plus `AtomicFileStateStore`. No second persistence, checkpoint or recovery architecture is justified.

Step 2166 adds only `state/loss_exposure.py`, a tamper-evident envelope around an already-built canonical `LossExposureObservation`.

## Persisted evidence

The checkpoint binds:

- canonical Loss/Exposure policy fingerprint;
- exact canonical observation including its own fingerprint;
- explicit caller-supplied timezone-aware observation timestamp, normalized to UTC;
- checkpoint fingerprint;
- non-executing safety flags.

Policy configuration itself remains separately owned by `LossExposurePolicy`; only its fingerprint is linked for restart compatibility.

## Restart behavior

The checkpoint can be encoded to deterministic UTF-8 JSON bytes and saved/loaded through any existing `StateStorePort` implementation. `assert_loss_exposure_checkpoint_compatible()` fails closed when restored state belongs to another policy identity.

Nested observation tampering, envelope tampering, schema drift and invalid safety flags fail closed.

## Explicit DEFER — observation production

Step 2166 deliberately does **not** define how the observation values are produced. The following remain deferred until separately evidenced semantics exist:

- realized PnL calculation;
- account/equity drawdown calculation;
- daily reset boundary;
- weekly reset boundary;
- broker timezone mapping;
- session/trading-calendar reset rules;
- reconciliation between SHADOW-derived and broker/account-derived loss state.

Those concerns must not be guessed merely to make persistence look complete.

## Existing-owner audit

- CAND-001 active-trade state persists one SHADOW trade and its causal lifecycle, not portfolio loss/exposure observations.
- CAND-001 virtual outcomes provide costed SHADOW outcome evidence, but are not silently promoted into product drawdown semantics.
- broker execution checkpoint persists lifecycle + telemetry journal, not product loss/exposure observations.
- `StateStorePort` already provides the required opaque persistence boundary.

## Safety boundary

- no PnL/account calculation;
- no account/broker API;
- no MT5 SDK/order API;
- no broker submission;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- PAPER not authorized;
- LIVE not authorized;
- persistence proof does not set readiness verification booleans true.
