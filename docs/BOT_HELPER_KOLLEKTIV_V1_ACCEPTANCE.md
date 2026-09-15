# Bot-Helper-Kollektiv V1 — Step 2241 acceptance record

## Step2244 real-host dogfood overlay — authoritative (2026-09-15)

The final-head-bound Windows/IG-DEMO read-only run supplies scoped real-host
evidence to the existing collective without expanding its authority:

| Role | Current scoped result | Boundary |
| --- | --- | --- |
| H — Host/runtime | PASS | Exact runtime head, Windows lane, 50/52 preflight with zero required failures, one session and successful cleanup. |
| D — Data truth | PASS | MARKET_V4 and M5 raw/derived contracts passed; no native tick/value semantics are invented. |
| B — Broker/recovery | PASS for READ ACQUISITION | Eight of eight broker GET outcomes passed; this is not order/deal lifecycle or reconciliation evidence. |
| S — Safety/decision | BLOCKED for DEMO ADMISSION | `economics_verified=false`; missing native economics/session/protection inputs retain the veto. |
| O — Evidence/operator | PASS | Raw, derived, Economics and component evidence were emitted under fixed sanitized schemas. |
| K — Coordination | BLOCKED for DEMO ADMISSION | H/D/B/O success cannot outvote S or the Step2240 lifecycle blockers. |

This closes the former current-host/provider action for the Step2238 acquisition
lane and provides real-host dogfood for the listed slice only. It does not turn
all T01–T15 synthetic/CI acceptance rows into real-broker evidence. Current
M01/27-gate truth is owned by `ACCELERATION_M01_DEMO_READINESS_MATRIX.md`.

Status: **COMPLETED / TECHNICALLY VERIFIED — SYNTHETIC + CI**.
Updated: 2026-09-15T10:33Z. This new technical V1 record does not replace historical
VERIFIED evidence, formal project acceptance or merge governance.
**FOLLOW-UP WORK DEBT: EXTERNAL_ONLY. Open internal V1 defects: 0.**

## Authority, pin and unchanged boundaries

| Field | Current recorded value |
| --- | --- |
| Repository / branch / PR | `hennebergtoni-lgtm/dax-Day` / `nextgen-bot-line-v1` / #109 OPEN, UNMERGED |
| Expected and observed start head | `aa11dc32fbd91c84edea19816e13fb6dc613a964` |
| main | `e0784ebfc11bee28475fd9c3385be661af58a738` |
| Runtime pin rechecked via GitHub | 2026-09-15T10:33Z; branch/head/main match, PR remains OPEN/UNMERGED |
| Start drift | NONE; only two authorized implementation commits, followed by documentation closeout |
| Accepted runtime commit | `6acb5399c1a9f23def20ada9660e09e023fdf33e` |
| CI execution commit (GitHub PR test merge, not an actual merge) | `39de0fad926a792e70ab17c0119477547d6b7a6e` |
| Identical runtime and CI tree | `b9fb2b5d194b6c049a8aff2bc495efe52d781ca7` |
| Final documentation head | Recorded by the containing documentation commit and final handoff; no new runtime authority is claimed from documentation |
| Mandate | Recovered complete `DAX_BOT_HELPER_KOLLEKTIV_V1_META_DESIGN_UND_ASTRA_AUFTRAG.md`, section 11; current user autonomy clauses take precedence |
| Scope | BOT_HELPER_KOLLEKTIV_V1_ONLY; one official work unit, Step 2241 |

`execution_capability="NONE"` and `order_execution_enabled=false` remain actual
string/boolean values. SHADOW remains allowed; DEMO/PAPER execution and LIVE are
not authorized. V11.2, CAND-001 strategy, parameters, costs and risk/loss policy
remain unchanged. No merge, force-push, foreign-worktree cleanup, broker retry,
order, cancel, modify, reservation release or new external publication target.

Step2233/2237 remain COMPLETED/VERIFIED on their historical runtime head;
2238/2239 remain IMPLEMENTED/WAITING_EXTERNAL; 2240 remains IN_PROGRESS/BLOCKED.
M01 remains IN_PROGRESS, with 8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL /
6 BLOCKED among 27 gates. This foundation does not close those lanes.

## Minimal architecture, canonical owners and rights

Two small runtime modules (`bot_helper_contract.py`, `bot_helper.py`) provide
closed immutable observations, bounded deterministic coordination and a narrow
eligibility binding. Existing `candidate_shadow_orchestrator.py` remains the
SHADOW state owner and rechecks the actual input at its entrance. The IG SHADOW
runner uses that entrance; historical catchup remains explicitly REPLAY and must
belong to a coherent window whose latest CLOSED-M5 is fresh.

| Role | Reused authority | Permitted effect |
| --- | --- | --- |
| H — Host/runtime | Existing Windows module, runtime probe and 52-check preflight | Read results, report prerequisite veto; no new host engine |
| D — Data truth | Candle contracts, quality, bar identity and resume anchor | Data findings and admission veto; no OHLC repair |
| B — Broker/recovery | Existing IG read owner, safety/lifecycle/reconciliation and checkpoint parsers | Keep broker observations separate from internal state; query/block recommendation only |
| S — Safety/decision | Existing Risk/Loss/Session owners and independent PTC | Existing vetoes bound to current account/instrument/policy; no second risk calculation |
| O — Custodian | Existing collector, atomic JSON and OS single-writer lock | New sanitized immutable raw receipts, publication/readback; no state deletion |
| O — Operator | Existing console GET route and `web/operator.*` | Read/projection only; no custodian, broker or state-write capability |
| K — Coordinator | Fixed H/D/B/S/O composition | Aggregate all causes, dependencies and delivery identity; never invent source truth or execution rights |

All helpers lack EXECUTE, broker RETRY, general shell/secret access and mutation
rights over strategy, policy, reservation, broker or foreign state. Local pure
re-evaluation is allowed. The existing runtime alone advances authorized SHADOW
state. Python modules are not an OS security sandbox.

The event contract separates ID from payload hash, source time from receipt time,
engineering maturity from operational status, and SYNTHETIC/REPLAY from REAL_HOST/
REAL_BROKER_READ. Provenance comes from the trusted adapter; parsed data cannot
promote its scope. VERIFIED requires scoped evidence and validation metadata.
Limits are 256 events, 64 KiB per envelope, 32 direct dependencies and eight
routing stages. Unknown identities, stale dependencies, source reversal,
contradictions, cycles and overflow remain visible; a heartbeat cannot clear
unresolved reservation/emergency truth. No event performs broker I/O.

The explicit V3 collector→IG safety binding preserves original schema/hash and
UNKNOWN economics/history. An IG source adapter feeds the existing console;
it invents no MT5 heartbeat or missing code/policy identity. Display failure and
broker failure remain distinct. NONE/false always projects EXECUTION=DISABLED.

## Evidence, restart and transfer guarantees

The collector retains sanitized per-slot observations before subsequent reads.
Byte-hash receipts confirm durable records; a complete seal binds all eight
receipts. Semantic hashes and file-byte hashes have different scopes. The existing
single-writer lock covers the local writer; a persistent lock filename alone is
not ownership. Publication failure does not delete confirmed raw observations.

Crash tests kill real child processes before/after receipt and Candidate checkpoint
commit. Recovery uses existing parsers, retains unresolved state and source time,
and rejects incomplete/tampered complete manifests. Duplicate delivery does not
create a second durable intent/session effect. Only confirmed records survive;
precommit/process/disk loss cannot be promised away. Missing records remain UNKNOWN.
No broker call is replayed and no cursor is a broker acknowledgment.

A fixed **synthetic** sink contract checks target, receipt and byte-for-byte
readback, including the manifest. Its success is not a demonstrated user-host
upload. Local originals survive a failed transfer. No general uploader, account,
secret, service, tunnel, database schema or new destination was created.

## Acceptance matrix — measured technical V1 result

All three required workflows passed on the accepted runtime tree. Each workflow
executed **pass 1 = 916 PASS / 0 SKIP / 0 FAIL** and **pass 2 = 916 PASS / 0 SKIP /
0 FAIL**, with fresh processes and stable source snapshots. Every T01–T15 group
passed in both passes. Actual Chromium executed at 390px on Linux and Windows.
Native Windows PowerShell 5.1 parser/import/failure-matrix tests and PS7 compatibility
passed; CI Windows is not evidence from the user's Windows machine.

Full research CI: **3450 passed / 1 skipped**, 23.43 seconds. The existing full-suite
skip is not counted as PASS. Its five conditional database steps (connection,
migrations, integrity, restore drill, detail-import drill) are **SKIPPED / external**.
Local repair freeze: **3443 passed / 8 skipped / 0 failed**; both helper passes
**915 passed / 1 Chromium skip**. Those local skips remain recorded as skips;
only the actual CI browser runs close T12/T14. Ruff and existing Safety/Recovery/
Reference/Registry gates passed without changing their acceptance thresholds.

All matrix rows below are measured **SYNTHETIC/REPLAY** assertions, with real
local state/process/file behavior. Real-host and real-broker coverage remains
**NOT_PROVEN** in every row. PASS does not mean every F001–F100 facet is solved.
The common CI/Windows column refers to the 916-case union on each runner plus
native PS5.1 parity; it is not a claim that the entire repository suite ran on Windows.

| Group | Pass 1 | Dogfood / injection evidence | Pass 2 | Three CIs / Windows | Scope / assertion reference |
| --- | --- | --- | --- | --- | --- |
| T01 Healthy / NO_TRADE | PASS | Real Candidate sequence, one intent/outcome; healthy NO_TRADE | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; `test_bot_helper_acceptance.py`, IG SHADOW e2e |
| T02 Data→admission | PASS | Stale/open/gap/duplicate/revision/nonfinite/ordering; actual entrance veto | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; acceptance + review + quality/IG adapter tests |
| T03 Broker truth | PASS | Unknown/None/manual inventory/bracket/history owner regressions | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; IG safety, inventory and reconciliation suites |
| T04 Lifecycle conflict | PASS | ACK/partial/timeout/duplicate/out-of-order; no retry/release | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; lifecycle/reconciliation/query/restart suites |
| T05 Subject binding | PASS | Account/instrument/run/session/code/policy/contract mixes | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; acceptance, review, IG safety/reservation |
| T06 Independent PTC | PASS | All 17 fixed veto cases; current subject binding; healthy PTC control | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; acceptance + independent PTC/protection |
| T07 Full matrices | PASS | 52 preflight / eight resource guards / derived-stage and cleanup faults | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; preflight and actual collector suites |
| T08 Failure isolation | PASS | Broken source/store/publisher/operator; retained independent outcomes | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; durability and HTTP/malformed suites |
| T09 Restart/recovery | PASS | Real process kills, receipts/checkpoints, tamper/restore invariants | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; acceptance + durability + canonical recovery |
| T10 Event bounds | PASS | Duplicate/conflicting IDs, stale dependencies, order, cycles/storm | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; acceptance + independent review + lock |
| T11 Leakage/trust | PASS | Closed schema, malformed/nested inputs, scope/JSON and output rejection | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; acceptance + credentials/durability |
| T12 Existing UI/HTTP | PASS | Actual GET/DOM/390px Chromium; source age preserved, failed refresh clears cached diagnosis | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC; operator suite + actual browser test |
| T13 Evidence transfer | PASS | Failed/wrong target, receipt/readback, duplicates; local originals retained | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC SINK ONLY; durability + acceptance |
| T14 Actual V3 chain | PASS | Collector→safety→coordinator→actual entrance/GET; connected review included | PASS | 3 GREEN / PS5.1 PASS | SYNTHETIC/REPLAY; operator, review, IG safety/e2e |
| T15 Registry | PASS | Exact IDs/meanings/statuses; skipped/missing assertions cannot become PASS | PASS | 3 GREEN / PS5.1 PASS | Registry invariants, not broker evidence |

The fixed specification is `tests/fixtures/bot_helper_acceptance_v1.json`.
`scripts/run_bot_helper_acceptance.py` runs the union in fresh subprocesses;
pass 2 uses a different session date and price scale with fixed independent
expectations. Its sanitized JSON/JUnit records actual cases, failure/skip counts,
import owner, source hashes and stability. An unassigned skipped test also prevents
overall PASS. A failed/absent browser, test or source pin is never cosmetically green.
CI artifact uploads run even on failure, with 30-day retention; actual upload
success remains the upload step's separate result.

## CI evidence and readback

| Workflow | Accepted run | Pass 1 / Pass 2 | Artifact ID | Upload/readback |
| --- | --- | --- | --- | --- |
| dax-bot-1x-ci | [#730](https://github.com/hennebergtoni-lgtm/dax-Day/actions/runs/34958170507) | 916 / 916 PASS | 10391974152 | PASS / exact ZIP digest + both JSON reports |
| research-lab-ci | [#1514](https://github.com/hennebergtoni-lgtm/dax-Day/actions/runs/34958170496) | 916 / 916 PASS | 10391617935 | PASS / exact ZIP digest + both JSON reports |
| windows-host-lane-ci | [#19](https://github.com/hennebergtoni-lgtm/dax-Day/actions/runs/34958170511) | 916 / 916 PASS | 10392486074 | PASS / exact ZIP digest + both JSON reports |

Archive SHA256 values, verified after actual download:

- 10391974152: `99360feb523ef191da89b3fd595e8a7aaa162dbf599c1710d5e5823c4e24b282`
- 10391617935: `6bf2a7071511e0d91332accc112cdc839ccded3fbe248ae8be1f366b103ea52c`
- 10392486074: `751447668a70726eb870ba8131a836c9958cb61209037995586205e13197f465`

All archives contain `pass1/acceptance.json`, `pass2/acceptance.json`, sanitized
JUnit and attempt records. The JSON reports bind the actual PR test-merge SHA,
original source/test hashes, stable before/after snapshots and required browser.
Both local and GitHub trees were compared, not inferred from branch names.
The CI output directory itself can make `worktree_dirty=true`; unchanged source
hashes and the execution tree remain explicit. There is no claim of a clean source
based on that flag alone. Artifact retention is 30 days, expiry 2026-10-15 around
10:30–10:31Z, checked separately from test success. CI upload/readback proves
GitHub CI evidence transport, not user-host collection or automatic host transfer.

Failure registry remains **53 GAP / 38 SYNTHETIC_ONLY / 9 WAITING_EXTERNAL**,
exactly F001–F100. No real-broker refs or legacy statuses were promoted. Selected
Detection/Reaction/Recovery assertions do not prove all Host/Broker facets.

## Defects found and fixed before user handoff

IDs below count distinct defects, not each failing parameter/test or rerun.
Repairs are implemented and both acceptance passes passed on all three CIs,
including actual browser and native Windows. No known internal V1 defect remains.
Test/harness defects are explicitly distinguished from runtime defects.

| ID | Discovery phase | Finding → repair / verification anchor |
| --- | --- | --- |
| D01 | Build | V3 producer rejected by V1 consumer → explicit V3 safety binding; real collector tests |
| D02 | Build | RAM-only raw matrix → durable per-slot receipts/seal; process-crash tests |
| D03 | Build | Arbitrary login context could leak → bounded allowlist; collector leakage injection |
| D04 | Dogfood | Wrong RunManifest field/config binding falsely blocked healthy inputs → canonical manifest/config fields; complete healthy sequence |
| D05 | Build | Offline console execution label contradicted NONE/false → DISABLED; HTTP/DOM regressions |
| D06 | Failure injection | Expired previous dependency could support PASS → dependency freshness; independent review |
| D07 | Failure injection | Current-cycle source reversal escaped → ordered-source validation; independent review |
| D08 | Failure injection | GOLD identity could cross-wire DE40 → explicit instrument binding; independent review |
| D09 | Failure injection | Missing last-transition evidence could be invented → retain UNKNOWN; operator tests |
| D10 | Failure injection | Healthy helper claim bypassed actual stale input → owner entrance recheck; two-guard mutation control |
| D11 | Failure injection | PTC policy could bind another subject → account/instrument/policy fingerprint checks; healthy and mismatched PTC tests |
| D12 | Failure injection | Broken M5 projection could hide raw eight rows → independent raw outcome projection; operator tests |
| D13 | Second pass | Test fixtures assumed first-pass prices/date → relative-price revisions and source-derived Berlin session identity; targeted and frozen full alternate-pass tests pass |
| D14 | Failure injection | VERIFIED/provenance assertions could cross trust scope → validation metadata and caller-owned parsed scope checks |
| D15 | Build | Global editable installation resolved another checkout → explicit PYTHONPATH and actual module-path pin; harness import check |
| D16 | Build | Connected V3 review ran but was omitted from T14 attribution → include review module in T14 mapping; frozen harness attributes connected cases |
| D17 | Failure injection | Console trusted payload-defined finite TTL → exact canonical `DEFAULT_MAX_AGE`; 601/3600/1e9-second injections preserve source bytes and all eight raw rows |
| D18 | Independent second review | V3 timestamp semantics/basis and raw snapshot could contradict normalized interval → canonical `ig_m5_interval` and metadata binding at runtime/console; connected mutation regressions |
| D19 | Native Windows CI | Recovery writer hashed LF text but wrote CRLF bytes → explicit UTF-8 byte publication, unchanged strict byte-hash verifier; newline injection and Windows replay |
| D20 | Native Windows CI | Test read metadata through another descriptor while Windows mandatory byte lock held → retain held assertion, inspect metadata after release; no runtime lock weakening |

Discovery counts: **6 build, 1 dogfood, 9 failure injection, 2 second-pass/review,
2 native Windows CI = 20**. D13/D15/D16/D20 are test/verification defects, not
claims of trading-engine defects. All **20 repairs are confirmed; 0 internal V1 defects remain** after the complete
repeat and native Windows acceptance. The first published runtime head
`ca5e500285736abb2f13d81e82b43b402f453a8d` had both Linux lanes green, including
two actual-browser passes; Windows run #18 found 11 failed assertions caused by
D19/D20. Its failure artifact was uploaded and read back. No failure was relabeled
PASS. The corrected whole union and all three lanes subsequently passed, as
recorded above. Bounded independent closure review confirmed D18/D19 at the exact
accepted tree; the active internal-remaining hunt has no open V1 finding.

Reuse rule: test owner-to-owner contracts and actual admission before polishing
projections; persist observations before derivation; bind source identity and
freshness independently; measure coverage and import ownership rather than assume it.

## Remaining gates and bounded host handoff

**FOLLOW-UP WORK DEBT: EXTERNAL_ONLY.** All internal V1 requirements above are
closed. Formal project acceptance and merge governance remain separate. This
technical closeout promotes no M01/2238/2239/2240 or historical host gate.

One new current-head Windows/IG observation remains
necessary. Use the existing wrapper, once, with a fresh namespace; no manual
endpoint series. The following is a **template**, not an executed command or a
verified installed-wrapper claim. The final response supplies the exact final PR SHA for `<FINAL_HEAD>`;
the wrapper must be supplied through the existing pinned deployment handoff:

```powershell
& 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck\scripts\run_ig_predemo_readiness_2238.ps1' -ExpectedHead '<FINAL_HEAD>' -RepoRoot 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck' -RuntimeRoot 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck' -Namespace '.runtime/bot_helper_v1_<FINAL_HEAD>_attempt_01' -CredentialsFile 'C:\Users\Mandy\ig_demo.env'
```

This reuses existing host paths and credential-file location without printing
credentials or changing policy. Verify installed wrapper/deployment provenance
before releasing the final command. Repeated completed 2233/2237 work is not
requested without a new evidence need. An inaccessible host blocks this lane only.

A compatible authorized automatic user-host→remote evidence channel has not been
proved. GitHub CI artifacts and the existing Neon operator path do not establish
that channel. Retain local evidence; if external transfer is required, gather the
single existing-channel configuration/access decision rather than create a new
uploader or ask the user to hunt/upload ZIP files.

| User-handoff cost | Current status |
| --- | --- |
| Manual host actions used for internal acceptance | 0; synthetic I/O/local processes |
| Manual file transfers used for internal acceptance | 0 |
| External user decisions used for internal acceptance | 0 |
| Additional host action prepared | 1 conditional existing-runner invocation, not yet released |
| Required manual external file transfers | None prescribed; automatic channel remains unproved |
| Additional external decision | Conditional channel configuration/access; exact necessity UNVERIFIED |
| Follow-up Work likely? | External host/channel evidence follow-through only; no internal repair-WORK outstanding |

## Deliberately not built

No runtime LLMs, agent chats, microservices, general plugin/event bus, broker
connection engine, second risk/state/evidence database or console: none is needed
for the bounded acceptance contracts. No new execution, risk limits, strategy,
Gold configuration or research/TCA/MFE suite: outside V1; Gold remains a documented
future market. No autonomous repair/retry/deployment service or universal uploader:
would introduce authority and state without an authorized V1 need. These are
separate deferred products, not names for unresolved V1 defects.

Credits were not metered here; no cost total or budget-consumption claim is made.
Feature expansion stopped at complete V1 acceptance. Runtime changes: 30 files,
4742 insertions / 48 deletions from the start head; most additions are fixed
acceptance specification, tests and evidence documentation. Published implementation
commits: `ca5e500285736abb2f13d81e82b43b402f453a8d` then
`6acb5399c1a9f23def20ada9660e09e023fdf33e`, both normal fast-forwards. The final
documentation commit only records this result. Direct CLI push had no login; the
authorized GitHub connection published byte-identical trees, verified before ref
updates. No force push, actual PR merge, main update or foreign checkout mutation.
Recovered mandate text SHA256: `12f789d8554bf54cd22d9395f326723bff353a1eb66f7ab1adb6047c944bb493`.
