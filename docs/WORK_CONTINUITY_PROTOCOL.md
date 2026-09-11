# WORK CONTINUITY PROTOCOL — BINDING

Status: BINDING
Updated: 2026-09-11
Applies to: DAX Daytrading Bot project work, especially long engineering/research sequences

## Purpose

Protect engineering time, debugging time, research time and optimization time from avoidable interruptions. A progress report is visibility only; it is never a stop signal by itself.

## 1. Core execution rule

Once a numbered work sequence has started, continue automatically through the next reasonable steps until one of the explicit stop conditions in section 4 is reached.

Required loop:

`STEP N -> perform concrete work -> report short result -> classify -> immediately continue with STEP N+1`

A message such as `Zwischenstand`, `✅`, `⚠️`, a discovered file, a partial result or a completed sub-check does NOT end the sequence.

## 2. Error-severity handling

Use the project's 1–5 severity scale.

- Severity 1: minor/weak issue. Handle internally and continue.
- Severity 2: noticeable but harmless issue. Retry, use an alternate path or reconstruct context and continue. No user approval required.
- Severity 3: requires work. Exhaust several reasonable recovery paths independently. Stop only if those paths fail and a real blocker remains.
- Severity 4: serious/near miss. Continue only where safe; stop if a real technical or safety blocker exists.
- Severity 5: broken/unsafe. Stop and surface the blocker clearly.

Tool/search/context failures are normally severity 1–2 unless evidence shows otherwise. Examples: stale response pointer, GitHub code-search miss, truncated search result, temporary context loss. These must trigger fallback/re-fetch/re-pin behavior, not a conversational stop.

A tool failure, context compaction/loss, stale resource pointer, search miss, intermediate summary or reconstructed status is NEVER by itself a valid stop condition. After recovery/reconstruction, concrete work must resume automatically unless one of the explicit stop conditions in section 4 actually applies.

## 3. Automatic recovery after context/tool/client disruption

When context or a tool view is lost:

1. Re-pin repository, branch and exact head SHA.
2. Reconcile PR and CI state if relevant.
3. Re-fetch concrete repository paths instead of trusting stale search results.
4. Reconstruct the last VERIFIED numbered step from repository truth.
5. Continue from that exact step without asking the user to repeat known information.

Repository truth outranks chat recollection.

Client visibility is not a permission gate. If the user backgrounds the ChatGPT app while the current turn remains active, continue the current work sequence without waiting for foreground interaction.

If iOS, network loss, the app, or the platform actually suspends/terminates the active turn, no claim may be made that work continued invisibly while execution was unavailable. At the first later turn where execution is available again, automatically reconstruct repo/branch/head/CI/last VERIFIED step and resume concrete work immediately without asking for re-approval or repetition of known context.

A temporary client disconnect is therefore a resume/recovery event, not a project stop condition.

## 4. The only valid stop conditions

A work sequence may stop only for one of these reasons:

1. A real milestone has been completed and the next phase requires a genuine project decision.
2. A concrete user action is technically necessary and cannot be performed through the available tools.
3. A hard technical blocker remains after reasonable recovery routes were exhausted.
4. A safety/security/execution-authorization boundary requires a stop.
5. Continuing would violate a binding project rule or corrupt VERIFIED evidence.

If none of these conditions is true, continue working.

## 5. No artificial approval gates

Do not ask for approval merely because:

- a sub-step finished;
- a test passed;
- a file was found;
- a harmless warning appeared;
- the next step was already defined;
- the work is long;
- a different read-only tool path is needed;
- the client was temporarily backgrounded or disconnected and execution has since resumed.

Intermediate reports are for operator visibility, not permission.

## 6. Durable knowledge trail for solved problems

Every unusual/non-obvious solved engineering or test problem must leave a reusable knowledge trail:

`Problem/Failure -> Root Cause -> Fix/Decision -> Regression Test/Evidence -> Reuse Rule`

A fix is not considered fully complete until cause, fix and regression evidence are later findable. Prefer the existing governance/problem-solution structures; do not create parallel architectures without need.

## 7. Time-protection principle

Before creating new code, tests, adapters, recovery layers or data structures, first inspect whether an existing owner already solves the problem. Reuse is preferred over duplication when correctness, evidence and safety remain equal or better.

Avoid re-solving known problems. Avoid unnecessary stop/start cycles. Avoid asking the user to re-provide repository facts that can be re-fetched.

## 8. Visibility rule

For long work blocks, keep the user informed with concise numbered updates, but continue execution after each update unless section 4 applies.

Preferred visible form:

`Schritt N: Tätigkeit -> Zwischenstand -> ✅ / ⚠️ / ❌ -> nächster Schritt läuft`

The phrase `nächster Schritt` means the next step is actually executed in the same ongoing work sequence, not merely announced.

## 9. Official step-numbering rule

Official project work uses one continuous integer sequence only:

`... -> STEP 2024 -> STEP 2025 -> STEP 2026 -> ...`

Do not introduce official decimal, letter or nested step numbers such as `2024.1`, `2024.3p`, `2024a` or similar. Such subdivisions distort the 500-step audit cadence and make milestone accounting ambiguous.

A step represents one independent concrete work unit or one tightly coupled verification unit. When that unit is finished, the next independent implementation, documentation change, adapter, test package, audit action or repository modification consumes the next integer step.

Several inseparable checks may stay inside the same step only when they verify the same concrete change and would be misleading as separate project work units. Do not use one step as a container for many distinct deliverables merely to avoid nested numbering.

Examples:
- implement one lifecycle module + its immediate direct regression check: may remain one tightly coupled step;
- then update the durable problem registry: next integer step;
- then add a separate forward-performance adapter: next integer step;
- then build a distinct end-to-end integration test package: next integer step.

The objective is a meaningful, approximately uniform work counter. Both excessive subdivision and excessive bundling are defects because either one distorts the 500-step audit cadence.

The 500-step audit cadence is measured only by the integer sequence. Therefore, after the completed STEP 2000 audit, the next full audit remains STEP 2500.

If an assistant previously introduced decimal/letter substeps or over-bundled several independent work units into one integer, do not rewrite historical repository evidence or renumber committed history. Correct prospectively by continuing with the next unused integer and applying this granularity rule consistently.

## 10. Project safety remains unchanged

This continuity rule never overrides execution authorization or scientific governance.

- SHADOW: authorized.
- PAPER: not authorized unless explicitly changed later.
- LIVE: not authorized.
- `execution_capability=NONE` remains binding where currently specified.
- `order_execution_enabled=false` remains binding where currently specified.
- VERIFIED baselines/evidence are never silently rewritten.

## 11. Operational acceptance criterion

This protocol is being followed only when progress reports are followed by continued concrete work unless a valid stop condition is explicitly identified. A status-only termination without a valid stop condition is a process defect and must not be repeated.

A response that ends merely because the assistant summarized recovered context, reported a tool error, restated the next step, reached an intermediate finding, or resumed after a temporary client interruption fails this acceptance criterion unless section 4 provides a real stop reason.
