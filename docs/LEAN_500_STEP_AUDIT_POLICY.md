# LEAN 500-STEP AUDIT POLICY — BINDING

Status: BINDING
Scope: full DAX Daytrading Bot project
Cadence: at least once every 500 numbered project steps, and earlier after major architecture or infrastructure changes

This policy specializes the recurring full-project audit defined in `docs/MASTERSTAND.md`.

## Objective

The project must not grow into a heavy, opaque or fragile system merely because new work accumulates over time. Every 500-step full-project audit must therefore include an explicit **lean-system review** whose purpose is to keep the bot and its infrastructure small, current, searchable, testable and fast to change.

The preferred outcome is **less code and fewer moving parts when equal or better safety, evidence quality and functionality can be preserved**.

## Mandatory lean review

Every 500-step audit must explicitly inspect and classify:

- dead, superseded or orphaned code paths;
- temporary test/probe/debug files that no longer provide durable value;
- stale fixtures, configs, docs and workflows;
- duplicate or overlapping implementations and truth stores;
- unused dependencies and unnecessary external services/connectors;
- redundant scheduled jobs, database reads/writes and telemetry bridges;
- scripts or notebooks that can be retired because a canonical implementation now exists;
- unnecessarily expensive loops, repeated checks or avoidable long-running research paths;
- code or infrastructure that became redundant because a supported plugin/connector now provides the same capability more directly;
- naming, folder or registry structures that make important objects difficult to find.

Deletion is never based on appearance alone. Compatibility, provenance, recovery and safety must be checked first.

## Cross-subsystem transfer review

Every 500-step audit must also ask:

1. Which recent improvement made one subsystem materially simpler, faster, safer or easier to operate?
2. Can the same pattern be transferred to other bot/research/infrastructure subsystems?
3. Does an established public/open-source project already solve an equivalent problem more cleanly?
4. Can an existing ChatGPT-side plugin/connector remove custom integration code or manual handoffs?
5. Can multiple parallel paths be consolidated behind one canonical interface without losing required evidence or safety boundaries?

Examples include checkpoint/resume patterns, deduplication, state persistence, vectorized research, database-backed telemetry, direct connector reads, contract tests, fail-closed gates and canonical registries.

## Required outcome

The audit must not stop at observations. For every material finding, classify it as one of:

- `VERIFIED`
- `FIX REQUIRED`
- `STALE`
- `DUPLICATE`
- `UNVERIFIED`

For `FIX REQUIRED`, `STALE` or `DUPLICATE`, record one of:

- remove now;
- consolidate/migrate;
- retain temporarily with explicit reason;
- defer with a named dependency or evidence gate.

The final audit summary must include a short **Lean Delta** stating what was removed, consolidated, accelerated or deliberately retained.

## Safety boundary

Lean does not mean removing controls blindly. Safety, provenance, reproducibility, recovery evidence, frozen-reference integrity and `execution_capability=NONE` / `order_execution_enabled=false` invariants take precedence over code-count reduction.

The target is not minimal code at any cost. The target is the **smallest system that remains correct, observable, reproducible, recoverable and safe**.
