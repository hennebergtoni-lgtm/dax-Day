# CAND-001 Operator Telemetry V1

Status: IMPLEMENTED / READ-ONLY / NO EXECUTION AUTHORIZATION
Updated: 2026-09-11

## Purpose

Publish fresh CAND-001 operator/runtime evidence without reusing stale static `web/status.json` and without creating any control path back to the bot.

## Data path

1. `scripts/mt5_shadow_supervisor.py` writes the latest local `candidate_operator_snapshot.json` atomically from the canonical `OperatorSnapshot.as_dict()` representation.
2. `src/daxlab/runtime/candidate_operator_telemetry.py` validates the payload as credential-free, structurally coherent and strictly order-disabled.
3. `scripts/export_mt5_shadow_telemetry.py` optionally appends the current Candidate snapshot to Neon together with the existing legacy MT5 SHADOW telemetry export.
4. `db/migrations/0008_cand001_operator_telemetry.sql` stores append-only Candidate snapshots keyed by deterministic `snapshot_fingerprint`.
5. `db/migrations/0009_cand001_operator_current_view.sql` exposes the latest Candidate snapshot through read-only view `cand001_operator_current`.

## Safety invariants

- No browser receives Neon credentials.
- No telemetry code imports MetaTrader5 or exposes an order API.
- Telemetry is observation-only and has no control channel back to the supervisor.
- `execution_capability='NONE'` and `order_execution_enabled=false` are validated in Python and constrained again in the database schema.
- Snapshot persistence is idempotent by `snapshot_fingerprint`.
- `web/status.json` remains stable/versioned evidence only and is not current runtime truth.

## Ownership

- Snapshot semantics: `src/daxlab/runtime/operator_snapshot.py`
- Candidate telemetry validation: `src/daxlab/runtime/candidate_operator_telemetry.py`
- Local supervisor persistence: `scripts/mt5_shadow_supervisor.py`
- Neon transport: `scripts/export_mt5_shadow_telemetry.py`
- Append-only storage/current read view: migrations `0008` / `0009`

## Current boundary

This contract creates a fresh read-only runtime source suitable for a later authenticated/backend web endpoint. It does not itself expose Neon directly to the browser and does not activate any V2 UI control.

Real Windows-host evidence for the current Candidate runtime remains `WAITING_EXTERNAL` and is separate from this repository-side observability implementation.
