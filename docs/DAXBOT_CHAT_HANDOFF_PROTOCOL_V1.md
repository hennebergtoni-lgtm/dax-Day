# DAX-BOT Chat Handoff Protocol V1

## Active Step2238 continuity overlay — V3 matrix invariant (2026-09-15)

Real Windows has reached authenticated READ after the proven host preflight, but
the latest exception produced no eight-row matrix. Treat it as a collector
availability-contract defect, not endpoint evidence. The repository-owned V3
collector now guarantees an ordered eight-row stdout matrix whenever login
succeeded. Unexpected per-resource exceptions are sanitized UNKNOWN rows;
independent reads continue unless authentication is definitively lost. Derived
processing, cleanup, evidence finalization and publication cannot erase the raw
rows.

Next status remains Step2238 IMPLEMENTED/WAITING_EXTERNAL, M01 IN_PROGRESS,
readiness 8/0/13/6 and DEMO NOT READY. Preserve all V2 evidence. Use one V3
exact-head host command only after mandatory CI. NONE/false; no retry, dealing,
order or LIVE.

## Step2238 module-isolation handoff — authoritative (2026-09-15)

The real `MODULE_IMPORT_EXCEPTION` at
`575666143c92d21d4fb211655098c41a936eac79` is historical and did not reach
preflight, credentials or IG. Its discarded raw exception must not be inferred.

The active runner uses a unique, hash-equal, runner-owned module identity and
prefixed exports, then unloads exactly that module. Any remaining failure emits
one sanitized `MODULE_DIAGNOSTIC` with stage, safe exception metadata, runtime
mode/policy, MOTW and fingerprints. Dot-sourcing is prohibited because it would
weaken module-scope/export and execution-policy boundaries. Handoff remains one
command and one result; the 52-check/eight-resource lane is unchanged.

## Step2238 module-load handoff — authoritative (2026-09-15)

Treat `HOST_RUNTIME_OWNER_IMPORT_FAILED` from real head
`5381fd144c0fdad9b1d8c4ffc7a304f1fbe75880` as historical evidence only: the
old wrapper did not preserve which module-load contract failed. Never ask for a
manual parser/import command.

The active runner owns a broker-free exact-deployment pre-import stage with the
five fixed `MODULE_*` outcomes, validates four exact exported functions and
labels this boundary POWERSHELL. Required CI imports the actual module using
Windows PowerShell 5.1; PowerShell 7 is supplemental. Handoff remains one
immutable-head command and one structured SUMMARY. The eight authenticated GET
resources are unchanged and cannot run after a module block. Step2238 stays
IMPLEMENTED/WAITING_EXTERNAL; NONE/false, no retry/order, LIVE prohibited.

## Step2238 IG readiness-matrix handoff — authoritative (2026-09-15)

Treat `IG_SESSION_READ_FAILED_NO_RETRY` from real head
`98de1476cde6667ee07f5fbc97d52de0f6da7dcd` as historical READ-lane
evidence, not as a named endpoint diagnosis. The active v2 runner must be invoked
once. It performs one login, up to eight no-retry GETs, one cleanup, and publishes
`READ_MATRIX.json` plus hash manifest. An incomplete matrix returns
`IG_READINESS_MATRIX_INCOMPLETE` while retaining the evidence namespace.

Do not ask for endpoint-by-endpoint commands. Review the single sanitized matrix
and advance only its proven dimensions. Step2238 is IMPLEMENTED/WAITING_EXTERNAL;
M01/gates remain 8/0/13/6 and NONE/false. See
`STEP_2238_IG_READINESS_MATRIX.md`.

## Step2238 exact-clone head handoff — authoritative (2026-09-15)

The real `HEAD_MISMATCH` on
`9ae082ce094967cedc3ab6525173a68041f76965` was valid domain evidence: the
collector inherited a different checkout as CWD. The active `_head()` derives
the exact clone from `Path(__file__).resolve()` and invokes `git -C` there.
Tests cover a different valid Git CWD and a non-Git CWD.

The wrapper now emits `COLLECTOR PRECHECK` before any client construction and
prints `AUTH READ-ONLY START` only after local HEAD/runtime/namespace/credential
checks pass. Handoff remains one command and one SUMMARY; no manual diagnosis,
retry or order.

## Step2238 authenticated collector handoff — authoritative (2026-09-15)

The host preflight is real-host proven at 50/52 PASS with zero required failures
on `ecd029924af4cd949676dace039c330fff31e12d`. The subsequent AUTH READ-ONLY
result was hidden by `HOST_LANE_PROCESS_EXIT_MISMATCH`.

The active owner preserves all allowlisted structured collector failures and
their result payload, independently records process-exit contradiction, validates
NONE/false, carries failure phase IG_SESSION, and never lets secondary cleanup
replace the primary collector error. Handoff is one exact-head invocation and
one SUMMARY only; no manual diagnostics, retry or order.

## Step2238 IG HTTP handoff — authoritative (2026-09-15)

The 49/51 real-host result on
`8defee400ccb40f8bde379f0d3acfed316f9d07c` is historical evidence: the only
required failure was the combined IG HTTPS check observing HTTP 5xx after DNS
and TLS passed. No authentication or broker access occurred.

The active V2 contract has 52 checks. Treat
`NETWORK_IG_HTTPS_TRANSPORT=PASS` as transport evidence only;
`IG_PROVIDER_HEALTH=UNKNOWN` is expected before the one authenticated read-only
flow because IG has no documented anonymous health endpoint. Never promote a
5xx to application health and never block transport merely because a valid HTTP
response is 5xx. No HTTP response remains a required NETWORK failure. Use the
payload's derived `failure_phase`; do not infer PYTHON from runner chronology.

Handoff requires one exact-final-head invocation only. Step2238 remains
IMPLEMENTED/WAITING_EXTERNAL; NONE/false; no order; LIVE prohibited.

## Step2238 canonical Python runtime handoff — authoritative (2026-09-15)

Runtime-selection implementation head:
`30d9575fc8b8526e281a86c9717d19e9dda6b71b`; native Windows #8, DAX #719 and
research #1503 CI are GREEN.

The latest Windows blocker `PYTHON_COMMAND_RESULT_MULTIPLE` occurred before the
51 checks and before authentication. The replacement owner probes resolver
outputs and selects by real executable identity, version, architecture and exact
project origins. Same-runtime `python`/`python.exe`/`py` results and duplicated
PATH rows are not ambiguous; Store aliases and invalid runtimes are rejected;
only multiple distinct valid best-rank identities block. On a block the runner
prints the sanitized candidate matrix and does not log in.

Handoff remains one exact-head invocation and its final output/evidence. Never
request a manual interpreter diagnostic chain. Step2238 stays
IMPLEMENTED/WAITING_EXTERNAL and NONE/false; no DEMO order; LIVE prohibited.

## Step2238 Windows host-lane overlay — authoritative (2026-09-15)

The active handoff uses the current PR head and the single runner
`scripts/run_ig_predemo_readiness_2238.ps1`. It owns exact-head isolated local
deployment and delegates runtime/process/output behavior to the shared
`dax_windows_host_lane.psm1`. Before any IG login, the runner emits all 51
sanitized preflight rows and aggregate counts. A failed run must be continued
from that matrix; the operator must not be asked for a manual diagnostic chain.

The exact credential key contract is shared with the collector and values are
never logged. Existing checkout/evidence are retained; only marker- and
token-bound temporary deployment/staging resources can be removed. Windows is
the target; a Linux worker is NOT_REQUIRED. Successful CI is not real-host
evidence. Step2238 stays IMPLEMENTED/WAITING_EXTERNAL until the one-command
real-host run succeeds. Keep NONE/false, no order and LIVE prohibited. See
`STEP_2238_WINDOWS_HOST_LANE_AUDIT.md`. Lower Step2238 handoff notes are
historical.

## Step2238 total Python-boundary normalization — authoritative (2026-09-15)

The exact-head Windows run on
`bbd1d29671f8d275179a38d04681dfdfca3fc248` reached WAIT and then failed closed
as `RUNNER_UNEXPECTED_FAILURE`. `legacy_partial_state=NONE_DETECTED`; existing
checkout/evidence were retained, execution was disabled and no broker side
effect occurred. No narrower cause may be inferred.

The successor wrapper has one tested PowerShell Python-runtime owner. All
discovery/version/identity/import-origin/collector-start operations, including
native .NET/path exceptions and malformed null/array/JSON shapes, terminate in
documented credential-free codes with secret stderr suppressed. Handoff is one
replacement command only; no manual diagnostics and no order. Step2238 remains
**IMPLEMENTED / WAITING_EXTERNAL**, NONE/false; LIVE prohibited.

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


## Step2238–2240 authoritative handoff (2026-09-15)

Continue with exactly one Step2238 exact-head Windows evidence run. The runner
uses one IG DEMO read-only session and emits a credential-free hash-bound bundle
for account, bracketed inventory, history scope, market v4 economics/stops,
quote/server clock and finalized M5. Step2239 consumes only verified bundle
values; absent tick/quantity/economics values remain blockers. Step2240 may not
promote capability until native IG reservation, confirm, reconciliation and
restart truth are complete.

Gate tally before that run: 8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL /
6 BLOCKED. Effective state is NONE/false; no order; LIVE prohibited.
Step2233/2237 are not reopened. Sentinel/Helperbot/Multi-Market remain queued.
See `STEP_2238_2240_PREDEMO_PROGRAM.md`.


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


Status: **BINDING**  
Updated: **2026-09-14 — Step2233 reopened / RAW provider truth before another contract**

Latest2233 continuity: user-supplied60s-policy FreshStart followed by changed-overlap block disproves any60s finality guarantee. Current source: `STEP_2233_IG_RAW_TIMESTAMP_TRUTH.md` and CURRENT_WORK_STEP pointer. RAW one-shot collection/local comparison are IMPLEMENTED_LOCAL; actual source snapshots, timestamp class, justified final contract and new Windows FreshStart/Resume/Operator proof are WAITING_EXTERNAL/UNKNOWN, not completed. Preserve old state and strict overlap. No inferred start/end convention, new grace guess, silent migration or execution authorization. Full PHASE2–12 mandate received. Classification C: OTHER / UNKNOWN pending complete RAW sources; live Candidate path blocks DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED with no CLI override. RAW V2 sampling/local comparison only; no final Candidate contract or new Candidate namespace selected. No subsequent whole-number step activated.

Purpose: make chat/context handovers deterministic and repository-backed so the DAX-BOT project resumes without asking the user to reconstruct long chats, including after conversation-length saturation. Repository truth and source Work artifacts are preferred over chat memory.

The binding step-closure/workflow-integrity rules remain defined in `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`. If this protocol conflicts with that gate on official step closure, pointer synchronization, interrupted-lane numbering, or claims about ongoing work, the workflow-integrity gate controls.

---

## 1. Resume codewords — BINDING

Canonical phrase:

`Weiter mit dem DAXBot`

Accepted aliases include:

`Weiter mit DAX Bot`

`Weiter mit DAXbot`

`Weiter DAX Bot`

When one of these phrases is used in a new or existing chat, treat it as an instruction to recover the DAX Daytrading Bot automatically. Do not ask the user to paste the prior masterstand, repeat known project facts, or manually re-upload Work artifacts when repository/File Library access is available.

---

## 2. Mandatory recovery sequence — BINDING

Before substantive work or any repository write:

1. read `docs/SESSION_EXECUTION_REFRESHER.md` as needed for active-turn rules;
2. pin repository `hennebergtoni-lgtm/dax-Day`, PR #109, working branch, fresh exact head SHA, base/main SHA, PR state and current required CI;
3. read `docs/CURRENT_WORK_STEP.md`; official whole-number numbering comes from this file, never chat inference;
4. read **`docs/MASTERSTAND_LATEST.md`**; it is the canonical latest handover overlay;
5. read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`;
6. read `docs/WORK_CONTINUITY_PROTOCOL.md` for Work delegation/model/thinking/credit-budget/out-of-band reconciliation rules;
7. read `docs/PROJECT_KNOWLEDGE_INDEX.md` and older `docs/MASTERSTAND.md` only when historical context is needed;
8. if ChatGPT File Library is available, search and load the Work rescue anchors in section 3 when their details are relevant;
9. reconcile branch drift, out-of-band Work results, WAITING_EXTERNAL/USER_AUTH/BLOCKED/INTERRUPTED lanes and CI before writing;
10. inspect only the active-step owners/code/tests/evidence plus directly relevant predecessor evidence;
11. continue the next safe action automatically after recovery; a recovered status report is not a stop.

Truth precedence:

1. fresh code/tests/machine/runtime/broker evidence;
2. `docs/CURRENT_WORK_STEP.md`;
3. binding safety/authorization/governance contracts;
4. `docs/MASTERSTAND_LATEST.md`;
5. original Work/File Library source artifacts;
6. historical repository docs;
7. chat memory.

If File Library is unavailable, continue from repository truth and explicitly state that source Work artifacts could not be reopened. Never invent their missing detail.

---

## 3. Work/File-Library rescue anchors — MUST SEARCH WHEN AVAILABLE

The following exact artifacts contain the original high-value Work results and must be treated as recovery sources, not disposable chat attachments:

1. `DAX_PRE_DEMO_DRIFT_REVIEW_2026-09-13.md`
2. `DAX_PRE_DEMO_HARDENING_2_FINAL_2026-09-13.md`
3. `DAX_RESEARCH_FACTORY_3_FINAL.md`
4. `DAX_POST_DEMO_NEXT_WORK.md`

Recovery rule:

- search File Library by exact filename first;
- read the relevant source file before relying on detailed Work claims;
- do not ask the user to upload it again unless File Library search genuinely cannot locate it;
- repository truth overrides Work prose where they disagree;
- Work summaries do not create broker evidence or authorization.

`DAX_RESEARCH_FACTORY_3_FINAL.md` is the canonical original source for the read-only Research Factory 3.0 output, including its 66 source entries, 40 falsifiable hypotheses, 100 deduplicated failure scenarios (not 100 independently observed incidents), 24 architecture/operations learnings, source-quality matrix and M01–M12 roadmap.

`DAX_POST_DEMO_NEXT_WORK.md` is **PLANNED / NOT EXECUTED** and must not be started merely because it exists.

---

## 4. Current milestone recovery — BINDING

Historical IG continuation before post60s failure (superseded; use latest overlay): first load `docs/IG_DEMO_M5_TIMESTAMP_HANDOFF.md`, pin the fresh PR head/main/required CI and `CURRENT_WORK_STEP.md`. Step 2231 is COMPLETED / VERIFIED AS SUPPLIED for the corrected real Windows IG feed slice, with original JSON/time/hash values not supplied to Work; see `STEP_2231_REAL_HOST_CLOSEOUT.md`. Protection/reconciliation UNKNOWN, broader M01 incomplete. Step2232 is COMPLETED / VERIFIED on actual Windows under the user-supplied binding2233 mandate (live/operator0, GREEN/FRESH, NO_TRADE/NONE/OR_INCOMPLETE/NO_SIGNAL, raw40/closed40, NONE/false/fingerprint). Subsequent provider revision correctly blocked overlap. Active2233 is IMPLEMENTED_LOCAL / real fresh-start+resume WAITING_EXTERNAL; run `STEP_2233_IG_M5_FINALIZATION_HANDOFF.md` with grace60 in Candidate-only input, unchanged600s/strict overlap, new V2 manifest/evidence and new namespace preserving2232 files. Legacy state blocks migration before collection. No rapid auth retries, MT5 supervisor or invented bundle.2206/2122 independent; next2234 only after real2233 proof. No order authorization implied.

As of the 2026-09-14 continuity update, the latest masterstand records the durable roadmap:

- M01 Real-host evidence
- M02 First bounded DEMO evidence — separately authorized only
- M03 Broker lifecycle truth
- M04 Expected vs Observed
- M05 TCA / latency / cost attribution
- M06 Data / clock parity
- M07 Continuous-DEMO safety / release operations
- M08 Tail / risk survival
- M09 Strategy robustness
- M10 Parameter plateau / multiple testing
- M11 New filters / research efficiency
- M12 Capital scaling / PRE-LIVE

This roadmap does not replace official whole-number governance. On recovery, the active official pointer remains authoritative. At the Research Factory anchor the active pointer was Step 2231, WAITING_EXTERNAL / USER_AUTH / NO BROKER SIDE EFFECT. Re-pin rather than assume that is still current.

---

## 5. Safety boundary — BINDING

This continuity protocol never grants execution.

Unless fresh authorized evidence says otherwise:

- SHADOW only is authorized under no-order contracts;
- first actual bounded DEMO evidence order requires separate explicit authorization;
- continuous DEMO/PAPER is not authorized;
- LIVE is not authorized;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no `mt5.order_send`;
- no cancel/modify;
- no automatic consumed-slot release;
- no blind retry/resubmit after ambiguous transport/restart;
- Linux/fixture/SHADOW/synthetic evidence never becomes broker truth by inference.

Do not weaken safety to satisfy a date or restore progress after a chat switch.

---

## 6. Durable Research Factory 3.0 rules to recover

A new chat should not rediscover these from scratch:

- broker connection != broker truth;
- negative evidence != proof of no execution/flatness;
- `tick_size != digits`;
- native order-price semantics != position average-price semantics;
- correct MT5 executable/data path/build/runtime owner is part of host identity;
- broker/UTC/session/DST/time semantics require real evidence;
- `order_check()` success is preflight, not execution guarantee;
- `order_calc_margin()` is not account exposure;
- quote session != trade session;
- deterministic rejects must not become blind retry;
- partial fill requires reconciliation;
- requote/price change requires revalidation;
- timeout/transport ambiguity -> UNKNOWN/QUERY_REQUIRED;
- PTC is independent from strategy risk;
- emergency/kill authority is separate from strategy and from the current read-only console;
- same-terminal MT5 history is not independent drop-copy;
- Expected-vs-Observed and TCA precede strong interpretation of forward/live drift;
- trade-R drawdown != real account-equity drawdown;
- dependent/block/regime/cluster simulation extends existing IID research;
- parameter plateaus/neighbourhood stability matter more than one best parameter;
- rollback != state reset;
- more architecture without added broker/risk/profit evidence should be rejected.

Research decision order remains:

**REGIME -> STRUCTURE -> ENTRY**

V11.2 remains frozen; CAND-001 is a product candidate, not a profitability proof.

---

## 7. Explicit masterstand command

Canonical phrase:

`Erstelle einen Masterstand`

When used, refresh `docs/MASTERSTAND_LATEST.md` to current repository truth and update other continuity/navigation files when their truth changed materially. Do not wait for the scheduled checkpoint if chat saturation, a major Work tranche, a major Research handoff, or a material execution/governance transition creates new durable knowledge.

The masterstand must preserve at least:

- repository/branch/PR and fresh-head guidance;
- current official pointer;
- current safety/authorization state;
- frozen reference facts;
- current CAND/product evidence maturity;
- important completed milestones since the prior handoff;
- unresolved external/auth/blocker lanes;
- Work/File-Library rescue anchors;
- current M01–M12 or successor roadmap;
- current CI/evidence truth without claiming a newer head green before verified;
- exact next safe action;
- chat/workflow/no-stop/integer-step rules.

---

## 8. Scheduled masterstand checkpoints

A masterstand checkpoint remains mandatory every 250 official whole-number work steps: 2250, 2500, 2750, ...

At each checkpoint:

1. refresh `docs/MASTERSTAND_LATEST.md`;
2. verify pointer/workflow/Work-protocol/Knowledge-Index consistency;
3. record fresh PR/head/CI truth;
4. summarize new durable findings, solved problems and remaining lanes;
5. preserve safety/authorization boundaries;
6. continue after the checkpoint unless a real global stop exists.

Every 500 steps, perform the full Architecture & Learning Review as already governed.

---

## 9. Chat-capacity saturation rule — BINDING

A platform message that the conversation is too long is a continuity interruption, not a DAX-BOT technical failure.

If saturation is approaching while actions still work:

1. stop starting new high-risk substantive work;
2. pin fresh repo/head/CI/pointer;
3. truthfully classify incomplete technical work;
4. refresh `docs/MASTERSTAND_LATEST.md` and continuity navigation if material knowledge changed;
5. ensure Work rescue anchors and exact next action are named;
6. tell the user to open a new chat and use `Weiter mit DAX Bot`.

If the old chat hard-stops first, the new chat performs the mandatory recovery sequence in section 2. Never infer completion from chat memory.

---

## 10. Whole-number / step discipline

- official steps are integers only;
- no decimal or letter suffixes;
- **Step-Close-Gate:** before a new independent whole-number step starts, the previous active step must be explicitly classified `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL`, or `BLOCKED`, with reason/evidence and `docs/CURRENT_WORK_STEP.md` synchronized;
- **Pointer-before-next-step:** the canonical pointer must be synchronized before any new independent official step begins;
- **visible numbering is monotonic**: once an official step number has been visibly used, later continuation must never reuse an older number as if it were current;
- if an interrupted lane later resumes, **resume its unfinished scope under the next unused integer** rather than reviving its old visible number;
- **the old wording `Fortsetzung Schritt N` must not be used** for a resumed interrupted lane;
- `WAITING_EXTERNAL` blocks only its lane unless it is the actual critical path;
- new independent steps require the previous active step to be truthfully classified and pointer synchronized;
- out-of-band Work commits are not retroactively relabeled as an unrelated unfinished step;
- chat audit blocks inside an active step are not new official step numbers;
- a documentation continuity refresh must not fake technical step completion.

---

## 11. Visible work / no-premature-stop contract

Preferred cadence:

`Schritt N -> Tätigkeit -> kurzer Zwischenstand -> ✅ / ⚠️ / ❌ -> tatsächliche nächste Aktion`

A status update is a visibility point, not a stop. If the next safe action can be executed with available tools/files/read-only diagnostics, execute it in the same active turn. Stop only for a real blocker, required user-side action/authorization, explicit user stop/review, milestone handoff, safety issue, or platform limit.

Do not claim autonomous background work unless an actual automation/background mechanism exists.

---

## 12. ChatGPT Work handoff reconciliation

`docs/WORK_CONTINUITY_PROTOCOL.md` remains the canonical Work operating contract.

On resume, if Work commits/results exist beyond the last numbered evidence:

1. pin exact Work commit chain/head/CI;
2. inspect actual changes/results;
3. separate skipped external gates;
4. do not auto-accept Work prose;
5. reconcile out-of-band results without corrupting official numbering;
6. preserve main-chat ownership of independent verification, Acceptance and merge unless explicitly delegated;
7. when source Work artifacts exist in File Library, read them rather than relying on a chat summary.

When Work is actively writing the branch, main chat must not concurrently write that branch.

---

## 13. End-of-recovery rule

A successful new-chat recovery should end its orientation phase with:

- fresh head/main/CI;
- official active step and external/auth lanes;
- whether Work artifacts were successfully rehydrated;
- current safety state;
- exact next action.

Then perform that next safe action if tools/evidence permit. Do not make the user prove that the previous work existed.
