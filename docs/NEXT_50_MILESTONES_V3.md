# NEXT 50 MILESTONES V3

Status: **BLOCK CLOSED AS FAR AS EVIDENCE ALLOWS — 2026-09-08**

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
16. [DONE] Re-establish fully green CI after recovery/readiness changes; latest full gate in this block is CI #165 SUCCESS.
17. [DONE] Re-audit public/open-source donor catalogue and licenses.
18. [DONE] Extend repo Open-Source Audit with later architecture donors.
19. [DONE] Freeze this V3 milestone roadmap and STOP-before-start rule.
20. [DONE] Re-check current active-reference registry and DB integrity after V3 writes.
21. [DONE] Confirm no clean-reference hashes/results changed during recovery work.
22. [DONE] Re-check engine/oracle artifact SHA contracts.
23. [DONE] Re-check fixture historical↔replay deterministic parity.
24. [DONE] Add operator-readable current readiness snapshot/status report.
25. [DONE] Verify clean replay fails closed when recovered data identity is only STRUCTURAL_MATCH.

## C. Audited-bundle / replay closure
26. [DONE] Search Drive specifically for original audited ZIP/bundle candidates without substituting other data; no exact ZIP candidate was found.
27. [BLOCKED — NO CANDIDATE] Hash any candidate bundle before use. No candidate exists to hash yet.
28. [BLOCKED — NO EXACT ZIP] Reproduce frozen dataset fingerprint through the committed canonical path only if the exact audited bundle/source identity is recovered.
29. [DONE] Preserve HASH_METHOD_UNRESOLVED explicitly and do not promote structural identity.
30. [DONE] Add guarded full-reference replay runner contract that refuses false clean-reference claims; also remove circular precondition that required full replay before running full replay.
31. [DONE] Make full runner/readiness require explicit HASH_VERIFIED identity when dataset identity is supplied for CLEAN_REFERENCE_REPLAY/PAPER.
32. [DEFERRED BY DESIGN] No separate RESEARCH_STRUCTURAL_ONLY full-run mode was added; avoiding a second near-clean mode reduces accidental promotion leakage. Structural data may still support explicitly labelled non-promotional diagnostics outside the clean-reference gate.
33. [DONE] Preflight guarded full runner through CI regression tests and existing fixture replay smoke.
34. [DONE] Require repeated replay equality and deterministic result fingerprints.
35. [DONE] Verify Berlin/DST behavior with explicit spring-jump/autumn-fold/naive-time rejection tests.
36. [DONE] Verify no-lookahead property surface rejects future-dependent features; full runner continues to consume safe closed candles through the existing V11.2 bridge.
37. [DONE] Verify failure injection forces NO_TRADE/fail-safe behavior for missing/gap, duplicate, out-of-order, stale/late, feed interruption, extreme spread and contradictory state.
38. [BLOCKED — DATA IDENTITY] Full 2014–2019 clean-reference replay may run only when identity/readiness gates permit; current recovered source is STRUCTURAL_MATCH, not HASH_VERIFIED.
39. [BLOCKED UNTIL 38] Reconcile full replay against frozen 856 trades / -31.309210619787684 R and WF expectations.
40. [BLOCKED UNTIL VERIFIED CLEAN SOURCE/RUN] Export/freeze clean detailed WF/trade artifacts only from a verified clean run/source.

## D. Research advancement without promotion leakage
41. [DONE / RESEARCH] Re-check BB001 canonical plan: causal prior-bar rule and diagnostic/data-derived-threshold caveat remain explicit; no promotion occurred.
42. [DONE / RESEARCH] Re-check FIB001 causal impulse/retracement contract; hindsight swing selection remains prohibited.
43. [DONE / RESEARCH] Re-check GAP001 opening-gap vs intraday-FVG separation.
44. [DONE / RESEARCH] Re-check FAIL001: empirical clean-reference trade analysis remains pending clean detail; recovered old trade rows are LEGACY_EVIDENCE_ONLY.
45. [DONE] Verify filter registry still enforces VISIBLE ≠ SWITCHABLE and RESEARCH ≠ DEPLOYABLE.
46. [DONE] Preserve targeted non-combinatorial research order: DATA/REGIME → STRUCTURE → ENTRY/FILTER; interactions only after isolated evidence.
47. [DONE] FAST screens remain subordinate to exact/parity confirmation for any promotion candidate.
48. [DONE] Promotion continues to require OOS/WF, normal/1.5x/2x costs, stability/neighborhood and prospective validation.
49. [DONE] Produce consolidated `V3_BLOCK_STATUS_2026_09_08.md` with VERIFIED / IMPLEMENTED / RESEARCH / BLOCKED sections.
50. [EVALUATED — START GATE NOT REACHED] Paper/Bot start is **not justified yet** because hash-verified clean historical identity/full-reference replay remains unresolved. Do not initiate Paper/Live. The user-stop rule remains active for the future point at which readiness is genuinely reached.

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
