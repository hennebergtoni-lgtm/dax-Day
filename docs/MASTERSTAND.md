# DAX-BOT MASTERSTAND — NEXT-CHAT HANDOVER

Status: **BINDING HANDOVER / REPOSITORY TRUTH FIRST**  
Updated: **2026-09-12**  
Repository: `hennebergtoni-lgtm/dax-Day`  
Working branch: `nextgen-bot-line-v1`  
Pull request: `#109` -> `main`

This file is the canonical next-chat handover. Exact repository code, tests, hashes, fresh CI, runtime telemetry and `docs/CURRENT_WORK_STEP.md` override prose if anything disagrees.

## 1. Mandatory resume protocol

On a new chat, context loss, reconnect, compaction, or `Weiter mit dem DAXBot`:

1. read `docs/SESSION_EXECUTION_REFRESHER.md`;
2. pin repository, branch, PR and **fresh exact branch HEAD**;
3. read `docs/CURRENT_WORK_STEP.md`;
4. read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`;
5. read this Masterstand;
6. read `docs/PROJECT_KNOWLEDGE_INDEX.md` and only the topic-specific owners needed for the active step;
7. continue the active step automatically when the Step-Close-Gate permits it.

Repository truth overrides chat memory. Tool/interface activity does not replace the required normal-text Zwischenstand.

Binding visible cadence:

`Step N -> short activity -> visible normal-text Zwischenstand -> ✅ / ⚠️ / ❌ -> actual next tool/action`.

A Zwischenstand is visibility, not a stop. Do not end a turn merely because a sub-check succeeded or CI is still running when safe executable work remains. A final answer ends the active tool turn; never claim invisible background continuation afterward.

Official step numbers are whole integers only. Visible numbering is monotonic. Interrupted older lanes resume only under a new later integer with provenance preserved.

Next mandatory Masterstand checkpoint: **2250**.  
Next mandatory full architecture/LEAN audit: **2500**.

## 2. Repository / branch / PR / CI truth at this handover

- Base branch: `main`.
- Working branch: `nextgen-bot-line-v1`.
- PR #109 is **open, unmerged, mergeable, not draft**.
- PR base SHA: `e0784ebfc11bee28475fd9c3385be661af58a738`.
- **Fresh branch HEAD immediately before this final Masterstand commit:** `cbcef2bb820a15c4aa454faaef4ffe4bbae21186`.
- GitHub PR/check metadata now also reports `cbcef2bb…` as the PR head.
- Exact checks on `cbcef2bb…`:
  - `candidate-core` -> **SUCCESS**;
  - broad `test` -> **SUCCESS**.
- This Masterstand update itself creates a newer documentation commit. The next chat must still re-pin the fresh branch HEAD rather than assuming any SHA written here is self-referential current truth.

No merge into `main` is authorized by this handover.

## 3. Safety / authorization — BINDING

- SHADOW: **AUTHORIZED only within the existing no-order contract**.
- PAPER/demo broker execution: **NOT AUTHORIZED**.
- LIVE: **NOT AUTHORIZED**.
- `execution_capability=NONE` where currently required.
- `order_execution_enabled=false` where currently required.
- No broker order-submission path is authorized.
- No research/backtest/CI result may silently grant PAPER/LIVE authority.
- Explicit later user authorization remains mandatory before PAPER or LIVE.

## 4. Scientific legacy anchor — REF-V11.2 — VERIFIED / IMMUTABLE

`REF-V11.2` is a frozen scientific comparison/reference, **not** the NextGen architecture and **not** CAND-001 performance evidence.

Canonical reference source: `research/V112_REFERENCE_V1/reference_result.json`.  
Audited dataset manifest: `data/manifests/dax_m5_2014_2019_audited.json`.

Verified historical surface:

- 2014–2019;
- 1,673 valid Europe/Berlin session days;
- 481,824 raw M5 rows;
- 172,319 Berlin-session M5 bars;
- 103 bars/session;
- session 09:00–17:30 Europe/Berlin;
- 0 known invalid OHLC rows;
- session OHLC SHA256 `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`;
- 144 variants;
- 81 WF windows; Train 45d / OOS 20d / Step 20d;
- 856 OOS trades;
- normal OOS total `-31.309210619787684 R`;
- 37 positive / 44 negative / 0 flat WFs;
- median WF PF `0.905769310256018`;
- stress 1.5x `-40.921695023387514 R`;
- stress 2x `-48.424611963007294 R`.

Never relabel these metrics as CAND-001 or NextGen performance.

## 5. DAX-BOT 1.0-alpha / CAND-001 legacy-product line

Repository-side DAX-BOT 1.0-alpha acceptance remains a correctness/control milestone, not a profitability proof. The frozen `CAND-001` product candidate remains available as reference/compatibility evidence while NextGen is built beside it.

Frozen CAND-001 semantics:

- DE40 M5;
- Europe/Berlin 09:00–17:30 session;
- OR15;
- closed-M5 confirmed breakout, not wick/touch;
- BOTH directions;
- stop = OR opposite;
- target = 1.5R;
- maximum one admitted trade/session.

Existing legacy-product/runtime work already includes deterministic closed-bar handling, candidate state, trade-plan/admission/decision pipeline, restart/idempotency controls, virtual lifecycle/costed outcome, operator snapshot/telemetry, SHADOW host integration, broker-neutral lifecycle/reconciliation/protection/checkpoint/telemetry evidence owners, and fail-closed PAPER readiness gates.

Do not silently migrate CAND-001 rules into NextGen core contracts. CAND-001 is now connected only through an explicit Strategy Plugin compatibility adapter.

## 6. CAND-001 historical/OOS evidence line — preserved but no longer architecture-driving

Steps 2102–2113 implemented a frozen CAND-001-specific historical/OOS evidence chain: deterministic replay, 45/20/20 WF/OOS schedule, normal/1.5x/2x costs, aggregation, immutable three-file evidence export, strict readers, cost-stress integrity, temporal stability diagnostics, standalone `diagnostics.json`, strict diagnostic verification, and post-processing CLI.

This line remains valid evidence infrastructure, but it no longer dictates the NextGen data or strategy architecture.

Historical Drive source remains known:

- root: `DAX_V14_RECOVERED_CACHE_V13`;
- `m5_daily` folder ID: `1p5-s3ccsBbohbephB7UIhUE_OL1M4b-y`.

Step 2137 proved one real private daily CSV can materialize locally and matches the old canonical loader shape. Bulk/folder materialization through the connector was not available. The user explicitly stopped this lane from becoming the NextGen chassis.

Therefore:

- historical-data existence/location: VERIFIED;
- old CAND-001 evidence code: IMPLEMENTED/CI-VERIFIED;
- first actual frozen full CAND-001 OOS result artifact: still not produced;
- CAND-001 profitability/robustness: still UNVERIFIED;
- old 1,673-file/CSV contract: **historical compatibility/evidence only**, not NextGen storage design.

## 7. Workflow/governance hardening completed during this chat

### Step 2132 — workflow-integrity gate — COMPLETED

Canonical owner: `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`.

Binding rules include:

- Step-Close-Gate;
- pointer-before-next-step;
- monotonic interrupted-lane carry-forward;
- visible text Zwischenstand separate from tool activity;
- no long tool-call chains without text visibility;
- a Zwischenstand is not a stop;
- no final/turn-ending response while executable safe work remains;
- no claim of background work after a turn has ended;
- exact-head CI/evidence discipline;
- explicit user intervention as a valid sequence interruption.

### Step 2133 — Recovery canonicalization — COMPLETED / RETAIN_WITH_REASON

`recovery_bundle.py` remains canonical. Legacy `recovery.py` is frozen forensic compatibility only, with no new active consumers.

### Step 2135 — CI ownership — COMPLETED

- `research-lab-ci` / `test` = broad integration/regression owner;
- `dax-bot-1x-ci` / `candidate-core` = focused candidate/broker-safety owner;
- `reference-payload-export` = frozen reference integrity/export owner.

No specialty gate replaces the broad integration regression.

### Step 2136 — stable-branch governance audit — COMPLETED AUDIT / ENFORCEMENT WAITING_EXTERNAL

Current observable GitHub state showed `main` unprotected and no repository ruleset. Minimal target protection is documented, but the current integration cannot apply the GitHub-admin setting. Do not claim `main` is protected until fresh admin evidence proves it.

## 8. Architecture intervention — Ferrari, not Golf — BINDING

The user explicitly corrected the project direction: do not treat historical V11.2/CSV/Colab/Drive constraints as the chassis for the new bot merely because they are already available.

New binding rule:

**Legacy is reference, regression evidence and compatibility input — not the NextGen architecture constraint.**

### Step 2138 — Greenfield / First-Principles reset — COMPLETED

Canonical architecture: `docs/NEXTGEN_GREENFIELD_ARCHITECTURE_V1.md`.

The contract defines:

- two speeds, shared semantics: fast Research Layer + deterministic Product Layer;
- event/domain-first product core;
- data, strategy, risk, execution, state/recovery and adapters separated by boundaries;
- broker/venue adapters at the edge;
- MT5/legacy/V11.2/CAND-001 isolated behind compatibility boundaries;
- modern columnar data-plane direction;
- research/promotion separation;
- KEEP / ADAPT / ISOLATE-LEGACY / REPLACE / RETIRE classification;
- strangler migration instead of Big-Bang rewrite.

Public/open-source architecture patterns were checked against LEAN, NautilusTrader, Freqtrade and vectorbt. Reuse patterns, not copied strategies/framework bulk.

Architecture commit `e4acdd2898c4275379b28348555a22e91e337106` passed `dax-bot-1x-ci` #333 and `research-lab-ci` #1117.

## 9. NextGen foundation — completed steps 2139–2143

### Step 2139 — canonical Domain + Ports — COMPLETED

Final head: `b0fe61a09ba70fbed51afce283f7e486288e9c44`.

Added:

- broker-independent opaque `InstrumentId`;
- canonical UTC market/Candle contracts;
- deterministic broker-neutral `ExecutionIntent` identity;
- Protocol-only external ports;
- negative architecture tests forbidding MT5/legacy-dataset/CAND-001/V11.2 coupling.

CI: `dax-bot-1x-ci` #339 GREEN; `research-lab-ci` #1123 GREEN.

### Step 2140 — Canonical Historical Data Catalog V1 — COMPLETED

Final head: `ccdc14ab681bfb7589bbdd04e14a893f497f8761`.

New Greenfield data path:

- Parquet V1 physical format;
- PyArrow confined to optional `data` dependency surface;
- deterministic content-based Dataset fingerprint independent of Parquet encoder bytes;
- separate physical `parquet_sha256` integrity;
- immutable fingerprint-addressed data + manifest;
- canonical UTC/instrument/data-quality roundtrip;
- fail-closed mixed-instrument/timeframe, open-candle, duplicate, out-of-order and tamper checks;
- no silent sort/fix-up;
- legacy 1,673-file CSV layout not imported or modified.

CI: `research-lab-ci` #1130 GREEN; `dax-bot-1x-ci` #346 GREEN.

### Step 2141 — Strategy Plugin V1 — COMPLETED

Final head: `2b345016b7be03c47462527c776d53a9df6bd3ee`.

Added:

- `src/daxlab/domain/strategy.py`;
- `src/daxlab/strategies/contracts.py`;
- canonical package exports;
- `tests/test_nextgen_strategy_plugin_contract.py`.

Contract:

- strategy output stops before risk sizing and execution;
- `NO_TRADE` or broker-neutral `TRADE_PLAN` only;
- LONG/SHORT entry/stop/target directional invariants;
- deterministic strategy-decision identity;
- `StrategyPlugin.initial_state()` + `on_candle(state, candle) -> StrategyTransition`;
- no quantity/account/broker/order authority;
- no MT5/runtime/legacy/CAND-001 dependency.

CI: `dax-bot-1x-ci` #352 GREEN; `research-lab-ci` #1136 GREEN.

### Step 2142 — CAND-001 Strategy Plugin compatibility adapter — COMPLETED

Final head: `6f8db8883df342d4d523e06c041ab1ce0cc5e9fb`.

Added:

- `src/daxlab/strategies/cand001/adapter.py`;
- package exports;
- `tests/test_nextgen_cand001_strategy_adapter.py`;
- focused Candidate-CI coverage for the adapter.

Purpose:

- preserve the existing CAND-001 pipeline as the behavior owner;
- translate its behavior through the new generic Strategy Plugin boundary;
- avoid rewriting CAND-001 into the NextGen core;
- add no broker/order/execution capability.

CI: `dax-bot-1x-ci` #357 GREEN; `research-lab-ci` #1141 GREEN.

### Step 2143 — deterministic NextGen Product Replay Engine — COMPLETED

Final head: `1151f1fdf6df66d426cfc1add45113305567aad1`.

Added:

- `src/daxlab/engine/replay.py`;
- `src/daxlab/engine/__init__.py`;
- `tests/test_nextgen_replay_engine.py`.

Purpose:

- generic deterministic product replay over canonical Candle + Strategy Plugin semantics;
- broker/storage neutral;
- fail closed;
- shared semantics foundation for historical/replay/forward product modes;
- execution capability remains `NONE`;
- no order submission or PAPER/LIVE authorization.

CI: `dax-bot-1x-ci` #363 GREEN; `research-lab-ci` #1147 GREEN.

## 10. ACTIVE STEP — 2144 — Research Experiment / Promotion Contract — IN PROGRESS

`docs/CURRENT_WORK_STEP.md` is authoritative and currently states:

- last completed step: **2143**;
- active step: **2144**;
- next step after successful completion: **2145**.

### 2144 goal

Define the deterministic NextGen research experiment / promotion contract.

The step must begin by auditing existing provenance instead of duplicating it, especially:

- `daxlab.contracts.ExperimentManifest`;
- `research.registry` and current research governance.

The intended promotion artifact must bind, at minimum:

- canonical strategy/product identity;
- canonical dataset identity/fingerprint;
- evaluation split/window identity;
- cost/fill assumptions;
- robustness evidence;
- source/provenance fingerprints;
- research/promotion state;
- explicit `order_execution_authorized=false`.

This step must **not** introduce:

- optimizer behavior;
- broker connectivity;
- order submission;
- automatic economic promotion claims;
- PAPER/LIVE authority.

### Exact 2144 state at handover

2144 is **formally active but substantively not yet implemented**.

After the final green 2143 head `1151f1fd…`, the branch contains only:

- `CURRENT_WORK_STEP.md` activation of 2144;
- Masterstand refresh commits;
- Knowledge Index refresh commits.

No 2144 production/research module or test has yet been added.

This is therefore a clean handover boundary.

### Exact next action in the next chat

Continue **Step 2144**, do not open 2145 yet.

1. Re-pin fresh branch HEAD and exact CI after the final Masterstand documentation commit.
2. Re-read `CURRENT_WORK_STEP.md`, workflow-integrity gate and this Masterstand.
3. Audit existing research provenance owners before writing code:
   - `src/daxlab/contracts.py` / `ExperimentManifest`;
   - current `src/daxlab/research/` registry/governance owner(s);
   - `docs/RESEARCH_GATES.md` / `docs/RESEARCH_MODULE_CATALOG.md` as applicable;
   - relevant tests.
4. Decide what is KEEP/ADAPT rather than creating a duplicate experiment registry.
5. Implement the smallest deterministic research experiment/promotion artifact on the new Domain/Data/Strategy/Replay identities.
6. Add regression/conformance tests proving deterministic identity, provenance completeness and explicit non-authorization.
7. Run exact-head broad CI + any relevant focused CI.
8. Only after required evidence is green: close 2144 and activate 2145.

## 11. External / waiting / interrupted lanes

These lanes remain separate and do not block independent safe NextGen work.

### Step 2122 origin — Windows/MT5 current-branch SHADOW host verification — WAITING_EXTERNAL

Verified so far:

- Windows host wiring/parity path;
- Git-canonical parity corrected for CRLF false positives;
- 56/56 parity evidence on the tested host commit;
- fail-closed weekend behavior with stale market feed;
- `execution_capability=NONE`;
- `order_execution_enabled=false`.

Still required in a fresh/open DE40 market window:

- fresh broker clock/timezone proof;
- GREEN isolated one-shot;
- candidate manifest/checkpoint/operator evidence;
- overlap/reconciliation repeat;
- controlled Scheduled Task reload/restart + runtime health.

`Europe/Helsinki` is configured but remains UNVERIFIED until fresh host evidence proves it.

When this lane is later resumed, use the then-next unused whole-number step; never display 2122 again as the active current step.

### Step 2136 enforcement lane — WAITING_EXTERNAL / MANUAL_GITHUB_ADMIN

Stable-branch governance target exists, but actual `main` protection/ruleset enforcement requires GitHub-admin action outside the current connector permission.

### Step 2137 — INTERRUPTED / HISTORICAL

Old Drive/CSV materialization is retained only for historical evidence compatibility. It must not steer NextGen design.

### PAPER / LIVE

PAPER remains not authorized. LIVE remains not authorized. Do not build broker submission merely because software evidence owners exist.

## 12. Research / product doctrine — BINDING

Primary objective: build a robust, economically useful DAX daytrading system. Profitability is the goal but **not yet proven**.

Research decision hierarchy remains:

`REGIME -> STRUCTURE -> ENTRY`.

Do not accumulate plausible filters without evidence. Use causal semantics, activation/removal evidence, OOS/WF discipline, cost stress, overlap/redundancy analysis and multiple-testing governance where applicable.

Use FAST/vectorized screening for broad idea search and a deterministic shared-semantics Product Layer for promoted candidates. Do not force the Product Layer to serve as the early-search brute-force engine.

Public/open-source scans remain mandatory when architecture/recovery/data/execution/research questions arise, especially LEAN, NautilusTrader, Freqtrade, vectorbt and comparable mature systems. Take proven patterns; do not import unnecessary framework bulk or strategies.

## 13. What must NOT be redone or silently changed

- Do not rewrite or optimize REF-V11.2.
- Do not use REF-V11.2/V12 metrics as CAND-001 or NextGen evidence.
- Do not let the old 1,673-file CSV contract dictate the NextGen Data Catalog.
- Do not make broker symbol `DE40` the canonical instrument identity.
- Do not mix Strategy output with quantity/risk authorization/execution.
- Do not rewrite CAND-001 as the NextGen architecture; use the explicit compatibility adapter.
- Do not create a second Experiment/Promotion registry before auditing the existing provenance owners.
- Do not add a second parallel data/session owner when the new canonical owner already exists.
- Do not introduce PAPER/LIVE/order submission while `NONE/false` and authorization gates remain binding.
- Do not backfill several step numbers after substantive work; pointer first.
- Do not call a step complete because a partial/general CI is green while its own acceptance work is missing.
- Do not stop after a normal Zwischenstand when the next safe action is executable.
- Do not claim work continues after a final response.

## 14. Next-chat one-line resume

Use:

`Weiter mit dem DAXBot`

The next chat should recover from repository truth and continue **Step 2144** by auditing the existing experiment/provenance registry first, then building the smallest deterministic research/promotion contract on top of the new Domain + Data Catalog + Strategy Plugin + Replay Engine foundation. PAPER/LIVE remain unauthorized.
