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

## 3. Automatic recovery after context/tool disruption

When context or a tool view is lost:

1. Re-pin repository, branch and exact head SHA.
2. Reconcile PR and CI state if relevant.
3. Re-fetch concrete repository paths instead of trusting stale search results.
4. Reconstruct the last VERIFIED numbered step from repository truth.
5. Continue from that exact step without asking the user to repeat known information.

Repository truth outranks chat recollection.

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
- a different read-only tool path is needed.

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

## 9. Project safety remains unchanged

This continuity rule never overrides execution authorization or scientific governance.

- SHADOW: authorized.
- PAPER: not authorized unless explicitly changed later.
- LIVE: not authorized.
- `execution_capability=NONE` remains binding where currently specified.
- `order_execution_enabled=false` remains binding where currently specified.
- VERIFIED baselines/evidence are never silently rewritten.

## 10. Operational acceptance criterion

This protocol is being followed only when progress reports are followed by continued concrete work unless a valid stop condition is explicitly identified. A status-only termination without a valid stop condition is a process defect and must not be repeated.
