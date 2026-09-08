# Detailed research artifact import contract

Status: IMPLEMENTED POLICY / IMPORTS REMAIN BLOCKED UNTIL SOURCE EVIDENCE EXISTS

## Purpose
Prevent unverified, duplicated, partially imported or silently transformed research rows from entering Neon.

## Eligible source requirements
A detailed artifact is import-eligible only if all are true:
1. provenance identifies the experiment/reference that produced it;
2. file content is immutable for the import attempt;
3. SHA-256 is known and checked before write;
4. expected row count is known and checked before write;
5. required typed fields/schema validate without display-string reconstruction;
6. active dataset and engine fingerprints match the experiment contract;
7. legacy artifacts are explicitly marked and cannot populate active-reference rows by default.

## Pre-import gate
Before opening a write transaction, record and verify:
- source filename/path or immutable locator;
- source SHA-256;
- source row count;
- schema version;
- experiment key;
- dataset fingerprint;
- engine fingerprint;
- expected WF/selection/trade counts where applicable;
- import code Git commit/config fingerprint.

Any mismatch => STOP with no write.

## Idempotency and duplicate protection
- use stable experiment keys;
- use natural/unique keys for WF records;
- use deterministic source row identity for trade rows when available;
- importing the exact same artifact twice must leave database row counts unchanged;
- conflicting content under the same stable identity must fail, never overwrite silently.

## Transaction rule
All rows for one artifact import are written inside one database transaction. Validation or reconciliation failure must roll back the complete import.

## Post-import reconciliation
Before commit, compare database state for the imported scope against the source:
- exact inserted/unchanged counts;
- exact expected unique keys;
- aggregate trade count;
- aggregate return-R where meaningful;
- WF count/cost-model coverage;
- source SHA recorded in import metadata.

After commit, the read-only database integrity gate must pass.

## Forbidden shortcuts
- no reconstruction of missing detailed rows from summary aggregates;
- no substitution of legacy rows for clean-reference rows;
- no parsing of human-readable parameter strings when typed parameters exist;
- no partial commit followed by manual cleanup;
- no changing expected hashes/counts merely to make a failing import pass.

## Current V11.2 clean-reference decision
The summary registry is verified, but its detailed WF/trade source artifacts are not currently present as independently verifiable repository artifacts. Therefore detailed import remains blocked and Neon must continue to report `detailed_rows=NOT_IMPORTED` until the evidence gate is satisfied.
