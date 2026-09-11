# Recovery Canonicalization Audit V1

Status: AUDITED / CLEANUP DECISION PENDING STEP-2000 LEAN GATE

Purpose: resolve the known ambiguity between `src/daxlab/runtime/recovery.py` and `src/daxlab/runtime/recovery_bundle.py` before DAX-BOT 1.x chooses a hot-path recovery design.

## 1. Finding

Two modules expose similarly named recovery-bundle concepts under the same schema label `DAXLAB_RECOVERY_BUNDLE_V1`, but their contracts are incompatible.

### Legacy `runtime/recovery.py`

- statuses: `RUNNING`, `COMPLETED`, `ABORTED`;
- manifest includes dataset/engine/config/mode plus file hashes;
- writes `recovery_bundle_manifest.json`;
- checkpoint is optional;
- result payload may be included;
- verification reads hashes embedded in the manifest.

### Canonical `runtime/recovery_bundle.py`

- statuses: `IN_PROGRESS`, `COMPLETED`, `ABORTED`;
- explicit `RecoveryBundleManifest.build(...)`;
- checkpoint required;
- manifest records checkpoint + decision-log fingerprints;
- writes `bundle_manifest.json` plus `SHA256SUMS`;
- writes through temporary files then replaces targets;
- resilience tests cover missing/corrupt files and orphan temp files.

The two modules must never be treated as interchangeable merely because they share a schema label.

## 2. Consumer → Module → Test → CI → Runtime Contract matrix

| Consumer / surface | Module used | Test/evidence | CI relationship | Runtime interpretation |
|---|---|---|---|---|
| New production-code boundary | `runtime/recovery_bundle.py` required | `tests/test_recovery_module_boundary.py` | full `pytest` | Explicitly forbids new production imports of legacy `runtime.recovery`. |
| Recovery bundle round-trip/tamper protection | `runtime/recovery_bundle.py` | `test_recovery_bundle.py` | full `pytest` | Canonical material-run bundle contract. |
| Recovery bundle resilience / partial-write behavior | `runtime/recovery_bundle.py` | `test_recovery_bundle_resilience.py` | full `pytest` | Canonical hash-addressed durable bundle surface. |
| Repository reconstruction preflight | requires `runtime/recovery_bundle.py` file | `scripts/recovery_preflight.py` | dedicated CI step + tests indirectly | Repository treats recovery_bundle as canonical reconstruction asset. |
| Recovery/reconstruction governance | material-run bundle requirement | `docs/RECOVERY_AND_RECONSTRUCTION_CONTRACT_V1.md` | recovery preflight | Requires run manifest, checkpoint, decision log, artifact hashes and source/data/engine/config identity. |
| Historical sequential replay | own `HistoricalReplayCheckpoint` | `test_historical_sequential_replay.py` and replay tests | full `pytest` | Separate deterministic replay-state contract; does not automatically consume either recovery bundle module. |
| MT5 SHADOW restart/recovery | SHADOW-specific restart/reconcile/state components | SHADOW recovery/equivalence/resume tests | full `pytest` / SHADOW smoke | Operational forward state is a distinct runtime concern; do not replace blindly with research material-run bundle. |
| Legacy `runtime/recovery.py` | legacy only | no authorization for new production import; module-boundary test protects against expansion | full `pytest` | RETIRE candidate, not a DAX-BOT 1.x dependency. |

## 3. Canonical decision

For all new DAX-BOT 1.x code:

- `runtime/recovery.py` = **LEGACY / RETIRE_AFTER_AUDIT**;
- `runtime/recovery_bundle.py` = **CANONICAL material-run recovery bundle**;
- SHADOW/forward bot state = **REUSE existing restart/reconcile/state semantics**, not silently replaced by the research bundle;
- any bridge from bot state to durable recovery must be explicit and tested.

No new code may import the legacy module.

## 4. Why legacy is not deleted yet

Deletion is deferred to the mandatory step-2000 LEAN/CLEANUP audit because removal must first prove:
- no non-indexed consumer remains;
- no script/doc/artifact contract still depends on its filenames/status vocabulary;
- removal does not reduce recovery evidence or break reconstruction;
- stale tests/docs can be migrated or removed together.

## 5. DAX-BOT 1.x recovery target

The bot should converge on a simple two-layer model, not another recovery implementation:

1. **Operational state** — deterministic bot state, last processed identities, virtual position lifecycle, duplicate/reconciliation metadata; restartable from persisted runtime truth.
2. **Material evidence bundle** — canonical `recovery_bundle.py` style immutable/hash-verified evidence for material replay/research/validation runs.

The layers may share identities and adapters, but they do not need identical persistence files.

## 6. Safety

This audit does not alter runtime behavior, broker integration, execution capability, database schema or Windows host configuration.