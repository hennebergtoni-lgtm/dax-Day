# PROMOTION EVIDENCE CONTRACT V2

Status: BINDING RESEARCH CONTRACT — 2026-09-08

## Principle
A useful retrospective pattern is not a deployable trading rule. Promotion requires independent evidence through a fixed sequence and may fail at any gate without forcing a replacement candidate.

## Mandatory path
RESEARCH IDEA
→ causal exact definition
→ FAST screening only when useful
→ EXACT engine parity
→ rolling OOS/WF
→ realistic cost model
→ 1.5x / 2x cost stress
→ parameter-neighborhood / stability review
→ prospective Shadow evidence
→ Paper eligibility review
→ user STOP-GATE before Paper start

No stage may be skipped because an aggregate PF or Return-R looks attractive.

## Evidence independence
- OOS data may evaluate a threshold; it may not be used to discover that threshold and then be called independent OOS proof.
- Any threshold discovered from full-sample/OOS diagnostics returns to RESEARCH status and must be redefined ex ante or train-only.
- Research families are tested isolated before interactions are considered.
- Interaction research requires a prior rationale and may not become an unrestricted combinatorial grid.

## Stability / neighborhood minimum
A candidate is not stable merely because one parameter point is best. Before prospective promotion, require:
- directionally consistent behavior across adjacent sensible parameter values or threshold bands;
- no collapse under modest cost stress;
- no result dominated by one WF, one month, one day or a tiny cluster of trades;
- enough active WFs to demonstrate behavior across multiple market periods;
- train/OOS behavior that does not rely on one exact fitted cutoff;
- no unexplained discontinuity from a small parameter change.

There is deliberately no fixed universal minimum trade count. Sufficiency depends on effect size, dispersion, number of active WFs and concentration. A small trade sample requires stronger uncertainty language and cannot be promoted just because PF is high.

## Concentration checks
Report at minimum:
- total trades and active WFs;
- positive / negative / flat active WFs;
- total Return-R and median WF PF;
- max drawdown R;
- largest single-WF contribution to total R;
- largest single-trade contribution when trade detail exists;
- year/session/regime concentration where available;
- normal, 1.5x and 2x cost results.

## Prospective validation
Shadow is not a ceremonial waiting period. Before Paper eligibility it must measure:
- decision parity / unexplained drift;
- NO_TRADE distribution and blocker frequencies;
- feed age, gaps, duplicate/out-of-order events and spread observations;
- decision latency;
- feature/regime distribution drift;
- operational restarts and manifest continuity;
- any discrepancy between expected and observed decision state.

A candidate may remain RESEARCH indefinitely if prospective evidence is insufficient.

## Current family ranking for next evidence value
### 1. BB001 — highest next-test value
Reason: strongest existing causal evidence and complete 856-trade feature alignment. Next test must use ex-ante/train-only thresholds; prior OOS-derived diagnostics cannot be treated as independent proof.

### 2. GAP001 — high isolation value
Reason: opening gap is objectively timestamped and can be defined without hindsight. Test gap size/direction/close behavior in isolation before any OR interaction.

### 3. FIB001 — moderate value, high causality risk
Reason: potentially useful structure tool but swing/impulse anchoring is highly vulnerable to hindsight. Only causal impulse definitions are admissible.

### 4. FAIL001 — high safety value, not alpha evidence
Reason: use clean replay failures/no-trades to generate bounded hypotheses and safety/diagnostic improvements. Never turn loss streaks directly into ad-hoc filters.

### 5. EVENT001 — lower immediate value
Reason: requires reliable event timestamps/provenance and raises alignment/selection issues. Do not prioritize before core price-only families and full-reference replay are closed.

## Next non-combinatorial experiments
1. `BB001_EXACT_EXANTE_THRESHOLD`: isolated BB position/bandwidth candidate with thresholds generated from training information only; exact engine and standard costs/stress.
2. `GAP001_OPENING_GAP_BASE`: opening-gap size/direction bins defined before OOS evaluation; no Fibonacci/BB interaction.
3. `FIB001_CAUSAL_IMPULSE_BASE`: one predeclared causal impulse rule and fixed retracement levels; no retrospective swing selection.
4. `FAIL001_REPLAY_DIAGNOSTICS`: after full clean replay yields legitimate detail, classify losing/no-trade contexts without changing strategy.
5. `EVENT001_PROVENANCE_GATE`: data-quality/provenance test only before any performance test.

## Promotion blockers
Any of the following returns a candidate to RESEARCH or blocks promotion:
- lookahead/repainting;
- same-bar causality violation;
- FAST/exact mismatch;
- dataset/engine/config fingerprint drift;
- OOS threshold discovery masquerading as validation;
- material instability across neighboring parameters;
- cost-stress collapse without a justified economic reason;
- unexplained concentration;
- insufficient prospective evidence;
- operational drift or unresolved execution state.
