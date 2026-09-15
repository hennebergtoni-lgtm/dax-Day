# DAX-BOT ÜBERGABE — RESUME KEYWORD

## Resume: canonical Windows Python selection (2026-09-15)

Runtime owner head: `30d9575fc8b8526e281a86c9717d19e9dda6b71b`;
all three mandatory CI lanes are GREEN.

The previous real run stopped safely with `PYTHON_COMMAND_RESULT_MULTIPLE`
before preflight/authentication. Use only the new exact-head command. The shared
owner now resolves multiple command rows into probed interpreter identities and
accepts duplicates only when they are the same runtime or when one valid
configured-family identity deterministically outranks fallback launchers.
WindowsApps aliases are not started. A true equal-rank ambiguity emits
`PYTHON_RUNTIME_AMBIGUOUS` plus the sanitized candidate matrix and performs no
IG login.

Exactly one Windows run remains. Do not ask for PATH, Python or `py` diagnostic
commands. Step2238 is IMPLEMENTED/WAITING_EXTERNAL; readiness remains 8/0/13/6,
M01 IN_PROGRESS, NONE/false, no order, LIVE prohibited.

## Resume: Step2238 full Windows host-lane audit (2026-09-15)

Use the exact current PR head, not an older Python-hardening head. Code commit
`6bf1a6bbbcc0af24ba35a6c8397a614f241013fe` replaces the duplicated
Step2238 bootstrap with `dax_windows_host_lane.psm1`, an aggregate 51-check
preflight and the shared canonical IG DEMO credential contract. It reuses the
Step2237-proven isolated local clone and direct Python execution. `-I -S`/runpy
and the old step-specific PowerShell runtime owner are retired.

Exactly one Windows run remains. If preflight blocks, use its complete sanitized
matrix; do not request manual Python, network or filesystem commands. If it
passes, the same invocation performs one authenticated read-only Step2238 flow,
publishes hash-bound evidence and cleans only its owned deployment. Step2238 is
IMPLEMENTED/WAITING_EXTERNAL; Step2239 IMPLEMENTED/WAITING_EXTERNAL; Step2240
IN_PROGRESS/BLOCKED; M01 IN_PROGRESS; readiness 8/0/13/6 and NOT READY. Linux is
NOT_REQUIRED. No DEMO or LIVE order, no promotion, NONE/false. See
`STEP_2238_WINDOWS_HOST_LANE_AUDIT.md`; older Step2238 sections are historical.

## Step2238 total Python-boundary normalization — authoritative (2026-09-15)

Immutable head `bbd1d29671f8d275179a38d04681dfdfca3fc248`
reached deployment and WAIT but returned `RUNNER_UNEXPECTED_FAILURE`.
`legacy_partial_state=NONE_DETECTED`; checkout/evidence remained intact,
execution disabled, and no broker side effect occurred. The unknown leaf must
not be guessed.

Use only the replacement exact-head command. Its dedicated Python-runtime owner
normalizes discovery, version/identity, import-origin, path/JSON anomalies and
collector bootstrap exceptions to fixed credential-free codes while suppressing
stderr. Do not run a manual diagnostic chain or any order. Step2238 remains
**IMPLEMENTED / WAITING_EXTERNAL** and capability remains NONE/false.

## Step2238 Python-start hardening — authoritative (2026-09-15)

The real Windows run on `60539746383cbf0753d282f149d447d6e63c1130`
passed exact-head isolated deployment and reached WAIT, then stopped fail-closed
with `PYTHON_START_FAILED`. `legacy_partial_state=NONE_DETECTED`; existing
checkout and evidence were retained; execution remained disabled. Because STDERR
was intentionally suppressed, this record proves only that failure occurred at
the former undifferentiated Python launch boundary. It does not prove a Python
version, import failure, credential failure or IG failure. No login, broker read
or side effect is claimed.

The hardened wrapper now resolves exactly one application executable, verifies
Python 3.11+, checks executable identity, verifies that both `daxlab` and the
Step2238 collector import from the isolated exact-head clone, and launches the
collector through an isolated `-I -S` bootstrap with explicit clone-owned
`src` and `scripts` roots. All checks run before the credentials file is
consumed by the collector or any IG login occurs. STDERR remains suppressed.

The former umbrella codes are retired. Discovery, ambiguity, executable,
version, identity, missing script, import, import-origin, collector start,
missing/multiline/invalid result and exit-status mismatch each have a fixed
credential-free code. Step2238 remains **IMPLEMENTED / WAITING_EXTERNAL** until
the replacement exact-head run succeeds. M01, the 27 gates and NONE/false do not
advance. No DEMO order; LIVE prohibited.


## Resume: STEP2238 WINDOWS READINESS EVIDENCE

Step2233/2237 remain COMPLETED/VERIFIED. Step2238/2239 repository work is
IMPLEMENTED but WAITING_EXTERNAL; Step2240 is IN_PROGRESS/BLOCKED. Run only the
single exact-head Step2238 Windows wrapper documented in
`STEP_2238_2240_PREDEMO_PROGRAM.md`, then return its SUMMARY and retained
namespace bundle. Do not issue a second diagnostic chain or any order.

Current readiness is 8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL / 6
BLOCKED. Capability remains NONE/false; LIVE prohibited.
Sentinel/Helperbot/Multi-Market remain queued.


## Step2233/2237 real-host closeout — authoritative (2026-09-15)

**Formal decision:** Step2233 and Step2237 are **COMPLETED / VERIFIED** on the
accepted runtime-evidence head
`62029df3353b74cc58884f06cd0c296ddd8d73cc`.

The user-supplied real Windows console record is:

- START: isolated exact-head local clone; existing checkout untouched;
- WAIT: one IG read-only session; Fresh Start; next true M5 close; Resume;
  Operator;
- SUMMARY: `SUCCESS / error_code=NONE`;
- namespace:
  `.runtime/ig_m5_contract_2237_interval_start_v2_attempt_03`;
- deployment cleaned; `execution_capability=NONE`;
  `order_execution_enabled=false`; no broker order and no LIVE authorization;
- `legacy_partial_state=DETECTED_RETAINED`.

This is sufficient for the two step closeouts because the exact runner emits
SUCCESS only after the published-head and isolated deployment gates, Windows and
import-parity checks, canonical INTERVAL_START contract check, an exclusive
fresh namespace, one login, two complete authenticated read-only probe cycles,
true-close freshness, strict unchanged-overlap and resume-anchor validation,
current Operator projection/fingerprint validation, one logout and
ownership-bound clone cleanup. The detected legacy partial worktree was
correctly retained and is **non-blocking contained technical debt**; it was not
pruned, deleted, migrated or used by the successful clone.

This closes the repeated market-data/session/state-resume evidence cycle. It
does **not** prove account identity, atomic flat inventory, broker/server clock,
DST/session policy, quote status, economics, native tick/quantity grids,
stop/target rules, broker history, execution reconciliation or dealing
lifecycle. M01 therefore advances to **IN_PROGRESS**, not COMPLETED. The current
27-gate result is **8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL /
6 BLOCKED**. Effective execution remains NONE/false; no DEMO order; LIVE
prohibited.

The accepted runtime commit and runner blobs remain immutable evidence:
PowerShell `cfad3ca6b4effb24fdd6dc0fa7ef0d7cb9fae63b`; Python
`8274ac096f33c8c2f2321964352e68ba3a59fb10`. A later documentation-only
closeout commit does not claim a different host run and does not alter these
runner blobs.

**Next work package:** Step2238 — M01 native IG read-only account, inventory,
clock, market-rules and economics evidence. Repository owners must first be
extended to validate and hash-bind those dimensions; afterwards exactly one new
Windows runner is required for that new evidence package. Re-running the
Step2237 runner is not required. Sentinel, Helperbot and Multi-Market expansion
remain deferred.

All lower sections that still describe Step2233/2237 as WAITING_EXTERNAL are
historical and superseded by this section.

## Step2237 Windows worktree-add hardening — authoritative overlay (2026-09-15)

The real Windows run at
`78fb8cf8648e51de964f09e205f7f278193c5439` reached START and then stopped
fail-closed with
`WORKTREE_ADD_FAILED_DEPLOYMENT_RETAINED`. WAIT, Python, IG login and
market-data requests were not reached; the existing checkout and all Evidence
remained unchanged. The exact Windows leaf cause is **UNKNOWN** because the
wrapper intentionally suppressed Git stderr. No host-specific explanation is
invented.

The repository audit identifies the unsafe dependency class: `git worktree add`
shares administrative state with the source repository and can fail after
creating some combination of the temporary directory, checkout files, a
worktree `.git` pointer, and `.git/worktrees/<id>` metadata. Windows path
limits, ACLs, antivirus/indexing locks, or stale partial registration are
possible causes, but none is claimed as the observed cause.

Implementation head
`47d2bffc9a6b0dab527f77726d606796cf1c1de2` retires worktree creation and
removal. The V3 deployment owner now:

- applies the origin, fetched published-head, ancestry and exact-commit gates
  before deployment;
- creates a short unique `%TEMP%\d2237-<128-bit-token>` parent and writes a
  head-bound `DAX_STEP2237_DEPLOYMENT_OWNER_V1` marker;
- creates an independent local clone with `--no-checkout --no-hardlinks`,
  Windows long-path handling and an empty hooks path, then checks out only the
  immutable expected commit inside that disposable clone;
- proves the deployed HEAD and clean tree before Python, while keeping durable
  State/Evidence in the caller-owned runtime root and exclusive `attempt_03`
  namespace;
- detects old Step2237 worktree registrations/directories read-only and reports
  only `NONE_DETECTED`, `DETECTED_RETAINED` or
  `QUERY_INCOMPLETE_RETAINED`; it never prunes or deletes them;
- recursively removes a new partial or complete clone only when temp-root,
  short-name pattern, allowed top-level layout, non-reparse paths, expected
  head and the in-memory ownership token all match. Otherwise it retains the
  deployment with `DEPLOYMENT_CLEANUP_FAILED_RETAINED`.

There is no `worktree add/remove/prune`, in-place checkout, reset, clean,
stash, merge, force operation, dealing route or retry. All errors exposed to the
operator remain fixed and credential-free. Code validation is green: focused
271, full 3103, Ruff, Python syntax, PowerShell parser, fixed fail-closed tests,
eight safety/recovery gates, `dax-bot-1x-ci` #702 and
`research-lab-ci` #1486.

Step2233/2237 remain **IMPLEMENTED / WAITING_EXTERNAL** until the new one-command
Windows run proves exact-head Fresh Start, next true M5 close, Resume, Operator
and cleanup. M01 and the 27-gate readiness tally do not advance from this
deployment-only change. Effective capability remains
`execution_capability=NONE`, `order_execution_enabled=false`; no DEMO order;
LIVE prohibited. Any lower section describing the temporary worktree or
`attempt_02` is superseded implementation history, not the current runner.


## Step2237 Windows exact-head deployment hardening — authoritative overlay

The real Windows attempt on
`236ea841d3d9e9d30532b08270995cc4925abaa5` stopped fail-closed with
`DETACHED_CHECKOUT_FAILED` before WAIT, Python, IG login or any market-data
request. Existing evidence remained intact; execution stayed NONE/false. Because
the former wrapper deliberately suppressed Git stderr, the precise Windows Git
sub-error is **UNKNOWN** and is not invented. The repository-side design defect is
verified: deployment depended on mutating `checkout --detach` inside the
existing host checkout.

The corrected owner no longer switches, cleans or requires a clean existing
checkout. It verifies the configured origin, fetches only the branch, requires
the published branch head to equal `ExpectedHead`, verifies ancestry from the
previous accepted Step2237 head, and materializes that immutable commit in a
unique temporary detached Git worktree. Candidate code runs only from that clean
exact-head worktree. Durable State/Evidence remains under the caller-owned host
runtime root in the new exclusive attempt02 namespace, outside the ephemeral
deployment.

After the one-session Fresh Start → next true M5 close → Resume → Operator flow,
the wrapper verifies that its own worktree is clean and removes it without
`--force`. It removes only its uniquely created empty parent. If safe cleanup
cannot be proven, it retains the deployment and emits a fixed credential-free
cleanup error instead of deleting blindly. There is no merge, reset, stash,
in-place checkout, clean, force-push, dealing route, relogin or retry.

Step2233/2237 remain **IMPLEMENTED / WAITING_EXTERNAL** until this corrected
single-command real Windows run succeeds. `execution_capability=NONE`,
`order_execution_enabled=false`; no DEMO order; LIVE prohibited.


## Step2237 final IG M5 contract — authoritative overlay

The original Attempt03 bundle is now received as binding source evidence:
A/B/C/AB/BC/SUMMARY plus the hash manifest and historical REVIEW, evidence head
`2a99f96e06f7ce1f311c767dec43d236bb63eedd`, export runtime head
`7728453c3c4f8fcd2cf6f8189b0f94562ccfa04f`. The original-byte artifacts and
their `DAX_IG_RAW_REVIEW_V1:OTHER_UNKNOWN` record remain historical and are not
rewritten.

A new V2 structural review promotes the operational mapping to
**INTERVAL_START**: raw T is the tail while T..T+5 accumulates; at T+5 the same
raw identity moves one row back; open stays fixed while high/low/close and volume
grow. The coupled pattern repeats for raw15:25 (volume57→1003) and raw15:30
(210→1379). Treating T as interval end would require two consecutive supposedly
closed bars to reopen and accumulate for exactly the following full M5 interval;
operationally that is the start mapping. Canonical `event_time=T`,
`close_time=T+5m`; freshness starts at true close. No post-close provider
revision SLA is claimed.

The one owner is `src/daxlab/adapters/ig_market_data.py`:
`DAXLAB_IG_M5_MARKET_DATA_CONTRACT_V2` /
`IG_MINUTE_5_SNAPSHOT_UTC_INTERVAL_START_V2`. The Candidate envelope/state and
RunManifest are bumped to V3 in a new namespace. Old interval-end/60-second state
is rejected deterministically; no silent migration/reset. The extra60-second
Candidate workaround is retired. Strict `STATE_CHANGED_OVERLAP`,600-second
freshness, `NONE / order_execution_enabled=false` and the hard LIVE block remain.

Repository implementation and one-session Windows fresh-start/resume/Operator
automation are prepared. Step2237 and Step2233 remain
**IMPLEMENTED / WAITING_EXTERNAL** until that one exact-final-head Windows runner
succeeds. M01 advances but is not complete;27 readiness gates are not all
VERIFIED, therefore no `DEMO_ONLY` promotion and no order. See
`STEP_2237_IG_M5_CONTRACT_CLOSEOUT.md` and
`ACCELERATION_M01_DEMO_READINESS_MATRIX.md`.


## Step2237 Windows export failure — authoritative update

Attempt at ef24d63470b2d2ec076089d7ee8a39d0dbcae2ec reached START but not WAIT; generic FAIL_CLOSED/RUNNER_FAILED; no ZIP. This localizes failure before Python but the old owner erased the exact Git-gate identity. Do not infer it. Corrected runner now emits one allowlisted credential-free error_code for every Git/deploy/Python/source/filesystem/publication failure and never exception/stderr/payload text. Originals unchanged; no login/broker call. Step2237 remains WAITING_EXTERNAL. See STEP_2237_WINDOWS_EXPORT_FAIL_CLOSED.md and use only the new immutable-head command after exact-head CI.

## Current acceleration closeout — 2026-09-14 authoritative

The acceleration mandate is implemented in existing owners, with complete40 hypotheses/100 failures/24 learnings reconciliation, original-byte export automation, one-session transport safety, full identity/TCA, risk/tail/DNA, independent PTC and causal hysteresis preparation. See [complete A–Z report](ACCELERATION_PROGRAM_FINAL_2026_09_14.md), [M01 +27 readiness gates](ACCELERATION_M01_DEMO_READINESS_MATRIX.md), [source/owner register](../research/acceleration_program_v1.json).

Current official pointer: last completed2236 (independent local lane), active2237 WAITING_EXTERNAL original-bundle/contract/native IG readiness, next2238 after successful closeout. Step2233 stays WAITING_EXTERNAL. Historical capture SUCCESS at2a99f96e is supplied evidence; original bytes and final provider mapping are missing. Current effective NONE/false, no bounded transport activated, no first order. Local green software cannot prove M01 account/economics/clock/inventory/native lifecycle/recovery.

**User authorization is current:** one small bounded diagnostic IG DEMO evidence order may execute autonomously after all27 gates VERIFIED; this supersedes historical DEMO NOT AUTHORIZED only for that scope. LIVE/real money/live switch/transfers/automatic promotion remain unauthorized. No blind retry/resubmit/slot release/reset. Continuous DEMO remains M07-gated. Cancel/modify requires verified lifecycle design.

One Windows START→WAIT→SUMMARY export runner is prepared; immutable exact-final-head start command is in the final handoff. No recapture03, manual six-command sequence, credentials or broker call. Need ZIP containing all six hash-bound originals before final contract interpretation.

Repository/code truth remains authoritative. Local code/check results and exact final documentation-head CI are distinguished in the report/final handoff. No Acceptance refresh/main merge/force push; no CAND-001/frozen-reference/cost mutation.



## Current binding user authorization — 2026-09-14 acceleration mandate

The user explicitly authorizes one first bounded, small diagnostic **IG DEMO** evidence order after all 27 Pre-DEMO readiness gates are VERIFIED. This supersedes older DEMO NOT AUTHORIZED text only for that bounded IG DEMO scope. LIVE, real money, live-account switching, cash transfers and automatic DEMO-to-LIVE promotion remain unauthorized. Cancel/modify is limited to a separately verified lifecycle design. No blind retry/resubmit, unknown transport replay or autonomous slot release.

Current effective capability remains **NONE / order_execution_enabled=false**. No readiness promotion has occurred; the IG read-only client remains read-only. Target DEMO_ONLY must be scoped to the bounded transport after real account/instrument/economics/policy/protection/reconciliation/restart evidence and final market-data contract are VERIFIED. Continuous DEMO remains gated by M07 and is not enabled by this mandate.

Attempt03 at exact head2a99f96e06f7ce1f311c767dec43d236bb63eedd is **SUCCESS / VERIFIED AS SUPPLIED**: one login, A/B/C, cleanup, AB/BC successful; Candidate false, NONE/false. Original A/B/C/AB/BC/SUMMARY bytes are still WAITING_EXTERNAL. Acquisition success is not interval semantics or provider finality proof. Use scripts/export_ig_raw_truth_2233.ps1 for exact-head deployment plus one offline hash-bound ZIP export; never repeat capture03 or overwrite prior evidence.

The acceleration mandate activates independent Post-DEMO A–J preparation/research/failure work when dependencies permit. Original rescue reports remain historical read-only artifacts. No Acceptance refresh, merge or force push is authorized.


## Historical capture overlays — not current roadmap

**Latest2233 session update:** attempts01/02 user-reported A success/B401 abort; original evidence preserved. One read-only in-memory IG session now owns A/B/C: one login, three PricesV3 GETs on success, one cleanup before local AB/BC. No relogin/refresh/retry; any session loss or cleanup failure aborts. Default unused namespace .runtime/ig_raw_m5_truth_2233_v2_attempt_03; one Windows PS1/CMD start with exact final -ExpectedHead. Attempt-summary V2 records session lifecycle; RAW timestamp/evidence V2 and Candidate/state/overlap contracts unchanged. Precise host401 root cause UNKNOWN. See current session section in STEP_2233_IG_RAW_TIMESTAMP_TRUTH.md; earlier per-capture subprocess procedure is historical. UNVERIFIED / WAITING_EXTERNAL; NONE/false, no Candidate or broker mutation, no later step activated. Local execution unavailable; exact-head mandatory CI required.


**2233 automation update (2026-09-14):** Existing RAW attempt01 aborted fail-closed as supplied: A Exit0 preserved at .runtime/ig_raw_m5_truth_2233_v2/A.json; B IG_AUTHENTICATION_FAILED_NO_RETRY Exit2; C/AB/BC NOT RUN. New one-command Windows RAW runner: scripts/run_ig_raw_truth_2233.ps1 (optional CMD), explicit -ExpectedHead from final closeout, default unused .runtime/ig_raw_m5_truth_2233_v2_attempt_02. Fixed UTC A/B/C windows, no retries/replacement sessions, local AB/BC only after all captures succeed, exclusive credential-free SUMMARY.json, NONE/false. See STEP_2233_IG_RAW_TIMESTAMP_TRUTH.md for the current automated procedure; the former manual command sequence is superseded. Automation is implemented repository-side, not timestamp proof. Step2233 remains UNVERIFIED / WAITING_EXTERNAL; Candidate quarantine and strict overlap remain, historical evidence untouched, no subsequent step activated. Local execution unavailable in this tranche; exact-head mandatory CI is the validation authority.


**Latest2233:** post60s real-host overlap failure reopens the finalization contract. UNVERIFIED / RAW PROVIDER TRUTH WAITING_EXTERNAL; use `STEP_2233_IG_RAW_TIMESTAMP_TRUTH.md`, not the superseded60s Candidate rerun. Diagnostic collects raw prices only; timestamp hypotheses/provider finality remain UNKNOWN. Strict overlap and old evidence preserved. Full PHASE2–12 mandate received. Classification C: OTHER / UNKNOWN; live Candidate path quarantined with DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED, no override. Use RAW V2 namespace .runtime/ig_raw_m5_truth_2233_v2; no final Candidate contract/schema/namespace is yet proven. SHADOW only/NONE/false; no subsequent step activated.

Status: **BINDING RESUME POINTER / REPOSITORY TRUTH FIRST**
Updated: **2026-09-14**
Repository: `hennebergtoni-lgtm/dax-Day`
Branch: `nextgen-bot-line-v1`
PR: `#109`
Publication head observed at handover creation: `20c781614c47ab945bebf56cb6b73d40764b149d`

## Kennwort

The canonical one-word resume command is:

`Übergabe`

When the user starts or continues a chat with `Übergabe`, recover the DAX Daytrading Bot project automatically from repository truth. Do not ask the user to reconstruct the previous chat when repository/File Library access is available.

## Mandatory recovery order

1. Fetch PR #109 and pin the **fresh current head SHA**, base/main SHA, PR state and required CI before any write. The publication head above is only the creation-time observation and must never override a newer head.
2. Read `docs/CURRENT_WORK_STEP.md`.
3. Read `docs/MASTERSTAND_LATEST.md`.
4. Read `docs/IG_DEMO_M5_TIMESTAMP_HANDOFF.md` for the current IG/M01 host-evidence lane.
5. Reconcile branch drift before any change; never force-push.
6. Continue the active safe work automatically instead of restarting setup already completed.

## Current operational handover

- Official active whole-number step is **2233**, IMPLEMENTED_LOCAL / real Windows finalization fresh-start+resume WAITING_EXTERNAL; last completed step is **2232**, COMPLETED / VERIFIED on actual Windows as supplied in the binding2233 mandate. Re-pin the fresh pointer before work.
- M01 remains the immediate operational milestone: **Real-host evidence**.
- IG Demo account/API setup, authenticated login, Deutschland-40 market discovery, live market status, contract/economics inspection and M5 retrieval have already been exercised on the real Windows host. Do **not** restart broker/account/API-key setup unless fresh evidence shows it is broken.
- Current target IG market: `IX.D.DAX.IFMM.IP` (Deutschland 40 cash, €1/point variant used for the host evidence lane).
- Real-host diagnostics established that IG M5 `snapshotTimeUTC` behaves as an interval-end label on the observed Demo response. The dedicated handoff `docs/IG_DEMO_M5_TIMESTAMP_HANDOFF.md` owns the exact evidence and correction details.
- The corrected IG timestamp/read-only implementation was validated before this handover; re-pin fresh head/CI before deployment because later documentation commits may have advanced the branch.
- Windows IG worktree used for this lane: `C:\Users\Mandy\Documents\dax-Day-ig-hostcheck`.
- Original MT5 hostcheck worktree remains separate: `C:\Users\Mandy\Documents\dax-Day-nextgen-hostcheck`; do not destabilize it merely to run IG evidence.
- Credentials remain local in `C:\Users\Mandy\ig_demo.env`; never print or commit them.
- The corrected read-only IG host probe has passed as supplied by the user; see `docs/STEP_2231_REAL_HOST_CLOSEOUT.md`. Protection/reconciliation remain UNKNOWN and broader M01 is incomplete.
- Historical continuation before the post60s failure (superseded by RAW truth/live quarantine): the exact-head **2233 finalization-contract fresh-start then later resume** in `docs/STEP_2233_IG_M5_FINALIZATION_HANDOFF.md`. Grace60 applies only to Candidate input;600s freshness/exact overlap unchanged. Use the new2233 namespace, preserve old2232 evidence, no silent migration/state reset or rapid login retries. Reuse known Python/external credentials; no MT5 supervisor or fixture-as-host claim. Next2234 only after real2233 verification.

## Safety state — binding

- SHADOW/read-only evidence: authorized under existing contracts.
- `execution_capability=NONE`.
- `order_execution_enabled=false`.
- No broker order/cancel/modify action is authorized by this handover.
- First bounded DEMO evidence order remains a separate gate and requires fresh reviewed readiness plus explicit authorization at that time.
- LIVE remains not authorized.
- V11.2 remains frozen; no handover action may silently mutate it.

## Continuity rule

If chat memory conflicts with repository truth, fresh code/tests/runtime/broker evidence and `docs/CURRENT_WORK_STEP.md` win. `docs/MASTERSTAND_LATEST.md` remains the canonical broad masterstand; this file only provides the durable one-word resume key and immediate operational pointer.
