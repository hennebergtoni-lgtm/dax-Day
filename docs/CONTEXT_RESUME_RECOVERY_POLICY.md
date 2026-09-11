# Context Resume & Recovery Policy

Status: IMPLEMENTED GOVERNANCE CONTRACT

Purpose: make project work restartable after chat/tool-context loss without changing any verified research result, frozen baseline, runtime state, or broker-safety boundary.

## 1. Truth hierarchy

When resuming work, durable project evidence outranks conversational context:

1. Git commit SHA / repository contents
2. Versioned database schema and persisted evidence
3. Fresh runtime telemetry read from its authoritative store
4. Verified tests / CI evidence
5. Project handoff or masterstand
6. Chat/tool search context

A missing or expired tool response is never evidence that a repository file, test, runtime component, or prior result is missing.

## 2. Deterministic resume sequence

After any material context loss, compaction, tool-response expiry, or uncertain handoff, resume in this order:

1. Pin the current repository branch and exact commit SHA.
2. Check open pull requests and active work branches.
3. Re-read fresh runtime telemetry before making any current-state claim.
4. Reconstruct only the required repository subtrees or direct file paths from the pinned SHA.
5. Resolve the last VERIFIED project step and its evidence.
6. Rebuild the smallest necessary dependency/consumer map.
7. Continue from that point; do not restart architecture design from memory.

## 3. Repository browsing rule

Prefer direct file paths, Repository Contents, and small pinned subtrees over large transient code-search result sets.

- A code-search result with zero hits is not evidence of absence.
- Absence is established only after checking authoritative repository contents or the relevant pinned subtree/path.
- Important paths, contracts, and architectural reuse points discovered during a work block must be recorded in a durable project artifact or the next masterstand when they materially affect continuation.

## 4. Freshness rule

Runtime statements such as GREEN/BLOCKED, latest heartbeat, latest decision, counts, or current safety state are point-in-time evidence.

Before later claiming a runtime state is still current, re-read the authoritative telemetry source. Never reuse an old heartbeat as a current-state claim.

## 5. Reconciliation rule

Resume by reconstruction and reconciliation, not by assumption.

- Repository state is reconciled against the pinned SHA.
- Database state is reconciled against the actual schema/content when relevant.
- Runtime state is reconciled against fresh telemetry.
- Strategy/runtime integration is reconciled against existing contracts and tests before new components are introduced.

This follows the same engineering principle seen in mature trading systems: persistent state plus deterministic reconstruction is safer than relying on process memory.

## 6. Lean reuse gate

Before creating a new module, schema, table, workflow, persistence path, or monitoring channel:

1. Search the authoritative repository for an existing abstraction.
2. Inspect its consumers, tests, CI/runtime contract, and safety boundary.
3. Reuse or extend the existing abstraction when semantics match.
4. Create something new only when the existing contract cannot represent the required state cleanly.

Do not build a second strategy engine, duplicate telemetry path, duplicate recovery path, or parallel paper-trading architecture without explicit evidence that reuse is unsafe or semantically wrong.

## 7. Public-project scan rule

Regularly compare the project against established open-source trading/backtesting systems, especially NautilusTrader, Freqtrade, QuantConnect LEAN, vectorbt, and comparable projects.

The scan is for engineering patterns such as:

- state persistence and restart behavior
- reconciliation and recovery
- observability / health / status interfaces
- deterministic backtest-to-forward parity
- paper/live separation
- data integrity and causal processing
- performance and overfitting protection
- governance and operational simplicity

Public-project findings are RESEARCH input only. They may improve future design but never retroactively modify VERIFIED baselines or historical evidence.

## 8. Visible continuation rule

Begun step sequences are continued independently and visibly. Intermediate reports are visibility points, not stopping points.

Stop only when:

1. a real milestone has been reached,
2. concrete user input/action is genuinely required,
3. a necessary decision/approval is required, or
4. a hard error or safety-relevant issue is found.

Normal successful checks and small correctable anomalies are not stopping conditions; report them and continue immediately.

## 9. Safety invariants

This policy does not authorize execution capability.

Until separately approved and verified:

- `execution_capability=NONE`
- `order_execution_enabled=false`
- no automatic MT5 `order_send`
- no real broker order
- no claim of profitability, paper readiness, or live readiness

V11.2 remains the frozen negative reference baseline. Resume/recovery work must never rewrite it.
