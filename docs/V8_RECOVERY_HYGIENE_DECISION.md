# V8 Recovery Hygiene Decision

Status: BINDING ARCHITECTURE HYGIENE DECISION

## Observed duplication
Two runtime modules currently overlap:
- `src/daxlab/runtime/recovery_bundle.py`
- `src/daxlab/runtime/recovery.py`

The canonical reconstruction preflight explicitly requires `recovery_bundle.py`. It provides canonical JSON, atomic temp-file replacement, SHA256SUMS, checkpoint and decision-log fingerprints, and dedicated round-trip/tamper tests.

`recovery.py` preserves useful richer provenance fields and optional result/checkpoint behavior, but uses a different status vocabulary and file-manifest shape.

## Decision
1. `recovery_bundle.py` is the canonical recovery implementation for new code.
2. No new production imports of `daxlab.runtime.recovery` are allowed.
3. `recovery.py` is retained temporarily for compatibility/forensics; no deletion yet.
4. Physical removal requires: dependency scan, behavior-union design, compatibility tests, CI green, restore drill green, and rollback path.
5. Any useful provenance field missing from the canonical implementation must be migrated deliberately before deletion.

## Why no immediate deletion
Absence of an obvious current import is not enough evidence to delete a recovery path in a system whose primary purpose includes reconstruction and resumability. The project hygiene rule remains fail-safe: prove redundancy before removing code.
