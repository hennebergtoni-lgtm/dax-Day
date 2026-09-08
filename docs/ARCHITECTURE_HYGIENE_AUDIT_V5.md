# Architecture Hygiene Audit V5

Status: CONTROLLED REVIEW — NO DESTRUCTIVE REFACTOR YET

## Purpose
Review the early-stage DAX Research Lab for duplicated truth, accidental parallel implementations, dead paths and unnecessary runtime cost before adding more research tooling.

## Safety rule
No code is removed because it merely looks unused. A candidate may be changed only after:
1. dependency/import scan;
2. test coverage review;
3. behavior comparison;
4. reference/replay impact review;
5. CI pass;
6. recovery/restore pass;
7. rollback path exists.

## Current architecture assessment
The top-level module boundaries remain clear and should stay intact:
- `contracts`
- `data`
- `reference`
- `research`
- `runtime`
- `operator`
- `import_guard`

No broad rewrite or directory collapse is justified.

## Confirmed redundancy candidate: runtime recovery bundle
Two implementations currently exist:
- `src/daxlab/runtime/recovery.py`
- `src/daxlab/runtime/recovery_bundle.py`

They overlap materially but are not behaviorally identical.

### `recovery.py` strengths
- records dataset, engine, config and mode fingerprints directly in the recovery manifest;
- supports optional checkpoint;
- supports optional `result.json`;
- manifest records file hashes;
- status vocabulary: `RUNNING`, `COMPLETED`, `ABORTED`.

### `recovery_bundle.py` strengths
- canonical compact JSON serialization;
- temporary-file replace for safer writes;
- explicit `SHA256SUMS`;
- explicit checkpoint and decision-log fingerprints;
- status vocabulary: `IN_PROGRESS`, `COMPLETED`, `ABORTED`;
- currently has dedicated round-trip/tamper tests.

### Decision
DO NOT DELETE EITHER IMPLEMENTATION YET.

The safe target is one canonical recovery contract that preserves the union of the useful properties above. Before consolidation, add compatibility tests proving equivalent accepted inputs, persisted fingerprints, tamper detection, optional result/checkpoint behavior and restore semantics. Only after that may the non-canonical module become a thin compatibility wrapper; physical deletion is a later decision.

## Reference vs research WF
No duplication should be removed here. `research.walk_forward.build_walk_forwards` owns generic deterministic scheduling. `reference.reference_runner` owns frozen V11.2 selection/ranking and binds the generic scheduler to the 45/20/20 reference contract. This is intentional layering, not accidental duplication.

## Reference vs runtime
Keep separate. `reference` contains frozen evidence/engine/reproduction concerns; `runtime` contains mode, data-safety, decision, replay, health, drift, checkpoint and operational readiness concerns. Merging these would increase coupling and make reference immutability harder to audit.

## Integrity checks
Repeated checks are acceptable when they protect different trust boundaries. The desired pattern is:
- one canonical value source;
- multiple boundary-specific assertions may read it;
- no copied business truth maintained independently.

Therefore DB integrity, Web status integrity, recovery preflight and runtime readiness should remain separate gates, but future work should centralize shared immutable reference constants where practical instead of copying literal values.

## Performance principle
Only optimize measured hotspots. The V5 profiling identified `_find_signal`/DataFrame scalar access as the dominant research bottleneck. The separate parity-verified accelerator is justified. Broad micro-optimization of safety or provenance code is not.

## V5 hygiene conclusion
The codebase is still small enough to remain understandable. No broad refactor is warranted. One concrete duplication area has been identified (runtime recovery bundle); it will be consolidated only through compatibility-first migration, not deletion-first cleanup.
