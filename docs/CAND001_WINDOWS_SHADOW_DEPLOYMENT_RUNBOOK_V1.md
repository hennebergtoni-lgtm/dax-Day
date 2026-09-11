# CAND-001 Windows SHADOW Deployment Runbook V1

Status: PLANNED HOST VERIFICATION — SHADOW ONLY
Updated: 2026-09-11

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
```

Expected: clean working tree after update.

## 2. Run existing one-shot preflight

Use the already-owned preflight script; do not create a second launcher.

```powershell
.\scripts\preflight_windows_mt5_shadow_autostart.ps1 -BrokerTimezone '<VERIFIED_BROKER_TIMEZONE>'
```

Required legacy safety result:

- heartbeat `status=GREEN`;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no order API/order submission.

## 3. Verify new CAND-001 evidence from the same one-shot cycle

The existing supervisor now writes additional files only after the established GREEN host/cross-cycle gate permits candidate processing.

Expected paths under the selected state directory:

- `candidate_manifest.json`
- `candidate_checkpoint.json`
- `candidate_operator_snapshot.json` when at least one new candidate bar was processed
- `candidate_intent_outbox\<client_order_id>.json` only if a virtual SHADOW TRADE decision occurred
- `candidate_outcome_outbox\<outcome_id>.json` only after a virtual lifecycle later closed

Absence of intent/outcome files is normal when no qualifying signal/outcome occurred.

## 4. Safety assertions

For every candidate evidence file that exists:

- execution capability must remain `NONE`;
- order execution must remain `false`;
- no broker order/ticket field may be inferred from virtual evidence;
- `candidate_manifest.json` mode must be `SHADOW`;
- checkpoint and manifest fingerprints must remain stable across ordinary sliding-window cycles.

## 5. Restart / overlap verification

After at least one successful candidate checkpoint exists:

1. stop/restart only through the existing Windows SHADOW process/task ownership;
2. let the next probe include the normal overlapping sliding window;
3. verify old bars are suppressed/reconciled rather than reprocessed as new market events;
4. verify the candidate checkpoint advances only on genuinely newer CLOSED bars;
5. if a virtual position was open before restart, verify its origin decision/lifecycle identity survives the restart;
6. if it later closes, verify a deterministic outcome file is produced exactly once by ID.

## 6. Existing runtime health check

Use the existing runtime check:

```powershell
.\scripts\check_windows_mt5_shadow_runtime.ps1
```

This remains the owner for Task Scheduler policy + legacy heartbeat safety. Candidate-specific evidence is supplementary and must not weaken this gate.

## 7. Fail-closed behavior

If any of the following occurs, do not promote the candidate path:

- legacy heartbeat not GREEN;
- cross-cycle overlap mutation/blocker;
- candidate checkpoint cannot be parsed/restored;
- RunManifest drift without an intentional version/config change;
- candidate safety fields differ from `NONE/false`;
- duplicate/out-of-order behavior differs from repository tests;
- any order capability/API appears.

A failed candidate layer must not be worked around by bypassing the legacy host gate.

## 8. Evidence to retain after the host test

Record at minimum:

- tested Git commit SHA;
- timestamp/timezone;
- legacy heartbeat summary;
- candidate manifest fingerprint;
- candidate checkpoint fingerprint;
- latest candidate operator snapshot fingerprint;
- restart result;
- duplicate/overlap result;
- any intent/outcome IDs observed;
- confirmation `execution_capability=NONE` / `order_execution_enabled=false`.

Only after this host evidence is reviewed may Windows-specific CAND-001 integration be labelled VERIFIED. Repository/CI success alone means IMPLEMENTED + CI-VERIFIED, not real-host VERIFIED.
