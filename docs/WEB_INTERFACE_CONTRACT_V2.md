# Web Interface Contract V2

Status: BINDING / SUPERSEDES WEB_INTERFACE_CONTRACT_V1 FOR CURRENT WEB ARCHITECTURE
Updated: 2026-09-11

## Purpose

Keep the DAX web surface useful without allowing static repository evidence, fresh runtime state and future operator controls to become one ambiguous source of truth.

## Two-source architecture

### 1. Static versioned evidence

Owner: `web/status.json`
Schema: `DAXLAB_WEB_STATIC_STATUS_V2`

May contain:
- frozen REF-V11.2 identity and audited historical metrics;
- versioned research registry/evidence maturity;
- stable replay/reproduction contracts;
- governance states such as PAPER/LIVE blocked;
- links/names of the fresh runtime contract.

Must NOT contain or infer current:
- MT5 terminal/account connection state;
- latest host heartbeat;
- current bar age/health;
- current Candidate decision/position/outcome;
- current Windows-host readiness.

### 2. Fresh Candidate runtime evidence

Owners:
- canonical snapshot: `src/daxlab/runtime/operator_snapshot.py`;
- validator: `src/daxlab/runtime/candidate_operator_telemetry.py`;
- local persistence: `scripts/mt5_shadow_supervisor.py`;
- Neon transport: `scripts/export_mt5_shadow_telemetry.py`;
- append-only storage/current view: migrations `0008` / `0009`;
- pure current read model: `src/daxlab/runtime/candidate_operator_query.py`;
- server/operator reader: `scripts/read_candidate_operator_runtime.py`.

A future browser endpoint must sit behind a server/backend boundary. Neon credentials must never be present in browser code or `web/status.json`.

## Current UI behavior

The current static dashboard must visibly label itself `STATIC EVIDENCE ONLY` and must not present static pre-host values as current runtime truth.

Until a secure runtime endpoint exists, current runtime display in the browser remains unavailable/unknown rather than guessed.

## Future operator controls

`docs/WEB_OPERATOR_CONTROLS_V2_PLANNED.md` defines planned controls for:
- trading tempo;
- risk/exposure profile;
- news/event handling.

Those controls remain disabled/research-only until each backend owner and authorization gate is separately verified. This contract does not authorize any write control.

## Safety invariants

- No order button or direct broker control in the browser.
- No database credential in browser/static assets.
- No strategy parameter mutation from the static dashboard.
- Static and runtime source labels must be explicit.
- Stale/unknown runtime evidence renders unknown/stale, never inferred GREEN.
- `execution_capability=NONE` and `order_execution_enabled=false` remain binding for current Candidate SHADOW telemetry.
- PAPER and LIVE authorization are outside the web layer.

## Supersession

This V2 contract supersedes `docs/WEB_INTERFACE_CONTRACT_V1.md` for current architecture. V1 remains historical provenance and must not be used to justify writing current runtime state into `web/status.json`.
