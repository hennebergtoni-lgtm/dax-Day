# Step 2233 — IG M5 provider-finalization grace

**SUPERSEDED FOR NEW HOST TESTS:** user-supplied post60s evidence again triggered STATE_CHANGED_OVERLAP. This file preserves the intermediate implementation, not a finality guarantee or current closeout plan. Follow `STEP_2233_IG_RAW_TIMESTAMP_TRUTH.md` for read-only RAW sampling first; keep existing files and the strict overlap gate.2233 is UNVERIFIED / WAITING_EXTERNAL, not completed. The current live entrypoint also blocks DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED until a RAW-proven canonical contract exists; no CLI override. Original60s contract/state below are historical, not silently migrated.

Status: **IMPLEMENTED_LOCAL / REAL WINDOWS RERUN WAITING_EXTERNAL**
Date: 2026-09-14
Repo/branch/PR: `hennebergtoni-lgtm/dax-Day` / `nextgen-bot-line-v1` / #109 OPEN, UNMERGED.
Exact task start: `7b715f958cd6c2a2bd4055e0e5914aea5519ba47`, no drift; main/base `e0784ebfc11bee28475fd9c3385be661af58a738`. Start DAX #674 and Research #1458 SUCCESS. Pointer/2232 supplied closeout commit `59f174311b4e66f0090dc30410f7748d6b0e162d`, DAX #675 / Research #1459 SUCCESS. Final deployment SHA and its required CI must be read from the final Work handoff/current PR, never inferred from an older green head.

## Real-host finding / scope

2231 remains COMPLETED / VERIFIED AS SUPPLIED. The binding user mandate closes 2232 as COMPLETED / VERIFIED on Windows: real IG raw40/closed40 -> CAND-001 Decision/SHADOW -> fresh telemetry/operator, both exits0, GREEN, NO_TRADE/NONE/OR_INCOMPLETE/NO_SIGNAL, FRESH, NONE/false, fingerprint present and no placement/cancel/modify. Work did not independently operate Windows or receive the original JSON bytes/hash value. This proves the initial E2E scope, not immutable provider bars or full MT5/Neon console parity.

A subsequent resume correctly blocked STATE_CHANGED_OVERLAP after IG revised nominal close `2026-09-14T11:40:00+00:00`: approximately high25451.3->25465.2, low25447.6->25447.3, close25451.3->25463.8, volume2->121. A probe around12:05:03UTC observed nominal close12:05 only about3.7s old. These are supplied host observations. NOMINALLY CLOSED is not provider-finalized. Sporadic401 after rapid sessions is also supplied; no retry/login-spam loop is introduced.

The minimal correction lives solely in `scripts/ig_cand001_shadow_e2e.py`; general IG closure/UTC/pagination/probe and CAND-001 rules, costs, sizing, risk/execution/MT5/V11.2 owners remain unchanged. Offline replay of original start code and the same synthetic3.7s fixture reproduces latest nominal processing before the fix and previous finalized-policy bar processing after it, with identical probe evidence. This is synthetic regression evidence, not another broker observation.

## Contract / reuse

| Owner | Behavior |
| --- | --- |
| Existing IG adapter/client/probe | Same complete nominal CLOSED-M5 observation and existing600s freshness; one live read-only session per invocation, no extra fetch/retry/dealing. |
| Existing DE40/5m runtime bridge | Preserve exact source/UTC/OHLC/volume. Add one selection helper after nominal validation, before Candidate processing. |
| `IG_M5_PROVIDER_FINALIZATION_GRACE_SECONDS` | Explicit **60** seconds. Contract `IG_M5_CAND001_PROVIDER_FINALIZATION_GRACE_V1`; eligibility clock PRICE_REQUEST_STARTED_AT_UTC. |
| Existing RunManifest | Dataset fingerprint includes exact grace contract/clock, independently of code-head binding. Candidate/sizing/config and fill defaults unchanged. |
| Existing complete Candidate checkpoint | Same parser/state owner; bound manifest makes old state incompatible. No new state machine or migration engine. |
| Existing atomic envelope/lock | One complete state/decision/telemetry write; new V2 evidence schema and default2233 namespace. |
| Existing resume/overlap | Exact comparison of all overlapping processed rows including OHLC, volume, source and timestamps. STATE_CHANGED_OVERLAP is preserved without tolerances. |
| Existing V3/parser/telemetry/browser DTO | Snapshot/decision/checkpoint/current identity follows the actual processed eligible bar, not the younger nominal observation. Hash-bound readback and600s age checks remain. |

Eligibility requires request-start minus nominal close >=60s. This conservative clock avoids promoting a snapshot fetched before the grace boundary merely because transport/processing crosses it. Thus processing age is also >=60s; latest Candidate bar must remain <=600s through processing, export and operator read. Sixty seconds is an eligibility policy, **not proof that IG cannot revise bars later**; later revisions still block strictly.

## V2 evidence and migration

- `ig_probe`: unchanged nominal probe, including full raw/nominal counts, latest nominal closed OHLC, observations and original fingerprint.
- `ig_closed_m5_observation`: complete validated nominal rows, explicitly observation-only.
- `input_window`: only Candidate-eligible rows. Grace-tail rows never receive Decisions, enter Candidate state or become its anchor.
- `provider_finalization_contract`, `finalization_as_of_utc`, eligible/excluded counts and `latest_finalized_m5`: explicit, recomputed and validated against the nominal observation.
- `candidate_m5_freshness_state` and latest-finalized age: separate from nominal probe freshness. Operator/current Decision follows this actual Candidate bar.
- `recovery_state`: FRESH_START or RESUME_ANCHOR_RECONCILED exposed in stdout as well as persisted source evidence.

Legacy V1/missing or changed grace contract -> `STATE_FINALIZATION_CONTRACT_MIGRATION_REQUIRED`, before any live collection on resume. Manifest mismatch -> `STATE_MANIFEST_DRIFT`. No silent migration, reset, deletion or overwrite of old2232 files. Explicitly pointing `--state-dir` at old2232 state blocks rather than migrating it.

New default path: `C:\Users\Mandy\Documents\dax-Day-ig-hostcheck\.runtime\ig_cand001_shadow_e2e_2233\evidence.json`.
Preserved old path: `.runtime/ig_cand001_shadow_e2e/evidence.json`.
No eligible/new eligible bar -> exit2 / `STATE_NO_NEW_FINALIZED_M5`; existing successful evidence stays unchanged and is not evidence of this failed invocation. Lock/head/import/source/anchor/gap conflicts remain fail-closed. HTTP401 -> fixed `IG_AUTHENTICATION_FAILED_NO_RETRY`, no provider text and one attempt. Other failures retain fixed stage codes. Stop on failure; never operator-read an old file as a successful new collection.

## Windows rerun — two manual cycles

Known worktree `C:\Users\Mandy\Documents\dax-Day-ig-hostcheck`; known external credentials `C:\Users\Mandy\ig_demo.env`. Reuse existing Python. Do not change the separate MT5 worktree/tasks. First use the final Work block to fetch, reject drift and `git switch --detach` the exact final SHA. `$ExpectedHead` is its actual literal SHA. No merge/force/reset/clean/stash/state deletion.

Choose a time at least60s after an M5 boundary, e.g. UTC minute11 after close10. No short-interval broker polling. The function below invokes one live read plus one local operator read, preserves each reviewed cycle as an archive, and performs no wait/retry loop:

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck'
$StateDir = '.runtime/ig_cand001_shadow_e2e_2233'
if (Test-Path "$StateDir/evidence.json") {
    throw '2233 fresh-start state already exists; review it, do not delete/reset.'
}

function Invoke-2233ShadowCycle([string]$Cycle) {
    $Archive = "$StateDir/$Cycle-evidence.json"
    if (Test-Path $Archive) { throw 'Archive already exists; stop.' }
    $Output = python scripts/ig_cand001_shadow_e2e.py --credentials-file 'C:\Users\Mandy\ig_demo.env' --expected-head $ExpectedHead --state-dir $StateDir | Out-String
    $LiveExit = $LASTEXITCODE
    $Output
    "Live exit: $LiveExit"
    if ($LiveExit -ne 0) { throw '2233 BLOCKED: no retry or old-evidence substitution.' }
    $Observed = $Output | ConvertFrom-Json
    $RequiredRecovery = if ($Cycle -eq 'fresh-start') { 'FRESH_START' } else { 'RESUME_ANCHOR_RECONCILED' }
    if ($Observed.recovery_state -ne $RequiredRecovery) { throw 'Unexpected recovery state; stop.' }
    python scripts/ig_cand001_shadow_e2e.py --read-evidence "$StateDir/evidence.json" --expected-head $ExpectedHead --expected-fingerprint $Observed.fingerprint
    $OperatorExit = $LASTEXITCODE
    "Operator exit: $OperatorExit"
    if ($OperatorExit -ne 0) { throw 'Operator read BLOCKED; stop.' }
    Copy-Item "$StateDir/evidence.json" $Archive
    $script:Last2233Observation = $Observed
}

Invoke-2233ShadowCycle 'fresh-start'
$NextEligibleAt = ([DateTimeOffset]::Parse($Last2233Observation.latest_closed_m5)).AddMinutes(5).AddSeconds(60)
"Second cycle no earlier than: $($NextEligibleAt.UtcDateTime.ToString('o')) UTC"
```

Pause manually until that printed UTC time. Run the second block separately, not immediately and not in a loop:

```powershell
if ([DateTimeOffset]::UtcNow -lt $NextEligibleAt) { throw 'Wait for the next M5 plus60s; no login yet.' }
Invoke-2233ShadowCycle 'resume'
```

Return both live/operator outputs and both new files `fresh-start-evidence.json` / `resume-evidence.json`; never the `.env`. These archives are source-evidence copies, not another runtime state owner. No automatic deletion or archive overwrite. If auth fails, stop and let sessions settle; do not start rapid retry probes.

## Expected evidence / close gate

First: exact final code head, new V2/grace60 contract, FRESH_START, new UTC times/hash, raw40 and consistent nominal/eligible/excluded counts, actual eligible latest bar age60..600, CAND-001/session/decision/config/run identity, GREEN, visible signal/admission/plan/virtual-state and safety NONE/false. Latest nominal may be younger than actual Candidate current; this is expected and must be explicit. NO_SIGNAL/OR_INCOMPLETE remains a valid decision; no range/rule override.

Second: same code/grace manifest, unchanged overlapping processed rows, a new eligible CURRENT bar/Decision, RESUME_ANCHOR_RECONCILED, new timestamps/hash, fresh validated V3/operator read, no STATE_CHANGED_OVERLAP and NONE/false. No anchor gap/reset or silent exception. If IG revises a processed >=60s bar, preserve strict blocker and review new real evidence; do not loosen it or extend grace automatically.

**2233 remains IMPLEMENTED_LOCAL / WAITING_EXTERNAL** until both real Windows cycles and hash-bound operator reads succeed and their source bundles are reviewed. Local Linux/CI does not prove Windows OS-lock or real transport/provider finalization. Protection/reconciliation UNKNOWN, broader M01 and2122/2206 unchanged. Next exact whole-number step **2234**, not started or execution-authorized here.

Local validation: 102 focused IG/Candidate/checkpoint regressions; full suite2736 passed /6 local PowerShell skips (2742 collected). Ruff and Python syntax/imports pass. JavaScript is unchanged. All eight existing offline/safety gates pass. Required final-head CI must be checked before deployment; old green heads are not final proof.

SHADOW only. Real broker orders/placement/cancel/modify, mt5.order_send, execution enablement, slot release, PAPER/LIVE/DEMO execution, Acceptance refresh, merge and force-push are not authorized. V11.2/CAND-001/OR15/risk/sizing/cost/execution owners unchanged. No profitability claim.
