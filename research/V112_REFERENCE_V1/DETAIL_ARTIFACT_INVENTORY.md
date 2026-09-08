# V11.2 clean reference — detailed artifact inventory

Status: VERIFIED INVENTORY / DETAIL IMPORT BLOCKED

## Verified active summary surface
- `manifest.json`
- `reference_result.json`
- active normal result: 856 OOS trades, -31.309210619787684 R
- WF summary expectation: 243 metric rows
- selected-variant expectation: 81 rows
- referenced WF metrics SHA-256: `4f61f57c21f469685488c52481f779b87b17b599fbcda0da942b5a2ed713709a`
- referenced selected-variants SHA-256: `8b604de454b615a3d789577be3295765e04eab06448cbcd0844a995af9b0a41e`

## Repository inventory result
The active-reference directory currently contains only the manifest and summary result. The detailed WF metrics, selected-variant rows and 856 trade-level rows are not present there as independently verifiable source artifacts.

Repository search did not establish a verifiable source file matching the referenced detailed hashes or selected-variant artifact name.

## Google Drive recovery result — 2026-09-08
Drive recovery located real historical per-WF artifacts, but their provenance is **legacy/recovery evidence**, not the frozen clean-reference source surface.

### V2.0 baseline folder
`ERGEBNIS_V11_2_BOT_V2_0_SESSION_BASELINE_81WF` contains genuine per-WF files such as:
- `Ergebnis_V11.2_BOT_V2.0_v11_WF9_OOS_trades_normal.csv`
- `Ergebnis_V11.2_BOT_V2.0_v11_WF10_OOS_trades_normal.csv`
- `Ergebnis_V11.2_BOT_V2.0_v11_WF11_OOS_trades_normal.csv`
- `..._top10_train.csv` companions

This proves that trade-level legacy artifacts exist on Drive.

### V2.6 recovery folder
`ERGEBNIS_V11_2_BOT_V2_6_SESSION_BASELINE_RESUME_81WF/RECOVERY_WF15_81` contains genuine OOS trade and top-10-train files for the resumed run.

The V2.6 status file explicitly records only WFs 15–23 as recovered, with `recovered_wf_count=9`; the run did not establish a complete 15–81 recovery artifact set.

### Classification
These located files are valuable for:
- legacy provenance,
- historical failure analysis where explicitly labelled legacy,
- diagnosing earlier serialization/parser behavior,
- cross-checking old reported values.

They are **not eligible** to populate the clean-reference 243 WF metric rows / 81 selected variants / 856 clean-reference trades unless an independent provenance/hash reconciliation establishes identity to the clean reference.

## Gate decision
**DO NOT IMPORT CLEAN-REFERENCE DETAIL ROWS.**

No clean-reference detailed WF or trade rows may be reconstructed from summary totals, inferred from legacy V4.0-FIX1/V2.x files, copied from unrelated research artifacts, or synthesized to satisfy expected counts.

The database may retain the verified active-reference registry and summary metadata while `detailed_rows=NOT_IMPORTED` remains explicit.

Legacy-detail artifacts may be catalogued separately under `LEGACY_EVIDENCE_ONLY`; they must never share the clean-reference provenance/status.

## Unblock condition
Clean-reference detail import becomes eligible only when a source artifact is located and all of the following pass before any database write:
1. provenance is attributable to the clean V11.2 reference run;
2. artifact byte hash matches a committed expected SHA-256 or is independently frozen through a new evidence artifact;
3. row counts reconcile with the clean reference contract;
4. schema and typed parameter fields are validated;
5. the import is transactional, idempotent and rollback-safe;
6. post-import reconciliation exactly matches the source artifact.

Missing evidence is a blocking condition, not a reason to rebuild the data.
