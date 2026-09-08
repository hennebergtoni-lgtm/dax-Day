# Web Interface Contract V1

Status: BINDING UI SAFETY CONTRACT

## Purpose
The web interface is a read-only observability surface for verified DAX Research Lab state. It must never become a second source of truth for strategy logic, reference values, research promotion, database content or trading permissions.

## Source-of-truth hierarchy
1. Versioned repository contracts and frozen reference metadata.
2. Verified database registries and integrity gates.
3. Immutable run/result artifacts with hashes.
4. UI snapshot generated from those sources.

The UI may display state; it may not silently create or modify canonical state.

## V1 dashboard sections
- Active reference identity and immutable flag.
- Dataset identity, session rows and days.
- Engine source fingerprints.
- WF contract and active-reference aggregate metrics.
- Recovery/readiness state.
- Detail-evidence state (`NOT_IMPORTED`, `PARTIAL`, `VERIFIED`).
- Research tool registry with evidence status.
- Last green CI / recovery-preflight state when available.

## Safety barriers
- No order buttons.
- No Paper/Live enable control.
- No strategy-parameter write controls.
- No database mutation from the static UI.
- Unknown or stale values render as UNKNOWN/STALE, never inferred green.
- Reference metrics are marked immutable and source-linked.
- Research-only tools are visibly separated from DEPLOYABLE tools.

## Architecture
V1 is static and dependency-light: `web/index.html` reads `web/status.json`. A future generator may refresh `status.json` from verified sources, but generation must fail closed on integrity errors. The UI itself contains no trading logic.
