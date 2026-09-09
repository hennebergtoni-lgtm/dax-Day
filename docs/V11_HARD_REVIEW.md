# V11 Hard Review — Pre-Host Hardening

Date: 2026-09-09
Status: PRE-HOST DEVELOPMENT COMPLETE PENDING FINAL MERGE/MAIN CI

## Scope reviewed
V11 milestones 211–230 prepare and harden the repository before the first real Windows MT5 host is attached. This review does not claim broker-host evidence and does not authorize LIVE execution.

## Frozen reference
- V11.2 remains the immutable active reference.
- Historical dataset/reference identities remain unchanged.
- Research candidates remain research objects and are not promoted into the bot.

## Safety and truthfulness
- Duplicate suppression is keyed to deterministic closed-bar identity, including resume after changed fault state.
- Strengthened checkpoint/recovery contracts use V2 identity tracking and tamper validation.
- Synthetic SHADOW evidence is explicitly `SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE`.
- Synthetic evidence cannot satisfy real Windows-host readiness.
- External MT5 milestones 102–110 remain incomplete.
- Paper remains NOT STARTED without verified real-host evidence.
- LIVE remains BLOCKED and NOT AUTHORIZED regardless of synthetic soak success.
- No broker order-submission capability is introduced by V11.
- `order_execution_enabled` remains false.

## CI evidence before merge
PR CI #461 completed successfully after V11 hardening. Required PR gates passed: Ruff, full pytest, recovery reconstruction preflight, research registry, hypothesis ledger, web-status integrity, V11 pre-host hardening smoke, V11.2 engine surface probe, guarded V11.2 replay smoke, and offline SHADOW soak smoke. Neon/database write gates are intentionally main-only and therefore must be verified by the post-merge main CI.

## SHADOW soak
The deterministic offline fixture covers 30 sessions × 103 closed M5 bars = 3,090 observations. It remains engineering evidence only and all actions are NO_ORDER.

## Remaining external blocker
The next external milestone is **102 — establish a real Windows MT5 host**. Only after that host exists may milestones 103–110 collect real terminal/account/symbol/timezone/closed-M5-feed evidence and validate the read-only host bundle.

## Merge rule
V11 may be merged only after the PR gates above are green. After merge, the main CI must also pass its Neon connection, migration, integrity, restore-drill, and detail-import gates before V11 is called fully closed.
