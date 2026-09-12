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