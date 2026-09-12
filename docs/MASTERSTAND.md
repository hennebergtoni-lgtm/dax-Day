# DAX-BOT MASTERSTAND — NEXT-CHAT HANDOVER

Status: **BINDING HANDOVER / REPOSITORY TRUTH FIRST**  
Updated: **2026-09-12 — Step 2152 continuity reconciliation**  
Repository: `hennebergtoni-lgtm/dax-Day`  
Working branch: `nextgen-bot-line-v1`  
Pull request: `#109` -> `main`

This file is the canonical durable handover below exact repository code/tests/evidence. If prose here ever disagrees with fresh repository evidence, the precedence is:

1. exact code / tests / machine evidence / fresh runtime telemetry;
2. `docs/CURRENT_WORK_STEP.md` for official step numbering;
3. binding safety/governance contracts;
4. this Masterstand;
5. chat memory.

## 1. Mandatory resume protocol

On a new chat, context loss, reconnect, compaction, or `Weiter mit dem DAXBot`:

1. read `docs/SESSION_EXECUTION_REFRESHER.md`;
2. pin repository, branch, PR and **fresh exact branch HEAD**;
3. read `docs/CURRENT_WORK_STEP.md` and use it as the only active-step authority;
4. read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`;
5. read this Masterstand;
6. read `docs/PROJECT_KNOWLEDGE_INDEX.md` and only the topic owners needed for the active step;
7. read the Problem/Solution registries before inventing a new fix;
8. continue automatically when the Step-Close-Gate permits safe work.

Repository truth overrides chat memory. Tool/interface activity does not replace the required normal-text Zwischenstand.

Binding visible cadence:

`Step N -> short activity -> visible normal-text Zwischenstand -> ✅ / ⚠️ / ❌ -> actual next tool/action`.

A Zwischenstand is visibility, not a stop. Do not end a turn merely because a sub-check succeeded or CI is still running when safe executable work remains. A final answer ends the active tool turn; never claim invisible background continuation afterward.

Official step numbers are whole integers only. Visible numbering is monotonic. Interrupted older lanes resume only under a new later integer with provenance preserved.

Next mandatory Masterstand checkpoint: **2250**.  
Next mandatory full architecture/LEAN audit: **2500**.

## 2. Repository / branch / PR truth at this reconciliation

Fresh PR metadata immediately before this Masterstand write:

- base branch: `main`;
- working branch: `nextgen-bot-line-v1`;
- PR #109: **OPEN / UNMERGED / MERGEABLE / NOT DRAFT**;
- PR base SHA: `e0784ebfc11bee28475fd9c3385be661af58a738`;
- documentation head immediately before this Masterstand commit: `de435cbad67cfd1204c3d7f2789838f8767fec53`;
- last fully tested technical/cleanup head before Step 2152 documentation work: `4a06038cb62be180e9d17afdc3389daf4b542aab`;
- on `4a06038c…`: `dax-bot-1x-ci` #416 **GREEN** and `research-lab-ci` #1200 **GREEN**.

This Masterstand commit creates a newer documentation head. Every later chat must therefore re-pin HEAD and CI rather than treating any SHA written here as self-referential current truth.

No merge into `main` is authorized by this handover. `main` protection enforcement remains a separate manual GitHub-admin dependency.

## 3. Safety / authorization — BINDING

- SHADOW: **AUTHORIZED only within the existing no-order contract**.
- PAPER/demo broker execution: **NOT AUTHORIZED**.
- LIVE: **NOT AUTHORIZED**.
- `execution_capability=NONE` where currently required.
- `order_execution_enabled=false` where currently required.
- No broker order-submission path is authorized.
- No research/backtest/CI result may silently grant PAPER/LIVE authority.
- Explicit later user authorization remains mandatory before PAPER or LIVE.
- Promotion of a research artifact changes software/evidence state only; it never grants trading authority.

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

Repository-side DAX-BOT 1.0-alpha acceptance remains a correctness/control milestone, not a profitability proof. Frozen `CAND-001` remains available as product/reference/compatibility evidence while NextGen is built beside it.

Frozen CAND-001 semantics:

- DE40 M5;
- Europe/Berlin 09:00–17:30 session;
- OR15;
- closed-M5 confirmed breakout, not wick/touch;
- BOTH directions;
- stop = OR opposite;
- target = 1.5R;
- maximum one admitted trade/session.

Existing legacy-product/runtime work includes deterministic closed-bar handling, candidate state, trade-plan/admission/decision pipeline, restart/idempotency controls, virtual lifecycle/costed outcome, operator snapshot/telemetry, SHADOW host integration, broker-neutral lifecycle/reconciliation/protection/checkpoint/telemetry evidence owners and fail-closed PAPER readiness gates.

Do not silently migrate CAND-001 rules into NextGen core contracts. CAND-001 is connected to NextGen only through explicit compatibility boundaries.

## 6. Historical CAND-001 OOS evidence line — preserved, not architecture-driving

Steps 2102–2113 implemented the frozen CAND-001 historical/OOS evidence chain: deterministic replay, 45/20/20 WF/OOS schedule, normal/1.5x/2x costs, aggregation, immutable evidence export/readers, cost-stress integrity, temporal stability diagnostics and diagnostic evidence.

Historical Drive source remains known:

- root: `DAX_V14_RECOVERED_CACHE_V13`;
- `m5_daily` folder ID: `1p5-s3ccsBbohbephB7UIhUE_OL1M4b-y`.

Step 2137 proved one real private daily CSV can materialize locally and matches the old loader shape. Bulk/folder materialization through the connector was not available. The user explicitly stopped this lane from becoming the NextGen chassis.

Therefore:

- historical-data existence/location: VERIFIED;
- old CAND-001 evidence code: IMPLEMENTED/CI-VERIFIED;
- first actual frozen full CAND-001 OOS result artifact: still not produced;
- CAND-001 profitability/robustness: still UNVERIFIED;
- old 1,673-file/CSV contract: **historical compatibility/evidence only**, not NextGen storage design.

## 7. Workflow / governance state

### Step 2132 — workflow-integrity gate — COMPLETED

Canonical owner: `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`.

Binding rules include:

- Step-Close-Gate;
- pointer-before-next-step;
- monotonic interrupted-lane carry-forward;
- visible text Zwischenstand separate from tool activity;
- no long meaningful tool-call chains without text visibility;
- a Zwischenstand is not a stop;
- no final/turn-ending response while executable safe work remains;
- no claim of background work after a turn ends;
- exact-head CI/evidence discipline;
- explicit user intervention as valid sequence interruption.

### Step 2133 — Recovery canonicalization — COMPLETED / RETAIN_WITH_REASON

`recovery_bundle.py` remains canonical. Legacy `recovery.py` is frozen forensic compatibility only, with no new active consumers.

### Step 2135 — CI ownership — COMPLETED

- `research-lab-ci` / `test` = broad integration/regression owner;
- `dax-bot-1x-ci` / `candidate-core` = focused candidate/broker-safety owner;
- `reference-payload-export` = frozen reference integrity/export owner.

No specialty gate replaces the broad integration regression.

### Step 2136 — stable-branch governance audit — COMPLETED AUDIT / ENFORCEMENT WAITING_EXTERNAL

Observed `main` state was unprotected with no ruleset. Minimal target protection is documented, but the current integration cannot apply the GitHub-admin setting. Do not claim `main` is protected until fresh admin evidence proves it.

## 8. Architecture intervention — Ferrari, not Golf — BINDING

The user explicitly corrected project direction: historical V11.2/CSV/Colab/Drive constraints are not the chassis for the new bot merely because they already exist.

Binding rule:

**Legacy is reference, regression evidence and compatibility input — not the NextGen architecture constraint.**

Canonical architecture: `docs/NEXTGEN_GREENFIELD_ARCHITECTURE_V1.md`.

The Step-2138 First-Principles contract defines:

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

## 9. Verified NextGen progression — Steps 2139–2151

The following sequence is repository/CI verified. Exact details and hashes remain in `docs/CURRENT_WORK_STEP.md` and topic tests.

### 2139 — Canonical Domain + Ports — COMPLETED

- broker-independent opaque `InstrumentId`;
- canonical UTC Candle contracts;
- deterministic broker-neutral execution-intent identity;
- Protocol-only external ports;
- negative dependency tests against MT5/legacy/CAND-001/V11.2.

Final tested head `b0fe61a09ba70fbed51afce283f7e486288e9c44`; CI #339/#1123 GREEN.

### 2140 — Canonical Historical Data Catalog V1 — COMPLETED

- immutable Parquet/Arrow catalog;
- canonical content fingerprint separate from physical Parquet SHA256;
- UTC/instrument/data-quality roundtrip;
- fail-closed mixed/open/duplicate/out-of-order/tamper handling;
- legacy 1,673-file layout is not the storage contract.

Final tested head `ccdc14ab681bfb7589bbdd04e14a893f497f8761`; CI #346/#1130 GREEN.

### 2141 — Strategy Plugin V1 — COMPLETED

- deterministic `StrategyDecision` / `TradePlan`;
- generic `StrategyPlugin` / `StrategyTransition`;
- strategy output stops before quantity/risk/broker/order authority.

Final tested head `2b345016b7be03c47462527c776d53a9df6bd3ee`; CI #352/#1136 GREEN.

### 2142 — CAND-001 compatibility adapter — COMPLETED

Existing CAND-001 pipeline remains behavior owner; adapter exposes it through the generic Strategy Plugin boundary without changing rules or adding execution capability.

Final tested head `6f8db8883df342d4d523e06c041ab1ce0cc5e9fb`; CI #357/#1141 GREEN.

### 2143 — Deterministic Product Replay Engine — COMPLETED

Generic fail-closed replay over canonical Candle + Strategy Plugin semantics; broker/storage neutral; execution capability remains `NONE`.

Final tested head `1151f1fdf6df66d426cfc1add45113305567aad1`; CI #363/#1147 GREEN.

### 2144 — Research Experiment / Promotion Artifact V1 — COMPLETED

`src/daxlab/research/promotion.py` binds strategy/config, dataset, split/WF, costs/fills, robustness evidence, source commit and limitations into deterministic experiment/product/promotion identities. Promotion does not authorize execution.

Final implementation head `b4f7152bff59ee85aa459348e6b72219d597df89`; CI #373/#1157 GREEN.

### 2145 — Research→Product conformance — COMPLETED

Frozen canonical fixtures bind research/product provenance to exact replay-input and ordered strategy-decision identities. Provenance/input/semantic drift fails closed.

Final tested head `50f908a861606c86d308824e224d506cb0197a13`; CI #378/#1162 GREEN.

### 2146 — Explicit read-only MT5 market-data adapter — COMPLETED

Validated Closed-M5 feed is translated into canonical UTC Candles behind `CandleSourcePort`; no MT5 SDK/order dependency enters the canonical adapter.

Final tested head `347f0cbe44350403656baf62ff82c3258f19317f`; CI #382/#1166 GREEN.

### 2147 — Generic atomic StateStorePort adapter — COMPLETED

Opaque bytes persist through an atomic fsync/replace file adapter with safe missing/replacement behavior; specialized/legacy recovery owners remain separate.

Final tested head `1c75bcf783572e80d79b865492791a486385c56d`; CI #386/#1170 GREEN.

### 2148 — Generic operator read model — COMPLETED

Product-neutral read-only operator view plus CAND-001 compatibility adapter. Candidate-specific detailed telemetry remains its own evidence surface; no control/order authority was promoted.

Final tested head `52ff0174597fd0a039510ce4f9b369c6e807b59e`; CI #392/#1176 GREEN.

### 2149 — Deterministic ProductCheckpointV1 — COMPLETED

Checkpoint binds run/engine/strategy/config/source/input/event/decision/state-codec identity with canonical tamper-checked serialization through `StateStorePort`.

Final tested head `91d60ff8c15735ad06be14d073e15dd93b5255da`; CI #397/#1181 GREEN.

### 2150 — Generic deterministic restart/resume parity — COMPLETED

`StrategyStateCodec` + replay-resume path restores from multiple split points and reproduces uninterrupted ordered decisions and final strategy state exactly while processing only the suffix.

Final tested head `0aa06bcc61655a589e4a2dc1ef8c1d0b5237b0e2`; CI #407/#1191 GREEN.

### 2151 — CAND-001 canonical state codec + real Candidate resume parity — COMPLETED

- strict canonical JSON `Cand001PipelineStateCodec`;
- explicit frozen schema/codec identity;
- UTC-only timestamp handling;
- exact-field and canonical-form checks;
- finite-price enforcement; no NaN/Inf, no pickle;
- real `Cand001StrategyPlugin` interruption/resume across multiple cut points;
- exact prefix+suffix decision parity and final-state parity against uninterrupted replay.

Final tested/cleaned head `4a06038cb62be180e9d17afdc3389daf4b542aab`; `dax-bot-1x-ci` #416 GREEN and `research-lab-ci` #1200 GREEN.

No CAND-001 strategy rule, broker/MT5 behavior, order capability or PAPER/LIVE authorization changed.

## 10. Continuity reconciliation — Step 2152

Step 2152 exists only to bring durable navigation/handover prose back in sync with verified repository progress through 2151. It changes no trading/runtime semantics.

At the time this Masterstand was refreshed, `docs/CURRENT_WORK_STEP.md` named 2152 as active. **Do not infer the current step from this sentence in a later chat.** Always read `CURRENT_WORK_STEP.md`; after Step 2152 closes, the pointer will advance normally.

Step-2152 responsibilities:

- reconcile `PROJECT_KNOWLEDGE_INDEX.md` through verified Step 2151;
- reconcile this Masterstand through verified Step 2151;
- preserve safety/external-lane truth;
- run exact-head CI for the documentation reconciliation;
- only after evidence is green, close 2152 and select/activate 2153 from current Greenfield/backlog truth.

## 11. External / waiting / interrupted lanes

These lanes remain separate and do not block independent safe NextGen work.

### Lane originating in Step 2122 — Windows/MT5 current-branch SHADOW host verification — WAITING_EXTERNAL

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

PAPER remains not authorized. LIVE remains not authorized. Do not build/enable broker submission merely because software evidence owners exist.

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
- Do not rewrite CAND-001 as the NextGen architecture; use explicit compatibility adapters.
- Do not duplicate existing research/promotion/conformance/state/recovery owners before auditing them.
- Do not add a second parallel data/session owner when the new canonical owner already exists.
- Do not introduce PAPER/LIVE/order submission while `NONE/false` and authorization gates remain binding.
- Do not backfill several step numbers after substantive work; pointer first.
- Do not call a step complete because partial/general CI is green while its own acceptance work is missing.
- Do not stop after a normal Zwischenstand when the next safe action is executable.
- Do not claim work continues after a final response.

## 14. Next-chat one-line resume

Use:

`Weiter mit dem DAXBot`

The next chat must recover from repository truth and continue the **active step named by `docs/CURRENT_WORK_STEP.md`**. Never infer the active step from an older Masterstand section. Re-pin fresh HEAD/CI, preserve all safety/external-lane boundaries, and continue the Greenfield migration from the current verified architecture rather than falling back to legacy constraints. PAPER/LIVE remain unauthorized.