# Current Readiness Snapshot — 2026-09-08

Status: **RESEARCH / REPLAY FOUNDATION GREEN; CLEAN FULL-REFERENCE REPLAY BLOCKED; PAPER NOT READY**

This is a dated operator snapshot, not a mutable strategy rule and not an automatic promotion decision.

## Current health

| Surface | State | Evidence / reason |
|---|---|---|
| Frozen V11.2 active reference | GREEN | `V112_REFERENCE_V1` remains unchanged: 856 OOS trades, -31.309210619787684 R normal, 37 positive / 44 negative WF. |
| Exact candidate engine contract | GREEN | Embedded source SHA-256 remains `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`. |
| Oracle engine contract | GREEN | Oracle source SHA-256 remains `62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f`. |
| Technical historical↔replay fixture parity | GREEN | Guarded replay smoke passes CI using the same exact V11.2 engine surface. |
| Deterministic/safety runtime tests | GREEN | Current test suite passes including recovery/readiness, causality, data-quality and failure-injection surfaces already committed. |
| Neon connection / migrations / integrity | GREEN | CI #159 passed connection, migrations and Neon integrity gates. Active reference remains VERIFIED; clean detailed rows remain NOT_IMPORTED. |
| Recovered 2014–2019 Drive source structure | YELLOW | `GER30_5m.csv` reproduces 481,824 raw rows; 1,673 Berlin-session days; 172,319 session M5 rows; 103 bars/day; 0 OHLC errors. |
| Frozen historical dataset identity | YELLOW | Structural match is verified but the frozen `e51b...` session fingerprint / audited ZIP identity has not been reproduced with the original historical hash method. |
| Full 2014–2019 clean-reference replay | BLOCKED | Readiness gate requires hash-verified dataset identity and full-reference reconciliation. |
| Clean detailed 243 WF metrics / 81 selections / 856 trade rows | BLOCKED | Original clean-reference detail source artifacts have not been independently recovered; legacy detail may not substitute. |
| Shadow | NOT STARTED | Promotion sequence requires clean replay closure first. |
| Paper | NOT READY | Full-reference replay/data identity and execution-boundary gates are not yet complete. |
| Live | NOT ELIGIBLE | No direct path; requires separate promotion after Replay → Shadow → Paper. |

## Current operator decision

**DO NOT START PAPER OR LIVE.**

The project is technically healthy for continued research, fixture replay, architecture work, guarded recovery work and non-promotional diagnostics. It is not yet justified to start the real bot/paper process.

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

1. Continue targeted search for exact audited data/bundle identity without accepting substitute datasets.
2. Keep `HASH_METHOD_UNRESOLVED` explicit if exact identity cannot be recovered.
3. Prepare a guarded full-reference replay runner that cannot mislabel structural-only data as clean-reference evidence.
4. Preserve clean-reference detailed-row import as blocked until genuine source/reproducible clean output exists.
5. Continue isolated research families only under RESEARCH status; no promotion leakage.
