# Step 2233 — RAW provider truth before another Candidate contract

Updated: 2026-09-14. Task start: `5b0b716f886361227fbe15152c9fa316fbe7a914`, exact/no drift. PR109 OPEN/UNMERGED, main/base `e0784ebfc11bee28475fd9c3385be661af58a738`; start CI DAX676 / Research1460 SUCCESS.

**2233 UNVERIFIED / RAW HOST EVIDENCE WAITING_EXTERNAL.** The implemented60s policy is not a verified finalization contract. Do not repeat the earlier Candidate fresh-start/resume runbook to close this step. Preserve all2232/2233 files. No change to strategy, general normalization, grace number, overlap, checkpoint or execution semantics is justified before raw evidence review. Step2231/2232 historical user-supplied successes remain bounded initial observations, not proof of timestamp semantics or immutable bars.

## New binding user-supplied findings

- Stored nominal close11:40 changed high/low/close/volume; strict resume correctly blocked STATE_CHANGED_OVERLAP.
- A successful60s-policy fresh-start processed nominal12:25. Subsequent resume again blocked overlap; later comparison reported close25405.6->25406.6 and volume175->192. Thus60s does not establish provider finality.
- SnapshotA at approximately12:45:47 observed raw snapshotTimeUTC12:45, normalized event12:40/close12:45; midpoint OHLC approximately25428.5/25429.3/25420.7/25424.7, volume29. Later same normalizedclose volume125. Original raw files, exact request/response times and hash bytes have not been supplied to this Work. No fabricated values or independent host run.

These demonstrate instability of rows treated as processed/closed by the existing lane. They do **not** distinguish timestamp-start from timestamp-end with historical revision or another convention. No finite grace or pair of unchanged observations proves permanent immutability.

## Owners reused / observation boundary

`scripts/ig_raw_m5_timestamp_diagnostic.py` performs one existing Demo login, one existing pricesV3 MINUTE_5/max40/pageSize0 GET and session cleanup. No inventory/account/dealing calls, polling, retries or Candidate processing. Existing external credentials loader, exact-head/import-parity guard, UTC parser, credential checks/fingerprint, JSON/atomic-write/OS-lock owners are reused. There is no new Candidate state or engine.

The artifact includes request-start and immediate response-observation UTC, exact head/EPIC, raw snapshotTimeUTC, bid/ask/lastTraded for each OHLC, and present numeric lastTradedVolume/volume (missing remains missing). Unknown fields, local snapshotTime, account IDs and all headers are excluded by structural projection. Numeric null remains null. Invalid values block rather than copying provider strings.

RAW V2 includes zero-based raw_row_index, a deterministic fingerprint for each projected row and the complete envelope. Authoritative normalized_event_time/normalized_close_time/is_closed/freshness_seconds remain null while their states are UNKNOWN; candidate_finalized is false because no Candidate input is authorized under an unresolved contract. Both current interval-end and alternative interval-start mappings are explicitly UNVERIFIED hypotheses. Each hypothesis separately displays event/close, request-start-based closure and response-observation age/freshness against the existing canonical600s limit. Negative hypothetical age means not-yet-closed, never current/finalized. No hypothesis asserts a provider-proven mapping, finality, current Candidate decision or successful resume. Local comparisons validate canonical source contracts/hashes, require same code head and sequential observations, identify changed raw fields by the **same raw timestamp**, retain both source hashes and indicate whether observation spanned timestamp+5minutes. Changed raw rows are facts; **historical closed-bar revision remains UNKNOWN until timestamp semantics is resolved**. Hashes bind artifact integrity, not provider authentication.

## Windows sampling — three single runs, manual five-minute pauses

Use the new RAW V2 diagnostic head. Older RAW V1 artifacts are preserved and rejected for V2 comparison with RAW_EVIDENCE_SCHEMA_MISMATCH, without rewrite/migration. This RAW observation schema bump is not a final Candidate state-contract migration. The current live Candidate CLI has no success path: after existing prior-state validation it blocks DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED before opening IG, Candidate processing or atomic evidence publication. Hash-bound local evidence reads retain existing head/manifest/freshness checks; prior-head/intermediate success cannot be presented as current new-head evidence. No CLI bypass, grace replacement, strategy or virtual-lifecycle change.

Known host: `C:\Users\Mandy\Documents\dax-Day-ig-hostcheck`; external credentials: `C:\Users\Mandy\ig_demo.env`. Use the exact published diagnostic head reported with this handoff, not its preceding start head. No reset/clean/deletion, no merge. The only host action is this read-only diagnostic; do not run Candidate processing under the disproven policy.

```powershell
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck'
# Set $ExpectedHead to the exact published diagnostic head from the Work closeout.
if ((git status --porcelain --untracked-files=no | Out-String).Trim()) { throw 'TRACKED_DRIFT' }
git fetch origin nextgen-bot-line-v1
if ($LASTEXITCODE -ne 0) { throw 'FETCH_FAILED' }
if ((git rev-parse origin/nextgen-bot-line-v1).Trim() -ne $ExpectedHead) { throw 'BRANCH_DRIFT' }
git merge-base --is-ancestor 5b0b716f886361227fbe15152c9fa316fbe7a914 HEAD
if ($LASTEXITCODE -ne 0) { throw 'UNKNOWN_LOCAL_ANCESTRY' }
git merge-base --is-ancestor HEAD $ExpectedHead
if ($LASTEXITCODE -ne 0) { throw 'PARALLEL_LOCAL_DRIFT' }
git switch --detach $ExpectedHead
if ($LASTEXITCODE -ne 0) { throw 'CHECKOUT_FAILED' }

$RawDir = '.runtime/ig_raw_m5_truth_2233_v2'
if (Test-Path $RawDir) { throw 'PRESERVE_EXISTING_RAW_EVIDENCE_REVIEW_BEFORE_NEW_RUN' }
$Now = [DateTimeOffset]::UtcNow
$Boundary = $Now.AddSeconds(-$Now.Second).AddMilliseconds(-$Now.Millisecond)
$Boundary = $Boundary.AddMinutes(-($Boundary.Minute % 5))
$AAt = $Boundary.AddSeconds(60)
if ($Now -gt $AAt) { $AAt = $AAt.AddMinutes(5) }
$BAt = $AAt.AddMinutes(5)
$CAt = $AAt.AddMinutes(10)
"Manual RAW A no earlier than $($AAt.ToString('o'))"
"Manual RAW B no earlier than $($BAt.ToString('o'))"
"Manual RAW C no earlier than $($CAt.ToString('o'))"

function Invoke-2233Raw([string]$Name, [DateTimeOffset]$At) {
    $Current = [DateTimeOffset]::UtcNow
    if ($Current -lt $At -or $Current -ge $At.AddMinutes(4)) { throw 'RAW_SAMPLING_WINDOW_MISSED' }
    python scripts/ig_raw_m5_timestamp_diagnostic.py --expected-head $ExpectedHead --credentials-file 'C:\Users\Mandy\ig_demo.env' --output "$RawDir/$Name.json"
    "RAW $Name Exit: $LASTEXITCODE"
    if ($LASTEXITCODE -ne 0) { throw 'RAW_FAILED_STOP_NO_RETRY' }
}
```

Wait manually until AAt, then execute only:

```powershell
Invoke-2233Raw 'A' $AAt
```

Wait until BAt, then only `Invoke-2233Raw 'B' $BAt`. Wait until CAt, then only `Invoke-2233Raw 'C' $CAt`. This covers two successive raw timestamps before/after their next boundary without rapid login sessions. A missed window or any failure stops the experiment; do not silently replace snapshots, retry or present older success as current. Session cleanup failure also blocks publication. If auth401, fixed credential-free code IG_AUTHENTICATION_FAILED_NO_RETRY; no retry policy.

Then these two comparisons run entirely locally, without credentials or IG requests:

```powershell
python scripts/ig_raw_m5_timestamp_diagnostic.py --expected-head $ExpectedHead --compare "$RawDir/A.json" "$RawDir/B.json" --output "$RawDir/AB.json"
if ($LASTEXITCODE -ne 0) { throw 'RAW_AB_COMPARE_FAILED' }
python scripts/ig_raw_m5_timestamp_diagnostic.py --expected-head $ExpectedHead --compare "$RawDir/B.json" "$RawDir/C.json" --output "$RawDir/BC.json"
if ($LASTEXITCODE -ne 0) { throw 'RAW_BC_COMPARE_FAILED' }
```

Supply A/B/C plus AB/BC JSON and actual stdout/exit codes. Never supply the credentials file. The experiment is accepted only if the actual request/response times show two successive timestamps observed before and after their respective next M5 boundaries; manual schedule alone is not evidence of that coverage.

## Semantics decision gate / remaining work

### Classification and acceptance at the full-mandate continuation

| Question | Current evidence/status |
| --- | --- |
| INTERVAL_START | UNVERIFIED; no full paired RAW source observations or interval-reference proof supplied |
| INTERVAL_END_WITH_REVISIONS | UNVERIFIED; changed normalized/processed rows do not establish their true intervals |
| OTHER / UNKNOWN | Current class C; timestamp semantics UNKNOWN, no final normalization selected |
| RAW mutation | User-supplied binding observations; screenshots IMG_3918.png and IMG_3910.png inspected as corroboration of normalized volume29->125 and resume/auth codes, not complete RAW JSON |
| Historical closed-bar revision | UNKNOWN until interval semantics is proven; no finite revision bound inferred |
| Final canonical Candidate contract/state migration | BLOCKED pending RAW proof;60s engine/manifest/evidence V2 remain superseded historical implementation |
| New-contract Windows fresh-start/resume/operator proof | WAITING_EXTERNAL after canonical contract implementation and its exact-head CI; not attempted under quarantine |

The complete PHASE2–12 mandate is received. The inspected screenshots expose normalized probe/operator output; they do not provide raw bid/ask/lastTraded OHLC plus exact request/response times for A/B/C. Source filenames shown on the host are not uploaded source bytes. No original raw JSON or exact source fingerprint is reconstructed from OCR/screenshots. Repository diagnostic namespace is .runtime/ig_raw_m5_truth_2233_v2; Candidate intermediate namespace remains .runtime/ig_cand001_shadow_e2e_2233, preserved/quarantined. Final Candidate namespace/schema/manifest will only be chosen after evidence-backed contract changes.

V2 comparisons include leaf-by-leaf bid/ask/lastTraded and volume differences, presence versus null, first_seen_at/later_seen_at and signed ages relative to the raw timestamp, plus source indices/bars back from raw tail. Seen times are explicitly scoped to THIS_COMPARISON_PAIR, not a claim of the provider's earliest historical observation. Mutation type is OHLC_ONLY, VOLUME_ONLY, MIXED or UNCHANGED; it is an observed RAW difference, not an asserted revision of a known closed interval. revision_duration_upper_bound_seconds stays null. Unchanged later observation gives bounded observed stability, not permanent finality.

After RAW proof: choose exactly one justified canonical market-data owner; all consumers derive closure/finalization/freshness from it. Any final timestamp/finalization change must bump Candidate manifest/evidence identity and use a new namespace, reject intermediate state deterministically and preserve old files. Keep every changed processed-row overlap strict. If class B is proven without a revision bound, evaluate a restart-safe later-unchanged-confirmation policy without session spam, retaining later-revision fail-closed behavior. If class A is proven, map close=raw+5min and remove gratuitous grace unless independent revision evidence justifies it. While class C persists, no live Candidate processing or invented contract.

PHASE7 acceptance tests for a final provider contract and PHASE9 new-contract Windows cycles remain UNVERIFIED. Current synthetic regressions exercise RAW facts/hypotheses, quarantine, preserved intermediate checkpoint/overlap/identity/virtual lifecycle, canonical600s limit,401/no-retry and credential-free hashes. They are not substitutes for the missing final-contract or host proofs. All14 PHASE10 acceptance items are required before2233 VERIFIED/COMPLETED; no later whole-number step is selected now.

The official [IG REST pricesV3 reference](https://labs.ig.com/reference/prices-epic.html), checked2026-09-14, calls snapshotTimeUTC only "Snapshot time"; it specifies MINUTE_5, bid/ask/lastTraded, nullable volume and pageSize0 but does not formally establish interval-start/end or a finalization deadline. Streaming conventions cannot be substituted as REST proof.

RAW changes over timestamp+5min are consistent with a forming start-labelled bar **and** an end-labelled historical bar being revised. They alone cannot prove which interval the OHLC represents. If these observations do not resolve that distinction, obtain a contemporaneous independently timestamped market trace or an explicit authoritative provider statement/controlled interval reference. Do not classify start/end by preference, volume growth or elapsed time alone. No additional grace is guessed.

Before a correct final Candidate contract can be implemented: review raw source files, classify what is actually proven, preserve UNKNOWN where unresolved, and apply the now-complete PHASE2–12 user mandate. Then bind any justified contract to manifest/state/evidence without silent legacy migration and keep strict changed-processed-overlap behavior. Only successful new-contract Windows fresh-start + subsequent resume + hash-bound operator reads and source evidence review can close2233 VERIFIED/COMPLETED. No subsequent whole-number step is activated.

Safety: NONE/false, no broker order/cancel/modify/order_send, no strategy/OR15/risk/sizing/cost/V11.2 changes, no execution enablement, merge, force push or Acceptance refresh. Protection/reconciliation and permanent provider finality remain UNKNOWN.

## Historical Phase1 validation

22 synthetic diagnostic tests;141 focused IG/Candidate/checkpoint tests passed. Full suite2758 passed/6 local PowerShell skips (2764 total). Full Ruff, IG AST syntax/import tests, diff whitespace and all eight existing offline/safety gates passed. JavaScript unchanged. Exact published diagnostic head and its DAX/Research CI must be verified after publication, separately from these local results. No real IG session or Windows run was performed by Work. Implemented diagnostic readiness does not close2233 or establish timestamp truth.

## Full-mandate continuation validation / publication gate

Actual continuation start420fc2a3f1332b7d3055a8cd97c414a03433d4cf, clean/no unknown drift; only Work's prior RAW Phase1 commit since original5b0b716. DAX677 / Research1461 SUCCESS on that preceding head,2764 CI tests. Current code:36 RAW diagnostic +50 Candidate/reader/quarantine tests (86);158 focused IG/Candidate/checkpoint,170 including two existing governance suites. Full2775 passed/6 local PowerShell skips (2781 total), full Ruff/syntax/imports and eight offline/safety gates pass. Initial full rerun caught two GOVERNANCE failures from the user-required deferred-next-step pointer; exact NOT ACTIVATED form now accepted only with explicit pending/blocked state, while integer monotonicity/audit checks remain. No data/strategy/risk/freshness/overlap threshold loosened.

13 changed files in this continuation: two IG scripts, their two tests, two governance tests and seven governance/runbook records. Required DAX/Research CI must be checked on the exact published continuation head, not420fc2a. Original/intermediate Candidate evidence is neither rewritten nor promoted. No actual IG network session/Windows Candidate run performed by Work. Step2233 remains UNVERIFIED / RAW HOST EVIDENCE WAITING_EXTERNAL; canonical-contract implementation and real new-contract cycles are not completed.
