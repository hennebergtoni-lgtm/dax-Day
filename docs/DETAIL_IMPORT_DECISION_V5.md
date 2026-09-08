# Detail Import Decision V5

Status: PRODUCTIVE DB UNCHANGED

## Decision
Do not import V11.2 detail rows into the productive research database during V5.

## Evidence now available
- WF metrics: 243 rows, frozen historical hash reproduced exactly.
- Selected variants: 81 rows, frozen historical hash reproduced exactly.
- Trades: 856 rows, clean reproducible artifact generated with a new deterministic hash; historical original trade-file hash was not recovered.

## Why import is still deferred
The repository has pre/post import guards and evidence contracts, but no completed dedicated idempotent detail-import writer is currently part of the production path. Creating one and immediately writing the productive DB in the same hygiene phase would unnecessarily combine two risks.

## Required before productive detail import
1. typed CSV/schema validation;
2. stable deterministic source-row identities;
3. source_artifact registration;
4. one-artifact-per-transaction import;
5. duplicate/idempotency test;
6. conflicting-row rollback test;
7. isolated-schema import drill;
8. post-import aggregate reconciliation;
9. normal DB integrity gate remains green;
10. explicit distinction between historically hash-matched artifacts and newly reproducible clean artifacts.

## Trade evidence semantics
The newly generated trade artifact is valid reproducible clean evidence, but it must not be mislabeled as the historically recovered original trade file. Until the evidence model explicitly represents that distinction, `TRADES` remains `NOT_IMPORTED` in the productive registry.

## Result
Safety and evidence have improved without changing the productive DB or weakening the old fail-closed contract.
