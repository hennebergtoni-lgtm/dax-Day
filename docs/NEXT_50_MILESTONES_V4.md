# NEXT 50 MILESTONES V4

Status: CLOSED EVIDENCE-BOUNDED ROADMAP — 2026-09-08

Purpose: continue from the evidence-bounded V3 closeout. This block prioritized provenance closure, replay/paper readiness architecture, empirical research hygiene, database truthfulness, public-project intelligence, and operator safety without modifying frozen V11.2.

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
3. [DONE] Re-read frozen active-reference and recovery manifests before new writes.
4. [DONE] Re-check Neon active-reference registry/integrity on V4 start.
5. [DONE] Re-search Drive for exact audited bundle name/hash identifiers.
6. [DONE] Re-open known recovered cache folder and inventory likely historical result subfolders.
7. [DONE] Search Drive for methodology-audit V3.5.4 evidence and WF81 recovery folders.
8. [DONE] Extract recoverable provenance clues from historical audit/log artifacts without upgrading evidence prematurely.
9. [DONE] Recover the exact historical dataset fingerprint serialization code/path from Git history.
10. [PARTIAL] Original ZIP container/path was not recovered; frozen ZIP SHA remains separately unobserved.
11. [DONE] Define canonical fingerprint method registry with version, columns, index encoding and serialization.
12. [DONE] Add negative tests proving unknown/different fingerprint methods cannot be called HASH_VERIFIED.
13. [DONE] Reconstruct and document source -> normalization -> Berlin session mask -> UTC index -> fingerprint provenance chain.
14. [DONE / SUPERSEDED] `HASH_METHOD_UNRESOLVED` blocker retired after method recovery; session identity subsequently became HASH_VERIFIED.
15. [DONE] Re-run CI/Neon after provenance changes.

## B. Database and evidence integrity
16. [DONE] Re-audit Neon schema against current evidence classes and active-reference registry.
17. [DONE] Preserve separation between legacy/research evidence and frozen active reference through import/readiness contracts.
18. [DONE] Source-artifact provenance contract retained and detail registry adds dataset/engine/source linkage.
19. [DONE] Deterministic source-row IDs exist for future clean detail imports.
20. [PARTIAL] Pre/post reconciliation failure tests exist, but a full PostgreSQL transaction/rollback integration test for a failed detail import is still future work.
21. [DONE] Deterministic source-row identity plus uniqueness/reconciliation rules provide idempotency guardrails; production detail importer remains unimplemented until genuine detail exists.
22. [DONE] Expected row/hash reconciliation is encoded for WF metrics and selections; trades remain intentionally blocked because expected trade-source hash is not recovered.
23. [DONE] DB migration 0004 adds explicit NOT_IMPORTED / PARTIAL / VERIFIED detail-state contract with DB-level VERIFIED constraints.
24. [DONE] Operator-readable DB integrity output reports migrations, active reference and detail-import state.
25. [DONE] Neon migration 0004/integrity passed; frozen active reference unchanged.

## C. Replay, shadow and paper-readiness engineering
26. [DONE] Re-audit guarded full-reference runner against current readiness contract; HASH_VERIFIED recovered session representation is eligible for clean replay.
27. [DONE] Add explicit run manifest containing dataset/engine/config fingerprints and mode.
28. [DONE] Add deterministic decision-log manifest including NO_TRADE records.
29. [PARTIAL] Run-manifest drift is fail-closed; full active-reference aggregate reconciliation remains pending actual 81-WF execution.
30. [DONE] Dataset identity downgrade blocks clean-reference replay through readiness tests.
31. [DONE] Engine/config/mode fingerprint mismatches abort through run-manifest tests.
32. [DONE FOUNDATION] Duplicate/out-of-order/unsafe classifications already fail closed; session-aware sequence tests add true intraday gap versus expected overnight boundary behavior.
33. [DONE] Session open/day boundary and DST-week behavior tested with Europe/Berlin semantics.
34. [DONE CONTRACT] Restart/resume determinism contract implemented through run-manifest identity.
35. [DONE] Checkpoint provenance prevents resumed replay from mixing configurations/data/engine/mode identities.
36. [DONE CONTRACT] Define SHADOW mode acceptance criteria without starting Shadow.
37. [DONE CONTRACT] Define PAPER mode execution-boundary contract without broker integration.
38. [DONE CONTRACT] Define broker/execution adapter boundary separately from Decision Core.
39. [DONE CONTRACT] Define paper fill model and execution-degradation telemetry requirements.
40. [DONE DECISION] Paper readiness re-evaluated: NOT READY. Full clean replay, Shadow evidence and execution implementation remain prerequisites.

## D. Research intelligence and controlled advancement
41. [DONE] Refresh public architecture/backtesting/replay project scan and licenses, including NautilusTrader, Lean and vectorbt.
42. [DONE] Refresh ORB public scan; current ORB donor patterns classified as hypothesis/engineering context, not DAX evidence.
43. [DONE] Explicit lookahead/repainting/selection-bias quarantine rules documented for external donors.
44. [DONE] Compact donor-to-project mapping created for DATA / REPLAY / RISK / RESEARCH / UI / OPERATIONS.
45. [DONE] Re-rank next-test value: BB001 -> GAP001 -> FIB001 -> FAIL001 -> EVENT001.
46. [DONE] Define targeted non-combinatorial experiments for BB/GAP/FIB/FAIL/EVENT with no automatic promotion claim.
47. [DONE] Strengthen prospective-validation contract for future candidates.
48. [DONE] Define neighborhood/stability/concentration/trade-sufficiency evidence without optimizing to a fixed trade count.
49. [DONE] Produce V4 consolidated status with VERIFIED / IMPLEMENTED / RESEARCH / BLOCKED and DB/replay/public-intelligence sections.
50. [STOP GATE / NOT TRIGGERED] Paper/Bot start is not justified. V4 closes without initiating Shadow, Paper or Live. The next major scientific gate is the actual full 2014–2019, 81-window Clean Reference reconciliation against the frozen 856-trade active-reference aggregate.

## Immediate stop conditions retained
- active-reference drift;
- dataset/hash identity misrepresented as clean evidence;
- engine/oracle/config fingerprint mismatch;
- DB migration/integrity/reconciliation failure;
- replay non-determinism;
- lookahead or same-bar causality violation;
- unexplained row/trade-count change;
- legacy/research evidence promoted as clean evidence;
- Paper/Live reachable without explicit readiness and user stop gate.
