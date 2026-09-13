# WORK CONTINUITY PROTOCOL — BINDING

Status: BINDING
Updated: 2026-09-13
Applies to: DAX Daytrading Bot project work, especially long engineering/research sequences and delegated ChatGPT Work tasks

## Purpose

Protect engineering time, debugging time, research time and optimization time from avoidable interruptions. A progress report is visibility only; it is never a stop signal by itself. This document is also the canonical owner for how the main project chat delegates bounded work to ChatGPT Work.

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

A dependency lane may stop only for one of these reasons:

1. A real milestone has been completed and the next phase requires a genuine project decision.
2. A concrete user action is technically necessary and cannot be performed through the available tools.
3. A hard technical blocker remains after reasonable recovery routes were exhausted.
4. A safety/security/execution-authorization boundary requires a stop.
5. Continuing would violate a binding project rule or corrupt VERIFIED evidence.
6. The user explicitly orders a STOP or a controlled chat handoff; this is an explicit sequence interruption and must be durably recorded before stopping when repository access is available.

### 4A. Lane blocker versus global project stop

A stop condition applies first to the dependency lane that actually needs it. It is NOT automatically a global project stop.

Examples of lane-local blockers:
- a real Windows/MT5 host test is required;
- the user must perform a physical/local action unavailable to tools;
- a future market session or external event must occur before evidence can exist;
- one unavailable credential/provider blocks one optional integration.

When a lane is blocked:
1. mark that exact step/dependency `WAITING_EXTERNAL`, `BLOCKED`, or the project's appropriate status;
2. preserve what evidence/user action will unblock it;
3. immediately inspect the backlog/gates for the next independent safe work unit;
4. continue with the next whole-number step without asking for permission.

A global work sequence may stop only when a valid stop condition exists AND no useful independent safe work unit remains, or when a project-wide safety/governance boundary itself forbids further work, or when the user explicitly requested a controlled STOP/chat handoff.

If independent safe work remains, finalizing because one lane is waiting is a process defect unless the user explicitly requested that stop.

## 5. No artificial approval gates

Do not ask for approval merely because:

- a sub-step finished;
- a test passed;
- a file was found;
- a harmless warning appeared;
- the next step was already defined;
- the work is long;
- a different read-only tool path is needed;
- the client was temporarily backgrounded or disconnected and execution has since resumed;
- one host/user/external dependency lane is waiting while independent work remains.

Intermediate reports are for operator visibility, not permission.

## 6. Durable knowledge trail for solved problems

Every unusual/non-obvious solved engineering or test problem must leave a reusable knowledge trail:

`Problem/Failure -> Root Cause -> Fix/Decision -> Regression Test/Evidence -> Reuse Rule`

A fix is not considered fully complete until cause, fix and regression evidence are later findable. Prefer the existing governance/problem-solution structures; do not create parallel architectures without need.

## 7. Time-protection principle

Before creating new code, tests, adapters, recovery layers or data structures, first inspect whether an existing owner already solves the problem. Reuse is preferred over duplication when correctness, evidence and safety remain equal or better.

Avoid re-solving known problems. Avoid unnecessary stop/start cycles. Avoid asking the user to re-provide repository facts that can be re-fetched.

## 8. Visibility rule

For long work blocks, keep the user informed with concise numbered updates, but continue execution after each update unless section 4 applies globally under section 4A.

Preferred visible form:

`Schritt N: Tätigkeit -> Zwischenstand -> ✅ / ⚠️ / ❌ -> nächster Schritt läuft`

The phrase `nächster Schritt` means the next step is actually executed in the same ongoing work sequence, not merely announced.

## 9. Official step-numbering rule

Official project work uses one continuous integer sequence only:

`... -> STEP 2024 -> STEP 2025 -> STEP 2026 -> ...`

Do not introduce official decimal, letter or nested step numbers such as `2024.1`, `2024.3p`, `2024a` or similar. Such subdivisions distort the 500-step audit cadence and make milestone accounting ambiguous.

A step represents one independent concrete work unit or one tightly coupled verification unit. When that unit is finished, the next independent implementation, documentation change, adapter, test package, audit action or repository modification consumes the next integer step.

Several inseparable checks may stay inside the same step only when they verify the same concrete change and would be misleading as separate project work units. Do not use one step as a container for many distinct deliverables merely to avoid nested numbering.

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

This protocol is being followed only when progress reports are followed by continued concrete work unless a valid global stop condition is explicitly identified.

A response that ends merely because the assistant summarized recovered context, reported a tool error, restated the next step, reached an intermediate finding, resumed after a temporary client interruption, or encountered one externally blocked lane fails this acceptance criterion unless section 4A shows that no independent safe work remains or the user explicitly ordered the stop/handoff.

## 12. Main chat versus ChatGPT Work — binding roles

ChatGPT Work is an independent bounded audit/Red-Team/implementation workbench. It is not the project master architect.

The main project chat owns:
- architecture and roadmap ordering;
- task selection and decomposition;
- scope boundaries and safety constraints;
- acceptance of Work results;
- final classification of evidence;
- Acceptance refresh and merge decisions;
- sequencing of numbered project steps.

ChatGPT Work is best used at high-leverage control points such as CI/truth-layer hardening, persistence/restore/recovery, execution safety, pre-merge and pre-PAPER reviews. Do not flood the project with many parallel Work jobs. Prefer one tightly scoped high-value assignment at a time.

A Work result is never automatically accepted merely because Work reports success. The main chat must re-pin repository truth, inspect the exact result/diff and required CI, distinguish skipped external gates, and then decide whether the result is VERIFIED/IMPLEMENTED, needs further hardening, changes Acceptance, or remains WAITING_EXTERNAL.

## 13. Mandatory Work-order header and assignment format

Every new Work assignment should begin with a compact header that makes capability/cost explicit, for example:

`👷 WORK-AUFTRAG — MODELL: GPT-5.6 SOL — DENKSTUFE: MITTEL — IMPLEMENTIERUNG ERLAUBT — 💳 CREDIT-BUDGET: NIEDRIG–MITTEL`

The exact model available may change; use the best appropriate currently available model/configuration rather than hard-coding an unavailable option. The header must still state the chosen model/configuration and thinking level when the product exposes them.

Thinking level is selected by task complexity, not status/prestige:
- LOW/LEICHT: narrow deterministic lookup, tiny isolated fix, mechanical verification;
- MEDIUM/MITTEL: bounded multi-file implementation, focused architecture/composition audit;
- HIGH/HOCH: cross-cutting Red-Team, recovery/consistency review, pre-merge/pre-PAPER architecture or safety audit.

Every Work order must pin or state at minimum:
1. repository, branch and PR;
2. exact starting HEAD SHA and instruction to re-check actual HEAD before work;
3. READ-ONLY audit versus IMPLEMENTATION permission;
4. exact scope/files/contracts and intended outcome;
5. forbidden actions and non-goals;
6. frozen/accepted reference constraints when relevant;
7. execution-safety boundary;
8. required local tests, CI checks and external evidence classification;
9. expected final evidence/report shape;
10. branch-drift rule: never overwrite a newer head blindly.

If the exact branch head moved unexpectedly, Work must re-pin and reconcile before writing. It must not force an old patch over newer repository truth.

## 14. Credit-budget discipline

Work credits are an engineering resource. Spend them where independent execution materially reduces risk or main-chat workload.

Use these practical classes:
- **LOW / NIEDRIG:** narrow file/test/docs fix, isolated deterministic audit, small bounded verification;
- **MEDIUM / MITTEL:** focused multi-file change, bounded architecture/composition implementation, moderate regression package;
- **HIGH / HOCH:** whole-PR Red-Team, cross-cutting restore/recovery/CI/security hardening, pre-merge or pre-PAPER independent review.

Ranges such as `NIEDRIG–MITTEL` or `MITTEL–HOCH` are allowed when uncertainty is genuine.

Credit rules:
- prefer the smallest Work unit that buys meaningful independent evidence;
- do not spend Work credits on repetitive status polling or cheap steering the main chat can do directly;
- use higher budget for hard-to-reconstruct semantic/state/recovery defects, broad regression campaigns and independent final gates;
- split very large umbrella requests into bounded high-value assignments when this improves auditability;
- connectors/plugins may be used when genuinely helpful and authorized, but Work must not assume an unavailable capability or silently replace missing external evidence with simulation.

## 15. Work safety, Acceptance and merge ownership

Unless a Work order explicitly says otherwise, Work must NOT:
- merge a PR;
- update Acceptance status;
- enable broker submission;
- set `order_execution_enabled=true`;
- authorize PAPER or LIVE;
- change frozen V11.2 evidence/fingerprints;
- change strategy parameters/cost assumptions outside the assigned scope;
- manufacture Windows/MT5/Neon/external evidence not actually executed.

Skipped external gates must be reported separately as `WAITING_EXTERNAL`; green Linux/unit CI cannot substitute for real-host evidence.

Acceptance and merge remain main-chat decisions. Before any merge, Acceptance must be deliberately refreshed against the exact current PR head and all required evidence classes.

## 16. Integrating out-of-band Work commits

If Work lands commits while the official numbered pointer is on a different unfinished step:
1. do not retroactively relabel those commits as that numbered step;
2. verify exact commit chain/diff/CI in the main chat;
3. record them as out-of-band Work evidence with classification and safety status;
4. mark the interrupted numbered step honestly if user/task interruption occurred;
5. use the next unused whole-number continuity/reconciliation step to restore pointer, Masterstand and handoff consistency;
6. carry the interrupted technical scope prospectively to a later whole-number step.

This preserves repository truth without falsifying the official work ledger.
