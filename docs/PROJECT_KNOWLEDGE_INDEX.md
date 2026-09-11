# Project Knowledge Index — DAX Daytrading Bot

Status: BINDING NAVIGATION CONTRACT
Updated: 2026-09-11

Purpose: make important project knowledge discoverable by topic so context loss never forces rediscovery from memory. This file is a navigation layer, not a replacement for evidence, code, tests or historical documents.

## Mandatory resume order

After context loss, compaction, long interruption, uncertainty about prior work, or any explicit `weiter` / `fortsetzen` instruction:

1. Read `docs/SESSION_EXECUTION_REFRESHER.md` first. Confirm integer-only step numbering and the no-artificial-stop rule before doing or reporting project work.
2. Pin repository, branch and exact commit SHA.
3. Read `docs/MASTERSTAND.md` for current project truth and safety boundaries.
4. Read this `docs/PROJECT_KNOWLEDGE_INDEX.md` to locate authoritative topic sources.
5. Read `docs/PROBLEM_SOLUTION_REGISTRY.md` and `docs/PROBLEM_SOLUTION_REGISTRY_ADDENDUM_V1.md` for previously solved engineering problems before designing a new fix.
6. Read only the topic-specific authoritative files and relevant tests/consumers listed below.
7. Re-read fresh runtime telemetry before making any current-runtime claim.
8. Continue from the last VERIFIED whole-number step; do not redesign from chat memory and do not introduce decimal/letter substeps.

## Knowledge map

| Topic | Authoritative/current source(s) | Status / usage | Historical / secondary sources |
|---|---|---|---|
| Overall project state | `docs/MASTERSTAND.md` | Primary durable handover/source-of-truth below exact repo/code/evidence | Older milestone files are provenance only |
| Session execution refresher | `docs/SESSION_EXECUTION_REFRESHER.md` | Mandatory first read on resume/continue; compact enforcement reminder for integer-only steps and no artificial stops | Detailed rules remain in `WORK_CONTINUITY_PROTOCOL.md` |
| Context recovery / continuous work | `docs/CONTEXT_RESUME_RECOVERY_POLICY.md`, `docs/WORK_CONTINUITY_PROTOCOL.md` | Binding resume/reconciliation and minimal-stop rules, including lane-blocker vs global-stop handling | None should override them |
| Previously solved problems | `docs/PROBLEM_SOLUTION_REGISTRY.md`, `docs/PROBLEM_SOLUTION_REGISTRY_ADDENDUM_V1.md` | Mandatory pre-design lookup; addendum continues PSR numbering and includes timeframe/causal-identity/lane-stop fixes | Local issue-specific docs remain evidence |
| Step-2000 migration backlog | `docs/DAX_BOT_1X_MIGRATION_BACKLOG_STEP_2000.md` | Canonical migration/cleanup backlog until superseded by a later full audit; also records required Bot-1.0 closeout report and planned risk-profile control | Older milestone plans are historical |
| DAX-BOT 1.x migration safety | `docs/DAX_BOT_1X_MIGRATION_SAFETY_GATE.md` | Binding migration constraints | Older V10/V11 reviews are context only |
| DAX-BOT 1.x alpha acceptance | `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_GATE.md`, `docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_STATUS.md` | Current gate plus current evidence/status; real Windows-host Candidate verification is a WAITING_EXTERNAL lane | Candidate tests/code remain executable proof |
| Versioning / identity | `docs/NEXTGEN_BOT_VERSIONING_V1.md` | Current product/candidate/versioning contract | Legacy V-number plans are provenance only |
| Frozen V11.2 reference | `research/V112_REFERENCE_V1/reference_result.json`, `docs/LEGACY_ENGINE_PROVENANCE.md`, audited manifests | Immutable reference evidence | Legacy evidence remains provenance only |
| Research modules / promotion | `docs/RESEARCH_MODULE_CATALOG.md`, `docs/RESEARCH_GATES.md` | Current research catalogue and promotion discipline | Family-specific research docs add detail |
| Fast trading / M1 | `docs/FAST_TRADING_M1_RESEARCH_V1.md` | Separate future candidate; M1 must not mutate CAND-001; preferred M1→M5 deterministic aggregation architecture | Public donor scans support lower-resolution subscription + upward consolidation |
| Operator risk / exposure profiles | `docs/OPERATOR_RISK_PROFILE_CONTROL_V1.md` | Planned bounded profile request layer; capital allocation is not max-loss-at-stop; no broker-aware sizing yet | Current normalized simulation sizing remains separate |
| News / macro event awareness | `docs/NEWS_EVENT_AWARENESS_RESEARCH_V1.md` | Always-on awareness concept with OBSERVE / EVENT_GUARD / NEWS_REACTIVE_RESEARCH policy separation | Scheduled official calendars and future breaking-news providers are external inputs |
| Planned web operator controls | `docs/WEB_OPERATOR_CONTROLS_V2_PLANNED.md` | Future gated controls for tempo, exposure profile and news policy; Web V1 remains read-only and authoritative today | Activation requires separately verified backend owners |
| Public/open-source donor knowledge | `docs/PUBLIC_DONOR_MAP_V4.md` + latest rescan `docs/PUBLIC_DONOR_RESCAN_V6.md` | Current donor map plus latest recheck; architecture/methodology only | `docs/PUBLIC_DONOR_RESCAN_V5.md`, `docs/OPEN_SOURCE_AUDIT.md`, `PUBLIC_ARCHITECTURE_DONORS_V2.md`, `PUBLIC_RESEARCH_DONORS_V3.md`, `PUBLIC_MT5_DONOR_SCAN_2026_09_08.md` are supporting/provenance sources |
| Recovery architecture | `docs/RECOVERY_CANONICALIZATION_AUDIT_V1.md`, `src/daxlab/runtime/recovery_bundle.py` | `recovery_bundle.py` is canonical material-run recovery; `recovery.py` is legacy/retire candidate | Separate runtime/replay restart state remains distinct |
| MT5 read-only adapter | `docs/MT5_ADAPTER_CONTRACT_V1.md`, `src/daxlab/runtime/mt5_readonly.py`, `scripts/mt5_windows_probe.py` | Current read-only host/feed boundary | Host runbooks are operational supplements |
| CAND-001 Windows SHADOW host verification | `docs/CAND001_WINDOWS_SHADOW_DEPLOYMENT_RUNBOOK_V1.md`, `scripts/mt5_shadow_supervisor.py`, `src/daxlab/runtime/candidate_shadow_host_cycle.py` | IMPLEMENTED + CI-verified repository integration; real Windows/MT5 host verification is `WAITING_EXTERNAL` | Existing Windows preflight/runtime scripts remain host owners |
| CAND-001 operator telemetry | `docs/CAND001_OPERATOR_TELEMETRY_V1.md`, `src/daxlab/runtime/operator_snapshot.py`, `src/daxlab/runtime/candidate_operator_telemetry.py`, `scripts/export_mt5_shadow_telemetry.py`, migrations `0008`/`0009` | Fresh read-only Candidate runtime source: local snapshot -> validated append-only Neon telemetry -> `cand001_operator_current` view; no browser credentials/control path | Static `web/status.json` is versioned evidence only, never current runtime truth |
| Broker time/session | `docs/MT5_BROKER_SESSION_CONTRACT_V1.md` | Current broker-time interpretation contract | Diagnostic scripts/evidence provide observations |
| Real forward SHADOW evidence | `docs/evidence/2026-09-11_forward_shadow_real_data_milestone.md` + machine-readable companion | Verified milestone only; re-read live telemetry for current state | Older heartbeats are point-in-time evidence |
| Paper preparation/contracts | `src/daxlab/runtime/paper_contracts.py`, `docs/PAPER_PREPARATION_V10.md`, relevant `tests/test_paper_*` | Simulation contracts only; broker execution is not implied | No broker adapter/live execution module is allowed by current design |
| CAND-001 virtual lifecycle | `src/daxlab/runtime/candidate_virtual_lifecycle.py`, `tests/test_candidate_virtual_lifecycle.py`, `PSR-011` | SHADOW-only stateful Intent→later-bar→STOP/TARGET owner; reuses canonical same-bar/gap/bar-identity contracts | Paper lifecycle vocabulary alone is not an engine |
| CAND-001 virtual outcome/costs | `src/daxlab/runtime/candidate_virtual_outcome.py`, `tests/test_candidate_virtual_outcome.py`, `PSR-012` | NEW_1X costed gross/net R bridge into existing `DatedShadowOutcome`; not claimed as V11.2 cost parity | Broker-demo evidence may later calibrate assumptions |
| Paper/SHADOW promotion | `docs/SHADOW_PAPER_ACCEPTANCE_V1.md`, readiness code/tests | Gate definition; authorization remains separate from software existence | Historical readiness docs are context only |
| R/cash research ledger | `src/daxlab/research/shadow_cash_ledger.py`, `tests/test_shadow_cash_ledger.py` | Simulated R→EUR research translation; not broker balance | Risk observation remains descriptive only |
| Forward performance | `src/daxlab/research/forward_shadow_performance.py`, relevant tests | Aggregate signal/trade/R/cash evidence; remains simulation/research evidence | Weekly/rolling attribution views are downstream |
| Web/operator surface | `docs/WEB_INTERFACE_CONTRACT_V1.md`, `src/daxlab/runtime/operator_snapshot.py`, `docs/CAND001_OPERATOR_TELEMETRY_V1.md`, `web/status.json` | Static dashboard explicitly uses `DAXLAB_WEB_STATIC_STATUS_V2`; current runtime source is separate Candidate telemetry and browser endpoint remains a later safe-backend task | Static V1 runtime/pre-host assertions are superseded |
| Architecture hygiene / LEAN | `docs/LEAN_500_STEP_AUDIT_POLICY.md`, latest full audit backlog | Mandatory every 500 steps | Older architecture audits are provenance |

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
- a new project-wide contract is introduced;
- a prior canonical source becomes stale/superseded;
- a new public-donor map becomes authoritative;
- a major recovery/runtime/paper/research boundary changes.

Do not add every file. This index should remain a small navigation map to the durable sources that matter for resuming work correctly.
