# V4 BLOCK STATUS — 2026-09-08

Status: CONSOLIDATED EVIDENCE SNAPSHOT

## VERIFIED
- Frozen V11.2 active reference remains unchanged: normal 856 OOS trades, -31.309210619787684 R, 37 positive / 44 negative WFs.
- Recovered 2014–2019 session dataset is HASH_VERIFIED against frozen SHA-256 `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`.
- Historical fingerprint method is recovered and versioned.
- Exact engine/oracle hash contracts remain frozen.
- Technical historical/replay fixture parity is green.
- Neon migrations/integrity are green through migration 0004.
- Detail evidence registry truthfully reports clean detail as NOT_IMPORTED.
- Runtime fail-closed safety, Berlin/DST handling and causal/no-lookahead foundations remain tested.

## IMPLEMENTED
- Versioned dataset fingerprint method contract.
- Recovery identity gate STRUCTURAL_MATCH / HASH_VERIFIED / MISMATCH.
- Clean Reference Replay may use evidence-equivalent HASH_VERIFIED recovered session data without requiring the original ZIP container.
- Paper retains stricter provenance/readiness prerequisites.
- Detail evidence registry with NOT_IMPORTED / PARTIAL / VERIFIED and DB-level verification constraints.
- Run manifests fingerprint dataset, engine, config and mode.
- Decision-log manifests include TRADE and NO_TRADE records.
- Drift aborts for dataset, engine, config and mode identity.
- Replay checkpoint provenance prevents mixed-configuration resume.
- Session-aware sequence classification prevents false overnight gaps while retaining true intraday gap detection.
- Shadow/Paper acceptance and execution-boundary contract.
- Public donor map and license-aware reuse rules.
- Promotion Evidence Contract V2.

## RESEARCH
- BB001: highest next-test value; next valid test requires ex-ante/train-only thresholds and exact OOS/WF evidence.
- GAP001: second priority; objectively timestamped opening-gap base test before interactions.
- FIB001: causal impulse-only; hindsight swing selection forbidden.
- FAIL001: high diagnostic/safety value after legitimate clean replay details exist; not direct alpha evidence.
- EVENT001: lower immediate priority pending timestamp/provenance gate.
- BOOST001 remains RESEARCH_ONLY and cannot bypass standard risk/promotion controls.

## BLOCKED / NOT YET VERIFIED
- Full 2014–2019, 81-window Clean Reference reconciliation against the frozen 856-trade active-reference aggregate has not yet been executed and verified in the new guarded path.
- Original audited ZIP with frozen SHA-256 `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870` has not been re-observed.
- Original clean detailed artifacts (243 WF metrics / 81 selections / 856 trades) remain NOT_IMPORTED; no synthetic substitute is permitted.
- Trade-detail expected source hash is intentionally unknown/NULL, preventing false VERIFIED status.
- Shadow has not started.
- Execution adapter is defined as a boundary contract but not implemented/verified for Paper.
- Paper is NOT READY.
- Live is NOT ELIGIBLE.

## DATABASE
- migrations: 0001–0004.
- active V11.2 registry remains frozen and verified.
- clean detail registry explicitly represents absence rather than fabricating rows.
- future VERIFIED detail import requires clean evidence class, exact rows/hash, source artifact, matching dataset/engine provenance and verified timestamp.

## REPLAY / OPERATIONS
The project now has the technical contracts needed to make a full historical reconciliation reproducible and fail-closed: run identity, decision identity, restart/resume identity, session sequencing and safety blockers. This engineering readiness is not itself proof that the 81-WF active-reference result has been reproduced.

## PUBLIC INTELLIGENCE
- NautilusTrader: LGPL-3.0 architecture donor.
- QuantConnect Lean: Apache-2.0 architecture donor.
- vectorbt: Apache-2.0 + Commons Clause; idea/research ergonomics donor only, no code reuse planned.
- prior audited donors retain their existing license/evidence classifications.
- no external repository is accepted as DAX performance evidence.

## V4 decision
V4 materially improves provenance, database truthfulness, replay determinism and prospective-mode discipline. The historical dataset identity blocker is closed at the normalized session level. The next major scientific gate is the actual full 81-window Clean Reference reconciliation.

**DO NOT START PAPER OR LIVE.**

The user STOP-GATE remains binding: if prospective Paper/Bot readiness becomes justified later, stop and present the complete evidence before any start action.
