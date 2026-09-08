# MT5 Read-Only Recovery Evidence V1

Status: IMPLEMENTED PREPARATION

- Host evidence is immutable, hash-addressed and credential-free.
- Canonical JSON is sorted and compact; payload SHA-256 plus timestamp/kind derive the evidence ID.
- Password, OTP, account-number, API-key, secret and related credential/account fields are rejected recursively.
- Recovery manifest entries retain only schema, evidence ID and payload hash; no account identifiers or credentials.
- Identical evidence is idempotent; tampering is detected during round-trip restore.
- This module is deliberately separate from the canonical `runtime/recovery_bundle.py` implementation and introduces no dependency on legacy recovery code.
- No deletion or consolidation of recovery implementations is performed in V7. Compatibility/recoverability must be proven before any later refactor.
- Evidence describes read-only host observations only. It cannot authorize Paper, Live or order execution.
