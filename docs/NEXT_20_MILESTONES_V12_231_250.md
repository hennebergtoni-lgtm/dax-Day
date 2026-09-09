# V12 — Next 20 Milestones (231–250)

Status: AUTHORIZED FOR NON-LIVE DEVELOPMENT
Date: 2026-09-09

Goal: one bounded pre-Paper optimization/replay phase before external Windows MT5 milestone 102. V11.2 stays frozen. New ideas are research candidates only until robust OOS evidence exists. No broker order API, no Paper start, no LIVE authorization.

## 231–235 — Freeze and research intake
- [x] 231. Confirm V11 merged and main CI green, including Neon/database gates.
- [x] 232. Create V12 pre-paper optimization branch from green main.
- [x] 233. Record a bounded public-research intake for additional non-volume filters; provenance only, no automatic promotion.
- [x] 234. Define ADX/trend-strength candidate with causal closed-bar calculation.
- [x] 235. Define breakout candle-body/quality candidate without lookahead.

## 236–240 — Additional isolated candidates
- [x] 236. Define ATR/range-compression candidate, separated from existing ATR001 evidence.
- [x] 237. Define retest-staleness candidate using bars-since-breakout only.
- [x] 238. Add candidate registry/status labels: RESEARCH / TESTED / REJECTED / ROBUST_CANDIDATE.
- [x] 239. Add leakage/lookahead tests for all four candidates.
- [x] 240. Add deterministic feature tests and missing/warm-up handling.

## 241–245 — Historical sequential SHADOW replay
- [ ] 241. Build a historical sequential replay contract that feeds only closed M5 bars in chronological order.
- [ ] 242. Bind replay to the verified 2014–2019 clean dataset fingerprint and frozen V11.2 reference.
- [ ] 243. Produce deterministic decision/no-decision logs with bar identity and reason codes.
- [ ] 244. Prove no future-bar access and duplicate-bar idempotency during historical replay.
- [ ] 245. Add checkpoint/resume parity and deterministic replay fingerprint.

## 246–250 — Selection discipline and handoff
- [ ] 246. Evaluate each new filter in isolation before any interaction test; include costs, trade count, PF, Return-R, DD and stability.
- [ ] 247. Reject candidates that only improve in-sample or collapse trade count; do not optimize to one headline PF.
- [ ] 248. Permit only a small predeclared interaction test among robust isolated candidates and existing research candidates.
- [ ] 249. Extend web/status telemetry contract for historical replay/research visibility without execution controls.
- [ ] 250. Hard review + CI: frozen-reference guard, leakage tests, deterministic replay, recovery/status truthfulness; merge only if green.

## Binding constraints
- V11.2 is immutable baseline/reference.
- Historical 2014–2019 evidence identities are not rewritten.
- New filters do not become production filters merely because they test positively.
- Synthetic/historical replay is not broker evidence and cannot complete MT5 milestones 102–110.
- Paper remains NOT STARTED.
- LIVE remains NOT AUTHORIZED.
- `order_execution_enabled=false`.
