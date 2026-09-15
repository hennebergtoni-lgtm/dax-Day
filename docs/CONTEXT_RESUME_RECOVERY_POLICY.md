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

After any material context loss, compaction, tool-response expiry, long interruption, or uncertain handoff, resume in this order:

1. Pin the current repository branch and exact commit SHA.
2. Check open pull requests and active work branches.
3. Read `docs/MASTERSTAND.md` for current project truth and safety boundaries.
4. Read `docs/PROJECT_KNOWLEDGE_INDEX.md` to locate the authoritative sources for the topic being resumed.
5. Read `docs/PROBLEM_SOLUTION_REGISTRY.md` before designing a fix, so previously solved engineering problems are reused rather than rediscovered.
6. Re-read fresh runtime telemetry before making any current-state claim.
7. Reconstruct only the required repository subtrees or direct file paths from the pinned SHA.
8. Resolve the last VERIFIED project step and its evidence.
9. Rebuild the smallest necessary dependency/consumer map.
10. Continue from that point; do not restart architecture design from memory.

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

1. Read `docs/PROJECT_KNOWLEDGE_INDEX.md` for the canonical abstraction/source for the topic.
2. Search `docs/PROBLEM_SOLUTION_REGISTRY.md` for earlier defects, root causes and accepted fixes in the same component.
3. Search the authoritative repository for an existing abstraction.
4. Inspect its consumers, tests, CI/runtime contract, and safety boundary.
5. Reuse or extend the existing abstraction when semantics match.
6. Create something new only when the existing contract cannot represent the required state cleanly.

Do not build a second strategy engine, duplicate telemetry path, duplicate recovery path, or parallel paper-trading architecture without explicit evidence that reuse is unsafe or semantically wrong.

## 7. Public-project scan rule

Regularly compare the project against established open-source trading/backtesting systems, especially NautilusTrader, Freqtrade, QuantConnect LEAN, vectorbt, and comparable projects.

Before rescanning a donor or topic, read the current public-donor sources from `docs/PROJECT_KNOWLEDGE_INDEX.md` so existing findings are treated as prior knowledge rather than rediscovered.

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

### Binding visible work cadence

For tool-backed project work, the visible interaction cadence is mandatory:

1. `Schritt N` plus a short plain-language statement of the activity being performed;
2. execute only the next bounded tool action or small logically inseparable tool cluster;
3. provide a visible **textual Zwischenstand** before starting the next tool block;
4. mark the result plainly as `✅` positive/verified, `⚠️` anomaly/open point, or `❌` error/blocker where applicable;
5. state the **immediate next step** in text;
6. continue automatically unless a real stop condition exists.

Tool output, activity indicators, or hidden/internal reasoning are **not** a substitute for the textual Zwischenstand. Do not run long chains of tool calls without explanatory text between meaningful work units. For a longer operation, expose meaningful checkpoints as the work proceeds rather than disappearing into an extended invisible block.

This visibility rule survives chat changes, compaction, reconnects and handovers. On resume, re-establish the same cadence immediately; do not fall back to silent tool chains.

Stop only when:

1. a real milestone has been reached,
2. concrete user input/action is genuinely required,
3. a necessary decision/approval is required, or
4. a hard error or safety-relevant issue is found.

Normal successful checks and small correctable anomalies are not stopping conditions; report them and continue immediately.

Operational error-severity rule for ongoing project work:
- severity 1–2/5: recover internally and continue; never stop solely for these levels;
- severity 3/5: attempt reasonable recovery paths first and stop only if it becomes a real blocker or requires user input;
- severity 4–5/5: stop the affected operation, state the cause and protect repository/runtime/safety state.

## 9. Safety invariants

This policy does not authorize execution capability.

Until separately approved and verified:

- `execution_capability=NONE`
- `order_execution_enabled=false`
- no automatic MT5 `order_send`
- no real broker order
- no claim of profitability, paper readiness, or live readiness

V11.2 remains the frozen negative reference baseline. Resume/recovery work must never rewrite it.

## 10. Durable engineering memory rule

Non-trivial engineering knowledge must not remain only in chat, transient tool output or an isolated test.

Record a durable entry in `docs/PROBLEM_SOLUTION_REGISTRY.md` when a problem has a reusable root cause or solution, including at minimum:
- observed problem/symptom;
- root cause;
- accepted solution or current decision;
- proof/evidence/tests;
- reuse rule / what must not be repeated;
- supersession link if a later solution replaces it.

Update `docs/PROJECT_KNOWLEDGE_INDEX.md` when a canonical source changes or a new project-wide knowledge category becomes material.

At every mandatory 500-step full-project audit, review both documents for stale, missing, duplicate or superseded knowledge. The objective is a small, navigable engineering memory, not documentation volume.
