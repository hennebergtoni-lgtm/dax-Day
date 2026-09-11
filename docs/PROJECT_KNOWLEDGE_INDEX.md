# Project Knowledge Index — DAX Daytrading Bot

Status: BINDING NAVIGATION CONTRACT
Updated: 2026-09-11

Purpose: make important project knowledge discoverable by topic so context loss never forces rediscovery from memory. This file is a navigation layer, not a replacement for evidence, code, tests or historical documents.

## Mandatory resume order

After context loss, compaction, long interruption, uncertainty about prior work, or any explicit `weiter` / `fortsetzen` instruction:

1. Read `docs/SESSION_EXECUTION_REFRESHER.md` first. Confirm integer-only step numbering and the no-artificial-stop rule before doing or reporting project work.
2. Pin repository, branch and exact commit SHA.
3. Read `docs/CURRENT_WORK_STEP.md` and use its canonical whole-number pointer. Reconstruct from commit evidence only if the ledger is missing/inconsistent; never infer a step number from chat memory or raw commit count.
4. Read `docs/MASTERSTAND.md` for current project truth and safety boundaries.
5. Read this `docs/PROJECT_KNOWLEDGE_INDEX.md` to locate authoritative topic sources.
6. Read `docs/PROBLEM_SOLUTION_REGISTRY.md` and `docs/PROBLEM_SOLUTION_REGISTRY_ADDENDUM_V1.md` for previously solved engineering problems before designing a new fix.
7. Read only the topic-specific authoritative files and relevant tests/consumers listed below.
8. Re-read fresh runtime telemetry before making any current-runtime claim.
9. Continue from the canonical whole-number step; do not redesign from chat memory and do not introduce decimal/letter substeps.

## Knowledge map

| Topic | Authoritative/current source(s) | Status / usage | Historical / secondary sources |
|---|---|---|---|
| Overall project state | `docs/MASTERSTAND.md` | Primary durable handover/source-of-truth below exact repo/code/evidence | Older milestone files are provenance only |
| Current work-step numbering | `docs/CURRENT_WORK_STEP.md` | Binding numbering pointer and reconstructed whole-number ledger; numbering only, never overrides code/evidence/safety | Commit history is reconstruction evidence when the pointer is inconsistent |
| Session execution refresher | `docs/SESSION_EXECUTION_REFRESHER.md` | Mandatory first read on resume/continue; compact enforcement reminder for integer-only steps and no artificial stops | Detailed rules remain in `WORK_CONTINUITY_PROTOCOL.md` |
| Context recovery / continuous work | `docs/CONTEXT_RESUME_RECOVERY_POLICY.md`, `docs/WORK_CONTINUITY_PROTOCOL.md` | Binding resume/reconciliation and minimal-stop rules, including lane-blocker vs global-stop handling | None should override them |
| Previously solved problems | `docs/PROBLEM_SOLUTION_REGISTRY.md`, `docs/PROBLEM_SOLUTION_REGISTRY_ADDENDUM_V1.md` | Mandatory pre-design lookup; addendum continues PSR numbering and includes timeframe/causal-identity/lane-stop fixes | Local issue-specific docs remain evidence |
| Step-2000 migration backlog | `docs/DAX_BOT_1X_MIGRATION_BACKLOG_STEP_2000.md` | Canonical migration/cleanup backlog until superseded by a later full audit; also records required Bot-1.0 closeout report and planned risk-profile control | Older milestone plans are historical |
| DAX-BOT 1.x migration safety | `docs/DAX_BOT_1X_MIGRATION_SAFETY_GATE.md` | Binding migration constraints | Older V10/V11 reviews are context only |
| DAX-BOT 1.x alpha acceptance | `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_GATE.md`, `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_STATUS.md`, `docs/DAX_BOT_1_0_CLOSEOUT_FINAL.md` | Repository-side 1.0-alpha accepted; real Windows-host Candidate verification remains a `WAITING_EXTERNAL` lane | Candidate tests/code remain executable proof |
| Versioning / identity | `docs/NEXTGEN_BOT_VERSIONING_V1.md` | Current product/candidate/versioning contract | Legacy V-number plans are provenance only |
| Frozen V11.2 reference | `research/V112_REFERENCE_V1/reference_result.json`, `docs/LEGACY_ENGINE_PROVENANCE.md`, audited manifests | Immutable reference evidence | Legacy evidence remains provenance only |
| Research modules / promotion | `docs/RESEARCH_MODULE_CATALOG.md`, `docs/RESEARCH_GATES.md` | Current research catalogue and promotion discipline | Family-specific research docs add detail |
| Fast trading / M1 | `docs/FAST_TRADING_M1_RESEARCH_V1.md` | Separate future candidate; M1 must not mutate CAND-001; preferred M1→M5 deterministic aggregation architecture | Public donor scans support lower-resolution subscription + upward consolidation |
| Operator risk / exposure profiles | `docs/OPERATOR_RISK_PROFILE_CONTROL_V1.md`, `src/daxlab/research/risk_profile_sizing.py`, `src/daxlab/research/loss_cap_gate.py` | Research-only BASE/BOOST/HIGH cash-at-stop profiles, lineage and loss-cap gates exist; no account-percentage inference and no broker execution authorization | Current normalized simulation sizing remains separate from broker-aware research estimates |
| Broker economics readiness | `docs/BROKER_ECONOMICS_READINESS_V1.md`, `src/daxlab/runtime/broker_economics_readiness.py`, `src/daxlab/research/broker_risk_sizing.py`, `tests/test_candidate_broker_economics_readiness.py`, `scripts/mt5_windows_probe.py` | Read-only venue metadata plus research-only cash-risk→volume translation; real DE40 economics are `WAITING_EXTERNAL`; neither is PAPER authorization | Current `candidate_sizing.py` remains normalized simulation-only sizing |
| News / macro event awareness | `docs/NEWS_EVENT_AWARENESS_RESEARCH_V1.md` | Always-on awareness concept with OBSERVE / EVENT_GUARD / NEWS_REACTIVE_RESEARCH policy separation | Scheduled official calendars and future breaking-news providers are external inputs |
| Planned web operator controls | `docs/WEB_OPERATOR_CONTROLS_V2_PLANNED.md` | Future gated controls for tempo, exposure profile and news policy; current Web V2 architecture remains read-only | Activation requires separately verified backend owners |
| Public/open-source donor knowledge | `docs/PUBLIC_DONOR_MAP_V4.md` + latest rescan `docs/PUBLIC_DONOR_RESCAN_V6.md` | Current donor map plus latest recheck; architecture/methodology only | `docs/PUBLIC_DONOR_RESCAN_V5.md`, `docs/OPEN_SOURCE_AUDIT.md`, `PUBLIC_ARCHITECTURE_DONORS_V2.md`, `PUBLIC_RESEARCH_DONORS_V3.md`, `PUBLIC_MT5_DONOR_SCAN_2026_09_08.md` are supporting/provenance sources |
| Recovery architecture | `docs/RECOVERY_CANONICALIZATION_AUDIT_V1.md`, `src/daxlab/runtime/recovery_bundle.py` | `recovery_bundle.py` is canonical material-run recovery; `recovery.py` is legacy/retire candidate | Separate runtime/replay restart state remains distinct |
| MT5 read-only adapter | `docs/MT5_ADAPTER_CONTRACT_V1.md`, `src/daxlab/runtime/mt5_readonly.py`, `scripts/mt5_windows_probe.py` | Current read-only host/feed boundary | Host runbooks are operational supplements |
| CAND-001 Windows SHADOW host verification | `docs/CAND001_WINDOWS_SHADOW_DEPLOYMENT_RUNBOOK_V1.md`, `scripts/mt5_shadow_supervisor.py`, `src/daxlab/runtime/candidate_shadow_host_cycle.py` | IMPLEMENTED + CI-verified repository integration; real Windows/MT5 host verification is `WAITING_EXTERNAL` | Existing Windows preflight/runtime scripts remain host owners |
| CAND-001 operator telemetry | `docs/CAND001_OPERATOR_TELEMETRY_V1.md`, `src/daxlab/runtime/operator_snapshot.py`, `src/daxlab/runtime/candidate_operator_telemetry.py`, `src/daxlab/runtime/candidate_operator_query.py`, `scripts/export_mt5_shadow_telemetry.py`, `scripts/read_candidate_operator_runtime.py`, migrations `0008`/`0009` | Fresh read-only Candidate runtime source: local snapshot -> validated append-only Neon telemetry -> `cand001_operator_current` -> validated server/operator read model; no browser credentials/control path | Static `web/status.json` is versioned evidence only, never current runtime truth |
| Broker time/session | `docs/MT5_BROKER_SESSION_CONTRACT_V1.md` | Current broker-time interpretation contract | Diagnostic scripts/evidence provide observations |
| Real forward SHADOW evidence | `docs/evidence/2026-09-11_forward_shadow_real_data_milestone.md` + machine-readable companion | Verified milestone only; re-read live telemetry for current state | Older heartbeats are point-in-time evidence |
| Paper preparation/contracts | `src/daxlab/runtime/paper_contracts.py`, `src/daxlab/runtime/readiness.py`, `docs/SHADOW_PAPER_ACCEPTANCE_V1.md`, `docs/PAPER_READINESS_GAP_MATRIX_V1.md`, `docs/PAPER_PREPARATION_V10.md`, relevant `tests/test_paper_*`, `tests/test_readiness.py` | Simulation/contracts/readiness only; current gap matrix separates REUSE, IMPLEMENTABLE_BEFORE_PAPER, `WAITING_EXTERNAL`, AUTHORIZATION-GATED and USER_STOP_GATE lanes | No broker adapter/live execution module is allowed by current design |
| CAND-001 virtual lifecycle | `src/daxlab/runtime/candidate_virtual_lifecycle.py`, `tests/test_candidate_virtual_lifecycle.py`, `PSR-011` | SHADOW-only stateful Intent→later-bar→STOP/TARGET owner; reuses canonical same-bar/gap/bar-identity contracts | Paper lifecycle vocabulary alone is not an engine |
| CAND-001 virtual outcome/costs | `src/daxlab/runtime/candidate_virtual_outcome.py`, `tests/test_candidate_virtual_outcome.py`, `PSR-012` | NEW_1X costed gross/net R bridge into existing `DatedShadowOutcome`; not claimed as V11.2 cost parity | Broker-demo evidence may later calibrate assumptions |
| Paper/SHADOW promotion | `docs/PAPER_READINESS_GAP_MATRIX_V1.md`, `docs/SHADOW_PAPER_ACCEPTANCE_V1.md`, readiness code/tests | PAPER remains unauthorized; broker-neutral lifecycle/reconciliation/protection owners are the immediate independent implementation lanes; real host/economics remain `WAITING_EXTERNAL`; explicit user STOP-gate remains mandatory | Historical readiness docs are context only |
| R/cash research ledger | `src/daxlab/research/shadow_cash_ledger.py`, `tests/test_shadow_cash_ledger.py` | Simulated R→EUR research translation; not broker balance | Risk observation remains descriptive only |
| Forward performance | `src/daxlab/research/forward_shadow_performance.py`, relevant tests | Aggregate signal/trade/R/cash evidence; remains simulation/research evidence | Weekly/rolling attribution views are downstream |
| Web/operator surface | `docs/WEB_INTERFACE_CONTRACT_V2.md`, `src/daxlab/runtime/operator_snapshot.py`, `docs/CAND001_OPERATOR_TELEMETRY_V1.md`, `web/status.json` | V2 is current: static dashboard uses `DAXLAB_WEB_STATIC_STATUS_V2`; fresh runtime source is separate Candidate telemetry and browser endpoint is post-alpha/non-blocking | `WEB_INTERFACE_CONTRACT_V1.md` and static V1 runtime/pre-host assertions are historical/superseded |
| Architecture hygiene / LEAN | `docs/LEAN_500_STEP_AUDIT_POLICY.md`, latest full audit backlog | Mandatory every 500 steps; next full audit remains Step 2500 | Older architecture audits are provenance |

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
- a new public-donor map becomes authoritative;
- a major recovery/runtime/paper/research boundary changes.

Do not add every file. This index should remain a small navigation map to the durable sources that matter for resuming work correctly.
