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
- PR base SHA reported by GitHub: `e0784ebfc11bee28475fd9c3385be661af58a738`.
- **Fresh technical branch HEAD before this Masterstand commit:** `cc8c06da4fed102879f953cffe0720e9751c2226`.
- On `cc8c06da…` both current checks are GREEN:
  - broad `test` / `research-lab-ci` -> SUCCESS;
  - focused `candidate-core` / `dax-bot-1x-ci` -> SUCCESS.
- GitHub PR metadata currently reports an older PR `head_sha` (`958165fa…`) than the real branch HEAD. Treat this as metadata lag; **the next chat must re-pin the branch HEAD directly**.
- This Masterstand update creates a newer documentation commit after `cc8c06da…`; do not treat any SHA written here as self-referential current-head truth after the commit.

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

Frozen CAND-001 semantics include:

- DE40 M5;
- Europe/Berlin 09:00–17:30 session;
- OR15;
- closed-M5 confirmed breakout, not wick/touch;
- BOTH directions;
- stop = OR opposite;
- target = 1.5R;
- maximum one admitted trade/session.

Existing product/runtime work already includes deterministic closed-bar handling, candidate state, trade-plan/admission/decision pipeline, restart/idempotency controls, virtual lifecycle/costed outcome, operator snapshot/telemetry, SHADOW host integration, broker-neutral lifecycle/reconciliation/protection/checkpoint/telemetry evidence owners, and fail-closed PAPER readiness gates.

Do not silently migrate CAND-001 rules into NextGen core contracts. Later, CAND-001 may become one adapter/plugin implementation if evidence supports it.

## 6. CAND-001 historical/OOS evidence line — preserved but no longer architecture-driving

Steps 2102–2113 implemented a frozen CAND-001-specific historical/OOS evidence chain: deterministic replay, 45/20/20 WF/OOS schedule, normal/1.5x/2x costs, aggregation, immutable three-file evidence export, strict readers, cost-stress integrity, temporal stability diagnostics, standalone `diagnostics.json`, strict diagnostic verification, and post-processing CLI.

This line remains valid evidence infrastructure, but it no longer dictates the NextGen data or strategy architecture.

Historical Drive source remains known:

- root: `DAX_V14_RECOVERED_CACHE_V13`;
- `m5_daily` folder ID: `1p5-s3ccsBbohbephB7UIhUE_OL1M4b-y`.

Step 2137 proved one real private daily CSV can now materialize locally and matches the old canonical loader shape. Bulk/folder materialization through the connector was not available. The user explicitly stopped this lane from becoming the NextGen chassis.

Therefore:

- historical-data existence/location: VERIFIED;
- old CAND-001 evidence code: IMPLEMENTED/CI-VERIFIED;
- first actual frozen full CAND-001 OOS result artifact: still not produced;
- CAND-001 profitability/robustness: still UNVERIFIED;
- old 1,673-file/CSV contract: **historical compatibility/evidence only**, not NextGen storage design.

## 7. Workflow/governance hardening completed during this chat

Repeated chat/workflow drift was treated as an engineering defect, not cosmetic formatting.

### Step 2132 — workflow-integrity gate — COMPLETED

Canonical owner: `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`.

Binding rules now include:

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

## 9. NextGen foundation already built

### Step 2139 — canonical domain + ports — COMPLETED

Final implementation head: `b0fe61a09ba70fbed51afce283f7e486288e9c44`.

Added canonical broker/storage-neutral domain foundation under `src/daxlab/domain/`:

- opaque `InstrumentId` independent of broker ticker;
- canonical UTC Candle / market-data semantics;
- deterministic `ExecutionIntent` identity;
- protocol-only external ports;
- negative architecture tests preventing MT5, legacy-dataset, CAND-001 and V11.2 coupling.

No existing runtime/strategy file was changed in the step.

CI:

- `dax-bot-1x-ci` #339 GREEN;
- `research-lab-ci` #1123 GREEN.

### Step 2140 — Canonical Historical Data Catalog V1 — COMPLETED

Final implementation head: `ccdc14ab681bfb7589bbdd04e14a893f497f8761`.

New Greenfield data path:

- Parquet as canonical V1 physical format;
- PyArrow confined to optional `data` dependency surface;
- content-based deterministic Dataset fingerprint independent of Parquet encoder bytes;
- separate `parquet_sha256` physical-file integrity;
- immutable fingerprint-addressed object + manifest;
- canonical UTC/instrument/data-quality roundtrip;
- fail-closed checks for mixed instrument/timeframe, open candles, duplicates, out-of-order data, manifest/file tampering;
- no silent sort/fix-up;
- legacy `1,673` CSV surface not imported and not modified.

CI:

- `research-lab-ci` #1130 GREEN;
- `dax-bot-1x-ci` #346 GREEN.

This is the first modern data chassis independent of the recovered CSV layout.

## 10. ACTIVE STEP — 2141 — Strategy Plugin Contract V1 — IN PROGRESS

`docs/CURRENT_WORK_STEP.md` is authoritative and currently states:

- last completed step: **2140**;
- active step: **2141**;
- next step after successful completion: **2142**.

### 2141 goal

Build the generic strategy boundary on the new domain contracts **without** migrating CAND-001 and without adding risk sizing or execution authority.

A strategy may output only:

- `NO_TRADE`, or
- a broker-neutral `TRADE_PLAN` with direction, entry, stop and target.

A strategy must **not** own or authorize:

- quantity/position size;
- account/cash risk;
- broker/venue;
- order submission;
- persistence backend;
- host scheduler;
- PAPER/LIVE authority.

Risk sizing and execution remain downstream systems.

### Exact 2141 implementation state at handover

Step activation commit: `711f73561ecc219346f068f17ab3ede3bcfc3b33`.

Current technical implementation head before this Masterstand commit: `cc8c06da4fed102879f953cffe0720e9751c2226`.

Exactly four 2141 files differ from the activation commit:

1. `src/daxlab/domain/strategy.py` — added;
2. `src/daxlab/domain/__init__.py` — exports strategy-domain contracts;
3. `src/daxlab/strategies/contracts.py` — added generic `StrategyTransition` + `StrategyPlugin` Protocol;
4. `src/daxlab/strategies/__init__.py` — added package exports.

Current contracts include:

- `StrategyAction.NO_TRADE / TRADE_PLAN`;
- `TradeDirection.LONG / SHORT`;
- `TradePlan` with instrument, entry, stop, target and directional invariants;
- deterministic `StrategyDecision` identity with strategy ID/version/fingerprint, event time, reasons and optional plan;
- `StrategyPlugin.initial_state()`;
- `StrategyPlugin.on_candle(state, candle) -> StrategyTransition`.

Current HEAD checks are GREEN (`test` and `candidate-core`), **but 2141 is NOT COMPLETED**.

Why not complete: the planned dedicated Strategy-Conformance/architecture test has not yet been created. Existing broad CI success does not substitute for the missing acceptance content.

### Exact next action in the next chat

Continue **Step 2141**, do not open 2142 yet.

1. Re-pin branch/head/pointer after the Masterstand documentation commit.
2. Re-read:
   - `src/daxlab/domain/strategy.py`;
   - `src/daxlab/strategies/contracts.py`;
   - `src/daxlab/domain/market.py`;
   - existing NextGen foundation tests.
3. Add the dedicated Strategy-Conformance test (expected naming can be `tests/test_nextgen_strategy_contract.py`, but repository truth decides).
4. Test at least:
   - same state + same candle -> deterministic transition/decision identity;
   - `NO_TRADE` and valid LONG/SHORT plan invariants;
   - mismatched instrument rejection;
   - no quantity/account/broker/order fields in strategy output;
   - no MT5/runtime/legacy-dataset/CAND-001/V11.2 imports in the new strategy boundary;
   - plugin remains pure/deterministic and broker/storage-neutral.
5. Run exact-head CI.
6. Only after required tests/CI are green: close 2141 in `CURRENT_WORK_STEP.md` and activate 2142.

Do **not** migrate CAND-001 in the handover step. Do **not** add order capability.

## 11. External / waiting / interrupted lanes

These lanes are preserved but do not block independent safe NextGen work.

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
- Do not migrate CAND-001 into the new strategy contract before the generic contract is tested and closed.
- Do not add a second parallel data/session owner when the new canonical owner already exists.
- Do not introduce PAPER/LIVE/order submission while `NONE/false` and authorization gates remain binding.
- Do not backfill several step numbers after substantive work; pointer first.
- Do not call a step complete because a partial/general CI is green while its own acceptance work is missing.
- Do not stop after a normal Zwischenstand when the next safe action is executable.
- Do not claim work continues after a final response.

## 14. Next-chat one-line resume

Use:

`Weiter mit dem DAXBot`

The next chat should recover from repository truth and continue **Step 2141** at the missing Strategy-Conformance test, then exact-head CI, then close 2141 only if all acceptance checks are genuinely green.
