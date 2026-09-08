# NEXT 50 MILESTONES V3

Status: ACTIVE ROADMAP — 2026-09-08

Purpose: continue from the completed V2 milestone block without losing frozen V11.2 evidence, recovered-data provenance, research families or runtime safety architecture.

Binding rules:
- V11.2 remains the immutable active reference.
- LEGACY / RESEARCH / IMPLEMENTED / VERIFIED / BLOCKED remain separate statuses.
- Public/open-source material is IDEA/architecture input only until independently validated on DAX evidence.
- Structural data recovery is not equivalent to frozen hash identity.
- No synthetic reconstruction of clean-reference detail rows.
- No Paper/Live start is automatic.
- **STOP BEFORE BOT/PAPER START:** when technical/research readiness reaches the point where a real Paper/Bot start is justified, stop and present the readiness state to the user before any start action.

## A. Recovery and provenance closure
1. [DONE] Locate historical 2014–2019 Drive source candidate.
2. [DONE] Verify raw row count against manifest.
3. [DONE] Verify Berlin session row/day invariants.
4. [DONE] Verify OHLC structural integrity.
5. [DONE] Distinguish structural identity from historical fingerprint identity.
6. [DONE] Preserve recovered-source evidence in GitHub.
7. [DONE] Verify recovery commit through CI/Neon gates.
8. [DONE] Recover historical V3.5.4 parity-gate evidence.
9. [DONE] Recover legacy per-WF trade artifacts from V2.0/V2.6.
10. [DONE] Keep legacy detail separated from clean-reference detail.
11. [DONE] Record legacy-detail findings in clean-reference inventory.
12. [DONE] Add typed RecoveryIdentity contract.
13. [DONE] Map recovery identity into operator health.
14. [DONE] Extend clean replay/paper readiness with recovery identity.
15. [DONE] Add recovery/readiness tests.

## B. Repository and evidence integrity
16. [IN PROGRESS] Re-establish fully green CI after recovery/readiness changes.
17. [DONE] Re-audit public/open-source donor catalogue and licenses.
18. [DONE] Extend repo Open-Source Audit with later architecture donors.
19. [DONE] Freeze this V3 milestone roadmap and STOP-before-start rule.
20. [NEXT] Re-check current active-reference registry and DB integrity after V3 writes.
21. [NEXT] Confirm no clean-reference hashes/results changed during recovery work.
22. [NEXT] Re-check engine/oracle artifact SHA contracts.
23. [NEXT] Re-check fixture historical↔replay deterministic parity.
24. [NEXT] Add operator-readable current readiness snapshot/status report.
25. [NEXT] Verify status report fails closed when data identity is only STRUCTURAL_MATCH.

## C. Audited-bundle / replay closure
26. [NEXT] Search Drive specifically for original audited ZIP/bundle candidates without substituting other data.
27. [NEXT] Hash any candidate bundle before use.
28. [NEXT] If exact ZIP is recovered, reproduce frozen dataset fingerprint through the committed canonical fingerprint path.
29. [NEXT] If exact ZIP is not recovered, preserve HASH_METHOD_UNRESOLVED explicitly and do not promote structural identity.
30. [NEXT] Add a guarded full-reference replay runner contract that refuses false clean-reference claims.
31. [NEXT] Make full runner accept only explicit verified data identity for CLEAN_REFERENCE_REPLAY mode.
32. [NEXT] Keep a separate RESEARCH_STRUCTURAL_ONLY mode for non-promotional diagnostics if useful.
33. [NEXT] Preflight full runner with small fixture/reference slices in CI.
34. [NEXT] Verify repeated replay hashes are deterministic.
35. [NEXT] Verify Berlin/DST/session closure in full-run preparation.
36. [NEXT] Verify no same-bar/future feature access can enter full replay.
37. [NEXT] Verify failure injection still forces NO_TRADE/fail-safe behavior.
38. [NEXT] Run full 2014–2019 clean-reference replay only when identity/readiness gates permit.
39. [BLOCKED UNTIL 38] Reconcile full replay against frozen 856 trades / -31.309210619787684 R and WF expectations.
40. [BLOCKED UNTIL SOURCE] Export/freeze clean detailed WF/trade artifacts only from a verified clean run/source.

## D. Research advancement without promotion leakage
41. [NEXT] Re-state BB001 current evidence and diagnostic-origin caveat in one canonical research status file.
42. [NEXT] Re-state FIB001 causal impulse/retracement contract and prohibit hindsight swing selection.
43. [NEXT] Re-state GAP001 opening-gap vs intraday-FVG separation.
44. [NEXT] Re-state FAIL001 actual-trade analysis as pending clean detailed trades; permit legacy analysis only as LEGACY_EVIDENCE_ONLY.
45. [NEXT] Verify filter registry still enforces VISIBLE ≠ SWITCHABLE and RESEARCH ≠ DEPLOYABLE.
46. [NEXT] Prepare targeted, non-combinatorial research queue: regime → structure → entry/filter.
47. [NEXT] Gate FAST screens behind exact/parity confirmation for any promotion candidate.
48. [NEXT] Require OOS/WF, normal/1.5x/2x costs, stability/neighborhood and prospective evidence before promotion.
49. [NEXT] Produce consolidated readiness + research report with VERIFIED / IMPLEMENTED / RESEARCH / BLOCKED sections.
50. [STOP GATE] If and only if Paper/Bot start now appears justified, STOP and inform the user before starting anything. Otherwise open the next milestone block without initiating Paper/Live.

## Immediate stop conditions
Any of the following halts promotion and triggers diagnosis/rollback instead of architecture replacement:
- active-reference drift;
- dataset identity/hash mismatch claimed as clean evidence;
- engine/oracle fingerprint mismatch;
- migration/database-integrity failure;
- non-deterministic replay;
- lookahead/causality violation;
- unexplained row/trade-count change;
- Paper/Live path reachable without explicit readiness and user stop gate.
