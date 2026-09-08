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

## Gate decision
**DO NOT IMPORT DETAIL ROWS.**

No detailed WF or trade rows may be reconstructed from summary totals, inferred from legacy V4.0-FIX1 files, copied from unrelated research artifacts, or synthesized to satisfy expected counts.

The database may retain the verified active-reference registry and summary metadata while `detailed_rows=NOT_IMPORTED` remains explicit.

## Unblock condition
Detail import becomes eligible only when a source artifact is located and all of the following pass before any database write:
1. provenance is attributable to the clean V11.2 reference run;
2. artifact byte hash matches a committed expected SHA-256 or is independently frozen through a new evidence artifact;
3. row counts reconcile with the clean reference contract;
4. schema and typed parameter fields are validated;
5. the import is transactional, idempotent and rollback-safe;
6. post-import reconciliation exactly matches the source artifact.

Missing evidence is a blocking condition, not a reason to rebuild the data.