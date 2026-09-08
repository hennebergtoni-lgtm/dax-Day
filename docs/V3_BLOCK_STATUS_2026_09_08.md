# V3 Block Status — 2026-09-08

Status: CONSOLIDATED PROJECT CHECKPOINT

This file closes the current ~50-step milestone block as far as evidence allows. It does not start Paper or Live trading and does not modify V11.2.

## VERIFIED

- V11.2 remains the immutable active reference.
- Active normal reference remains 856 OOS trades, -31.309210619787684 R, 37 positive / 44 negative WF.
- Exact candidate engine source SHA-256 remains `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`.
- Oracle source SHA-256 remains `62adde1ccd630d01e9500b20c0efa88a0a8bd277e74c1a2c932ec6fc6efd3a0f`.
- Recovered Drive source `GER30_5m.csv` structurally matches the frozen 2014–2019 manifest: 481,824 raw rows; 1,673 Berlin-session days; 172,319 session M5 rows; 103 bars/day; 0 OHLC errors.
- Historical V3.5.4 parity evidence was recovered: 1,296/1,296 comparisons matched with zero mismatches, strategy unchanged and data unrepaired.
- Technical historical↔replay fixture parity is green.
- Replay reruns are guarded for deterministic equality/fingerprint equality.
- DST handling has explicit spring-jump/autumn-fold tests and rejects naive runtime timestamps.
- No-lookahead property tests reject future-dependent features.
- Failure injection for gap/duplicate/out-of-order/stale/feed/spread/contradiction fails safe to NO_TRADE.
- CI #165 completed successfully after the latest readiness/full-reference changes: Ruff, tests, V11.2 engine probe, guarded replay smoke, Neon connection, migrations and Neon integrity all green.
- Neon retains the verified active reference; clean detailed rows remain explicitly NOT_IMPORTED.

## IMPLEMENTED

- `RecoveryIdentity`: MISMATCH / STRUCTURAL_MATCH / HASH_VERIFIED.
- Structural data recovery cannot be promoted as clean-reference identity.
- Operator health maps HASH_VERIFIED→GREEN, STRUCTURAL_MATCH→YELLOW, MISMATCH→RED.
- Clean-reference replay and Paper readiness can explicitly require hash-verified dataset identity.
- Readiness was corrected to avoid a circular gate: CLEAN_REFERENCE_REPLAY may produce full-reference replay evidence; PAPER must consume verified full-reference replay evidence.
- Guarded full-reference replay wrapper uses the same V11.2 bridge/engine path; it does not contain a second strategy implementation.
- Full-reference wrapper checks readiness before execution, historical↔replay parity, replay rerun determinism and result fingerprints.
- Legacy per-WF OOS trade artifacts recovered from V2.0/V2.6 are catalogued separately from clean-reference evidence.
- Public/open-source donor audit now includes later architecture donors and license/reuse boundaries; no foreign code was copied during this block.
- Current operator-readiness snapshot and audited-data-recovery record are committed.
- FAST policy remains subordinate to exact parity and independent validation.

## RESEARCH

- BB001 remains RESEARCH. Causal prior-bar state is binding; same-entry-bar state and evaluation-derived thresholds are not promotion proof.
- FIB001 remains RESEARCH ONLY. The impulse must be known causally before retracement measurement; no hindsight swing selection.
- GAP001 remains RESEARCH ONLY. Opening gap and intraday FVG remain separate families.
- FAIL001 remains a research contract. Losing-trade patterns generate hypotheses only; empirical clean-reference failure analysis remains pending clean detailed trades.
- BOOST001 remains RESEARCH ONLY; no martingale, revenge sizing or loss-triggered risk escalation.
- Research filter registry keeps current research tools VISIBLE_ONLY and not live-switchable.
- Research order remains DATA/REGIME → STRUCTURE → ENTRY/FILTER, with targeted interactions only after isolated evidence.
- Promotion path remains FAST → EXACT/PARITY → OOS/WF → COST STRESS → STABILITY/NEIGHBORHOOD → PROSPECTIVE VALIDATION.

## BLOCKED / UNVERIFIED

- Frozen dataset session fingerprint `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2` has not been reproduced from the recovered CSV with the original historical serialization method.
- Frozen audited ZIP SHA-256 `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870` has not been re-observed; no matching ZIP was found in the connected Drive search.
- Therefore recovered data identity remains STRUCTURAL_MATCH, not HASH_VERIFIED.
- Full 2014–2019 clean-reference replay is blocked by dataset identity / audited bundle evidence.
- Reconciliation against frozen 856 trades / -31.309210619787684 R is not yet a new full historical replay result.
- Original clean-reference 243 WF metric rows / 81 selected variants / 856 trade rows have not been independently recovered; no synthetic import is allowed.
- Shadow has not started.
- Paper is NOT READY.
- Live is NOT ELIGIBLE.

## Decision at milestone 50

**BOT/PAPER START GATE NOT REACHED.**

The project is healthy for continued research, guarded replay engineering, data-provenance work and fixture-based validation. It is not yet justified to start the real Paper/Bot process because clean historical data identity/full-reference replay evidence remains unresolved.

Binding user-stop rule remains active: if a future block reaches a justified Paper/Bot start state, stop first and present the readiness evidence before initiating anything.
