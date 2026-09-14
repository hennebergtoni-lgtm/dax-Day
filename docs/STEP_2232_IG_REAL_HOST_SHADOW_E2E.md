# Step 2232 — Real-host SHADOW end-to-end observability

Status: **IMPLEMENTED_LOCAL / REAL WINDOWS RUN WAITING_EXTERNAL**
Date: 2026-09-14
Repository: `hennebergtoni-lgtm/dax-Day`, branch `nextgen-bot-line-v1`, PR #109 OPEN / UNMERGED.
Task start: `8523c6cd98944c6ed95f6f7af585e2c4d9eb41de`; no initial drift.
2231 closeout commit: `576fee53b08d6c6aafd6d07ef0a0fdc922c8fa6f`; DAX #671 and Research #1455 SUCCESS.
Only the exact final publication head with both required CI checks green may be deployed for this test. Its SHA is in the final Work handoff; this document cannot contain its own commit SHA.

## Scope and predecessor

2231 is COMPLETED / VERIFIED AS SUPPLIED for the corrected real Windows IG feed slice (see `STEP_2231_REAL_HOST_CLOSEOUT.md`). No raw JSON bytes, exact observation/close timestamps or fingerprint string were supplied for that closeout. Broader M01, MT5 lane 2122 and independent review/authorization lane 2206 remain incomplete/external. Protection/reconciliation remain UNKNOWN.

2232 tests **live IG read -> canonical CLOSED-M5 -> unchanged CAND-001 -> existing SHADOW coordinator/virtual state -> validated V3 telemetry -> operator display projection read from persisted evidence**. NO_SIGNAL is a valid observable decision; no profitability, signal frequency or execution readiness is asserted. Work has no established control of the Windows host. Offline synthetic tests do not close this step.

## Reuse audit

| Existing component | Finding / use |
| --- | --- |
| `ig_demo_readonly_probe.py`, IG REST/client and market-data adapter | Already validated IG read-only owner. Expose the SAME validated closed bars alongside its existing redacted probe, without another network request or changed old CLI. |
| `mt5_shadow_supervisor.py` | Requires Windows MT5 probe/bundle and MT5 host cycle. Do not start it with IG or invent an MT5 bundle. |
| `windows_mt5_shadow_start.ps1` | MT5 scheduled-task/venv launcher; not the IG test launcher. |
| `check_windows_mt5_shadow_runtime.ps1` | MT5 tasks/heartbeat; not evidence for this isolated IG invocation. |
| `check_windows_mt5_shadow_code_parity.ps1` | MT5 parity surface. IG test instead binds exact Git HEAD and rejects tracked/untracked source-code drift before and after processing. Runtime output/cache files are not code drift. |
| `export_mt5_shadow_telemetry.py`, `windows_mt5_shadow_telemetry_export.ps1` | MT5/Neon export; not fed fabricated IG-as-MT5 data. |
| `read_candidate_operator_runtime.py` | Reads the Neon current projection. This local test does not claim a Neon write/read. |
| `serve_operator_console.py` | Existing full console consumes MT5 bundle/heartbeat/checkpoint. Its browser/mobile rendering is not verified by this test. |
| Candidate pipeline/orchestrator | Generic canonical `runtime.Candle`; reused unchanged including strategy, admission, intent, virtual lifecycle and publication owners. |
| Candidate checkpoint, atomic JSON, single-instance lock | Reuse complete manifest-bound state and one atomic evidence/state envelope; no second strategy/state engine. |
| OperatorSnapshot parser, telemetry validator, browser projection | Reuse actual V3 source validation and display DTO. Persist, read back, compare identities and fingerprint. Clearly labelled local operator scope. |

Reproduced ADAPTER gap: the validated IG domain Candle has `instrument_id`/`M5`; CAND-001 requires runtime `symbol`/`5m`. Passing the domain Candle directly fails with AttributeError on `symbol`. The narrow bridge maps the verified exact EPIC to existing DE40/5m and preserves source, UTC interval, OHLC and volume. It changes no strategy/config, costs, risk or execution owner.

The new `scripts/ig_cand001_shadow_e2e.py` is one executable test connection, not a daemon or replacement supervisor. Its live CLI requires Windows and calls only the existing read-only collector. There is no replay-input CLI. Manifest binds the IG stream contract, exact code head, unchanged Candidate/sizing contract and existing default virtual fill model.

## Acceptance criteria

| Criterion | Required real-host proof |
| --- | --- |
| Host/code | Known Windows worktree, exact tested publication SHA; tracked code clean and no untracked source code. |
| Live data/time | Newly collected 40-row IG response, exact EPIC/source, UTC collection/request/response/processing/export times, closed intervals, continuous M5, latest close fresh through export and operator read under unchanged 600 s. |
| Candidate/decision | CAND-001/config/run/session identity, signal or NO_SIGNAL, admission, full DecisionRecord and proposed plan if any; latest CURRENT decision matches latest closed input and operator identity. |
| SHADOW lifecycle | Existing virtual lifecycle/checkpoint, origin decision/publication state, NONE/false throughout. Virtual fills/outcomes are simulation only. |
| Runtime/telemetry | GREEN latest Candidate input health, no errors, warnings preserved, fresh validated source snapshot and complete envelope fingerprint. |
| Operator | Persisted V3 snapshot parses and validates; display projection agrees, independent read checks the fingerprint returned by the successful live invocation. No Neon/full console parity claim. |
| Restart/conflict | Reuse prior complete checkpoint only with exact manifest/head and unchanged overlapping rows plus a present anchor. No gaps, silent resets or duplicate decision processing. |
| Safety | No broker placement/cancel/modify, MT5 send, execution enablement, slot release, merge or Acceptance refresh. Protection/reconciliation UNKNOWN. |

Older bars processed for initial warmup/catchup are marked HISTORICAL_CATCHUP and are not contemporaneous decision evidence. Only the newest closed bar is CURRENT. Missing opening-range history yields the existing OR_INCOMPLETE/NO_SIGNAL with a visible warning; no invented range or threshold relaxation.

## Smallest Windows run

Known worktree: `C:\Users\Mandy\Documents\dax-Day-ig-hostcheck`.
Known external credentials: `C:\Users\Mandy\ig_demo.env` (never print their contents).
Evidence/state: `C:\Users\Mandy\Documents\dax-Day-ig-hostcheck\.runtime\ig_cand001_shadow_e2e\evidence.json`.

1. Use the exact PowerShell block in the final Work handoff: it pins the actual final SHA, checks tracked cleanliness and uses `git merge --ff-only` solely to synchronize the local checkout (no PR merge). Stop on any unknown remote/checkout drift. No force/reset/clean/stash commands.
2. Run the single live test below with `$ExpectedHead` set by that pinned block. The already working `python` environment is reused; do not change the separate MT5 task/environment. Dependencies are existing project dependencies, including Windows tzdata.

```powershell
Set-Location 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck'
$ShadowOutput = python scripts/ig_cand001_shadow_e2e.py --credentials-file 'C:\Users\Mandy\ig_demo.env' --expected-head $ExpectedHead | Out-String
$ShadowExit = $LASTEXITCODE
$ShadowOutput
if ($ShadowExit -ne 0) { throw '2232 BLOCKED: stop; prior evidence is not this run.' }
$ShadowEvidence = $ShadowOutput | ConvertFrom-Json
python scripts/ig_cand001_shadow_e2e.py --read-evidence '.runtime/ig_cand001_shadow_e2e/evidence.json' --expected-head $ExpectedHead --expected-fingerprint $ShadowEvidence.fingerprint
if ($LASTEXITCODE -ne 0) { throw '2232 operator read BLOCKED; stop.' }
```

3. Return both outputs, both exit codes and the newly written `evidence.json` for source review. It is structurally credential-free; do not send the `.env` file. Review actual UTC times, last-close/freshness, candidate/session/decision identities, signal/admission, virtual lifecycle, operator projection, warnings and hash. Only after that real source review may 2232 be COMPLETED / VERIFIED.

The script's success status is SHADOW_E2E_OBSERVED, not a governance completion. A read is bound to the hash just returned by the successful live command, so a surviving old file cannot substitute for a failed current invocation.

## Fail-closed behavior

On failure exit 2, fixed credential-free error code; no provider exception text. Existing successful evidence is not overwritten and is not current-run evidence. Stop before operator read if the live command fails. Lock conflicts block before collection. Changed head/manifest, changed overlap or missing anchor block rather than reset. Same latest closed bar blocks STATE_NO_NEW_CLOSED_M5; a fresh rerun needs the next new M5 and the existing unchanged anchor. No automatic retry, state deletion or gap masking.

Classify actual failure as DATA/CLOCK/ADAPTER/STRATEGY/STATE/RUNTIME/TELEMETRY/OPERATOR/GOVERNANCE, reproduce it, minimally fix, regress and rerun the real host. Offline success cannot establish Windows OS-lock behavior or real transport/clock/state correctness.

## Closeout boundary

Local validation: 70 existing IG regressions and 22 new connection/state/operator/CLI regressions pass; full suite **2711 passed / 6 local PowerShell skips** (2717 collected). Ruff on src/tests/scripts, AST syntax/imports and JavaScript syntax pass. All eight existing offline gates pass: recovery preflight, research registry, hypothesis ledger, web status, static runtime safety, V11.2 probe, V11.2 replay and SHADOW soak. Required CI must still be checked on the actual publication head; prior #671/#1455 results belong only to the 2231 documentation commit.

2232 remains WAITING_EXTERNAL until the real bundle is reviewed; next exact whole-number step is **2233**, reserved for the single evidence-driven successor after 2232 passes. 2233 is not started or execution-authorized here. NONE/false, SHADOW only; V11.2/CAND-001 rules and MT5 path remain unchanged. No DEMO/PAPER/LIVE order authorization.
