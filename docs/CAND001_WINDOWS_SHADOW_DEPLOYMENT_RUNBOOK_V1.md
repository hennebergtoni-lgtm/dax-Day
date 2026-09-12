# CAND-001 Windows SHADOW Deployment Runbook V1

Status: PREFLIGHTED HOST VERIFICATION — SHADOW ONLY / REAL HOST STILL WAITING_EXTERNAL
Updated: 2026-09-12

## Purpose

Provide the smallest safe sequence for verifying the newly integrated CAND-001 SHADOW path on the existing Windows/MT5 host. This runbook does not authorize PAPER/LIVE and introduces no order API.

## Preconditions

- MT5 terminal is already installed/running and the existing read-only SHADOW host path has previously been verified.
- Repository clone exists on the Windows host.
- Existing `.venv-mt5` Python environment exists.
- Broker timezone value is already known/verified for the host.
- Branch under test: `nextgen-bot-line-v1` until PR #109 is later merged.

## 1. Update code without changing runtime authorization

From the repository root:

```powershell
git fetch origin
git checkout nextgen-bot-line-v1
git pull --ff-only origin nextgen-bot-line-v1
git status --short
git rev-parse HEAD
```

Expected: clean working tree after update. Retain the full tested commit SHA.

## 2. Verify exact host-code parity before touching runtime state

Run the existing parity owner after the update:

```powershell
.\scripts\check_windows_mt5_shadow_code_parity.ps1
```

The checker now resolves the branch upstream commit automatically, requires local `HEAD` to match that upstream commit and verifies the committed host-facing surface including all `candidate_*.py` and `mt5_*.py` runtime modules at that commit.

Required result:

- `HEAD PARITY | MATCH`;
- `PARITY SUMMARY ... failed=0`;
- `execution_capability=NONE`;
- `order_execution_enabled=false`.

If parity fails, STOP this host-verification lane and fix/sync the checkout before any runtime restart.

## 3. Run one-shot preflight in its isolated state directory

Use the already-owned preflight script; do not create a second launcher. Keep its isolated default state directory so the one-shot does not overwrite the scheduled task's normal state.

```powershell
.\scripts\preflight_windows_mt5_shadow_autostart.ps1 -BrokerTimezone '<VERIFIED_BROKER_TIMEZONE>' -StateDir '.runtime\mt5_shadow_preflight'
```

Required legacy safety result:

- heartbeat `status=GREEN`;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no order API/order submission.

State-directory ownership is intentional:

- one-shot preflight: `.runtime\mt5_shadow_preflight`;
- installed/scheduled SHADOW runtime: `.runtime\mt5_shadow` by default.

Do not mix evidence from those directories without recording which owner produced it.

## 4. Verify new CAND-001 evidence from the same one-shot cycle

The existing supervisor writes additional files only after the established GREEN host/cross-cycle gate permits candidate processing.

Expected paths under `.runtime\mt5_shadow_preflight` for the one-shot test:

- `candidate_manifest.json`
- `candidate_checkpoint.json`
- `candidate_operator_snapshot.json` when at least one new candidate bar was processed
- `candidate_intent_outbox\<client_order_id>.json` only if a virtual SHADOW TRADE decision occurred
- `candidate_outcome_outbox\<outcome_id>.json` only after a virtual lifecycle later closed

Absence of intent/outcome files is normal when no qualifying signal/outcome occurred.

## 5. Safety assertions

For every candidate evidence file that exists:

- execution capability must remain `NONE`;
- order execution must remain `false`;
- no broker order/ticket field may be inferred from virtual evidence;
- `candidate_manifest.json` mode must be `SHADOW`;
- checkpoint and manifest fingerprints must remain stable across ordinary sliding-window cycles.

## 6. Fast overlap/reconciliation check in isolated preflight state

After the first one-shot succeeds, run the same preflight command again with the same `.runtime\mt5_shadow_preflight` state directory. This is a safe early check that re-observing the normal sliding window does not treat old CLOSED bars as new causal market events.

Required behavior:

- legacy heartbeat remains GREEN;
- no execution capability appears;
- old bars are suppressed/reconciled rather than duplicated;
- candidate checkpoint does not regress;
- any newly advanced checkpoint is attributable only to a genuinely newer CLOSED bar.

This fast overlap check does not replace the scheduled-task restart proof below.

## 7. Scheduled-task restart / overlap verification

Only after parity and one-shot checks are green:

1. use the existing Windows SHADOW Scheduled Task as the process owner; do not launch an unmanaged parallel supervisor;
2. stop/start that SHADOW task through Task Scheduler ownership if a reload of the newly pulled code is required;
3. let the next probe include the normal overlapping sliding window;
4. verify old bars are suppressed/reconciled rather than reprocessed as new market events;
5. verify the candidate checkpoint advances only on genuinely newer CLOSED bars;
6. if a virtual position was open before restart, verify its origin decision/lifecycle identity survives the restart;
7. if it later closes, verify a deterministic outcome file is produced exactly once by ID.

The scheduled task normally owns `.runtime\mt5_shadow`; do not use the isolated preflight directory when judging scheduled-task recovery.

## 8. Existing runtime health check

Use the existing runtime check against the scheduled-task state:

```powershell
.\scripts\check_windows_mt5_shadow_runtime.ps1 -StateDir '.runtime\mt5_shadow'
```

This remains the owner for Task Scheduler policy + legacy heartbeat safety. Candidate-specific evidence is supplementary and must not weaken this gate.

## 9. Fail-closed behavior

If any of the following occurs, do not promote the candidate path:

- code parity/HEAD parity fails;
- legacy heartbeat not GREEN;
- cross-cycle overlap mutation/blocker;
- candidate checkpoint cannot be parsed/restored;
- RunManifest drift without an intentional version/config change;
- candidate safety fields differ from `NONE/false`;
- duplicate/out-of-order behavior differs from repository tests;
- any order capability/API appears.

A failed candidate layer must not be worked around by bypassing the legacy host gate.

## 10. Evidence to retain after the host test

Record at minimum:

- tested Git commit SHA and successful parity summary;
- timestamp/timezone;
- legacy heartbeat summary;
- candidate manifest fingerprint;
- candidate checkpoint fingerprint;
- latest candidate operator snapshot fingerprint when present;
- isolated overlap result;
- scheduled-task restart result;
- scheduled-task duplicate/overlap result;
- any intent/outcome IDs observed;
- confirmation `execution_capability=NONE` / `order_execution_enabled=false`.

Only after this host evidence is reviewed may Windows-specific CAND-001 integration be labelled VERIFIED. Repository/CI success alone means IMPLEMENTED + CI-VERIFIED, not real-host VERIFIED.