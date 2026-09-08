# NEXT 50 MILESTONES V5

Status: ACTIVE ROADMAP — 2026-09-08

Purpose: move from V4 engineering readiness into full clean-reference reproduction, disaster recovery, research-lab reactivation and a read-only operator web surface, while preserving the frozen V11.2 reference and all evidence boundaries.

Binding rules:
- V11.2 remains immutable active reference.
- No Paper/Live start in this block unless STOP GATE is explicitly reached; if reached, stop and present evidence first.
- HASH_VERIFIED dataset identity and exact engine/oracle fingerprints are mandatory for clean-reference replay.
- No synthetic clean-reference detail rows.
- Legacy/research/public evidence cannot be promoted to active reference.
- DATA UNSAFE => NO_TRADE.
- FAST remains screening only; exact engine remains promotion surface.
- All long-running work must be restartable from deterministic checkpoints.
- Project recovery must tie code commit, DB evidence state, dataset identity and run manifests together.
- Web UI is read-only/operator-facing until prospective execution gates are separately verified.

## A. V5 start and full-reference materialization
1. [DONE] Carry forward V4 closeout and frozen V11.2 active-reference metrics.
2. [DONE] Reconfirm local availability of the HASH_VERIFIED 2014–2019 recovered CSV.
3. [DONE] Export the repository-stored recovered V11.2 oracle/exact sources through SHA-verified GitHub Actions artifact.
4. [DONE] Re-audit repository/root and current CI/project accessibility.
5. [DONE] Identify disaster-recovery and web-interface gaps.
6. [DONE] Refresh public WFA/grid/replay and Neon recovery intelligence.
7. [NEXT] Locally re-verify exported oracle/exact source SHA-256 values.
8. [NEXT] Probe exact engine function signatures and required data schema locally.
9. [NEXT] Build a deterministic local clean-reference runner wrapper around the recovered exact engine.
10. [NEXT] Execute a small exact-engine dry run against HASH_VERIFIED data before full WFA.
11. [NEXT] Verify dry-run trade/result determinism across two identical runs.
12. [NEXT] Materialize the canonical 81-window Train45/OOS20/Step20 schedule from 2014–2019.
13. [NEXT] Verify all 81 windows have exact expected train/OOS boundaries and no overlap/leakage.
14. [NEXT] Execute full 81-WF exact clean-reference reconciliation.
15. [NEXT] Compare aggregate normal-cost result to frozen 856 trades / -31.309210619787684R / 37 positive / 44 negative WFs / median PF 0.9057693102560179.
16. [NEXT] Compare stress1.5 and stress2 aggregates to frozen active-reference metrics.
17. [NEXT] Produce deterministic full-replay manifest and source hashes.
18. [NEXT] Persist genuine reproduced WF/trade detail only if exact reconciliation is achieved.
19. [NEXT] Reconcile genuine detail artifacts against expected 243 WF metrics / 81 selections / 856 trades.
20. [NEXT] Keep detail registry NOT_IMPORTED/PARTIAL if reconciliation is not exact.

## B. Disaster recovery and database safety
21. [NEXT] Define ProjectRecoveryManifest tying git commit, dataset SHA, engine SHA, DB migration set, active-reference id and latest replay checkpoint.
22. [NEXT] Add deterministic project-state snapshot generator.
23. [NEXT] Add snapshot checksum and schema version.
24. [NEXT] Add restore-plan validator that fails closed on commit/dataset/engine mismatch.
25. [NEXT] Add database logical-backup contract using pg_dump-compatible export metadata without storing secrets in repo.
26. [NEXT] Add database restore-probe procedure into an isolated target/branch only.
27. [NEXT] Document Neon PITR/branch recovery as secondary recovery layer, not sole backup.
28. [NEXT] Add recovery runbook for DB loss, repo loss, interrupted replay and stale local cache.
29. [NEXT] Add CI artifact retention for operator recovery manifests and integrity summaries.
30. [NEXT] Add regression tests proving interrupted replay can resume without changing decisions/results.
31. [NEXT] Add rollback/idempotency integration coverage where practical for detail imports.
32. [NEXT] Add fail-closed protection against partial DB migration or active-reference drift during restore.
33. [NEXT] Produce operator-readable recovery health: GREEN/YELLOW/RED.
34. [NEXT] Re-run CI/Neon after recovery hardening.

## C. Public/grid optimization and research-lab reactivation
35. [NEXT] Audit current public WFA/grid projects for reproducibility patterns, license and leakage risk.
36. [NEXT] Compare exhaustive grid vs bounded/random/coarse-to-fine search for runtime efficiency without changing V11.2 reference methodology.
37. [NEXT] Define research-only acceleration policy: cache shared daily context, precompute indicators, vectorize safe surfaces, parallelize only independent deterministic jobs.
38. [NEXT] Benchmark current FAST/exact bottlenecks and identify highest-value runtime optimizations.
39. [NEXT] Add deterministic timing/profiling output so future slowdowns are measurable.
40. [NEXT] Re-open Research Lab queue with BB001 -> GAP001 -> FIB001 -> FAIL001 -> EVENT001 priorities.
41. [NEXT] Reconfirm BB001 ex-ante/train-only threshold rules and no post-OOS threshold tuning.
42. [NEXT] Define first targeted non-combinatorial BB001 exact experiment after clean-reference reconciliation.
43. [NEXT] Define GAP001 base experiment with objective timestamped opening-gap definition.
44. [NEXT] Preserve FIB001 causal impulse-only and FAIL001 diagnostic-only promotion rules.

## D. Read-only web/operator interface
45. [NEXT] Define read-only web dashboard contract: reference status, CI, DB health, recovery health, replay progress, research queue, blockers.
46. [NEXT] Implement static/read-only web prototype without broker or mutation controls.
47. [NEXT] Add machine-readable status JSON generator from repository evidence only.
48. [NEXT] Add mobile-first layout suitable for iPhone use and explicit VERIFIED/RESEARCH/BLOCKED badges.
49. [NEXT] CI-test web status generation and ensure UI cannot mark Paper/Live ready independently of readiness engine.
50. [STOP GATE] Re-evaluate full project readiness. If serious Shadow/Paper/Bot start is justified, STOP and present evidence to user before any start; otherwise close V5 and continue Research Lab without starting execution.

## Immediate stop conditions
- active-reference drift;
- dataset/engine/oracle/config fingerprint mismatch;
- 81-WF schedule mismatch or leakage;
- unexplained trade/R/PF deviation from frozen reference;
- DB integrity/migration/recovery mismatch;
- non-deterministic restart/resume;
- synthetic detail substitution;
- lookahead/same-bar causality violation;
- external/public claim treated as DAX evidence;
- web UI bypassing readiness/safety gates;
- Paper/Live becoming reachable without explicit STOP GATE presentation.
