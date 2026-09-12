# DAX-BOT MASTERSTAND — NEXT-CHAT HANDOVER

Status: **BINDING HANDOVER / REPOSITORY TRUTH FIRST**  
Updated: **2026-09-12**  
Repository: `hennebergtoni-lgtm/dax-Day`  
Working branch: `nextgen-bot-line-v1`  
Pull request: `#109` → `main`

This file is the canonical next-chat handover. It consolidates the current project state without replacing exact code, hashed evidence, fresh runtime telemetry or CI. If this prose conflicts with exact repository evidence, exact repository evidence wins.

## 1. Mandatory resume protocol

After a new chat, context loss, compaction, tool reconnect, or any explicit `weiter` / `fortsetzen`:

1. read `docs/SESSION_EXECUTION_REFRESHER.md`;
2. pin repository, branch, PR and **fresh exact head SHA**;
3. read `docs/CURRENT_WORK_STEP.md` and use its whole-number pointer;
4. read this `docs/MASTERSTAND.md`;
5. read `docs/PROJECT_KNOWLEDGE_INDEX.md` and only the topic-specific owners needed for the active step;
6. continue the active step automatically.

Binding continuity rule: **a Zwischenstand, successful test, warning, found file, recovered context, CI state or completed sub-check is visibility only, not a stop.** Continue to the next concrete work unit unless a real stop condition from `docs/WORK_CONTINUITY_PROTOCOL.md` exists.

A lane-local blocker such as Windows hardware, market time, broker metadata or a user-only action does not stop unrelated safe work.

Official step numbers are integers only. Decimal/letter pseudo-steps are prohibited.

## 2. Repository / PR / CI truth at handover

- Base branch: `main`.
- PR #109 base SHA: `e0784ebfc11bee28475fd9c3385be661af58a738`.
- Working branch: `nextgen-bot-line-v1`.
- PR #109 is open, unmerged and mergeable at the handover refresh.
- Repository-side DAX-BOT 1.0-alpha acceptance was previously recorded at `2df6e20893144f87f04511823bc7b72699ad7cce`; later 1.x work continues on the same branch and does not invalidate that milestone.
- Last fully CI-verified implementation head before this handover documentation refresh: `f5fcf2ea715897a4b471c9dd1d1495f2dfca9371`.
- At `f5fcf2ea…`: `dax-bot-1x-ci` #253 = **GREEN** and `research-lab-ci` #1037 = **GREEN**.
- The subsequent pointer-only handover-start commit is `0b28a5fa4b396b6a2a72e93237d51cf0501569ee`.
- Because this document itself creates a newer commit, the next chat must pin the fresh branch head rather than treating any SHA written inside this document as self-referential current head truth.

No merge into `main` is authorized by this handover.

## 3. Safety and authorization — BINDING

- SHADOW: **AUTHORIZED**.
- PAPER/demo broker execution: **NOT AUTHORIZED**.
- LIVE: **NOT AUTHORIZED**.
- `execution_capability=NONE`.
- `order_execution_enabled=false`.
- No broker order-submission path is authorized.
- No `mt5.order_send` path may be introduced by research/evidence work.

No backtest, OOS result, stability metric, CI success, version label, operator setting or readiness object silently grants PAPER/LIVE permission. Explicit later user authorization remains mandatory.

## 4. Frozen reference — REF-V11.2 — VERIFIED / IMMUTABLE

`REF-V11.2` is the scientific legacy/reference anchor, not the current product strategy and not CAND-001 performance evidence.

Canonical active result source: `research/V112_REFERENCE_V1/reference_result.json`.  
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
- 81 WF windows, Train 45d / OOS 20d / Step 20d;
- 856 OOS trades;
- normal OOS total `-31.309210619787684 R`;
- 37 positive / 44 negative / 0 flat WFs;
- median WF PF `0.905769310256018`;
- stress 1.5× `-40.921695023387514 R`;
- stress 2× `-48.424611963007294 R`.

These metrics must never be relabeled as CAND-001 results.

## 5. DAX-BOT 1.x / CAND-001 product line — IMPLEMENTED / CI-VERIFIED where stated

Product identities are intentionally separate:

- `REF-V11.2` = frozen reference;
- `DAX-BOT 1.x` = active product line;
- `CAND-001` = current frozen alpha candidate, not a bot-version number.

CAND-001 frozen strategy semantics:

- symbol `DE40`;
- timeframe M5;
- Europe/Berlin session 09:00–17:30;
- OR15;
- confirmed breakout requires a **closed M5 close** beyond the completed opening range; wick/touch is insufficient;
- BOTH directions, symmetric long/short logic;
- stop = OR opposite;
- target = 1.5R;
- maximum one admitted trade per session.

Causal/runtime rules:

- only CLOSED bars mutate strategy state;
- no open M5 candle is used;
- duplicate/out-of-order/unsafe bars fail closed;
- future bars cannot rewrite prior signal/decision identity;
- decision event time is the bar close time;
- strategy hot path has no pandas/DB/MT5/broker dependency.

Implemented architecture includes product/candidate/config identity, signal state, trade plan, session admission, DecisionRecord, OperatorSnapshot, pure candidate pipeline, restart-safe candidate state, virtual lifecycle, costed virtual outcome, forward observation/performance plumbing, SHADOW host integration, telemetry/publication state, and broker-neutral pre-PAPER evidence owners.

Restart/duplicate safety remains a first-class requirement. Deterministic IDs alone are not treated as restart-safe publication; persisted publication/checkpoint state is used where required.

## 6. CAND-001 economic-evidence line — Steps 2102–2114

This is the major change since the previous masterstand.

### Step 2102 — evidence boundary audit — VERIFIED

CAND-001-specific historical/OOS evidence was audited separately from REF-V11.2/V12. Legacy/reference metrics cannot be borrowed. Profitability and robustness remained explicitly UNVERIFIED pending CAND-001-bound measurement.

### Step 2103 — deterministic historical descriptive replay — IMPLEMENTED / CI-VERIFIED

A historical CAND-001 replay harness now reuses the canonical runtime semantics and audited recovered-M5 owner rather than creating a second DataFrame strategy engine. Dataset fingerprint mismatch fails closed.

### Step 2104 — frozen OOS/WF contract — IMPLEMENTED / CI-VERIFIED

- deterministic 45/20/20 scheduling;
- no train-time candidate selection/tuning;
- frozen candidate/config identity;
- normal / 1.5× / 2× cost hooks;
- no profitability claim and no automatic promotion.

### Step 2105 — OOS/WF measurement runner — IMPLEMENTED / CI-VERIFIED

The runner evaluates OOS slices only over the audited recovered-M5 Berlin-session data and reuses frozen SHADOW replay/fill/outcome semantics. It emits deterministic per-window evidence.

### Step 2106 — deterministic aggregation — IMPLEMENTED / CI-VERIFIED

Per-cost totals, window signs, medians, worst-window risk, open-end counts and adjacent cost degradation are aggregated with full lineage/fingerprints.

### Step 2107 — immutable base evidence export — IMPLEMENTED / CI-VERIFIED

The base export is intentionally exactly three JSON files:

- `measurements.json`;
- `aggregation.json`;
- `manifest.json` written last.

Existing target directories are refused.

### Step 2108 — strict base-evidence reader — IMPLEMENTED / CI-VERIFIED

The reader requires the exact three-file layout, rejects missing/unknown fields, reconstructs typed objects and recomputes lineage/fingerprints. External JSON is never trusted on syntax alone.

### Step 2109 — cost-stress consistency audit — IMPLEMENTED / CI-VERIFIED

It verifies path/count/Gross-R invariance, exact `net_r = gross_r - cost_r`, linear cost scaling and monotone adverse cost effects across normal/1.5×/2×. This is evidence-integrity checking, not an economic pass/fail threshold.

Exact head evidence: `681f1306…` / `3fd127e4…`; `dax-bot-1x-ci` #240 GREEN; `research-lab-ci` #1024 GREEN.

### Step 2110 — temporal OOS stability diagnostics — IMPLEMENTED / CI-VERIFIED

Per cost model the project now reports, descriptively:

- mean/median window net-R;
- positive/negative/flat window rates;
- zero-trade windows;
- mean/median completed trades/window;
- longest positive/negative window streaks;
- cumulative window-net-R max drawdown;
- first-half vs second-half net-R and activity;
- full source fingerprints.

There is no composite score, no economic pass threshold and no auto-promotion. PBO/DSR are explicitly not applied to this one frozen-candidate/no-new-selection surface.

Head `4b9bb341…`: CI #243 / #1027 GREEN.

### Step 2111 — standalone diagnostic evidence — IMPLEMENTED / CI-VERIFIED

A separate immutable `diagnostics.json` binds the canonical measurement/aggregation evidence, unchanged Step-2107 base-manifest fingerprint, PASS cost-consistency audit and temporal stability diagnostics. The frozen three-file base export is not changed.

Head `999d4995…`: CI #246 / #1030 GREEN.

### Step 2112 — strict diagnostic reader — IMPLEMENTED / CI-VERIFIED

The reader recomputes the canonical source chain and rejects schema/metric/fingerprint/safety tampering. A discovered false mismatch caused by Python tuple → JSON array normalization was fixed by comparing canonical JSON identity; the reader returns the freshly recomputed canonical object rather than trusting raw input.

Head `3bf23550…`: CI #250 / #1034 GREEN.

### Step 2113 — post-processing diagnostic CLI — IMPLEMENTED / CI-VERIFIED

`scripts/build_cand001_oos_diagnostics.py` consumes only an already verified Step-2107 evidence directory, recomputes Step-2109/2110 diagnostics and writes one separate immutable `diagnostics.json`.

Regression coverage proves:

- no historical measurement rerun;
- base evidence stays byte-identical;
- base and diagnostic output directories must be separate;
- overwrite is refused;
- no optimizer, promotion or execution path is introduced.

Head `f5fcf2ea…`: CI #253 / #1037 GREEN.

### Step 2114 — LEAN/data-lane audit — COMPLETED

No additional “combined verification receipt” layer is required. The existing chain is sufficient:

`strict base reader -> canonical cost audit -> canonical stability -> standalone diagnostic artifact -> strict diagnostic reader`.

Adding another wrapper now would be overengineering.

The highest-value next step is therefore **actual frozen CAND-001 OOS evidence generation**, not more scaffolding.

## 7. Historical data source for the first real CAND-001 OOS run — LOCATED / NOT YET MATERIALIZED IN THIS EXECUTION ENVIRONMENT

The repository intentionally stores the audited manifest, not thousands of raw daily CSV files.

The persisted historical source has been located in the connected Google Drive:

- root folder: `DAX_V14_RECOVERED_CACHE_V13`;
- root folder ID: `12aNhN7dNWZ9j9YqqaiOdcOsCm-cqhzUN`;
- daily M5 folder: `m5_daily`;
- `m5_daily` folder ID: `1p5-s3ccsBbohbephB7UIhUE_OL1M4b-y`.

Drive listing confirmed ordinary daily `text/csv` files through `2019-12-31.csv` and reported about 1,694 folder items. **Do not equate Drive item count with the 1,673 audited valid session days.** The canonical loader/manifest determines the valid historical surface.

Canonical dataset fingerprint expected by the recovered-M5 owner:
`e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`.

Current state:

- data existence/location: **VERIFIED**;
- repository manifest: **VERIFIED**;
- CAND-001 OOS runner/export/diagnostics code: **IMPLEMENTED + CI-VERIFIED**;
- first actual full CAND-001 OOS result artifact: **NOT YET PRODUCED**;
- CAND-001 profitability: **UNVERIFIED**;
- CAND-001 robustness: **UNVERIFIED**.

No attractive future result may bypass the frozen no-tuning contract, cost-stress checks or prospective SHADOW/PAPER evidence.

## 8. Parallel external / waiting lanes

These lanes remain separate and must not globally stop independent repository/research work.

### Current Candidate Windows/MT5 host verification

Repository integration/runbook exists. Fresh real Windows/MT5 verification of the current Candidate-integrated branch remains a separate host lane until fresh host evidence is captured.

### Real broker economics

Read-only economics plumbing and research-only sizing translation exist, but verified venue-specific economics required for PAPER sizing/readiness remain an external evidence lane.

### PAPER authorization

Broker-neutral lifecycle, reconciliation, protection, telemetry/checkpoint and readiness infrastructure exist, but repository fixtures do not authorize PAPER. Explicit user authorization remains an independent STOP-gate.

### LIVE

Not authorized and not part of the current evidence-generation sequence.

## 9. Research / architecture doctrine — BINDING

Research decision hierarchy remains:

`REGIME -> STRUCTURE -> ENTRY`.

Do not accumulate filters merely because they are plausible. Use activation/removal evidence, R/Cash/DD impact, overlap/redundancy checks, OOS/WF discipline and multiple-testing governance where applicable.

Public/open-source comparison remains required, especially for engineering patterns from LEAN, NautilusTrader, Freqtrade, vectorbt and comparable systems. Reuse proven patterns for state/recovery/reconciliation, persistence, dry/forward discipline, data integrity, performance, overfitting control, observability and governance. Do not copy large generic frameworks or introduce multi-venue/portfolio complexity without a defined need.

Avoid blind multi-hour grids. Prefer FAST screening, targeted stages, checkpoints/resume and causal/event-driven semantics.

## 10. What must NOT be redone or silently changed

- Do not optimize or rewrite REF-V11.2.
- Do not borrow REF-V11.2/V12 performance metrics for CAND-001.
- Do not create a second CAND-001 strategy engine for historical testing.
- Do not create a second historical-data/session owner.
- Do not create a second paper/order contract.
- Do not add another verification-wrapper/receipt layer unless a concrete evidence gap appears.
- Do not introduce broker order submission while `NONE/false` is binding.
- Do not change the Step-2107 exactly-three-file base evidence contract merely to append diagnostics.
- Do not apply PBO/DSR mechanically to a single frozen candidate with no new multi-trial selection surface.
- Do not use chat memory as current head/step truth when repository truth is available.
- Do not stop after a normal Zwischenstand when the next safe step is known.

## 11. Current work pointer and exact next technical value

Canonical numbering lives only in `docs/CURRENT_WORK_STEP.md`.

At the start of this handover refresh:

- Step 2114: completed;
- Step 2115: new canonical masterstand / next-chat handover;
- next independent technical work after successful 2115 closeout: Step 2116.

Planned Step 2116 intent:

**Reuse the located Google Drive `m5_daily` source and existing dataset owner to materialize/attach the audited historical data in a suitable execution workspace, verify the freshly loaded session fingerprint against the authoritative audited SHA256, then run the frozen CAND-001 OOS/WF measurement → aggregation → immutable three-file export → strict verification → cost-consistency → temporal-stability → standalone diagnostic chain to produce the first actual CAND-001 OOS evidence. No tuning, no promotion and no execution.**

If bulk Drive materialization is not practical in the current tool environment, that is a lane-local execution constraint, not a reason to invent a new data format or globally stop the project. Reuse an existing Colab/Drive or other already-approved execution path and continue other safe work independently.

## 12. Source precedence

For active facts, prefer:

1. exact repository code/contracts at the pinned SHA;
2. audited manifests and hashed machine-readable evidence;
3. fresh runtime telemetry for current runtime claims;
4. current CI and specific audits;
5. this masterstand;
6. older prose only for provenance.

Step 2000 full audit is complete. Next mandatory full-project audit: **Step 2500**.
