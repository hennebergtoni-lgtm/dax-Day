# Recovery and Reconstruction Contract V1

Status: BINDING SAFETY CONTRACT

## Goal
A database outage, CI interruption, Colab/runtime loss, repository connection loss, or interrupted research run must not force reconstruction from memory or silently change the active V11.2 reference.

## Canonical recovery layers
1. **Git repository** — source, migrations, manifests, tests, research definitions, frozen reference metadata.
2. **Audited market-data identity** — normalized session SHA-256 `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`; any recovered data must reproduce it before clean-reference use.
3. **Database migrations + registries** — schema is reconstructible from versioned migrations; active-reference and detail-evidence registries must reconcile after restore.
4. **Run manifest** — every material run binds dataset, engine, configuration and runtime mode fingerprints.
5. **Checkpoint chain** — long runs persist progress only with the matching run-manifest fingerprint and decision-log fingerprint.
6. **Immutable result artifact** — completed material runs export machine-readable results plus hashes before database promotion/import.
7. **Independent evidence state** — missing detailed artifacts remain `NOT_IMPORTED`; never synthesize rows to repair a database.

## Crash barriers
- DATA UNSAFE => NO TRADE / NO PROMOTION.
- Dataset/engine/config/mode fingerprint mismatch => abort run or resume.
- A checkpoint may resume only against the exact run-manifest fingerprint.
- A database restore is incomplete until migrations and integrity/reconciliation checks pass.
- Active V11.2 reference values are never inferred from partial detail rows.
- A CI or runtime interruption is not evidence of a completed research run.
- Temporary GitHub Actions artifacts are convenience copies, not the sole recovery source.

## Required material-run recovery bundle
For every full WF/research run that could affect conclusions, retain:
- `run_manifest.json`
- `checkpoint.json` (during execution)
- `decision_log_manifest.json`
- aggregate result JSON/CSV
- detail artifacts when generated
- SHA-256 checksums for retained artifacts
- source commit SHA
- dataset fingerprint
- engine fingerprint
- configuration fingerprint
- completed/aborted status

## Database recovery procedure
1. Recreate an empty database from versioned migrations in order.
2. Run the DB integrity gate.
3. Restore/import only artifacts whose provenance contract passes.
4. Reconcile expected vs observed rows and hashes.
5. Confirm the active reference registry still identifies the frozen V11.2 aggregate reference.
6. Leave unavailable detail evidence as `NOT_IMPORTED` rather than fabricating it.

## Project/runtime recovery procedure
1. Checkout the last known green commit.
2. Verify CI and engine surface.
3. Verify recovered market-data session fingerprint.
4. Rebuild database from migrations if required.
5. Load the last checkpoint only if its manifest fingerprint matches the intended run.
6. Resume from the checkpoint boundary; otherwise restart the affected run from a deterministic boundary.
7. Compare final artifact hashes/results with any prior retained result before promotion.

## Current gap addressed by V5
The runtime already has in-memory checkpoint provenance and strict resume compatibility, but a complete persistent material-run recovery bundle and restore drill must be added and tested before Paper/Live readiness.
