# Current Readiness Snapshot — 2026-09-08

Status: **RESEARCH / REPLAY FOUNDATION GREEN; DATASET SESSION HASH VERIFIED; CLEAN FULL-REFERENCE REPLAY ELIGIBLE; PAPER NOT READY**

This is a dated operator snapshot, not a mutable strategy rule and not an automatic promotion decision.

## Current health

| Surface | State | Evidence / reason |
|---|---|---|
| Frozen V11.2 active reference | GREEN | `V112_REFERENCE_V1` remains unchanged: 856 OOS trades, -31.309210619787684 R normal, 37 positive / 44 negative WF. |
| Exact candidate engine contract | GREEN | Embedded source SHA-256 remains `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`. |
| Oracle engine contract | GREEN | Oracle source SHA-256 remains `62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f`. |
| Technical historical↔replay fixture parity | GREEN | Guarded replay smoke passes CI using the same exact V11.2 engine surface. |
| Deterministic/safety runtime tests | GREEN | Current test suite covers recovery/readiness, causality, data-quality and failure-injection surfaces. |
| Neon connection / migrations / integrity | GREEN | Last fully completed CI/Neon gate before the current readiness edits passed. Active reference remains VERIFIED; clean detailed rows remain NOT_IMPORTED. |
| Recovered 2014–2019 Drive source structure | GREEN | `GER30_5m.csv` reproduces 481,824 raw rows; 1,673 Berlin-session days; 172,319 session M5 rows; 103 bars/day; 0 OHLC errors. |
| Frozen historical dataset session identity | GREEN / HASH_VERIFIED | Evidence-equivalent historical normalization reproduces frozen session SHA-256 `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2` exactly. |
| Original audited ZIP container | YELLOW / UNOBSERVED | The original archive with frozen ZIP SHA-256 `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870` has not been re-observed. This no longer blocks Clean Reference Replay because the normalized session surface is HASH_VERIFIED, but it remains a Paper provenance blocker. |
| Full 2014–2019 clean-reference replay | ELIGIBLE / NOT YET VERIFIED | Data, engine, database and technical replay prerequisites can now reach the guarded clean-reference replay gate; full 81-WF reconciliation is the next evidence-producing step. |
| Clean detailed 243 WF metrics / 81 selections / 856 trade rows | BLOCKED | Original clean-reference detail source artifacts have not been independently recovered; legacy detail may not substitute. |
| Shadow | NOT STARTED | Promotion sequence requires clean full-reference replay closure first. |
| Paper | NOT READY | Requires full-reference replay verification, execution-boundary verification and retained provenance gate. |
| Live | NOT ELIGIBLE | No direct path; requires separate promotion after Replay → Shadow → Paper. |

## Current operator decision

**DO NOT START PAPER OR LIVE.**

The project is now technically eligible to execute the guarded full clean-reference replay. That replay is research/reconciliation evidence, not a Paper or Live start.

## Binding start rule

When all material Paper-readiness blockers are cleared, stop before initiating Paper/Bot execution and present the readiness evidence to the user. No automatic start is permitted.

## Research status

- BB001: RESEARCH; causal prior-bar logic retained; diagnostic/data-derived thresholds are not deployable proof.
- FIB001: RESEARCH ONLY; causal impulse required; no hindsight swing anchoring.
- GAP001: RESEARCH ONLY; opening gap distinct from intraday FVG.
- FAIL001: RESEARCH CONTRACT; failures create hypotheses, not immediate filters.
- BOOST001: RESEARCH ONLY; bounded sleeve concept, never martingale/revenge sizing.
- filter registry: research filters are visible-only and cannot be live-switchable.

## Next highest-value blockers

1. Run and reconcile guarded full 2014–2019 V11.2 Clean Reference Replay against the frozen active-reference aggregate.
2. Keep original ZIP-container identity separate from session OHLC identity; do not downgrade the latter now that the session fingerprint is reproduced.
3. Preserve clean-reference detailed-row import as blocked until genuine source or reproducibly regenerated clean detail artifacts exist.
4. Continue database/evidence-integrity hardening before any prospective promotion stage.
5. Continue isolated research families only under RESEARCH status; no promotion leakage.
