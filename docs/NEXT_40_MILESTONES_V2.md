# Next 40 guarded milestones — V2

Status: ACTIVE PLAN

Principle: preserve the frozen clean V11.2 reference, validate before extending, and stop rather than rebuild when a gate fails.

1. Re-read active reference and provenance.
2. Confirm CI green before new research work.
3. Confirm Neon connectivity and migration integrity.
4. Verify active-reference dataset fingerprint.
5. Verify frozen engine/reference fingerprint.
6. Keep legacy 1384/-68.1095R evidence explicitly legacy-only.
7. Inventory detailed clean WF/trade artifacts before importing anything.
8. Refuse synthetic reconstruction of missing detailed rows.
9. Add negative-trade/failure taxonomy.
10. Add NO_TRADE outcome taxonomy.
11. Define detailed artifact import contract.
12. Add idempotent import design and duplicate guards.
13. Add pre-import row/hash/count gate.
14. Add post-import reconciliation gate.
15. Add rollback/transaction requirement for imports.
16. Re-run DB integrity after persistence changes.
17. Close historical-vs-replay parity on the clean reference surface.
18. Verify closed-candle/no-lookahead causality in replay.
19. Verify Berlin-session/DST semantics in replay.
20. Verify deterministic rerun hashes.
21. Produce first guarded replay smoke run.
22. Compare replay outputs with frozen reference expectations.
23. Classify losing trades without hindsight rule changes.
24. Analyse MFE/MAE and stop-out clusters.
25. Analyse false-breakout/failed-retest clusters.
26. Analyse OR/ATR and previous-range failure concentration.
27. Analyse cost-sensitive outcome flips.
28. Analyse NO_TRADE protection and opportunity cost.
29. Convert only robust failure patterns into hypotheses.
30. Advance FIB001 as isolated research only.
31. Advance GAP001 as isolated research only.
32. Recheck BB001 evidence and causal feature timing.
33. Run targeted interaction screens, not combinatorial explosion.
34. Keep FAST screening subordinate to exact parity checks.
35. Extend filter UI with evidence/provenance/blocker states.
36. Add operator-facing data-integrity/reference health state.
37. Add BOOST001 bounded-sleeve simulation contract.
38. Simulate booster risk-of-ruin; prohibit martingale/revenge logic.
39. Keep BOOST001 paper-only until independent promotion.
40. Gate the next visible bot/replay run on all critical checks green.

## Stop conditions
Any active-reference drift, dataset hash mismatch, engine fingerprint mismatch, migration failure, non-deterministic replay, lookahead finding or unexplained row-count change blocks advancement. The response is diagnosis and rollback to the last verified state — not a replacement architecture.
