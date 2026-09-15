# M01 and bounded IG DEMO readiness — current acceleration matrix

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


Step2237 V2 review promotes the original Attempt03 structure to the canonical operational INTERVAL_START contract. The first Windows bootstrap then failed before Python with DETACHED_CHECKOUT_FAILED; isolated exact-head worktree deployment is now implemented, while the corrected host result remains WAITING_EXTERNAL. The historical OTHER_UNKNOWN review remains preserved. Current effective execution NONE/false. One small first bounded diagnostic IG DEMO order is conditionally user-authorized; LIVE unauthorized. Matrix statuses describe actual current evidence, with local software scope explicit. Old MT5 terminal/retcode/session/MQL owner details cannot substitute for native IG truth. Full details and limits: ACCELERATION_PROGRAM_FINAL_2026_09_14.md.

## M01

| M01 requirement | Status | Current evidence / limit |
| --- | --- | --- |
| Exact code head | WAITING_EXTERNAL | GitHub CI exact head locally verifiable; final Windows runtime must be exported. |
| Windows runtime identity | WAITING_EXTERNAL | Path/old runtime supplied; final machine/Python/import identity missing. |
| IG DEMO environment/account/server | WAITING_EXTERNAL | DEMO-only client and reported IG lane; reviewed current context original source missing. |
| EPIC/instrument/symbol mapping | WAITING_EXTERNAL | IX.D.DAX.IFMM.IP supplied; DE40/5m adapter reused; full actual instrument context required. |
| Market status/fresh quote | WAITING_EXTERNAL | Earlier TRADEABLE/FRESH supplied, not current final-head snapshot. |
| Finalized M5 | IMPLEMENTED | Original bundle received; V2 structural review promotes INTERVAL_START. Canonical event=T/close=T+5, active tail excluded,60s workaround retired. Final-head Windows cycles remain external. |
| Broker/UTC/session clock | WAITING_EXTERNAL | Explicit UTC diagnostic guards; actual independent clock observations absent. |
| DST/session semantics | WAITING_EXTERNAL | Broker-neutral gate retained; no inferred MT5 server offset transferred to IG. |
| Full inventory/working orders/positions | WAITING_EXTERNAL | GET owners exist; earlier reported zero is not final negative-evidence flatness proof. |
| History scope | WAITING_EXTERNAL | Native IG broker history/confirmation conformance scope not observed. |
| Economics/precision/min size/margin | WAITING_EXTERNAL | PTC requires explicit point value/tick/increment/size; no provider values invented. |
| Stops/freeze/protection | WAITING_EXTERNAL | Existing risk/protection + native-grid/collar PTC prepared; actual IG rules/integration missing. |
| Feed freshness | WAITING_EXTERNAL | 600s unchanged, never treated as finality/stability proof. |
| Risk/loss/session policy | WAITING_EXTERNAL | Canonical owners retained; reviewed actual policy/source binding required. |
| Reconciliation | WAITING_EXTERNAL | Generic local conformance is not IG real broker truth. |
| Restart/resume | IMPLEMENTED | V3 state/manifest/new namespace, strict overlap and single fresh/resume/Operator runner implemented; real Windows result WAITING_EXTERNAL. |

##27 Pre-DEMO gates

| Gate | Requirement | Status | Evidence / limit |
| --- | --- | --- | --- |
| 1 | Exact final runtime head | WAITING_EXTERNAL | Final GitHub head must be proven on Windows; old Attempt03 head remains provenance. |
| 2 | IG DEMO environment | WAITING_EXTERNAL | DEMO URL hard-pinned and transport rechecked locally; final real session source required. |
| 3 | DEMO account identity | WAITING_EXTERNAL | Reviewed actual account identity/context pins absent. |
| 4 | Instrument identity | WAITING_EXTERNAL | Supplied EPIC IX.D.DAX.IFMM.IP; final market/account observation binding required. |
| 5 | Finalized market-data contract | IMPLEMENTED | Original bundle received; canonical INTERVAL_START V2 plus true close/600s freshness separation implemented and tested. Real final-head fresh/resume remains external. |
| 6 | Feed freshness | WAITING_EXTERNAL | 600s separate from finality; final venue source age not proven. |
| 7 | Clock/session | WAITING_EXTERNAL | UTC availability tests implemented; actual host/broker drift/DST/session evidence absent. |
| 8 | Understood inventory | WAITING_EXTERNAL | Earlier empty inventory supplied; not current final-head flatness proof. |
| 9 | Working-order truth | WAITING_EXTERNAL | Final full source query/context/history required. |
| 10 | Economics | WAITING_EXTERNAL | Broker-native point value/currency/margin evidence required. |
| 11 | Tick size | WAITING_EXTERNAL | Native grid PTC tested; real IG tick size not manufactured from digits/scaling. |
| 12 | Quantity increment | WAITING_EXTERNAL | Explicit native increment required; policy diagnostic has no inferred default. |
| 13 | Min/max size | WAITING_EXTERNAL | Actual IG bounds/policy scope required. |
| 14 | Stop/target constraints | WAITING_EXTERNAL | Provider geometry/guaranteed-stop/freeze rules require actual market evidence. |
| 15 | Fixed-Cash Risk | WAITING_EXTERNAL | Canonical risk owner reused; reviewed broker-aware policy/calculation still absent. |
| 16 | Loss/exposure admission | WAITING_EXTERNAL | Existing owner plus independent PTC; current account exposure/equity source required. |
| 17 | Session guard | WAITING_EXTERNAL | Canonical guard/checkpoint implemented; real broker/UTC/session observation required. |
| 18 | One-trade-per-session guard | WAITING_EXTERNAL | Existing durable guard reused; IG real restart/session evidence required. |
| 19 | Attempt reservation | BLOCKED | Existing durable reservation owner; IG context/native ID adaptation not verified. Native IG integration/review must be completed; external evidence alone does not auto-enable transport. |
| 20 | Idempotency | BLOCKED | No blind resubmit; IG dealReference is not proven exactly-once broker submission. Native IG integration/review must be completed; external evidence alone does not auto-enable transport. |
| 21 | Reconciliation | BLOCKED | Existing generic owner tested synthetically; native IG positions/orders/history conformance absent. Native IG integration/review must be completed; external evidence alone does not auto-enable transport. |
| 22 | Protection | BLOCKED | Independent PTC implemented and tested; request-time bounded transport integration not verified. Native IG integration/review must be completed; external evidence alone does not auto-enable transport. |
| 23 | Telemetry | IMPLEMENTED | Existing operator/telemetry owner retained; fresh final-head real lifecycle evidence required. |
| 24 | Operator visibility | IMPLEMENTED | Credential-free mobile console reused; actual mobile/IG order truth remains external. |
| 25 | Restart/recovery | BLOCKED | Quarantine/strict overlap intact; final contract fresh-start/resume + unresolved IG recovery unproven. Native IG integration/review must be completed; external evidence alone does not auto-enable transport. |
| 26 | Explicit DEMO_ONLY capability | BLOCKED | User target authorized; effective NONE/false. No scoped bounded transport activated. |
| 27 | Hard LIVE block | VERIFIED | LOCAL SOFTWARE SCOPE: constructor and per-request endpoint/dealing veto tests; no LIVE call made. |

Current27-gate tally:1 VERIFIED,3 IMPLEMENTED,17 WAITING_EXTERNAL and6 BLOCKED. No all-VERIFIED readiness, no DEMO_ONLY promotion and no order. Existing PTC/risk/reservation/reconciliation/lifecycle owners remain canonical; native IG transport/context/evidence gaps still need completion. The received source bundle closes the contract-decision dependency, not the broker-readiness set.

## Roadmap

| Milestone | Scope | Status | Next evidence |
| --- | --- | --- | --- |
| M01 | Real-host evidence | WAITING_EXTERNAL | Market-data contract implemented; one final-head fresh/resume/Operator run plus IG host/context/economics/clock/inventory evidence remains. |
| M02 | First bounded DEMO | BLOCKED | 27 VERIFIED gates required; one diagnostic order authorized conditionally but not executed. |
| M03 | Broker lifecycle truth | IN_PROGRESS | Generic conformance/failure mapping reused; real IG native lifecycle still external. |
| M04 | Expected vs Observed | IN_PROGRESS | Complete component-pin dimensional diagnostic implemented; real paired artifacts missing. |
| M05 | TCA / latency / cost | IN_PROGRESS | Pre-request/native-decimal attribution implemented; actual quote/request/fill source missing. |
| M06 | Data / clock parity | IN_PROGRESS | Canonical raw/event/close mapping is fixed; paired research/broker dataset and independent clock/session evidence remain. |
| M07 | Continuous-DEMO safety | BLOCKED | Independent PTC prepared; real startup recon/kill/watchdog/reconnect/restore/DR evidence required. |
| M08 | Tail / risk survival | IN_PROGRESS | Five seeded resampling modes/three cost stresses + cash/floor/horizon implemented; pinned ledger absent. |
| M09 | Strategy robustness | IN_PROGRESS | 40 hypotheses staged; causal hysteresis feature tested, no economic/OOS claim or CAND mutation. |
| M10 | Parameter plateau / multiple testing | IN_PROGRESS | Existing DSR/PBO/SPA/trial registry reused; aligned trial-family ledger missing. |
| M11 | New filters / research efficiency | IN_PROGRESS | Cheap-reject/staged screening plan and complete source/owner register; numerical screening not executed. |
| M12 | Capital scaling / PRE-LIVE | PLANNED | No capital expansion/PRE-LIVE promotion; LIVE remains unauthorized. |
