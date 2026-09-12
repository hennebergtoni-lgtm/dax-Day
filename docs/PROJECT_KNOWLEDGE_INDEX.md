# Project Knowledge Index — DAX Daytrading Bot

Status: BINDING NAVIGATION CONTRACT
Updated: 2026-09-12

Purpose: make important project knowledge discoverable by topic so context loss never forces rediscovery from memory. This file is a navigation layer, not a replacement for evidence, code, tests or historical documents.

## Mandatory resume order

After context loss, compaction, long interruption, uncertainty about prior work, or any explicit `weiter` / `fortsetzen` instruction:

1. Read `docs/SESSION_EXECUTION_REFRESHER.md` first.
2. Pin repository, branch and exact commit SHA.
3. Read `docs/CURRENT_WORK_STEP.md` and use its canonical whole-number pointer. Reconstruct from commit evidence only if the ledger is missing/inconsistent; never infer the step number from chat memory or raw commit count.
4. Read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md` and confirm the Step-Close-Gate/pointer state is consistent before substantive work.
5. Read `docs/MASTERSTAND.md` for current project truth and safety boundaries.
6. Read this `docs/PROJECT_KNOWLEDGE_INDEX.md` to locate authoritative topic sources.
7. Read `docs/PROBLEM_SOLUTION_REGISTRY.md` and `docs/PROBLEM_SOLUTION_REGISTRY_ADDENDUM_V1.md` for previously solved engineering problems before designing a new fix.
8. Read only the topic-specific authoritative files and relevant tests/consumers listed below.
9. Re-read fresh runtime telemetry before making any current-runtime claim.
10. Continue from the canonical whole-number step; do not redesign from chat memory and do not introduce decimal/letter substeps.

## Knowledge map

| Topic | Authoritative/current source(s) | Status / usage | Historical / secondary sources |
|---|---|---|---|
| Overall project state | `docs/MASTERSTAND.md` | Primary durable handover/source-of-truth below exact repo/code/evidence; refreshed for the 2026-09-12 next-chat handover | Older Masterstand revisions remain available through Git history |
| Current work-step numbering | `docs/CURRENT_WORK_STEP.md` | Binding numbering pointer and reconstructed whole-number ledger; numbering only, never overrides code/evidence/safety | Commit history is reconstruction evidence when the pointer is inconsistent |
| Workflow integrity / step close | `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`, `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`, `tests/test_workflow_integrity_gate.py` | Binding Step-Close-Gate, pointer-before-next-step, monotonic interrupted-lane carry-forward, visible-progress and no-background-work truth | `WORK_CONTINUITY_PROTOCOL.md` remains detailed continuity policy |
| Session execution refresher | `docs/SESSION_EXECUTION_REFRESHER.md` | Mandatory first read on resume/continue; compact enforcement reminder before substantive work | Detailed rules remain in workflow-integrity/handoff/continuity contracts |
| Context recovery / continuous work | `docs/CONTEXT_RESUME_RECOVERY_POLICY.md`, `docs/WORK_CONTINUITY_PROTOCOL.md` | Binding resume/reconciliation and minimal-stop rules, including lane-blocker vs global-stop handling | None should override the Workflow Integrity Gate on step closure/numbering |
| Previously solved problems | `docs/PROBLEM_SOLUTION_REGISTRY.md`, `docs/PROBLEM_SOLUTION_REGISTRY_ADDENDUM_V1.md` | Mandatory pre-design lookup; addendum includes `PSR-018` workflow-drift protection | Local issue-specific docs remain evidence |
| Step-2000 migration backlog | `docs/DAX_BOT_1X_MIGRATION_BACKLOG_STEP_2000.md`, `docs/DAX_BOT_1X_BACKLOG_RECONCILIATION_2134.md` | Step-2000 remains historical audit snapshot; Step-2134 reconciliation records current resolved/open/external status and selects CI ownership as the next safe repo gap | Future full audit at Step 2500 supersedes when completed |
| CI ownership / responsibility | `docs/CI_OWNERSHIP_CONTRACT_V1.md`, `tests/test_ci_ownership_contract.py`, `.github/workflows/ci.yml`, `.github/workflows/dax-bot-1x-ci.yml`, `.github/workflows/reference-payload-export.yml` | Hybrid CI contract: broad repository integration/regression owner + focused Candidate/broker-safety owner + immutable legacy-reference owner; focused gates do not replace aggregate regression and CI never grants PAPER/LIVE authorization | Step-2000 CI-mixing observation and Step-2134 public comparison are provenance |
| Stable branch governance | `docs/STABLE_BRANCH_GOVERNANCE_V1.md`, `tests/test_stable_branch_governance.py` | `main` is currently observed unprotected with no rulesets; minimum target is PR-only changes + universal broad `test` check + no force-push/delete. Enforcement remains `WAITING_EXTERNAL / MANUAL_GITHUB_ADMIN` until fresh GitHub evidence proves protection is active. | Step-2000 branch-protection observation is provenance |
| DAX-BOT 1.x migration safety | `docs/DAX_BOT_1X_MIGRATION_SAFETY_GATE.md` | Binding migration constraints | Older V10/V11 reviews are context only |
| DAX-BOT 1.x alpha acceptance | `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_GATE.md`, `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_STATUS.md`, `docs/DAX_BOT_1_0_CLOSEOUT_FINAL.md` | Repository-side 1.0-alpha accepted; real Windows-host Candidate verification remains a separate `WAITING_EXTERNAL` lane | Candidate tests/code remain executable proof |
| CAND-001 economic evidence | `docs/CAND001_ECONOMIC_EVIDENCE_AUDIT_V1.md`, `src/daxlab/research/cand001_historical_replay.py`, `src/daxlab/research/cand001_recovered_m5_replay.py`, `src/daxlab/research/cand001_oos_walk_forward.py`, `src/daxlab/research/cand001_oos_measurement_runner.py`, `src/daxlab/research/cand001_oos_aggregation.py`, `src/daxlab/research/cand001_oos_evidence_export.py`, `src/daxlab/research/cand001_oos_evidence_reader.py`, `src/daxlab/research/cand001_oos_cost_consistency.py`, `src/daxlab/research/cand001_oos_stability.py`, `src/daxlab/research/cand001_oos_diagnostic_evidence.py`, `src/daxlab/research/cand001_oos_diagnostic_reader.py`, `scripts/run_cand001_oos_wf.py`, `scripts/build_cand001_oos_diagnostics.py` | Descriptive replay, frozen 45/20/20 OOS contract, measurement runner, aggregation, immutable base export/reader, cost-integrity audit, temporal stability and standalone diagnostic evidence/reader/CLI are IMPLEMENTED + CI-verified. Historical source is located in Drive at `DAX_V14_RECOVERED_CACHE_V13/m5_daily`; the first actual full CAND-001 OOS result artifact is still NOT PRODUCED. Profitability/robustness remain `UNVERIFIED`; REF-V11.2/V12 metrics must never be borrowed. | Technical benchmark and synthetic forward-performance fixtures are plumbing/correctness evidence only; Drive item count is not the audited session-day count |
| Versioning / identity | `docs/NEXTGEN_BOT_VERSIONING_V1.md` | Python distribution/package, DAX-BOT product, Candidate/config and evidence-schema namespaces are explicitly separate | Legacy V-number plans are provenance only |
| Frozen V11.2 reference | `research/V112_REFERENCE_V1/reference_result.json`, `docs/LEGACY_ENGINE_PROVENANCE.md`, audited manifests | Immutable reference evidence | Legacy evidence remains provenance only |
| Research modules / promotion | `docs/RESEARCH_MODULE_CATALOG.md`, `docs/RESEARCH_GATES.md` | Current research catalogue and promotion discipline | Family-specific research docs add detail |
| Fast trading / M1 | `docs/FAST_TRADING_M1_RESEARCH_V1.md` | Separate future candidate; M1 must not mutate CAND-001; preferred M1→M5 deterministic aggregation architecture | Public donor scans support lower-resolution subscription + upward consolidation |
| Operator risk / exposure profiles | `docs/OPERATOR_RISK_PROFILE_CONTROL_V1.md`, `src/daxlab/research/risk_profile_sizing.py`, `src/daxlab/research/loss_cap_gate.py` | Research-only BASE/BOOST/HIGH cash-at-stop profiles, lineage and loss-cap gates exist; no account-percentage inference and no broker execution authorization | Current normalized simulation sizing remains separate from broker-aware research estimates |
| Broker economics readiness | `docs/BROKER_ECONOMICS_READINESS_V1.md`, `src/daxlab/runtime/broker_economics_readiness.py`, `src/daxlab/research/broker_risk_sizing.py`, `tests/test_candidate_broker_economics_readiness.py`, `scripts/mt5_windows_probe.py` | Read-only venue metadata plus research-only cash-risk→volume translation; real DE40 economics are `WAITING_EXTERNAL`; neither is PAPER authorization | Current `candidate_sizing.py` remains normalized simulation-only sizing |
| News / macro event awareness | `docs/NEWS_EVENT_AWARENESS_RESEARCH_V1.md` | Always-on awareness concept with OBSERVE / EVENT_GUARD / NEWS_REACTIVE_RESEARCH policy separation | Scheduled official calendars and future breaking-news providers are external inputs |
| Planned web operator controls | `docs/WEB_OPERATOR_CONTROLS_V2_PLANNED.md` | Future gated controls for tempo, exposure profile and news policy; current Web V2 architecture remains read-only | Activation requires separately verified backend owners |
| Public/open-source donor knowledge | `docs/PUBLIC_DONOR_MAP_V4.md` + latest rescan `docs/PUBLIC_DONOR_RESCAN_V6.md` + `docs/DAX_BOT_1X_BACKLOG_RECONCILIATION_2134.md` | Current donor map/latest rescan plus Step-2134 targeted CI-layout recheck; architecture/methodology only | V5 and older donor audits remain provenance |
| Recovery architecture | `docs/RECOVERY_CANONICALIZATION_AUDIT_V1.md`, `src/daxlab/runtime/recovery_bundle.py`, `tests/test_legacy_recovery_retirement_audit.py` | `recovery_bundle.py` is canonical material-run recovery; legacy `recovery.py` is frozen `RETAIN_WITH_REASON` forensic compatibility with no new consumers; deletion requires explicit compatibility/evidence-retirement proof | Historical hygiene/audit docs remain provenance |
| MT5 read-only adapter | `docs/MT5_ADAPTER_CONTRACT_V1.md`, `src/daxlab/runtime/mt5_readonly.py`, `scripts/mt5_windows_probe.py` | Current read-only host/feed boundary | Host runbooks are operational supplements |
| CAND-001 Windows SHADOW host verification | `docs/CAND001_WINDOWS_SHADOW_DEPLOYMENT_RUNBOOK_V1.md`, `scripts/mt5_shadow_supervisor.py`, `src/daxlab/runtime/candidate_shadow_host_cycle.py` | IMPLEMENTED + CI-verified repository integration; real Windows/MT5 host verification is `WAITING_EXTERNAL` | Existing Windows preflight/runtime scripts remain host owners |
| CAND-001 operator telemetry | `docs/CAND001_OPERATOR_TELEMETRY_V1.md`, `src/daxlab/runtime/operator_snapshot.py`, `src/daxlab/runtime/candidate_operator_telemetry.py`, `src/daxlab/runtime/candidate_operator_query.py`, `scripts/export_mt5_shadow_telemetry.py`, `scripts/read_candidate_operator_runtime.py`, migrations `0008`/`0009` | Fresh read-only Candidate runtime source: local snapshot -> validated append-only Neon telemetry -> `cand001_operator_current` -> validated server/operator read model; no browser credentials/control path | Static `web/status.json` is versioned evidence only, never current runtime truth |
| Broker time/session | `docs/MT5_BROKER_SESSION_CONTRACT_V1.md` | Current broker-time interpretation contract | Diagnostic scripts/evidence provide observations |
| Real forward SHADOW evidence | `docs/evidence/2026-09-11_forward_shadow_real_data_milestone.md` + machine-readable companion | Verified milestone only; re-read live telemetry for current state | Older heartbeats are point-in-time evidence |
| Paper preparation/contracts | `src/daxlab/runtime/paper_contracts.py`, `src/daxlab/runtime/readiness.py`, `docs/SHADOW_PAPER_ACCEPTANCE_V1.md`, `docs/PAPER_READINESS_GAP_MATRIX_V1.md`, `docs/PAPER_PREPARATION_V10.md`, relevant broker/readiness tests | Simulation/contracts/readiness only; broker-neutral lifecycle/reconciliation/protection/telemetry/checkpoint owners now exist, while real host/economics evidence and explicit user authorization remain separate gates | No broker adapter/live execution module is allowed by current design |
| CAND-001 virtual lifecycle | `src/daxlab/runtime/candidate_virtual_lifecycle.py`, `tests/test_candidate_virtual_lifecycle.py`, `PSR-011` | SHADOW-only stateful Intent→later-bar→STOP/TARGET owner; reuses canonical same-bar/gap/bar-identity contracts | Paper lifecycle vocabulary alone is not an engine |
| CAND-001 virtual outcome/costs | `src/daxlab/runtime/candidate_virtual_outcome.py`, `tests/test_candidate_virtual_outcome.py`, `PSR-012` | NEW_1X costed gross/net R bridge into existing `DatedShadowOutcome`; not claimed as V11.2 cost parity | Broker-demo evidence may later calibrate assumptions |
| Paper/SHADOW promotion | `docs/PAPER_READINESS_GAP_MATRIX_V1.md`, `docs/SHADOW_PAPER_ACCEPTANCE_V1.md`, readiness code/tests | PAPER remains unauthorized. Broker-neutral software evidence owners are implemented; real host/economics evidence and the explicit user STOP-gate remain independent requirements. No research/OOS result can auto-promote to PAPER. | Historical readiness docs are context only |
| R/cash research ledger | `src/daxlab/research/shadow_cash_ledger.py`, `tests/test_shadow_cash_ledger.py` | Simulated R→EUR research translation; not broker balance | Risk observation remains descriptive only |
| Forward performance | `src/daxlab/research/forward_shadow_performance.py`, relevant tests | Aggregate signal/trade/R/cash evidence; remains simulation/research evidence | Weekly/rolling attribution views are downstream |
| Web/operator surface | `docs/WEB_INTERFACE_CONTRACT_V2.md`, `src/daxlab/runtime/operator_snapshot.py`, `docs/CAND001_OPERATOR_TELEMETRY_V1.md`, `web/status.json` | V2 is current: static dashboard uses `DAXLAB_WEB_STATIC_STATUS_V2`; fresh runtime source is separate Candidate telemetry and browser endpoint is post-alpha/non-blocking | `WEB_INTERFACE_CONTRACT_V1.md` and static V1 runtime/pre-host assertions are historical/superseded |
| Architecture hygiene / LEAN | `docs/LEAN_500_STEP_AUDIT_POLICY.md`, `docs/DAX_BOT_1X_BACKLOG_RECONCILIATION_2134.md` | Full audit mandatory every 500 steps; next full audit remains Step 2500. Step-2134 reconciliation prevents redoing already-solved Step-2000 cleanup. | Step-2000 backlog remains historical audit snapshot |

## Public donor precedence

Public-project knowledge must not be rediscovered from scratch when already recorded.

Before a new donor scan or architectural comparison:
1. read `PUBLIC_DONOR_MAP_V4.md`;
2. read the latest `PUBLIC_DONOR_RESCAN_*.md`;
3. inspect supporting donor audit files only for details not summarized there;
4. record any genuinely new donor finding in the current map/rescan or next canonical replacement.

A public donor never changes VERIFIED DAX evidence. It may contribute architecture, testing, recovery, performance, observability or research-governance patterns only.

## Test / contract lookup rule

Before creating a new implementation or saying a capability/test is missing:
1. locate the authoritative component file at the pinned SHA;
2. enumerate its existing tests and consumers from authoritative repository contents;
3. check `PROBLEM_SOLUTION_REGISTRY.md` and its binding addendum for an earlier failure/fix in that component;
4. only then design a new test, adapter or module.

Zero code-search hits are never absence proof.

## Supersession rule

When a newer document replaces an older one, the new canonical document must name the superseded source or this index must be updated. Historical files are retained for provenance unless a separate cleanup decision explicitly removes them.

## Update rule

Update this index when any of the following changes materially:
- canonical source for a topic;
- the current work-step pointer/numbering reconstruction changes;
- a new project-wide contract is introduced;
- a prior canonical source becomes stale/superseded;
- a new public-donor map/reconciliation becomes authoritative;
- a major recovery/runtime/paper/research boundary changes.

Do not add every file. This index should remain a small navigation map to the durable sources that matter for resuming work correctly.