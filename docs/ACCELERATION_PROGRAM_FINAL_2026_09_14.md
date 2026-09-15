# DAX Major Acceleration Program — 2026-09-14 closeout

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


## Step2237 Windows deployment correction

The first final-contract bootstrap reached START but failed
`DETACHED_CHECKOUT_FAILED` before Python/login/GET. Exact Git stderr was
suppressed, so the leaf cause remains UNKNOWN. The in-place checkout dependency
is retired. The corrected wrapper uses a unique temporary exact-head worktree,
keeps durable runtime/evidence in the existing caller-owned root, and cleans only
the verified-clean worktree it created. Existing checkout/evidence is never
switched, cleaned, reset or stashed. Step2233/2237 remain WAITING_EXTERNAL;
NONE/false, no order and hard LIVE prohibition are unchanged.


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


Repository truth is the authority. This report separates implemented local software, supplied host observations, actual broker evidence and future work. Bounded IG DEMO authorization is recorded; effective execution remains NONE/false. No broker order was submitted. LIVE remains unauthorized.

## A — Repository / drift

Repository hennebergtoni-lgtm/dax-Day; branch nextgen-bot-line-v1; PR109 open/unmerged; main/base e0784ebfc11bee28475fd9c3385be661af58a738. Expected and actual start head both2a99f96e06f7ce1f311c767dec43d236bb63eedd. Each write/ref update rechecked the actual PR head. Subsequent drift consists only of this run's linear explained commits. No force push, merge, reset or Acceptance refresh.

Last implementation head reviewed for this report: 7381ceaaab80d87d5e39348da2639978866916a7. The containing documentation commit is the final publication tree; its exact SHA/CI run IDs are supplied in the final handoff, avoiding a self-referential SHA inside its own commit. Windows has not yet proven that final runtime head. All historical source heads remain preserved.

## B — Commits

| Commit | Coherent tranche |
| --- | --- |
| 1a2a50912ce0b2f074ce7b66838ede5128ee0b2b | Preserve and export original IG RAW attempt03 evidence; record bounded DEMO authorization |
| 766fb0dc8bf87e8131b49bf74d403432aad62b5b | Pause Step2233 for source evidence and activate independent Research Factory reconciliation |
| 3867fcd486a4a1145c4352b60c2660436a237449 | Map all Research Factory hypotheses, failures and learnings to existing owners and conservative evidence |
| 576183c227a67530099a1a5277ad94c5f92ee8f8 | Publish complete source reconciliation and activate existing risk research owner expansion |
| 7aa2aba37b648d47747a0372b5c3970c1cce8aa4 | Extend existing research risk owners with fixed-cash tail stress and drawdown DNA |
| 25b84c9c32b08ed3c8bf93aec9d237bfefc43bbd | Record formal pause ledger and activate session/evidence hardening step2236 |
| 86b9719d38fc76c5248456620e3e11a5e66f6e4f | Harden single IG read-only session owner and extend full-spec identity/TCA diagnostics |
| 44262aeae01ae86c957253f0fff4257510b13c09 | Extend existing protection owner with independent native-grid DEMO PTC vetoes |
| ccf31359e821bfc0c5630e2bc25e6a6cba7f5936 | Prepare causal hysteresis research and validate one-command Windows export syntax |
| b026fe9e4f98f9475a5846c2dc79ec08fd27edfc | Enforce DEMO pin at transport boundary; refresh partial coverage and cache mandatory CI dependencies |
| 7381ceaaab80d87d5e39348da2639978866916a7 | Distinguish lower-capital worst outcomes from upper capital quantiles |

The report/masterstand/pointer closeout is one further documentation commit after the tested implementation head. Review actual final GitHub compare/checks for that exact final SHA.

## C — Step2233 DATA TRUTH

**WAITING_EXTERNAL / UNKNOWN.** User reports Attempt03 at exact start head succeeded: one login → A/B/C → one cleanup; RAW A/B/C, AB/BC and final SUMMARY SUCCESS; Candidate false; NONE/false. Six original JSON byte streams have not been supplied to Work. Successful acquisition is not proof of interval START, END_WITH_REVISIONS or stabilization.

Implemented one credential-free original-bundle runner: scripts/export_ig_raw_truth_2233.ps1 + existing Python exporter. It verifies exact published/runtime head, expected origin, clean tracked/untracked Python code and ancestry; deploys via detached checkout without merge/reset; validates all six canonical artifacts/summary/compare bindings; retains originals byte-for-byte in an exclusive ZIP with SHA256/size manifest and factual mutation review; checks source/code again; no login/broker call, no overwrite, deterministic fail-closed exit/cleanup.

Export review is intentionally OTHER_UNKNOWN unless actual source proves semantics. SnapshotTimeUTC, OHLC bid/ask/lastTraded, volume, A→B/B→C same-timestamp mutations, request/response timing, row positions/boundaries/source age/stability must be evaluated from original data. No raw values, ages, hashes or final mapping have been invented.

Audit: ig_market_data remains the normalized market-data owner; ig_rest_readonly is read/session transport; probe/raw diagnostic/shadow entry reuse those owners. Existing interval-end normalization is an unproven interim hypothesis and cannot feed Candidate because DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED quarantines the live path. Do not turn observed nominal closure/grace into finality.

If START is proved: event_time=snapshotTimeUTC, close_time=+5m. If END_WITH_REVISIONS: model revision semantics separately. If unknown: remain blocked. Any incompatible final contract requires schema+manifest+namespace bump, preserved legacy evidence and deterministic legacy blocker; no silent migration.

Strict STATE_CHANGED_OVERLAP, exact anchor, no gaps/duplicate/mutable persisted Candidate decision/operator current and no reset remain binding. The final provider contract fresh-start/resume real-host test is NOT VERIFIED. Existing60s interim grace is not proven stabilization;600s freshness stays separate. Current Candidate quarantine prevents pretending those tests closed.

## D — M01 real-host matrix

| M01 requirement | Status | Current evidence / limit |
| --- | --- | --- |
| Exact code head | WAITING_EXTERNAL | GitHub CI exact head locally verifiable; final Windows runtime must be exported. |
| Windows runtime identity | WAITING_EXTERNAL | Path/old runtime supplied; final machine/Python/import identity missing. |
| IG DEMO environment/account/server | WAITING_EXTERNAL | DEMO-only client and reported IG lane; reviewed current context original source missing. |
| EPIC/instrument/symbol mapping | WAITING_EXTERNAL | IX.D.DAX.IFMM.IP supplied; DE40/5m adapter reused; full actual instrument context required. |
| Market status/fresh quote | WAITING_EXTERNAL | Earlier TRADEABLE/FRESH supplied, not current final-head snapshot. |
| Finalized M5 | BLOCKED | Successful RAW acquisition is not timestamp/finality evidence without originals. |
| Broker/UTC/session clock | WAITING_EXTERNAL | Explicit UTC diagnostic guards; actual independent clock observations absent. |
| DST/session semantics | WAITING_EXTERNAL | Broker-neutral gate retained; no inferred MT5 server offset transferred to IG. |
| Full inventory/working orders/positions | WAITING_EXTERNAL | GET owners exist; earlier reported zero is not final negative-evidence flatness proof. |
| History scope | WAITING_EXTERNAL | Native IG broker history/confirmation conformance scope not observed. |
| Economics/precision/min size/margin | WAITING_EXTERNAL | PTC requires explicit point value/tick/increment/size; no provider values invented. |
| Stops/freeze/protection | WAITING_EXTERNAL | Existing risk/protection + native-grid/collar PTC prepared; actual IG rules/integration missing. |
| Feed freshness | WAITING_EXTERNAL | 600s unchanged, never treated as finality/stability proof. |
| Risk/loss/session policy | WAITING_EXTERNAL | Canonical owners retained; reviewed actual policy/source binding required. |
| Reconciliation | WAITING_EXTERNAL | Generic local conformance is not IG real broker truth. |
| Restart/resume | BLOCKED | Final contract missing; no mutable Candidate evidence or silent legacy migration. |

M01 is not completed. Earlier2231/2232/Attempt03 supplied host observations remain historical evidence with original-byte limitations. No MT5 terminal/MQL defaults or server-offset claims are imposed on IG. Broker-neutral inventory, economic, clock, protection, reconciliation and recovery requirements remain.

## E — Pre-DEMO readiness

| Gate | Requirement | Status | Evidence / limit |
| --- | --- | --- | --- |
| 1 | Exact final runtime head | WAITING_EXTERNAL | Final GitHub head must be proven on Windows; old Attempt03 head remains provenance. |
| 2 | IG DEMO environment | WAITING_EXTERNAL | DEMO URL hard-pinned and transport rechecked locally; final real session source required. |
| 3 | DEMO account identity | WAITING_EXTERNAL | Reviewed actual account identity/context pins absent. |
| 4 | Instrument identity | WAITING_EXTERNAL | Supplied EPIC IX.D.DAX.IFMM.IP; final market/account observation binding required. |
| 5 | Finalized market-data contract | BLOCKED | Six Attempt03 originals absent; no interval START/END/finality promotion. |
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

None of the local ALLOW_EVIDENCE diagnostics grants execution. Several gates need both native IG integration/review and external source evidence. They are not resolved by a green CI or a bundle alone. Promotion NONE→DEMO_ONLY may happen only after all27 are genuinely VERIFIED and transport scope is explicitly bounded. The current user has already authorized that conditional first order; no new blanket authorization is invented.

## F — First bounded DEMO order

**BLOCKED / NOT EXECUTED.** No order, fill, position lifecycle, cancel/modify or broker inventory mutation was performed. No second order can follow an unresolved first outcome. Future timeout/unknown means QUERY_REQUIRED, deterministic reject means no retry, partial means reconciliation and fresh price-change means fresh revalidation. Profit is not the diagnostic objective.

## G — M03 broker lifecycle truth / Post A

**Existing owners reused; real IG conformance WAITING_EXTERNAL.** Broker lifecycle, reconciliation, durable reservation/session/loss checkpoints and query-required retry prohibition retain ownership. F040 partial, F039 out-of-order, F024/25/43/44/45 incomplete/short-history/query truth, F030/31 disconnect/timeout, F036/37/52/53 foreign/startup inventory are conservatively synthetic/partial cases, not actual IG evidence.

Native IG dealReference/confirmation/affectedDeals is provider context, not an MT5 retcode translation or demonstrated exactly-once idempotency. Need provenance-bound account/environment/EPIC, request/ACK/reference/deal/order/position/history, native+cumulative quantity and protection observations. Partial/duplicate/out-of-order/delayed-history/restart-under-reservation/wrong context/quantity/grid cases remain on the register; no synthetic missing fill is promoted to broker truth.

## H — Expected vs Observed / Post B

**IMPLEMENTED** in the existing research conformance owner: full component-pin comparison across dataset/data contract, engine/strategy/code, risk/execution assumptions, cost, session/timezone, adapter/broker context and lifecycle. Dimensional DATA/CLOCK/SIGNAL/EXECUTION/COST/BROKER/LIFECYCLE mismatch and unknown are explicit. Missing identity is UNKNOWN, never MATCH. Complete source manifests still required; hashes alone are not conformance. Frozen replay conformance, RunManifest and trial registry stay canonical.

## I — TCA / Post C

**IMPLEMENTED** in existing failure_analysis diagnostics: native Decimal precision; reference price, arrival bid/ask/time, request/response, optional observed fill/time/native quantity, requested quantity, explicit cost, tick grid and optional cash-point conversion. Reference shortfall, arrival slippage, spread and explicit costs stay distinct. Client-observed round-trip is not broker-internal latency. Missing cost is unknown. Single fill below request is not terminal partial/cumulative quantity proof. Missing fill remains unresolved; opportunity movement not captured. Actual quote/request/fill source is external.

## J — Data / clock parity / Post D / M06

**IMPLEMENTED PARTIAL / WAITING_EXTERNAL.** Existing RAW A→B/B→C comparisons + full DATA/CLOCK/BROKER identity dimensions and strict UTC availability support diagnostic parity. Research-vs-broker OHLC/quote side/spread/calendar/DST/receive/venue/gap/duplicate/symbol/full bar contract need pinned paired sources. No aggregate magic score and no alternate timestamp owner. Final normalized IG contract still blocked; finalized M5 source parity not claimed.

## K — Risk science / Post E

**IMPLEMENTED** existing failure_analysis extension: additive net-R drawdown episodes, recovery boundary/trade duration, right-censoring, underwater trade counts, loss streaks and top1/5/10 winner removal/concentration sensitivity. Negative net profit does not receive a misleading winner/net concentration ratio. Existing historical_risk_envelope reuses validated detail preflight for MAE/MFE/duration/quantiles and segregated WF/variant scopes.

No pinned current CAND-001 detail/gross-cost ledger was available. Therefore no numerical MAE/MFE/P90/P95/P99, weekly account chains, long/short/regime/structure/setup result is invented. Trade-count durations are not elapsed time; net-R path is not account equity. Realized/unrealized/equity/cashflow must remain separated in future source import.

## L — Tail survival / Post F

**IMPLEMENTED** existing boost001 extension: explicit fixed cash/capital/floor/trade-horizon model; IID baseline, circular block, contiguous session block, contiguous cluster block and homogeneous regime-run sampling. Source/spec/seed/mode/labels/cost arrays hash-bound. Same sampled indices across normal/1.5×/2× explicit cost stress. Terminal unit censoring reported; REGIME_RUN does not claim preserved transition probabilities. Bounded work budget and finite/type guards.

Cash risk is capped at fixed baseline and floor headroom; adverse outcomes below−1R are not clamped into a fictitious floor guarantee. Account equity/margin/cashflows/intrabar/unseen shocks are not modeled. Lower capital is the worst capital outcome; upper capital quantiles are explicitly not loss-tail probabilities. Empirical floor-hit rate is conditional research, never future survival guarantee. Actual results need aligned gross-R and explicit cost-R ledger; source pin is caller-supplied, not independent data validation.

## M — Strategy robustness / Post G / M09–M10

**RESEARCH / IMPLEMENTED FEATURE PREPARATION.** Strict REGIME→STRUCTURE→ENTRY ordering is recorded. Existing ATR/structure/promotion/OOS/trial/multiple-testing owners reused. causal_hysteresis_regime adds explicit enter>exit thresholds, consecutive confirmations, dead band, measured flips/delay and caller-pinned closed feature available_at strictly before decision. Equal/future values cannot change causal prefix; insufficient history remains unknown. This is not another runtime regime/indicator engine.

H04 mechanism locally tested; economic hypothesis stays PREPARE. ATR compression/expansion/relative volatility may reuse this feature only with valid causal input; macro/VWAP/M1 publication/volume validity dependencies remain. Structure OR/breakout/failure/retest/previous-day/gap/liquidity/CPR/Fibonacci and later entry/stop/trailing hypotheses are not deployed into CAND-001. Exit/intrabar ambiguity/outcome leakage guards and parameter-neighborhood/plateau/top-trade sensitivity require pinned OOS trial families. Existing DSR/PBO/SPA/preflight/immutable registry reused; exploratory is not confirmatory.

## N — Failure Factory F001–F100 / Post I

**100/100 mapped**, preserving original source detection/reaction/priorities and actual owner paths. Current machine-readable status:53 GAP,38 SYNTHETIC_ONLY,9 WAITING_EXTERNAL;42 scenarios have narrowly scoped test references. These are not complete conformance percentages and zero cases are REAL_DEMO_VERIFIED.

Added automated P0/P1 facets: read401/429/503/unknown exception/None/malformed/array; one-login/no relogin/cleanup; credential nesting; literal safety booleans/NONE-false persisted contradictions; source/identity/clock errors; native price/quantity grids; stale/collar/notional/attempt/duplicate/inventory/account/instrument/session/reservation/emergency vetoes; causal-prefix/hysteresis; malformed risk values/overflow/censoring. Existing unknown reservation/restart/duplicate/out-of-order/short-history/telemetry owner tests retained.

F033 duplicate-login and F050 native grid now narrowly SYNTHETIC_ONLY. F001 source-age, F020 real reconnect, F064 account exposure and F090 native reconnect conformance gain partial tests while their broader GAP stays open. F021 private-report outage, F026 delayed history, F038 duplicate cumulative reports, F047 stop gap, F066 ACK durability, F070 actual restore, F089 state-preserving rollback and F096 ACK/slot release remain explicit gaps unless their full owner/source proof is established. No real broker fault injection performed.

## O — H01–H40

**40/40 captured** with mechanism/current status/owner/evidence/cost/information value/leakage/overfit/dependencies/decision.37 PREPARE,3 LATER (volume/news/M1 data dependencies); no claimed tested edge. H04 has implemented causal-hysteresis preparation. Dataset + immutable trial family + aligned costs + OOS/WF required. Full rows: ACCELERATION_RESEARCH_FACTORY_RECONCILIATION.md and acceleration_program_v1.json. No indicator collection or automatic Candidate mutation.

## P — 24 architecture learnings

**24/24 mapped:**9 ALREADY_HAVE,14 EXTEND,1 REJECT with real owner. Separate connection/feed/inventory truth; negative evidence not flatness; reconnect needs recon; PTC independent from risk; emergency authority independent; TCA before request; tick size not digits; complete component identity; rollback preserves broker/state truth; dimensional health. This run extends these facets through the existing client, protection and research owners. Duplicate architecture without measurable information gain is rejected. No second engine/store/risk/recon/lifecycle/readiness/health stack.

## Q — Public donor rescan

**RESEARCH / REUSE-ADAPT-REJECT reviewed** against primary sources for NautilusTrader, Freqtrade, QuantConnect LEAN, vectorbt, Backtrader, Hummingbot, Passivbot and official IG session/markets/positions/confirmation docs. Findings map to actual owners in ACCELERATION_PUBLIC_DONOR_RESCAN_2026_09_14.md. Reuse local tracking-before-request, bounded reconciliation, causal/lookahead/warmup checks, memory-efficient selected research and explicit dimensional metrics; adapt semantics only after source proof. Reject fabricated fills as broker evidence, blind venue retry, grid/rescue/revenge sizing and performance marketing. No donor dependency/second framework installed.

## R — Research efficiency / Post J

**PREPARED / RESEARCH.** Cheap reject → coarse selected screening → deep selected test → OOS/WF → forward, with immutable hypotheses/trial families/dataset/engine/cost/code/parameters/result provenance. Existing owner paths and dependency fences are explicit for all40; no brute force or benchmark profitability result. Full family-aware trial accounting/DSR/PBO/SPA and causal feature availability remain required. Numeric screening cannot run without pinned source data.

## S — Mobile / host automation / soak

**IMPLEMENTED:** one START→WAIT→SUMMARY credential-free export runner; exact head/drift/namespace/code/size/schema/hash/no-overwrite/cleanup protections. Existing mobile operator and actual JS/HTTP synthetic tests retained, no second backend truth. Session health never turns connection into feed/inventory truth. Actual iPhone/Windows final-runtime and order-panel evidence remain external.

Multi-hour/day finalized Candidate SHADOW soak remains **WAITING_EXTERNAL / PLANNED** until provider contract and fresh-start/resume are verified. Reuse existing Candidate supervisor/soak/runtime telemetry; no second daemon or fabricated decisions. Continuous DEMO remains M07-gated, not authorized by one first-order grant.

## T — Technical debt / Post H operations

**AUDITED / EXTEND.** Unproven interval-end/grace interim contracts are explicitly quarantined; no destructive deletion/migration before raw proof. Existing session owner consolidated with lifetime login latch and cleanup, existing normalized data owner retained, docs gain current authority/historical labels. MT5-specific reservation/lookup/terminal/MQL paths remain provider-specific history, not IG conformance.

Full immutable release fingerprint/startup barrier/recon, semantic watchdog/alerts dedup/debounce/ACK, separate kill authority, state-preserving rollback, restore and DR remain incomplete native IG operational evidence. Local full-spec diagnostics do not replace release manifests or grant deploy readiness. Rollback must never reset consumed reservation/session/state/broker inventory.

## U — Tests / CI acceleration

Mandatory FAST: candidate broker-neutral core; focused: RAW/export/session/risk/identity/TCA/PTC/regime; full: entire pytest suite; governance and all eight safety gates remain required. Broker-free local suites do not claim Windows/broker truth. PowerShell parser is now mandatory and green on the prior implementation head; it is syntax evidence only. Existing actual JS/DOM/HTTP tests run in full suite; JS source unchanged.

Both required workflows gain documented pip dependency caching keyed by pyproject.toml; no test/coverage/safety removal. Last completed prior code-tranche suite on ccf31359:3075 passed, Ruff/syntax/focused and eight gates green. Later transport-pin/coverage-cache/capital-direction additions and final documentation require exact final-head CI; definitive counts/check IDs are delivered in the final handoff. No local shell/Windows execution was available in Work; GitHub Actions is the actual local-code validation source.

## V — Exact-head CI

Required workflows: dax-bot-1x-ci and research-lab-ci. CI is checked on the exact final containing commit before final response. Do not use green from an ancestor to label a new head verified. The five main-only Neon/restore/import steps are intentionally skipped on this PR; historical DB evidence is not fresh connected validation. No merge/Acceptance refresh.

## W — Safety

Current user authorization: one small bounded diagnostic IG DEMO evidence order after all27 verified, superseding historical DEMO NOT AUTHORIZED only in that scope. Effective NONE/false and no bounded transport activated. LIVE/hard endpoint/dealing-route controls tested without a LIVE call. No cash transfer/live switch, blind retry/resubmit, automatic slot release/risk expansion/Martingale/grid rescue, reset-as-recovery or synthetic broker truth.

Comparison since expected start changed no src/daxlab/strategies/cand001, src/daxlab/reference or research/V112_REFERENCE_V1 file. Strategy parameters/cost assumptions unchanged. No main/base change, force push, merge, Acceptance/ruleset edit or broker side effect. Raw/probe/Candidate finalization schemas remain preserved pending evidence-based final bump.

## X — Remaining external/internal gates

1. Six hash-bound Attempt03 originals via one runner: decisive raw contract review.
2. Final-head Windows runtime/import/context/clock/feed/inventory/working-order/economics/size/grid/stop/margin source.
3. Native IG bounded request/reservation/confirmation/query/reconciliation/protection/restart integration review and genuine broker evidence.
4. Current pinned Candidate detail/gross/cost/session/regime/WF/trial-family source for risk/tail/robustness/TCA/parity.
5. Real operator/mobile/soak/reconnect/recovery/restore/DR/kill/watchdog evidence before continuous DEMO.

Missing evidence does not invalidate delivered local implementation, but blocks stronger broker/demo/research-result claims. Further duplicate scaffolding cannot replace these sources.

## Y — Next three major milestones

| Milestone | Scope | Status | Next evidence |
| --- | --- | --- | --- |
| M01 | Real-host evidence | WAITING_EXTERNAL | Original RAW source + full final-head IG host/context/economics/clock/inventory. |
| M02 | First bounded DEMO | BLOCKED | 27 VERIFIED gates required; one diagnostic order authorized conditionally but not executed. |
| M03 | Broker lifecycle truth | IN_PROGRESS | Generic conformance/failure mapping reused; real IG native lifecycle still external. |
| M04 | Expected vs Observed | IN_PROGRESS | Complete component-pin dimensional diagnostic implemented; real paired artifacts missing. |
| M05 | TCA / latency / cost | IN_PROGRESS | Pre-request/native-decimal attribution implemented; actual quote/request/fill source missing. |
| M06 | Data / clock parity | IN_PROGRESS | RAW comparisons + dimensional identity + causal UTC availability prepared; final contract/dataset pair missing. |
| M07 | Continuous-DEMO safety | BLOCKED | Independent PTC prepared; real startup recon/kill/watchdog/reconnect/restore/DR evidence required. |
| M08 | Tail / risk survival | IN_PROGRESS | Five seeded resampling modes/three cost stresses + cash/floor/horizon implemented; pinned ledger absent. |
| M09 | Strategy robustness | IN_PROGRESS | 40 hypotheses staged; causal hysteresis feature tested, no economic/OOS claim or CAND mutation. |
| M10 | Parameter plateau / multiple testing | IN_PROGRESS | Existing DSR/PBO/SPA/trial registry reused; aligned trial-family ledger missing. |
| M11 | New filters / research efficiency | IN_PROGRESS | Cheap-reject/staged screening plan and complete source/owner register; numerical screening not executed. |
| M12 | Capital scaling / PRE-LIVE | PLANNED | No capital expansion/PRE-LIVE promotion; LIVE remains unauthorized. |

Next major sequence: (1) M01 DATA + host/economics/context closeout; (2) M02 one bounded DEMO and M03 full native lifecycle evaluation, fail-closed on contradiction; (3) M04–M10 paired forward evidence/research plus M07 continuous-DEMO safety. No PRE-LIVE jump.

## Z — Exactly one Windows start

Final handoff provides exactly one immutable-final-head PowerShell bootstrap command for export_ig_raw_truth_2233.ps1. START→WAIT→SUMMARY; no credential input/new login/manual capture sequence. Result .runtime/ig_raw_truth_2233_attempt_03_originals.zip contains all six originals plus hash manifest/review. Provide that ZIP to continue raw review. Do not rerun acquisition03 or overwrite old evidence. Original host path defaults to C:\Users\Mandy\Documents\dax-Day-ig-hostcheck; broker credentials remain external and unused by this export.
