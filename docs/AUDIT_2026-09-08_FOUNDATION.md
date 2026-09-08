# Whole-project audit — 2026-09-08 foundation block

## Verified before changes
- GitHub `main` and CI are readable/writable through the connected GitHub integration.
- V11.2 remains frozen; no strategy semantics were changed in this block.
- `research/V112_REFERENCE_V1/reference_result.json` declares the clean active reference.
- The reference runner sends the selected typed parameter object directly into OOS `cached_metrics`; it does not reconstruct OOS parameters from display strings.
- Neon CI proves connection and migration execution, not that the clean reference result has already been persisted.
- FIB001, GAP001, BB001, filter registry and interaction-matrix code already existed and were not recreated.

## Implemented and CI-gated in this block
- runtime modes: HISTORICAL / REPLAY / SHADOW / PAPER / LIVE
- canonical timezone-aware Candle contract
- explicit data-quality states
- closed-safe-candle replay admission
- deterministic config/data fingerprints and decision IDs
- first-class NO_TRADE decision records
- bounded drift state with no self-optimization
- FAIL001 catalog and technical-control mapping
- hard runtime safety gate
- Europe/Berlin DST tests
- failure injection for missing, duplicate, out-of-order, late, feed interruption, extreme spread and contradictory state
- explicit typed-params OOS regression test

## Hygiene decisions
1. `V112_REFERENCE_V1/manifest.json`: corrected from `RESEARCH` to `ACTIVE_REFERENCE` and marked `FROZEN_REFERENCE`.
2. `reference_runner.select_variant`: wording corrected to the frozen clean train-ranking rule.
3. Typed params: direct object flow retained and now regression-tested.
4. Clean reference persistence in Neon: **UNVERIFIED**. Do not claim it exists until an explicit database read proves it.

## Historical integrity check
Several previously questioned BB001 SHAs were directly resolved in GitHub during this audit, including `1112805a0afbc7b62629afd3e3211e0b78985306`, `3d357deefcb61ffd99202ac3d74d4ddf04be9be6` and `b24e7c862ca593a03f639882f7dd9842105658f5`. Their existence is verified; their contents remain research evidence, not automatic promotion.

Shortened historical SHA strings containing `...` remain unverified because they are not unique commit identifiers.

## Stale-document finding
`docs/MASTERSTAND.md` contains older milestone wording that predates the clean active reference and the new runtime foundation. Where it conflicts, `docs/RESEARCH_GATES.md`, `research/V112_REFERENCE_V1/reference_result.json`, this audit, and passing CI on the current commit take precedence. A later editorial consolidation may rewrite the old handover document, but scientific facts are not changed merely to make prose consistent.

## Gate decision after steps 1–25
Do **not** resume FIB001/GAP001 promotion yet. The generic replay/data-safety foundation is now strong enough to keep, but one mandatory engineering gate remains: wire the actual frozen V11.2 decision/feature path through HISTORICAL vs REPLAY and prove end-to-end feature/decision/config/ID parity on deterministic fixtures from the audited reference surface.

After that gate is green, return to isolated FIB001 and then GAP001 research. Do not introduce cross-market logic or a candidate bot before those gates.
