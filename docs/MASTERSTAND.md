# MASTERSTAND — DAX Daytrading Bot

Updated: 2026-09-11

This document is the durable project handover/source-of-truth. New work must preserve verified findings and must keep VERIFIED / IMPLEMENTED / RESEARCH / PLANNED / UNVERIFIED / STALE / DUPLICATE / FIX REQUIRED states separate.

## 0. Current active development line — BINDING

The project has two deliberately separate identities:

- `REF-V11.2` = immutable legacy/reference baseline. It is a negative comparison and scientific provenance anchor, not the current product bot and not a profitability claim.
- `DAX-BOT 1.0-alpha` = the new product line under controlled construction. Incremental generations may become 1.1, 1.2, 1.3, 1.5, etc.; `2.0` is reserved for a genuinely new generation rather than routine iteration.
- Strategy ideas/candidates use candidate IDs such as `CAND-001`; candidate IDs are not bot version numbers.

Current development PR: `#109`, branch `nextgen-bot-line-v1`, base `main`.
Last fully CI-verified 1.x implementation head before this documentation refresh: `61dc2e3d50debb5dfd86eb2005f067829879dd7c`.
Verified CI at that implementation head:
- `dax-bot-1x-ci` run #1: GREEN.
- `research-lab-ci` run #785: GREEN.

DAX-BOT 1.x success is not defined first by profitability. The alpha must be deterministic, causal, observable, restart-safe, duplicate-safe, parameter-identifiable, modular, testable and operationally understandable. Profitability remains unproven.

## 1. Repository and recovery anchors
- Repository: `hennebergtoni-lgtm/dax-Day`, default branch `main`.
- Current `main` base for PR #109: `e0784ebfc11bee28475fd9c3385be661af58a738` (context/resume recovery governance merged in PR #108).
- Earlier historical anchor `ff38849978112ca25cec91aa5246cfa56bbed30c` remains a valid recovery/provenance point, not the current head.
- Historical anchors remain valid recovery points even after newer `main` commits are created.
- Repository truth and fresh runtime telemetry outrank chat recollection.

## 2. Immutable V11.2 active reference — VERIFIED
V11.2 remains unchanged and frozen. New hypotheses, filters, diagnostics, forward evidence or DAX-BOT 1.x code never silently modify it.

Canonical active result source:
`research/V112_REFERENCE_V1/reference_result.json`

Audited data source:
`data/manifests/dax_m5_2014_2019_audited.json`

Verified historical surface:
- Research period: 2014–2019.
- 1,673 valid Europe/Berlin session days.
- 481,824 raw M5 rows.
- 172,319 Berlin-session M5 bars.
- 103 M5 session bars/day, session 09:00–17:30 Europe/Berlin.
- 0 invalid OHLC rows; 0 duplicate UTC timestamps.
- Session OHLC SHA256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`.
- Audited migration ZIP SHA256: `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870`.
- V11.2 exact-candidate engine SHA256: `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`.
- Oracle source SHA256: `62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f`.
- 144 variants.
- Walk-forward: 81 windows, Train 45d, OOS 20d, Step 20d.
- Normal OOS: 856 trades, `-31.309210619787684 R`, 37 positive / 44 negative / 0 flat WFs, median WF PF `0.905769310256018`.
- Stress 1.5×: 856 trades, `-40.921695023387514 R`.
- Stress 2×: 856 trades, `-48.424611963007294 R`.

The older values 1,384 trades / -68.10950257808015 R / 36 positive / 45 negative WFs belong to `LEGACY_EVIDENCE_ONLY` (`V4.0-FIX1`). They are retained for provenance and are not the active V11.2 reference.

## 3. Scientific governance — IMPLEMENTED / RESEARCH
The research layer includes Git-based predeclaration/chronology, multiple-testing preflight, statistics readiness, classical DSR, CSCV/PBO research, K_eff diagnostics, SPA using the established `arch.bootstrap.SPA` implementation, block-length diagnostics, filter efficiency/ablation, filter overlap, backward elimination, Pareto diagnostics and simulated EUR-cash analysis.

These methods reduce the risk of fooling ourselves with backtests. DSR, PBO, K_eff, SPA or any other robustness statistic is not proof of profitability and does not create edge.

Current filter doctrine: do not accumulate filters merely because they look plausible. A filter must be shown to activate, remove trades in a meaningful way, improve relevant R/Cash/DD evidence where claimed, and be checked for redundancy/overlap with other filters.

Research families and tools — Bollinger, Fibonacci, close gaps, ATR/ATR25, liquidity sweeps, momentum, volatility, TWAP/anchored price, CPR, macro events, session filters, stop/trailing variants and related ideas — remain research unless explicitly promoted through the governed process.

Decision architecture remains:
`REGIME -> STRUCTURE -> ENTRY`.

## 4. Forward evidence — REAL-DATA SHADOW VERIFIED, observation only
The narrow real-data milestone is VERIFIED in `docs/evidence/2026-09-11_forward_shadow_real_data_milestone.md`.

Verified scope:
- real closed DE40 broker M5 bars reach the SHADOW path;
- SHADOW remained observation-only with `action=NO_ORDER`;
- closed-bar fingerprints link deterministically to V11.2-reference observations;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- broker timezone recorded as `Europe/Helsinki`;
- timestamp interpretation recorded as `EXPLICIT_BROKER_WALL_CLOCK`;
- cross-cycle overlap integrity was GREEN in the captured milestone;
- profitability, PAPER readiness and LIVE readiness are NOT proven.

The forward stability/degradation research remains descriptive and non-promotional. Backtest→forward degradation is not a second strategy architecture and has no automatic promotion rule.

Forward cash curves remain simulated. Broker balances are not treated as research capital.

## 5. Execution authorization — BINDING
- SHADOW: AUTHORIZED.
- PAPER: NOT AUTHORIZED.
- LIVE: NOT AUTHORIZED.
- Host-facing execution remains `execution_capability=NONE`.
- `order_execution_enabled=false`.

DAX-BOT 1.x may construct simulation-only contracts and virtual trade geometry, but no code, research result, stability/degradation metric, CI result or version label changes broker authorization. PAPER or LIVE requires an explicit later user decision.

## 6. MT5 / Windows host state — VERIFIED where stated
VERIFIED:
- Windows MT5 Python IPC/bridge works.
- DE40 is detected.
- `trade_mode=0`, digits=2, point=0.01, contract size=1, profit currency EUR.
- Broker timezone is `Europe/Helsinki` for the verified SHADOW evidence.
- Timestamp interpretation is `EXPLICIT_BROKER_WALL_CLOCK`.
- Real closed DE40 M5 bars reached the SHADOW path.
- Windows read-only SHADOW host path has real host evidence.

Binding safety:
- no automatic broker order submission in the current research/SHADOW path;
- `execution_capability=NONE`;
- `order_execution_enabled=false`.

Windows host operating rule: exactly one concrete PowerShell/host command at a time; inspect the returned result before issuing the next command.

## 7. Runtime / reliability architecture
Repository infrastructure includes Windows autostart, single-instance locking, heartbeat history, resume, cross-cycle integrity, gap diagnostics, decision outbox/telemetry and forward-evidence handling.

Recovery canonicalization from the Step-2000 audit:
- `src/daxlab/runtime/recovery_bundle.py` = canonical material-run recovery contract.
- `src/daxlab/runtime/recovery.py` = legacy / retirement candidate; do not use for new production paths.
- active SHADOW/replay state remains an operational restart/reconcile concern and is not silently collapsed into the material-run bundle.

DAX-BOT 1.x now reuses the existing atomic JSON persistence primitive for candidate state rather than adding a new writer/recovery subsystem.

Research execution should avoid blind 12–14-hour grids. Prefer FAST screening, targeted stages, checkpoints/resume and efficient/vectorized evaluation where scientifically appropriate.

## 8. DAX-BOT 1.x modular transition — IMPLEMENTED / VERIFIED
The migration is compatibility-first, not rewrite-first. Existing useful infrastructure is preserved and components migrate individually.

Implemented component routing:
- `LEGACY`
- `DUAL_COMPARE`
- `BOT_1X`

`DUAL_COMPARE` may compute both providers for comparison, but exactly one provider is authoritative. Routing does not grant safety or execution authorization.

Implemented deterministic product identity binds:
- product name/version;
- candidate ID;
- full config fingerprint;
- stable core version.

Current alpha candidate: `CAND-001`.
Its current rules are explicit `NEW_1X_SELECTION`, not a profitability claim and not a silent V11.2 inheritance:
- symbol `DE40`;
- timeframe `5m`;
- Europe/Berlin session 09:00–17:30;
- OR15 structure from exact closed 09:00/09:05/09:10 M5 slots;
- confirmed breakout requires closed M5 close beyond completed OR, not wick-only touch;
- LONG/SHORT symmetric;
- OR-opposite stop;
- fixed 1.5R target for the alpha candidate;
- max one admitted trade per session.

Implemented 1.x path:
`canonical Candle -> pure signal state transition -> proposed trade geometry -> per-session admission -> canonical DecisionRecord -> read-only OperatorSnapshot`.

Key behavior:
- closed bars only;
- duplicate/out-of-order bars are fail-closed/side-effect free;
- unsafe bars do not mutate strategy state;
- signals remain observable even when trade admission blocks them;
- the second directional signal in one session can remain visible while `SESSION_TRADE_LIMIT` forces `NO_TRADE`;
- no MT5, DB, pandas, Paper or broker dependency is allowed inside the candidate hot path by architecture test;
- no broker order API is introduced.

Pure one-bar orchestration is implemented so one closed Candle produces signal → proposed plan → admission → DecisionRecord → OperatorSnapshot without DB/MT5/Paper side effects.

Candidate state persistence is restart-safe and fail-closed:
- schema/candidate/core/config identity is checked;
- state payload is hashed;
- safety fields cannot escalate execution capability;
- continuous processing and save→load→resume produce identical downstream signal/plan/decision/snapshot identities in the verified restart-parity tests;
- the per-session admitted-trade limit survives restart.

CI evidence at implementation head `61dc2e3d50debb5dfd86eb2005f067829879dd7c`:
- `dax-bot-1x-ci` run #1: GREEN.
- Candidate Ruff: GREEN.
- Candidate correctness/restart tests: GREEN.
- Candidate performance observation: GREEN.
- Benchmark artifact upload: GREEN.
- `research-lab-ci` run #785: GREEN across full tests plus existing recovery/reference/SHADOW smokes.

Neon-dependent main-push CI steps remain environment/secret dependent; a skipped DB step is not treated as equivalent to DB verification.

## 9. Performance doctrine for DAX-BOT 1.x — BINDING / BASELINE VERIFIED
Runtime performance is measured before optimization.

Current hot-path rules:
- one incremental state transition per closed M5 bar;
- no repeated DataFrame rebuild in the runtime decision loop;
- no per-bar DB/history query;
- no MT5-specific type inside strategy logic;
- only active/promoted runtime features are computed;
- research may remain vectorized/Pandas-oriented outside the runtime hot path;
- correctness, causality, provenance and safety are never removed merely for speed.

First reproducible product benchmark at CI run #1:
- 50 synthetic sessions;
- 103 bars/session;
- 3 repeats;
- 5,150 events/repeat;
- median `309375.4221359223 ns/event` (~309 µs/event);
- p95 `313607.3145631068 ns/event` (~314 µs/event);
- median `3232.318821889658 events/s`;
- Python 3.11.16 on GitHub-hosted Linux runner;
- `performance_gate=OBSERVATION_ONLY`.

Benchmark artifact:
- artifact ID `10264245107`;
- artifact SHA256 `a6b0614bc2db8b8fdf4b96f7c214174fa9d906705066fdd483badca90287037c`;
- 30-day retention from the verified run.

No hard runtime threshold is inferred from a single CI baseline. Future budgets should be based on repeated comparable evidence and should preferably detect regressions rather than encode an arbitrary absolute number.

## 10. Web / observability architecture — PRESERVE + MODERNIZE
The existing `web/index.html` is preserved as a useful small read-only UI shell.

The old `web/status.json` is STALE for live runtime state because it mixes stable evidence with historical/pre-host runtime claims. The old validator also encodes pre-host expectations and is a 1.x cleanup item.

DAX-BOT 1.x separates:
1. stable/reference evidence — versioned and rarely changing;
2. fresh operator/runtime state — generated from current bot/SHADOW contracts.

`DAX_BOT_OPERATOR_SNAPSHOT_V1` is IMPLEMENTED as a credential-free read-only contract. It exposes product identity, signal reason/direction, admission status, final decision/blockers, proposed entry/stop/target/RR and explicit safety (`NONE`/`false`).

The browser must not receive Neon credentials. GitHub must not be reintroduced as a Neon→JSON→ChatGPT runtime relay. A later small read-only operator surface may serve fresh snapshots, while stable evidence remains versioned.

## 11. Open-source research doctrine
Public/open-source research remains part of development. Relevant projects/methods include LEAN, NautilusTrader, vectorbt, Freqtrade, VN.PY, purged cross-validation implementations, RiskLabAI, ml4t/diagnostic, `arch` and related projects.

Do not copy external systems blindly. Reuse proven patterns only when they solve a defined project need.

Current adopted engineering principles include:
- LEAN: separation of signal/alpha, risk and execution; measure performance before optimizing; keep repeated handlers thin.
- NautilusTrader: deterministic/event-driven state, persistence/reconciliation and mode consistency where useful.
- Freqtrade: explicit dry/forward discipline, closed-candle/no-lookahead testing and small health/operator surfaces.
- vectorbt: powerful vectorized research, but event-driven/causal execution semantics remain the reference for runtime behavior.
- GitHub Actions: new DAX-BOT 1.x product workflow uses current v7 action lines rather than intentionally inheriting the older Node-runtime warnings of the legacy workflow.

External frameworks, generic multi-asset abstractions, venue complexity and large portfolio layers are not imported merely because they exist.

## 12. Promotion architecture
The high-level path remains:

`DATA INTEGRITY -> FROZEN REFERENCE -> RESEARCH LAB -> ROBUST OOS / MULTIPLE-TESTING CHECKS -> REAL-DATA SHADOW -> DAX-BOT 1.x DUAL_COMPARE -> PAPER -> POSSIBLE LIVE`

PAPER and LIVE are future states, not current permissions.

The economic objective remains a systematic DAX daytrading bot that can eventually earn money under robust real-world conditions. Profitability is currently NOT proven. Starting-capital discussions around roughly EUR 1,000–2,000 are planning context only and are not live-trading authorization.

## 13. Source precedence
For active facts, prefer in this order:
1. repository code/contracts and canonical active-reference artifacts at the exact commit under discussion;
2. audited data manifests / hashed evidence files;
3. fresh runtime telemetry for runtime status;
4. current passing CI and specific audit documents;
5. this consolidated handover document;
6. older legacy prose/documents only for provenance.

If older prose conflicts with canonical evidence, preserve the legacy record but use the canonical active evidence for current work.

## 14. Recurring 500-step full-project audit — BINDING
A full-project hygiene and integrity audit must be performed at least once every 500 numbered project steps, and may be triggered earlier after major architecture, data, database, recovery or research changes.

Step 2000 audit: COMPLETED. Durable result: `docs/DAX_BOT_1X_MIGRATION_BACKLOG_STEP_2000.md`.
Next mandatory full audit: Step 2500.

The audit is a stop/go governance gate. It must cover identity/entities, searchability, code↔test↔registry mapping, reference integrity, data/database integrity, duplication/stale/dead paths, runtime/recovery/safety, performance/simplification and a selected public-project comparison.

Each audit ends with material findings classified using `VERIFIED`, `FIX REQUIRED`, `STALE`, `DUPLICATE`, or `UNVERIFIED` and a remediation decision where applicable.

Consolidation is compatibility-first, not deletion-first.

## 15. Continuous visible-work rule — BINDING
Begun step sequences are continued independently and visibly. Intermediate reports exist for visibility and are not stopping points.

Normal positive checks, ordinary intermediate results and completion of a sub-check do not stop the sequence. Work stops only when:
- a genuine milestone has been reached;
- a concrete user input/action or user decision is required;
- a hard technical error prevents reliable continuation;
- a safety-relevant finding requires a stop.

If no user action is required, work continues automatically with the next numbered step.

There is no invisible background work. If work stops, the stop and its exact reason must be stated explicitly so the user never has to assume that work continues after the last assistant message.

After context/tool-view loss, resume deterministically: pin repository SHA/branch, reconcile open PR/current CI, refresh runtime telemetry when making current-runtime claims, reload the necessary small repository subtrees/files, reconstruct the last VERIFIED numbered step and only then continue.

## 16. Immediate next milestones after Step 2019 refresh
- bind the implemented CAND-001 pure pipeline into `DUAL_COMPARE` without creating a second strategy architecture and without changing the authoritative provider prematurely;
- define an explicit simulation-only sizing/risk policy before mapping a candidate trade to the existing `ExecutionIntent` contract;
- reuse the existing Paper/virtual lifecycle only after its contracts are inspected and acceptance tests preserve `execution_capability=NONE` / `order_execution_enabled=false`;
- connect CAND-001 read-only to real closed MT5 SHADOW bars only after DUAL_COMPARE/replay parity is proven;
- modernize the web data contract so the existing UI shell consumes stable evidence plus a fresh read-only OperatorSnapshot source without browser credentials or GitHub-as-runtime-relay;
- continue benchmark evidence across materially changed 1.x generations and introduce a regression budget only after comparable repeated observations exist;
- continue regular public-project delta scans focused on performance, state/recovery, reconciliation, event-driven design, operator surfaces and version/migration governance;
- use `LEGACY / DUAL_COMPARE / BOT_1X` for incremental component migration rather than a big-bang cutover;
- keep PAPER and LIVE blocked until explicit later acceptance gates and user authorization.