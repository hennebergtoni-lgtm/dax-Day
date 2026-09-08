# Current Readiness Snapshot — 2026-09-08

Status: **RESEARCH / REPLAY FOUNDATION GREEN; DATASET SESSION HASH VERIFIED; CLEAN FULL-REFERENCE REPRODUCTION VERIFIED; PAPER NOT READY**

This is a dated operator snapshot, not a mutable strategy rule and not an automatic promotion decision.

## Current health

| Surface | State | Evidence / reason |
|---|---|---|
| Frozen V11.2 active reference | GREEN | `V112_REFERENCE_V1` remains unchanged: 856 OOS trades, -31.309210619787684 R normal, 37 positive / 44 negative WF. |
| Exact candidate engine contract | GREEN | Embedded source SHA-256 remains `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`. |
| Oracle engine contract | GREEN | Oracle source SHA-256 remains `62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f`. |
| Technical historical↔replay fixture parity | GREEN | Guarded replay smoke passes CI using the same exact V11.2 engine surface. |
| Deterministic/safety runtime tests | GREEN | Current test suite covers recovery/readiness, causality, data-quality and failure-injection surfaces. |
| Neon connection / migrations / integrity | GREEN | CI/Neon gate remains fail-closed; active reference remains VERIFIED; productive clean detailed rows remain NOT_IMPORTED. |
| Recovered 2014–2019 Drive source structure | GREEN | `GER30_5m.csv` reproduces 481,824 raw rows; 1,673 Berlin-session days; 172,319 session M5 rows; 103 bars/day; 0 OHLC errors. |
| Frozen historical dataset session identity | GREEN / HASH_VERIFIED | Evidence-equivalent historical normalization reproduces frozen session SHA-256 `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2` exactly. |
| Original audited ZIP container | YELLOW / UNOBSERVED | The original archive with frozen ZIP SHA-256 `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870` has not been re-observed. This does not invalidate the HASH_VERIFIED normalized session surface, but remains a separate provenance limitation. |
| Full 2014–2019 clean-reference reproduction | GREEN / VERIFIED | Canonical rolling-fixed 45/20/20 runner reproduced all 81 WF and the active aggregate exactly: 856 trades, -31.309210619787684 R normal, 37 positive / 44 negative WF. |
| Clean 243 WF metrics | GREEN / REPRODUCED | Frozen SHA-256 `4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a` reproduced exactly. Productive DB remains NOT_IMPORTED pending importer drill. |
| Clean 81 selected variants | GREEN / REPRODUCED | Frozen SHA-256 `8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e` reproduced exactly. Productive DB remains NOT_IMPORTED pending importer drill. |
| Clean 856 normal OOS trades | GREEN / REPRODUCIBLE EVIDENCE | New deterministic SHA-256 `f60bb5fc15b5e620a37ca44bdb5bdcea20381261c06d40cb78aba34387f56023`; no historical frozen trade-file hash existed, so this is not claimed as historical file identity. Productive DB remains NOT_IMPORTED. |
| Research accelerator | GREEN / RESEARCH-ONLY | NumPy signal harness matched 960 sampled exact signal cases with 0 mismatches and reproduced the complete frozen WF/detail evidence; it does not modify or promote V11.2. |
| Recovery / DB reconstruction | GREEN | Recovery preflight, persistent bundles and isolated database restore drill are implemented and tested. Recovery ZIP for clean-reference evidence is also retained in Drive. |
| Architecture hygiene | GREEN / CONTROLLED | No broad refactor warranted. One real duplication candidate exists in runtime recovery bundles; consolidation is compatibility-first, not deletion-first. |
| Shadow | NOT STARTED | Not automatically started from replay/research success. |
| Paper | NOT READY | Requires an explicit prospective promotion decision, execution-boundary verification and remaining provenance/readiness review. |
| Live | NOT ELIGIBLE | No direct path; requires separate promotion after Replay → Shadow → Paper. |

## Current operator decision

**DO NOT START PAPER OR LIVE.**

The clean historical reference and detail evidence are now reproducible. The next phase returns to controlled Research Lab work and remaining prospective-readiness engineering; this is not an automatic bot promotion.

## Binding start rule

When all material Paper-readiness blockers are cleared, stop before initiating Paper/Bot execution and present the readiness evidence to the user. No automatic start is permitted.

## Research status

- BB001: RESEARCH; causal prior-bar logic retained; diagnostic/data-derived thresholds are not deployable proof.
- FIB001: RESEARCH ONLY; causal impulse required; no hindsight swing anchoring.
- GAP001: RESEARCH ONLY; opening gap distinct from intraday FVG.
- FAIL001: RESEARCH CONTRACT; failures create hypotheses, not immediate filters.
- BOOST001: RESEARCH ONLY; bounded sleeve concept, never martingale/revenge sizing.
- filter registry: research filters are visible-only and cannot be live-switchable.

## Next highest-value work

1. Finish V5 stop-gate and preserve the exact reproduction evidence as the clean baseline.
2. Build the detail importer only through typed validation, idempotency, rollback and isolated-schema reconciliation before any productive DB import.
3. Consolidate the duplicate runtime recovery implementations only through compatibility tests; no deletion-first cleanup.
4. Return to isolated Research Lab families (BB/FIB/GAP/ATR/liquidity/session/structure) using the verified accelerator only under exact/parity control.
5. Continue Web UI as read-only observability; it must never become a second source of strategy or reference truth.
