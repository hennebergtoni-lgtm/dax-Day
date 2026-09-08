# NEXT 50 MILESTONES V4

Status: ACTIVE ROADMAP — 2026-09-08

Purpose: continue from the evidence-bounded V3 closeout. This block prioritizes provenance closure, replay/paper readiness architecture, empirical research hygiene, database truthfulness, public-project intelligence, and operator safety without modifying frozen V11.2.

Binding rules:
- V11.2 remains immutable active reference.
- VERIFIED / IMPLEMENTED / RESEARCH / LEGACY / BLOCKED / UNVERIFIED remain separate.
- Structural data equivalence is not hash identity.
- No synthetic clean-reference rows.
- Public projects/papers are idea or architecture donors only; no DAX evidence substitution.
- License must be checked before code reuse; independent reimplementation is preferred when uncertain.
- DATA UNSAFE => NO_TRADE; hard safety is not UI-overridable.
- FAST is screening only; exact engine remains promotion surface.
- No Paper/Live start is automatic.
- STOP BEFORE BOT/PAPER START: if readiness becomes justified, stop and present evidence to the user before any start action.

## A. V3 closeout and provenance re-open
1. [DONE] Verify V3 final HEAD and final CI rather than relying on the earlier CI #165 statement.
2. [DONE] Confirm final V3 HEAD `d1791e23632b0d40c97d95bc5b0e37bbf48a9734` has CI #167 SUCCESS.
3. [NEXT] Re-read frozen active-reference and recovery manifests before new writes.
4. [NEXT] Re-check Neon active-reference registry/integrity on V4 start.
5. [DONE] Re-search Drive for exact audited bundle name/hash identifiers.
6. [DONE] Re-open known recovered cache folder and inventory likely historical result subfolders.
7. [DONE] Search Drive for methodology-audit V3.5.4 evidence and WF81 recovery folders.
8. [NEXT] Extract every recoverable provenance clue from historical audit/log artifacts without upgrading evidence class.
9. [NEXT] Search old notebooks/logs for the exact historical dataset fingerprint serialization code/path.
10. [NEXT] Search old notebooks/logs for the exact ZIP creation path/name and archive method.
11. [NEXT] Define a canonical fingerprint-method registry with method version, columns, ordering, timezone and serialization.
12. [NEXT] Add negative tests proving different serialization cannot accidentally be called HASH_VERIFIED.
13. [NEXT] Add provenance-chain representation from source file -> normalization -> session slice -> fingerprint -> reference run.
14. [NEXT] Add machine-readable blocker reason for HASH_METHOD_UNRESOLVED.
15. [NEXT] Re-run CI/Neon after provenance changes.

## B. Database and evidence integrity
16. [NEXT] Re-audit Neon schema against current evidence classes and active-reference registry.
17. [NEXT] Verify no legacy/research artifact can be marked active reference by schema/import path.
18. [NEXT] Add source-artifact provenance fields/contract where missing.
19. [NEXT] Add deterministic source-row IDs to any future clean detail import path.
20. [NEXT] Add transaction/rollback test for failed detail import reconciliation.
21. [NEXT] Add duplicate/re-import idempotency regression test.
22. [NEXT] Add expected row-count/hash reconciliation for WF metrics, selections and trades.
23. [NEXT] Add explicit NOT_IMPORTED / PARTIAL / VERIFIED detail-state contract if not already sufficient.
24. [NEXT] Add operator-readable DB evidence-health summary.
25. [NEXT] Re-run Neon migrations/integrity and verify frozen active reference unchanged.

## C. Replay, shadow and paper-readiness engineering
26. [NEXT] Re-audit guarded full-reference runner against current readiness contract.
27. [NEXT] Add explicit run manifest containing dataset/engine/config fingerprints and mode.
28. [NEXT] Add deterministic decision-log manifest including NO_TRADE records.
29. [NEXT] Add replay abort-on-reference-drift test.
30. [NEXT] Add replay abort-on-dataset-identity downgrade test.
31. [NEXT] Add replay abort-on-engine/config fingerprint mismatch test.
32. [NEXT] Add sequence tests for duplicate/out-of-order/late bars across session boundaries.
33. [NEXT] Add market-session open/close edge-case tests including DST weeks.
34. [NEXT] Add restart/resume determinism contract for replay.
35. [NEXT] Add checkpoint provenance so resumed replay cannot mix configurations.
36. [NEXT] Define SHADOW mode acceptance criteria without starting Shadow.
37. [NEXT] Define PAPER mode execution-boundary contract without broker integration.
38. [NEXT] Define broker/execution adapter interface separately from strategy/decision core.
39. [NEXT] Define paper fill model and execution-degradation telemetry requirements.
40. [NEXT] Re-evaluate Paper readiness; if not justified, remain blocked and continue research.

## D. Research intelligence and controlled advancement
41. [NEXT] Refresh public architecture/backtesting/replay project scan for useful current ideas and licenses.
42. [NEXT] Refresh public DAX/ORB/multi-timeframe/filter research scan; classify claim vs evidence vs reusable engineering pattern.
43. [NEXT] Audit whether any public donor introduces lookahead/repainting/selection-bias risk before adopting ideas.
44. [NEXT] Build a compact donor-to-project mapping: DATA / REPLAY / RISK / RESEARCH / UI / OPERATIONS.
45. [NEXT] Re-rank BB001, FIB001, GAP001, FAIL001 and EVENT001 by evidence quality and next-test value.
46. [NEXT] Define next targeted non-combinatorial experiments that can run on structural data only as RESEARCH, with no promotion claim.
47. [NEXT] Strengthen prospective-validation contract for any future promotion candidate.
48. [NEXT] Define neighborhood/stability minimum evidence and trade-count sufficiency rules without optimizing to a fixed trade count.
49. [NEXT] Produce V4 consolidated status with VERIFIED / IMPLEMENTED / RESEARCH / BLOCKED and explicit database/replay/public-intelligence sections.
50. [STOP GATE] If Paper/Bot start is genuinely justified, STOP and present readiness evidence before any start. Otherwise close V4 as evidence allows and open the next block without initiating Paper/Live.

## Immediate stop conditions
- active-reference drift;
- dataset/hash identity misrepresented as clean evidence;
- engine/oracle/config fingerprint mismatch;
- DB migration/integrity/reconciliation failure;
- replay non-determinism;
- lookahead or same-bar causality violation;
- unexplained row/trade-count change;
- legacy/research evidence promoted as clean evidence;
- Paper/Live reachable without explicit readiness and user stop gate.
