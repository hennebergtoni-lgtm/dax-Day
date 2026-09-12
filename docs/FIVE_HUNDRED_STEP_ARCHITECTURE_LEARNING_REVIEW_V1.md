# 500-Step Architecture & Learning Review V1

Status: **BINDING GOVERNANCE CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Every 500 official whole-number steps, normal forward construction pauses for a deliberate architecture and learning review. The checkpoint is not a ceremonial recap. Its job is to prevent the project from building another large block on assumptions, structures, performance characteristics or workflows that newer evidence has made obsolete.

The first next checkpoint governed by this contract is **Step 2500**.

## Review horizon

The review must inspect at least the preceding 500-step block and may reach further back whenever current behavior depends on older assumptions. A design is not protected from review merely because later work was built on top of it.

VERIFIED historical evidence, fingerprints and frozen baselines remain preserved as evidence. The review may change architecture, interpretation, implementation strategy or migration plan only with explicit provenance; it must not rewrite history.

## Mandatory pause

At the 500-step checkpoint:

1. pause ordinary feature expansion;
2. pin repository HEAD, active pointer, CI state and relevant runtime/evidence state;
3. reconstruct what was intended versus what was actually built and observed;
4. complete the review and publish its decisions before normal forward construction resumes.

A 500-step checkpoint does **not** mandate a rewrite. `KEEP` is a valid and preferred result when evidence supports the current design.

## Mandatory review questions

The review must explicitly ask:

- What do we know now that we did not know when the relevant design was chosen?
- Which assumptions proved correct, weak, false or still unverified?
- Which failures, repeated fixes, CI friction or operational incidents reveal structural debt?
- Where is runtime, research or operator workflow slower or more expensive than expected?
- Which modules or contracts carry duplicated truth, unnecessary coupling, dead paths or avoidable compatibility debt?
- Are recovery, persistence, reconciliation, idempotency, data integrity and fail-closed boundaries still coherent?
- Are tests proving behavior or merely preserving implementation shape?
- Are current module boundaries still the cheapest safe way to change one subsystem without destabilizing the rest?
- Which earlier choices would be made differently if the current evidence had been available at the time?
- Have relevant established/public systems, libraries or engineering patterns changed enough to materially improve our approach?

## External / public-source refresh

The review must refresh relevant external knowledge instead of relying only on sources examined hundreds of steps earlier. This may include established trading/backtesting/execution projects and current engineering patterns relevant to the issue under review.

External popularity is not a reason to rewrite. A source matters only when it provides a concrete capability, failure lesson, performance pattern, recovery model, testing pattern or architectural technique that is relevant to our evidence.

## Review dimensions

At minimum evaluate:

- architecture and dependency direction;
- correctness and evidence quality;
- performance and scalability;
- research efficiency and overfitting protection;
- data integrity and provenance;
- state persistence, restart and recovery;
- reconciliation and idempotency;
- safety and authorization boundaries;
- test/CI effectiveness and maintenance cost;
- operator observability and workflow friction;
- obsolete, duplicated or overly complex code paths;
- modularity and migration cost.

## Decision taxonomy

Every material finding must be classified as exactly one of:

- `KEEP` — current design remains justified;
- `IMPROVE` — retain the owner/boundary but improve implementation, tests, performance or workflow;
- `REFACTOR` — architecture/boundary should change while preserving required behavior/evidence;
- `RETIRE` — an owner/path is demonstrably redundant or obsolete and has a safe retirement path;
- `DEFER` — evidence is insufficient or dependency ordering makes change premature.

## Required evidence for change

For every `IMPROVE`, `REFACTOR` or `RETIRE` decision, record before implementation:

- concrete evidence/problem;
- affected owners/modules/contracts;
- expected benefit, preferably measurable;
- compatibility/parity requirements;
- migration sequence;
- failure and rollback path;
- impact on VERIFIED evidence and frozen baselines;
- dependencies and blockers.

Broad rewrites without this evidence are prohibited.

## Performance and efficiency gate

The review must inspect measured or observable cost, not just code style. It should identify slow research loops, unnecessary repeated work, oversized CI/test surfaces, expensive data movement, excessive manual steps, poor resume/checkpoint behavior and operator friction before another 500-step block compounds them.

Optimization remains evidence-led: measured hotspots first. Safety/provenance checks are not removed merely because they cost time unless equivalent protection is proven by a better design.

## Modular-change principle

The project is intentionally modular so that better knowledge can change one subsystem without collapsing the whole system. The review may therefore recommend new boundaries, adapters, ports or migrations when they reduce coupling or improve correctness/efficiency.

Prefer compatibility-first migration and parity proof over deletion-first refactoring. Do not preserve a bad boundary merely because many later steps depend on it; instead design a controlled strangler/migration path.

## Required review output

Before normal construction resumes, the checkpoint must leave durable repository evidence containing:

1. reviewed step range and repository/evidence anchors;
2. major achievements and retained strengths;
3. mistakes, failures and lessons learned;
4. performance/workflow findings;
5. refreshed external/public-source findings where relevant;
6. `KEEP / IMPROVE / REFACTOR / RETIRE / DEFER` decision table;
7. prioritized post-review work plan with dependencies;
8. explicit statement of unchanged VERIFIED baselines/safety constraints;
9. any new risks or unknowns exposed by the review.

## Safety invariants

The review process itself does not authorize broker execution or strategy promotion. Existing authorization and evidence gates remain in force. In particular, no 500-step review may silently change frozen V11.2 evidence, verified historical fingerprints, `NO_STRATEGY_AUTO_PROMOTION`, PAPER/LIVE authorization, or execution safety state.

## Anti-patterns

The following do not satisfy the checkpoint:

- a chronological list of the last 500 steps without critique;
- declaring everything successful because CI is green;
- copying the previous roadmap unchanged without re-evaluation;
- adopting external architecture solely because it is popular;
- rewriting large areas only to make the architecture look cleaner;
- optimizing unmeasured code while leaving known bottlenecks untouched;
- hiding failures or treating prior effort as a reason not to change course.

The objective is controlled learning: preserve what is proven, challenge what is merely inherited, and use new evidence before committing the next large block of work.
