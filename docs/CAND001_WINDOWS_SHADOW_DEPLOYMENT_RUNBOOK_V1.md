# CAND-001 Windows SHADOW Deployment Runbook V1

Status: REAL-HOST PARTIAL VERIFIED / MARKET-OPEN CLOCK GATE WAITING_EXTERNAL — SHADOW ONLY
Updated: 2026-09-12

## Purpose

Provide the smallest safe sequence for verifying the newly integrated CAND-001 SHADOW path on the existing Windows/MT5 host. This runbook does not authorize PAPER/LIVE and introduces no order API.

## Preconditions

- MT5 terminal is already installed/running and the existing read-only SHADOW host path has previously been verified.
- Repository clone exists on the Windows host.
- Existing `.venv-mt5` Python environment exists.
- Broker timezone must be explicitly configured and then verified from real host evidence during an open/fresh market window. A configured value alone is not VERIFIED.
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

The checker resolves the branch upstream commit automatically, requires local `HEAD` to match that upstream commit and verifies the committed host-facing surface including all `candidate_*.py` and `mt5_*.py` runtime modules at that commit. On Windows it compares Git-canonical blob identity so CRLF working-tree normalization does not create false mismatches.

Required result:

- `HEAD PARITY | MATCH`;
- `PARITY SUMMARY ... failed=0`;
- `execution_capability=NONE`;
- `order_execution_enabled=false`.

If parity fails, STOP this host-verification lane and fix/sync the checkout before any runtime restart.

## 3. Run one-shot preflight in its isolated state directory

Use the already-owned preflight script; do not create a second launcher. Keep its isolated default state directory so the one-shot does not overwrite the scheduled task's normal state.

```powershell
.\scripts\preflight_windows_mt5_shadow_autostart.ps1 -BrokerTimezone '<CONFIGURED_BROKER_TIMEZONE>' -StateDir '.runtime\mt5_shadow_preflight'
```

Required final verification result during an open/fresh market window:

- heartbeat `status=GREEN`;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no order API/order submission;
- broker clock/timestamp interpretation is supported by fresh real-host evidence rather than configuration alone.

State-directory ownership is intentional:

- one-shot preflight: `.runtime\mt5_shadow_preflight`;
- installed/scheduled SHADOW runtime: `.runtime\mt5_shadow` by default.

Do not mix evidence from those directories without recording which owner produced it.

## 4. Verify new CAND-001 evidence from the same one-shot cycle

The existing supervisor writes additional files only after the established GREEN host/cross-cycle gate permits candidate processing.

Expected paths under `.runtime\mt5_shadow_preflight` for a GREEN one-shot test:

- `candidate_manifest.json`
- `candidate_checkpoint.json`
- `candidate_operator_snapshot.json` when at least one new candidate bar was processed
- `candidate_intent_outbox\<client_order_id>.json` only if a virtual SHADOW TRADE decision occurred
- `candidate_outcome_outbox\<outcome_id>.json` only after a virtual lifecycle later closed

Absence of intent/outcome files is normal when no qualifying signal/outcome occurred. If the legacy host/market-data gate blocks before candidate processing, absence of all candidate files is also expected and must not be misreported as candidate success.

## 5. Safety assertions

For every candidate evidence file that exists:

- execution capability must remain `NONE`;
- order execution must remain `false`;
- no broker order/ticket field may be inferred from virtual evidence;
- `candidate_manifest.json` mode must be `SHADOW`;
- checkpoint and manifest fingerprints must remain stable across ordinary sliding-window cycles.

## 6. Fast overlap/reconciliation check in isolated preflight state

After the first GREEN one-shot succeeds, run the same preflight command again with the same `.runtime\mt5_shadow_preflight` state directory. This is a safe early check that re-observing the normal sliding window does not treat old CLOSED bars as new causal market events.

Required behavior:

- legacy heartbeat remains GREEN;
- no execution capability appears;
- old bars are suppressed/reconciled rather than duplicated;
- candidate checkpoint does not regress;
- any newly advanced checkpoint is attributable only to a genuinely newer CLOSED bar.

This fast overlap check does not replace the scheduled-task restart proof below.

## 7. Scheduled-task restart / overlap verification

Only after parity and GREEN one-shot checks are complete:

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
- market data stale or CLOSED-M5 feed not fresh;
- broker clock/timezone cannot be supported by fresh host evidence;
- cross-cycle overlap mutation/blocker;
- candidate checkpoint cannot be parsed/restored;
- RunManifest drift without an intentional version/config change;
- candidate safety fields differ from `NONE/false`;
- duplicate/out-of-order behavior differs from repository tests;
- any order capability/API appears.

A failed candidate layer or upstream host gate must not be worked around by bypassing the legacy host gate.

## 10. Evidence to retain after the host test

Record at minimum:

- tested Git commit SHA and successful parity summary;
- timestamp/timezone;
- legacy heartbeat summary;
- broker clock/timezone verification result;
- candidate manifest fingerprint;
- candidate checkpoint fingerprint;
- latest candidate operator snapshot fingerprint when present;
- isolated overlap result;
- scheduled-task restart result;
- scheduled-task duplicate/overlap result;
- any intent/outcome IDs observed;
- confirmation `execution_capability=NONE` / `order_execution_enabled=false`.

Only after the remaining market-open and restart evidence is reviewed may the full Windows-specific CAND-001 integration be labelled VERIFIED. Repository/CI success alone means IMPLEMENTED + CI-VERIFIED, not complete real-host VERIFIED.

## 11. Real-host evidence — 2026-09-12 / Step 2122

VERIFIED on the Windows host:

- separate host-check worktree on `nextgen-bot-line-v1` was created so the existing scheduled SHADOW process was not mutated during verification;
- tested commit after parity-fix update: `785fe94354db8f53fe3306390d3fcbb394719308`;
- Windows `core.autocrlf=true` exposed a false-positive raw-byte parity failure (`0/56`) in the first checker revision; Git-canonical blob comparison corrected that host-specific defect;
- corrected parity result: `total=56 | match=56 | failed=0`;
- safety result: `execution_capability=NONE | order_execution_enabled=false`;
- existing Scheduled Task `DAXLAB MT5 SHADOW` is configured with `BrokerTimezone=Europe/Helsinki`, symbol `DE40`, working directory in `dax-Day-git`, state directory under `dax-Day-main\.runtime\mt5_shadow`, and the existing `.venv-mt5` Python interpreter;
- `Europe/Helsinki` is CONFIGURED but remains UNVERIFIED because the verification occurred on Saturday with the last DE40 tick stale from Friday evening and no retained historical `clock_ok=true` JSON evidence was found;
- isolated one-shot preflight used `.runtime\mt5_shadow_preflight_2122` and the current branch source via the runbook launcher;
- one-shot heartbeat correctly failed closed with `status=BLOCKED` and blockers `MARKET_DATA_STALE`, `MT5_HOST_NOT_HEALTHY`, `CLOSED_M5_FEED_NOT_FRESH`, `CLOCK_NOT_SAFE`;
- the blocked heartbeat retained `execution_capability=NONE` and `order_execution_enabled=false`;
- no candidate manifest/checkpoint/operator snapshot was emitted because the upstream host/market-data gate blocked before candidate processing, which is the expected fail-closed boundary.

Still WAITING_EXTERNAL for the next open/fresh DE40 market window:

- verify broker clock/timezone from a fresh tick and closed-M5 feed;
- obtain a GREEN isolated one-shot heartbeat;
- confirm candidate manifest/checkpoint/operator evidence from the GREEN cycle;
- repeat the isolated cycle for overlap/reconciliation evidence;
- only after those are green, perform the controlled Scheduled Task reload/restart and runtime-health/reconciliation proof.

No PAPER or LIVE authorization is granted by this evidence.

## 12. Optional weekend / 24/7 broker-clock cross-check — READ-ONLY DIAGNOSTIC ONLY

Use this optional path when DE40 is closed and the broker exposes an actually active 24/7 instrument such as a crypto CFD. This can provide independent evidence about the broker's current encoded wall clock. It does **not** replace the market-open DE40 checks in Step 2122 and it does **not** by itself prove a unique IANA timezone/DST regime.

### 12.1 Discover the broker's exact 24/7 symbol name first

Do not assume the broker uses `BTCUSD`. With MT5 already open and logged in, use the existing MT5 Python environment and inspect names only:

```powershell
$py = "$HOME\Documents\dax-Day-main\.venv-mt5\Scripts\python.exe"

@'
import MetaTrader5 as mt5

if not mt5.initialize():
    print("MT5 INIT FAILED:", mt5.last_error())
    raise SystemExit(1)

try:
    names = sorted(
        str(s.name)
        for s in (mt5.symbols_get() or ())
        if "BTC" in str(s.name).upper() or "BITCOIN" in str(s.name).upper()
    )
    print("24X7 SYMBOL CANDIDATES:")
    for name in names:
        print(name)
    print("COUNT =", len(names))
finally:
    mt5.shutdown()
'@ | & $py -
```

This discovery call uses `initialize()`, `symbols_get()` and `shutdown()` only. It does not select a symbol, request prices, alter the SHADOW Scheduled Task or call an order API.

Interpretation:

- zero candidates: stop this optional path; do not guess a ticker;
- multiple candidates: inspect the broker-visible instrument names/metadata and choose only an exact intended 24/7 market-data symbol; do not auto-pick by substring;
- one plausible candidate: retain the exact broker symbol string for the diagnostic below.

### 12.2 Compare explicit timezone candidates with the existing probe

Use the existing diagnostic owner; do not create a second probe. Create a separate evidence directory so no scheduled-SHADOW state is touched:

```powershell
$symbol = '<EXACT_BROKER_24X7_SYMBOL>'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = '.runtime\mt5_timezone_diagnostic'
New-Item -ItemType Directory -Force $outDir | Out-Null
$out = Join-Path $outDir "broker_timezone_24x7_$stamp.json"

& $py .\scripts\diagnose_mt5_broker_timezone.py `
  --symbol $symbol `
  --candidate UTC `
  --candidate Europe/Berlin `
  --candidate Europe/Helsinki `
  --bars 20 `
  --max-age-seconds 600 `
  --output $out
```

The diagnostic intentionally runs the credential-free MT5 probe once per timezone candidate and emits, per candidate, `clock_ok`, raw tick delta, normalized tick delta and closed-M5 timestamps. The underlying probe may call `symbol_select(<exact-symbol>, True)` to subscribe/show that market-data symbol in MT5; this is not broker order submission and does not alter the SHADOW task/state directory.

Required safety surface in the diagnostic result:

- `decision_state=HUMAN_REVIEW_REQUIRED`;
- `auto_selected_timezone=null`;
- `verification_state=UNVERIFIED`;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- notes include `READ_ONLY`, `DIAGNOSTIC_ONLY`, `NO_AUTO_TIMEZONE_SELECTION`, `NO_CREDENTIALS`, `NO_ORDER_API`.

### 12.3 Evidence interpretation — never auto-verify the IANA zone

A useful 24/7 observation requires the selected instrument to be genuinely active at observation time and at least one candidate to produce a plausibly fresh normalized tick delta within the configured age bound. Compare all candidates; do not judge from the raw tick alone.

A point-in-time match may:

- reject a timezone candidate whose normalized clock remains materially stale/shifted while another candidate is fresh;
- support the **current UTC offset interpretation** of the configured broker timezone;
- expose that the configured `Europe/Helsinki` interpretation is inconsistent with the active 24/7 feed.

A point-in-time match may **not** by itself:

- prove that the broker's IANA timezone identity is uniquely `Europe/Helsinki` rather than another zone with the same current offset;
- prove the broker's DST transition rules over the year;
- set `broker_timezone_verified=true`;
- make the DE40 market-open host gate GREEN;
- authorize PAPER/LIVE or any order capability.

Retain the diagnostic JSON, exact Git commit, exact broker symbol and observation time as supporting evidence. Final broker-timezone verification remains fail-closed and requires evidence sufficient to distinguish the actual broker clock regime; the Step-2122 DE40 market-open freshness/candidate/restart gates remain separately mandatory.
