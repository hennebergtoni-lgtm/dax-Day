# DAX-BOT Workflow Integrity Gate V1

Status: BINDING
Updated: 2026-09-12

Purpose: keep technical work, visible progress, CI/evidence truth and the official whole-number step ledger synchronized. This workflow is a quality-control system for the bot, not chat formatting.

If older continuity/handoff wording conflicts with this gate on step closure, pointer synchronization, interrupted-lane numbering or claims about ongoing work, this gate controls until the older wording is reconciled.

## 1. Step-Close-Gate

Before the next independent official step may begin, the current step must be in exactly one explicit terminal/paused state:

- `COMPLETED` — required implementation/audit work is done, direct evidence exists, required CI/tests are green or explicitly not applicable, and the pointer is synchronized;
- `INTERRUPTED` — work is deliberately stopped before completion, the reason/evidence is recorded, and unfinished scope is preserved for carry-forward;
- `WAITING_EXTERNAL` — the lane needs external/user/market/host evidence and the exact unblock condition is recorded;
- `BLOCKED` — a hard blocker remains after reasonable recovery and the blocker evidence is recorded.

Commits alone do not make a step complete. A green partial CI does not make a step complete. A chat statement does not make a step complete.

## 2. Pointer-before-next-step rule

`docs/CURRENT_WORK_STEP.md` must identify the correct active whole-number step before the first substantive action of that new independent work unit.

Do not perform multiple independent work units and backfill several step numbers afterward.

A tightly coupled implementation + immediate regression fix/test may remain one step. A different deliverable requires the next integer.

## 3. Monotonic interrupted-lane rule

Visible official numbering never moves backwards.

If older Step N is still open after later steps have started, never display Step N again as the current active official step. Preserve it as provenance and resume the unfinished scope under the next unused integer, for example:

`Step 2140 — continuation of the lane originating in Step 2122`.

The wording `Fortsetzung Schritt N` must not be used as an official current step after a higher number has already started.

## 4. User intervention rule

An explicit user instruction to stop, review, audit or correct the workflow is a valid sequence interruption.

When this happens:
1. stop further substantive work on the active technical step;
2. inspect its real repo/CI/evidence state;
3. mark it `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL` or `BLOCKED` truthfully;
4. synchronize `CURRENT_WORK_STEP.md`;
5. only then start the governance/review work under the next unused integer;
6. later resume unfinished technical scope only under a later unused integer.

## 5. Visible progress contract

For sustained engineering work, the user-visible cadence is:

`Step N: activity -> normal-text Zwischenstand -> ✅ / ⚠️ / ❌ -> actual next tool/action`.

Tool/interface activity lines do not count as the normal-text Zwischenstand.

Do not run long chains of meaningful tool actions without a normal-text progress report. The report must state what was checked, what the result means and what action actually follows.

## 6. No-background-work truth

A final/turn-ending response ends the active work turn. Do not say or imply that repository work is continuing after that response unless a real scheduled automation/background system has actually been created for that purpose.

While the current turn is active, work may continue through tools after intermediate commentary. If the platform/app/network ends or suspends the turn, no invisible continuation may be claimed.

At the next available turn, re-pin repo/branch/head/CI and `CURRENT_WORK_STEP.md` before resuming.

## 7. CI/evidence discipline

When a step has required CI/tests:
- inspect the exact current head, not an older green head;
- distinguish partial green from full required green;
- a newly red required CI keeps the step open/interrupted until resolved or explicitly carried forward;
- record the concrete failure rather than calling the step complete.

A later unrelated step must not erase or cosmetically hide inherited red evidence from an interrupted step.

## 8. Checkpoint rules remain binding

- next mandatory 250-step Masterstand checkpoint: `2250`;
- next mandatory 500-step full architecture/LEAN audit: `2500`;
- an explicit user-requested stop/audit may occur at any time and does not replace those scheduled checkpoints unless it occurs exactly at the checkpoint number.

## 9. Safety boundary

This workflow gate never authorizes PAPER or LIVE, never changes VERIFIED evidence, never changes strategy semantics and never weakens execution safety.

Current safety remains:
- SHADOW authorized within its existing no-order contract;
- PAPER not authorized;
- LIVE not authorized;
- `execution_capability=NONE` where currently required;
- `order_execution_enabled=false` where currently required.

## 10. Acceptance criterion

The workflow is healthy only when all of the following remain true:
- current visible step == repository pointer;
- previous independent step has an explicit truthful state before the next begins;
- user can see normal-text intermediate reports during long work;
- tool activity never substitutes for those reports;
- old lanes resume only under a new higher integer;
- no claim is made that work continues after the active turn has ended;
- required CI/evidence state is checked on the exact head before a step is called complete.
