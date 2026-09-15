# Recovery Canonicalization Audit V1

Status: AUDITED / RETAIN_WITH_REASON — STEP 2133
Updated: 2026-09-12

Purpose: resolve the known ambiguity between `src/daxlab/runtime/recovery.py` and `src/daxlab/runtime/recovery_bundle.py` and keep one canonical material-run recovery owner without deleting useful forensic compatibility before evidence permits it.

## 1. Finding

Two modules expose similarly named recovery-bundle concepts under the same schema label `DAXLAB_RECOVERY_BUNDLE_V1`, but their contracts are incompatible.

### Legacy `runtime/recovery.py`

- statuses: `RUNNING`, `COMPLETED`, `ABORTED`;
- manifest includes dataset/engine/config/mode plus file hashes;
- writes `recovery_bundle_manifest.json`;
- checkpoint is optional;
- result payload may be included as `result.json`;
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
| Active repository surfaces | no legacy consumer permitted | `tests/test_legacy_recovery_retirement_audit.py` | full `pytest` | Scans `src`, `scripts`, `tests`, `.github`, `web`; audit-only files excluded. |
| Historical documentation / forensics | legacy references allowed only in reviewed provenance set | `tests/test_legacy_recovery_document_provenance.py` | full `pytest` | Historical architecture facts may describe legacy without creating a current consumer. |
| Recovery bundle round-trip/tamper protection | `runtime/recovery_bundle.py` | `test_recovery_bundle.py` | full `pytest` | Canonical material-run bundle contract. |
| Recovery bundle resilience / partial-write behavior | `runtime/recovery_bundle.py` | `test_recovery_bundle_resilience.py` | full `pytest` | Canonical hash-addressed durable bundle surface. |
| Repository reconstruction preflight | requires `runtime/recovery_bundle.py` only | `scripts/recovery_preflight.py` | dedicated CI step + tests indirectly | Repository reconstruction does not require legacy `recovery.py`. |
| Recovery/reconstruction governance | material-run bundle requirement | `docs/RECOVERY_AND_RECONSTRUCTION_CONTRACT_V1.md` | recovery preflight | Requires run manifest, checkpoint, decision log, artifact hashes and source/data/engine/config identity. |
| Historical sequential replay | own `HistoricalReplayCheckpoint` | `test_historical_sequential_replay.py` and replay tests | full `pytest` | Separate deterministic replay-state contract; does not automatically consume either recovery bundle module. |
| MT5 SHADOW restart/recovery | SHADOW-specific restart/reconcile/state components | SHADOW recovery/equivalence/resume tests | full `pytest` / SHADOW smoke | Operational forward state is a distinct runtime concern; do not replace blindly with research material-run bundle. |
| Legacy `runtime/recovery.py` | legacy forensic compatibility only | module boundary + retirement/provenance audits | full `pytest` | Frozen noncanonical RETIRE candidate; no new runtime dependency. |

## 3. Canonical decision

For all new DAX-BOT 1.x code:

- `runtime/recovery.py` = **LEGACY / FROZEN / RETAIN_WITH_REASON**;
- `runtime/recovery_bundle.py` = **CANONICAL material-run recovery bundle**;
- SHADOW/forward bot state = **REUSE existing restart/reconcile/state semantics**, not silently replaced by the research bundle;
- any bridge from bot state to durable recovery must be explicit and tested.

No new code may import the legacy module. No feature work should be added to it.

## 4. Step 2133 retirement decision

**Current retirement decision: `RETAIN_WITH_REASON`.**

Step 2133 completed the consumer and semantics audit that Step 2131 had started before the governance interruption.

Evidence supporting eventual retirement:
- active code/config/script scan finds no consumer of `daxlab.runtime.recovery` or `recovery_bundle_manifest.json` outside audit-only surfaces;
- production import boundary forbids new legacy imports;
- repository reconstruction preflight requires `recovery_bundle.py`, not `recovery.py`;
- canonical bundle has stronger atomic-write/checksum/resilience behavior and dedicated tests.

Evidence blocking `RETIRE_NOW`:
- legacy and canonical contracts are still behaviorally different rather than parity-proven replacements;
- legacy accepts an optional checkpoint while the canonical bundle requires one;
- legacy may persist an optional `result.json` payload while the canonical bundle has no equivalent result-payload field;
- legacy embeds dataset/engine/config/mode and file hashes directly in `recovery_bundle_manifest.json`, while the canonical design reaches related provenance through the run manifest plus separate checksums;
- there is no compatibility reader/migration test proving that a retained historical legacy bundle can be reconstructed after deleting the legacy reader/writer;
- there is no explicit evidence-deprecation decision proving that all externally retained legacy recovery artifacts may safely become unreadable.

The absence of active imports proves the module is not on the hot path. It does **not** prove that deleting the only implementation of the old artifact contract is evidence-neutral.

## 5. Retirement unlock conditions

A future step may change the decision to `RETIRE_NOW` only after all applicable conditions are evidenced:

1. active consumer scan remains clean;
2. historical/provenance references are classified rather than mistaken for active consumers;
3. useful legacy behavior is either migrated deliberately or explicitly declared obsolete with evidence;
4. retained historical `recovery_bundle_manifest.json` artifacts have a tested compatibility reader/migration path, or an explicit evidence-retirement decision proves none must remain readable;
5. canonical material-run recovery still satisfies `RECOVERY_AND_RECONSTRUCTION_CONTRACT_V1.md`, including result-artifact provenance outside or inside the bundle as deliberately designed;
6. recovery preflight and full research CI are green;
7. restore/reconstruction drill remains green where applicable;
8. rollback path exists for the removal commit.

Until then, retain `recovery.py` as frozen forensic compatibility. Retention does not make it canonical and does not justify new callers.

## 6. DAX-BOT 1.x recovery target

The bot converges on a simple two-layer model, not another recovery implementation:

1. **Operational state** — deterministic bot state, last processed identities, virtual position lifecycle, duplicate/reconciliation metadata; restartable from persisted runtime truth.
2. **Material evidence bundle** — canonical `recovery_bundle.py` style immutable/hash-verified evidence for material replay/research/validation runs.

The layers may share identities and adapters, but they do not need identical persistence files.

## 7. Safety

This audit changes no runtime behavior, broker integration, execution capability, database schema or Windows host configuration.

- SHADOW authorization is unchanged;
- PAPER remains unauthorized;
- LIVE remains unauthorized;
- `execution_capability=NONE` and `order_execution_enabled=false` remain binding where currently required.
