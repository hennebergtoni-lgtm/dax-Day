# MASTERSTAND — DAX Daytrading Bot

Updated: 2026-09-10

This document is the durable project handover/source-of-truth. New work must preserve verified findings and must keep VERIFIED / IMPLEMENTED / RESEARCH / PLANNED / UNVERIFIED states separate.

## 1. Repository and recovery anchors
- Repository: `hennebergtoni-lgtm/dax-Day`, default branch `main`.
- Verified 2026-09-10 handoff anchor before the forward-degradation work: `ff38849978112ca25cec91aa5246cfa56bbed30c` (merge of PR #67).
- PR #68 added the descriptive backtest→forward degradation layer and passed PR CI plus the full `main` push CI.
- PR #69 binds that degradation layer to the canonical V11.2 active-reference identity; its PR CI passed before merge.
- Historical anchors remain valid recovery points even after newer `main` commits are created.

## 2. Immutable V11.2 active reference — VERIFIED
V11.2 remains unchanged and frozen. New hypotheses, filters, diagnostics or forward evidence never silently become the bot.

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
The research layer now includes Git-based predeclaration/chronology, multiple-testing preflight, statistics readiness, classical DSR, CSCV/PBO research, K_eff diagnostics, SPA using the established `arch.bootstrap.SPA` implementation, block-length diagnostics, filter efficiency/ablation, filter overlap, backward elimination, Pareto diagnostics and simulated EUR-cash analysis.

These methods reduce the risk of fooling ourselves with backtests. DSR, PBO, K_eff, SPA or any other robustness statistic is not proof of profitability and does not create edge.

Current filter doctrine: do not accumulate filters merely because they look plausible. A filter must be shown to activate, remove trades in a meaningful way, improve relevant R/Cash/DD evidence where claimed, and be checked for redundancy/overlap with other filters.

Research families and tools — Bollinger, Fibonacci, close gaps, ATR/ATR25, liquidity sweeps, momentum, volatility, TWAP/anchored price, CPR, macro events, session filters, stop/trailing variants and related ideas — remain research unless explicitly promoted through the governed process.

Decision architecture remains:
`REGIME -> STRUCTURE -> ENTRY`.

## 4. Forward evidence — SHADOW only
The forward layer contains per-window SHADOW performance, rolling summaries, positive/negative window streak diagnostics and an explicit Forward Stability Gate.

The stability gate:
- requires explicit caller thresholds;
- has no invented default promotion limits;
- has no automatic promotion;
- is `research_only=true`;
- preserves `execution_capability=NONE`;
- preserves `order_execution_enabled=false`.

Backtest→forward degradation is a descriptive diagnostic built on this same forward architecture, not a parallel strategy architecture. It compares normalized historical OOS expectations with forward SHADOW evidence and deliberately has no composite score or automatic pass/fail promotion rule. The canonical V11.2 helper is bound to the active-reference source identity, repository blob identity, audited session fingerprint and engine SHA.

Forward cash curves remain simulated. Broker balances are not treated as research capital.

## 5. Execution authorization — BINDING
- SHADOW: AUTHORIZED.
- PAPER: NOT AUTHORIZED.
- LIVE: NOT AUTHORIZED.
- `execution_capability=NONE`.
- `order_execution_enabled=false`.

No code, research result, stability/degradation metric or CI result changes this authorization. PAPER or LIVE requires an explicit later user decision.

## 6. MT5 / Windows host state
VERIFIED:
- Windows MT5 Python IPC/bridge works.
- DE40 is detected.
- `trade_mode=0`, digits=2, point=0.01, contract size=1, profit currency EUR.
- Current MetaQuotes demo DE40 is suitable for read-only/SHADOW work, not assumed tradeable.

UNVERIFIED / OPEN:
- Actual MT5 broker/server timezone relative to `Europe/Berlin` remains an open gate.
- Windows-specific runtime paths are not VERIFIED merely because code/CI exists; host behavior must be tested on the Windows machine.

Windows host operating rule: exactly one concrete PowerShell/host command at a time; inspect the returned result before issuing the next command.

## 7. Runtime / reliability architecture
Repository infrastructure includes substantial support for Windows autostart, single-instance locking, heartbeat history, resume, cross-cycle integrity, gap diagnostics and forward-evidence handling. Treat a Windows-specific behavior as VERIFIED only after host execution evidence.

Research execution should avoid blind 12–14-hour grids. Prefer FAST screening, targeted stages, checkpoints/resume and efficient/vectorized evaluation where scientifically appropriate.

## 8. Open-source research doctrine
Public/open-source research remains part of development. Relevant projects/methods include LEAN, NautilusTrader, vectorbt, Freqtrade, VN.PY, purged cross-validation implementations, RiskLabAI, ml4t/diagnostic, `arch` and related projects.

Do not copy external systems blindly. Reuse established, tested methods when they solve a defined need better than inventing a private replacement; `arch.bootstrap.SPA` is an example.

## 9. Promotion architecture
The high-level path remains:

`DATA INTEGRITY -> FROZEN BASELINE -> RESEARCH LAB -> ROBUST OOS / MULTIPLE-TESTING CHECKS -> SHADOW -> PAPER -> POSSIBLE LIVE`

PAPER and LIVE stages are future states, not current permissions.

The economic objective remains a systematic DAX daytrading bot that can eventually earn money under robust real-world conditions. Profitability is currently NOT proven. Starting-capital discussions around roughly EUR 1,000–2,000 are planning context only and are not live-trading authorization.

## 10. Source precedence
For active V11.2 facts, prefer in this order:
1. `research/V112_REFERENCE_V1/reference_result.json`
2. `data/manifests/dax_m5_2014_2019_audited.json` for audited data identity
3. current passing CI and specific audit documents
4. this consolidated handover document
5. older legacy prose/documents only for provenance

If older prose conflicts with the canonical active-reference artifact, do not rewrite scientific history to make the documents look consistent: preserve the legacy record and use the active reference for current work.

## 11. Recurring 500-step full-project audit — BINDING
In addition to normal per-change tests and intermediate checks, a full-project hygiene and integrity audit must be performed at least once every 500 numbered project steps, and may be triggered earlier after major architecture, data, database, recovery or research changes.

The audit is a stop/go governance gate, not a cosmetic review. If a material contradiction, stale truth source, ambiguous entity, broken provenance chain or unsafe runtime/data path is found, the relevant issue must be corrected and re-verified before the next major development block continues.

The recurring audit must cover:
- **Identity / entities:** modules, tests, research artifacts, datasets, evidence objects and runtime components have unambiguous names and ownership; parallel objects with effectively identical meaning are detected.
- **Searchability:** canonical project objects must be reliably discoverable using expected repository search terms, filenames, registries and ledgers; search/index limitations must not be mistaken for missing implementation.
- **Code ↔ test ↔ registry mapping:** relevant implementations are mapped to their tests and registry/ledger entries; stale tests or fixtures expecting historical values are identified explicitly.
- **Reference integrity:** frozen V11.2 values, engine/data fingerprints and other VERIFIED constants are reconciled against tests, fixtures, manifests and documentation without rewriting legacy scientific history.
- **Data/database integrity:** migrations, schemas, keys, provenance, fingerprints, import/restore paths, evidence rows and backup/recovery assumptions are checked for consistency and recoverability.
- **Duplication / stale / dead paths:** overlapping implementations, superseded scripts, stale configs, duplicate truth stores and dead code are reviewed using compatibility-first migration; nothing is deleted solely because it appears unused.
- **Runtime / recovery / safety:** fail-closed behavior, checkpoints, restart/resume, reconciliation, stale-data handling, write boundaries and `execution_capability=NONE` / `order_execution_enabled=false` invariants are checked.
- **Performance / simplification:** redundant work, repeated expensive checks, avoidable long-running paths and unnecessary complexity are identified, while safety/provenance checks are not removed merely for speed.
- **Public-project comparison:** selected mature open-source systems may be reviewed for proven architecture, recovery, data-integrity and testing patterns, but external designs do not override project evidence or create new work without a defined need.

Each full audit must end with an explicit classification of material findings using `VERIFIED`, `FIX REQUIRED`, `STALE`, `DUPLICATE`, or `UNVERIFIED`, plus a short remediation decision where applicable. The audit result itself becomes durable project evidence.

The existing architecture-hygiene safety principle remains binding: consolidation is compatibility-first, not deletion-first, and one canonical truth source may be protected by multiple boundary-specific assertions.
