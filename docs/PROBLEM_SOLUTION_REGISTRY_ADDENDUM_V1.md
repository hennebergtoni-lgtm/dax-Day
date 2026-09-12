# Problem / Solution Registry — Addendum V1

Status: BINDING ENGINEERING MEMORY / EXTENDS `PROBLEM_SOLUTION_REGISTRY.md`
Updated: 2026-09-12

This addendum continues the canonical PSR numbering without rewriting the large historical registry. It is part of the same mandatory lookup surface and must be reviewed together with `docs/PROBLEM_SOLUTION_REGISTRY.md` until a later canonical consolidation.

---

## PSR-014 — Timeframe literals can pass isolated tests while integration is incompatible

**Status:** VERIFIED / FIXED
**Component:** CAND-001 MT5 feed -> virtual lifecycle integration

**Problem:** The MT5-to-Candidate bridge emitted the canonical timeframe literal `5m`, while the first virtual lifecycle implementation required the literal `M5`. Both components could pass their isolated tests but failed when connected in the real forward path.

**Root cause:** Timeframe semantics were duplicated as component-local string assumptions instead of being owned by the Candidate config contract and exercised through an integration path.

**Accepted solution:** Treat `Cand001Config.bar_timeframe == "5m"` as the canonical CAND-001 runtime representation. The forward MT5 path uses `5m`. The lifecycle was corrected to accept the canonical representation; any temporary `M5` compatibility exists only for legacy isolated evidence and must not become a second canonical runtime spelling.

**Proof/evidence:** `src/daxlab/runtime/candidate_config.py`; `src/daxlab/runtime/candidate_mt5_feed.py`; `src/daxlab/runtime/candidate_virtual_lifecycle.py`; `tests/test_candidate_virtual_lifecycle_timeframe.py`; end-to-end CAND-001 SHADOW orchestrator/feed tests on PR #109.

**Reuse rule:** Shared semantic values such as symbol/timeframe/session must have one canonical owner. Isolated green tests are insufficient when neighboring components can encode the same concept differently; add an integration contract at each boundary.

---

## PSR-015 — Transport observation time must not change causal strategy identity

**Status:** VERIFIED / FIXED
**Component:** CAND-001 deterministic data/decision identity

**Problem:** Re-fetching the same already-closed market bar at a later supervisor cycle could produce a different Candidate data fingerprint and downstream Decision ID solely because `received_at` had changed.

**Root cause:** `received_at` is transport/observability metadata, but it was included in a fingerprint intended to represent causal market/strategy evidence.

**Accepted solution:** Exclude `received_at` from causal strategy fingerprints while retaining it on the Candle/runtime object for observability and freshness. Strategy identity remains bound to market-event information and deterministic strategy state, not to the wall-clock time at which the transport happened to observe the same closed bar.

**Proof/evidence:** Candidate causal-identity tests and continuous-vs-restart/sliding-feed tests on PR #109; same closed market bar with different observation time now retains the same signal/data/Decision identity.

**Reuse rule:** Classify every timestamp as market-event time, effective time, processing time or observation/transport time before including it in deterministic identity. Never allow re-observation metadata to mutate causal strategy identity unless that timing is explicitly part of the strategy definition.

---

## PSR-016 — A blocked dependency lane is not a global project stop

**Status:** BINDING PROCESS FIX
**Component:** engineering continuity / host-dependent evidence

**Problem:** Work was repeatedly finalized when the next sequential proof required the user's Windows/MT5 host even though many safe independent repository tasks remained.

**Root cause:** A valid stop condition for one dependency lane was incorrectly treated as a stop condition for the entire project sequence.

**Accepted solution:** Apply stop conditions first to the affected lane. Mark host/user/future-event dependencies `WAITING_EXTERNAL`, record the unblock evidence, then immediately continue the next independent whole-number work unit. Global stop is allowed only when no useful independent safe work remains or a project-wide safety/governance boundary forbids further work.

**Proof/evidence:** `docs/SESSION_EXECUTION_REFRESHER.md`; `docs/WORK_CONTINUITY_PROTOCOL.md`; DAX-BOT alpha status explicitly classifies current Windows/MT5 Candidate verification as `WAITING_EXTERNAL` while repository work continues.

**Reuse rule:** Before any final/status-only response in an active engineering sequence, check both: (1) is the blocker global, and (2) are there truly no independent safe work units left? If either answer is no, continue working.

---

## PSR-017 — Stale stage-status prose must not override current authorization truth

**Status:** VERIFIED / FIXED
**Component:** project governance / SHADOW-PAPER acceptance state

**Problem:** `docs/SHADOW_PAPER_ACCEPTANCE_V1.md` remained a binding/referenced acceptance contract but still said `Shadow: NOT STARTED` after the project had already authorized no-order SHADOW, accepted repository-side CAND-001 SHADOW integration and recorded real Forward SHADOW milestone evidence. The stale prose could mislead resume logic into downgrading the current stage or, in the opposite direction, a future stale file could incorrectly imply stronger execution authority.

**Root cause:** A long-lived acceptance document mixed stable prerequisite definitions with a mutable point-in-time stage decision and was not reconciled when later canonical Masterstand/acceptance/runtime truth advanced.

**Accepted solution:** Preserve the stable SHADOW/PAPER prerequisites and execution boundaries, but reconcile the current decision against authoritative contemporary sources. The contract now records SHADOW as authorized with no broker orders, keeps current-branch CAND-001 Windows/MT5 host verification separately `WAITING_EXTERNAL`, keeps PAPER not ready/not authorized and LIVE not eligible/not authorized, and explicitly states that the document itself cannot create execution authority.

**Proof/evidence:** Step 2118 repository/backlog reconciliation; Step 2119 update/readback of `docs/SHADOW_PAPER_ACCEPTANCE_V1.md`; current Masterstand, `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_STATUS.md`, `docs/DAX_BOT_1_0_CLOSEOUT_FINAL.md`, `docs/CAND001_WINDOWS_SHADOW_DEPLOYMENT_RUNBOOK_V1.md`, and `docs/CURRENT_WORK_STEP.md`.

**Reuse rule:** During every resume/audit that touches stage or authorization claims, separate stable gate definitions from mutable current-state prose. Reconcile mutable stage claims against the current Masterstand/acceptance status and fresh runtime evidence. A stale document may neither downgrade nor upgrade actual execution authorization; only the canonical current authorization/evidence chain may do that.

---

## PSR-018 — Technical progress, visible step state and pointer/CI truth can drift apart

**Status:** BINDING PROCESS FIX / REGRESSION-GUARDED
**Component:** workflow integrity / step ledger / user-visible progress

**Problem:** Several work units advanced technically while the visible step narrative and `CURRENT_WORK_STEP.md` lagged behind. Tool/interface activity was shown without sufficient normal-text progress reports, older lane wording conflicted with monotonic numbering, and turn-ending language could imply that work continued after the active model turn had actually ended. The result was that the user could no longer reliably tell which step was active, which work was finished, which CI was still red, and whether the project was genuinely progressing.

**Root cause:** The workflow had strong continuity rules but no single explicit Step-Close-Gate tying together: (1) active pointer, (2) step terminal/paused state, (3) exact-head CI/evidence, (4) visible normal-text reporting, (5) interrupted-lane carry-forward, and (6) truthful limits on work after a final response. A conflicting older `Fortsetzung Schritt N` rule also allowed apparent numbering rollback.

**Accepted solution:** Introduce `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md` as the binding owner. Before a new independent step starts, the current step must be explicitly `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL` or `BLOCKED`, with evidence and pointer synchronized. `CURRENT_WORK_STEP.md` must point to the new step before its first substantive action. Old lanes resume only under the next unused higher integer with provenance wording. Explicit user workflow intervention first freezes the current step truth, then consumes the next integer for governance/review. Tool UI does not count as the required normal-text Zwischenstand. A final response ends the active work turn; no invisible continuation may be claimed.

**Proof/evidence:** User-directed general check on 2026-09-12; Step 2131 correctly left incomplete after `research-lab-ci #1089` failed while `dax-bot-1x-ci #305` was green; Step 2132 pointer synchronization; `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`; reconciled `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`; hardened `docs/SESSION_EXECUTION_REFRESHER.md`; workflow-integrity regression tests added in Step 2132.

**Reuse rule:** At every resume and before every step transition ask four concrete questions: `Does the pointer name the actual active step?`, `Is the previous step explicitly closed/paused with evidence?`, `Is required CI checked on the exact current head?`, and `Will the user see a normal-text Zwischenstand before another meaningful tool chain?` If any answer is no, fix workflow state before advancing technical scope.
