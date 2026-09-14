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

## Windows sampling — one-command runner (current procedure)

Automation task start: **8105fae4247370ea6ee5e367a89c44786a6a922e**, exact/no drift; main/base e0784ebfc11bee28475fd9c3385be661af58a738, PR109 OPEN/UNMERGED, preceding CI DAX678 / Research1462 SUCCESS.

Attempt01 is **ABORTED_FAIL_CLOSED AS SUPPLIED**: A Exit0 at .runtime/ig_raw_m5_truth_2233_v2/A.json; B Exit2 / IG_AUTHENTICATION_FAILED_NO_RETRY; C/AB/BC NOT RUN. Work has not received original A bytes. Preserve that directory and A unchanged; never mix it into attempt02.

The current launcher is scripts/run_ig_raw_truth_2233.ps1, optionally scripts/run_ig_raw_truth_2233.cmd. It runs scripts/run_ig_raw_truth_2233.py, which exclusively invokes the existing diagnostic with the same Python interpreter and absolute script/output paths. No new engine, Candidate processing, state migration or provider policy is introduced.

Known Windows worktree: C:\Users\Mandy\Documents\dax-Day-ig-hostcheck. Deployment must first put this clean worktree on the **exact published final head from the Work closeout**. The launcher intentionally does not fetch, switch, reset, clean or accept a newer head automatically. Once deployed, the entire attempt needs just this one start command, from the worktree:

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_ig_raw_truth_2233.ps1 -ExpectedHead FINAL_HEAD_FROM_CLOSEOUT

The closeout supplies this command with the actual final SHA substituted, rather than asking the mobile user to calculate anything. The default external credential path is the already-used C:\Users\Mandy\ig_demo.env; it is never displayed or copied into the Summary. Python defaults to python, matching the verified host command; an explicit interpreter path with spaces is supported via -PythonExecutable. The optional CMD launcher accepts the same parameters. Do not run Candidate fresh-start/resume while DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED remains active.

Default new namespace: **.runtime/ig_raw_m5_truth_2233_v2_attempt_02**. If it already exists, STOP; no overwrite, delete, reuse or automatic namespace increment. A deliberately later attempt requires an explicitly chosen new numbered namespace via -Namespace. Old RAW V1/V2 files and intermediate Candidate state remain untouched.

### Schedule, failures and visible evidence

- Preflight: Windows, exact head, tracked drift/untracked Python/import parity via the existing guard, restricted unused attempt namespace, external credential file presence. Namespace is claimed atomically with mkdir. RAW output uses the existing JSON persistence owner with overwrite=false: a same-filesystem hard link publishes complete bytes atomically and fails if the destination appeared during collection. Unsupported filesystem publication fails closed; there is no replace fallback. Other runtime-state callers retain the existing default replacement behavior. No credential contents are read by the runner.
- A is scheduled 60 seconds after the **next** UTC five-minute boundary; B exactly five minutes later, C ten minutes later. This sampling offset is not a finalization grace and changes no timestamp interpretation.
- Each permitted Request window is [scheduled UTC, scheduled UTC + 60 seconds). Windows are fixed once, never replanned. Waits are at most30 seconds per clock check, with wall/monotonic continuity checks and no network polling. Allow roughly11–16 minutes plus local comparisons; keep the Windows host awake.
- Each child diagnostic gets one invocation, no shell, no retry: one login, one read-only prices request, cleanup. B follows only successful A; C only successful B. Three separately scheduled sessions are intentional; no automatic replacement session after a failure.
- A success requires Exit0, a freshly created, canonical hash-valid RAW V2 artifact with matching head and the **actual price request_started_at_utc inside its fixed window**. A login that delays the request beyond the window produces a preserved artifact but an aborted attempt, never an accepted replacement. Response observation remains the diagnostic's actual clock, never the schedule.
- Network/auth/nonzero exit, missing/invalid artifact, missed window, clock/code drift or timeout immediately abort. Child timeouts:120s RAW,30s local compare; no automatic rerun. Auth401 remains IG_AUTHENTICATION_FAILED_NO_RETRY. Child provider text/stdout/stderr and exceptions are never forwarded.
- Only all successful A/B/C permit AB, then BC. Both use --compare locally, no credentials or provider calls; canonical comparison output is checked against the exact source artifacts. A failed AB stops BC.
- Exit0 means **RAW acquisition and local comparisons succeeded**, never that timestamp semantics or Step2233 was verified. Any other attempt result returns Exit2 / ABORTED_FAIL_CLOSED.

The console displays HEAD, namespace and all schedules; WAITING FOR A/B/C, acquisition status/exit, compare statuses and FINAL STATUS. Supply the final screenshot/summary first; then A/B/C/AB/BC source JSON for substantive review. Do not supply credentials.

SUMMARY.json is published once with exclusive creation. It contains exact_head, attempt_namespace, started_at/finished_at, scheduled_at/invoked_at, per-capture requested/success/exit/status and actual request/response clocks/fingerprint, compare status/exit/fingerprint, final_state/error_code, NONE/false and deterministic fingerprint. Here requested means the child acquisition was invoked; actual successful price-request clocks are recorded separately. NOT_RUN captures have requested=false/exit=null. Provider text, API keys, account IDs and tokens are excluded. Preflight rejection does not create/alter an attempt directory: its safe summary is stdout only. A hard host termination cannot guarantee a summary; never infer success from partial artifacts.

The runner preserves all published files on failure and does not compare incomplete or mixed attempts. Successful automation alone does not establish interval-start/end, a maximum revision window or provider finality. Actual raw clocks and cross-boundary comparisons still require review under the unchanged classification gate below. Existing live Candidate quarantine, strict overlap and all safety limits remain.

### Automation validation scope

Offline regressions cover exact-head/tracked-drift blocking, exclusive namespace/summary and race-safe RAW publication, A/B/C/compare short circuits, no retries, retained previous A, actual Request windows, clock discontinuities, hash-bound source/compare validation, safe errors, NONE/false, single-child paths with spaces and PowerShell exit propagation. The local selected environment is unavailable for this tranche; no local execution is claimed. Mandatory GitHub CI executes a focused runner/RAW diagnostic regression selection and Python syntax compilation, then the full suite, Ruff and all eight existing offline/safety gates on the published head. No JavaScript changed and no real Windows/IG attempt is executed by Work.

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
