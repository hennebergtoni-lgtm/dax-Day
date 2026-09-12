# Current Work Step — DAX Daytrading Bot

Status: BINDING NUMBERING POINTER
Updated: 2026-09-12
Branch: `nextgen-bot-line-v1`

Purpose: preserve one unambiguous whole-number work sequence across chat/context loss while keeping the active pointer compact. Repository code, tests, evidence, safety contracts and verified runtime evidence remain authoritative for technical truth.

## Current pointer

- Last completed whole-number step: **2154**
- Active whole-number step: **2155**
- Next step after successful completion: **2156**
- Active Step 2155 scope: **Define Canonical Risk Decision V1 between canonical `TradePlan` and `ExecutionIntent`: broker-neutral instrument/sizing inputs, deterministic ALLOW/DENY identity, quantity output only after risk approval, and fail-closed validation. No MT5/order adapter, no broker submission, no PAPER/LIVE authorization, no automatic adoption of legacy BASE/BOOST/HIGH research profiles.**
- Active host-verification lane: **2122 — WAITING_EXTERNAL / current-branch CAND-001 Windows/MT5 SHADOW real-host verification; host wiring/parity/fail-closed evidence VERIFIED, market-open clock/GREEN/candidate/restart evidence still WAITING_EXTERNAL**
- Stable-branch governance lane: **2136 — VERIFIED PROTECTED / repository ruleset `Projekt main` is active on `refs/heads/main`; pull request required; strict required checks `dax-bot-1x-ci` + `research-lab-ci`; deletions and non-fast-forward pushes blocked; bypass list empty. Verified 2026-09-12 via GitHub ruleset API.**
- Historical interrupted scopes retained in archive: **2116 / 2123 / 2131 / 2137**
- Next mandatory 250-step Masterstand checkpoint: **2250**
- Next mandatory 500-step full audit: **2500**
- Decimal or letter step IDs: **PROHIBITED**

## Ledger archive

The exact prior full ledger has been preserved without rewriting at:

- `docs/CURRENT_WORK_STEP_ARCHIVE_THROUGH_2154_PRE_CLOSE.md`
- archived blob SHA: `4d96586f85cf32f2e726080cf728837ea6dd20ef`
- archive state: full historical pointer through Step 2154 while 2154 was still marked `IN PROGRESS`.
- reconstruction anchor `199e6bf073da1a717839b37e70a314f203e9ffa4` remains the canonical reconstruction anchor; detailed reconstructed history is preserved in the archive.

The archive preserves reconstructed Steps 2081–2089, direct numbering from Step 2090 onward, all historical/interrupted/waiting lanes, evidence references, CI references and the prior full numbering rules. This compact pointer is now the authoritative active navigation surface; the archive is provenance/history and must not be edited retroactively.

## Recent verified sequence

| Step | Work unit | Evidence / state |
| ---: | --- | --- |
| 2150 | Prove deterministic interrupted-replay restart/resume parity on the NextGen engine. | **COMPLETED.** Exact tested head `0aa06bcc61655a589e4a2dc1ef8c1d0b5237b0e2`; `dax-bot-1x-ci` #407 GREEN and `research-lab-ci` #1191 GREEN. |
| 2151 | Add canonical CAND-001 strategy-state codec and prove real Candidate resume parity. | **COMPLETED.** Candidate restart/resume parity and canonical codec verified; no strategy/order authorization change. |
| 2152 | Reconcile durable project continuity/navigation with verified NextGen progress. | **COMPLETED.** Knowledge Index and Masterstand reconciled; no runtime/authorization change. |
| 2153 | Audit and enforce the NextGen legacy-dependency isolation boundary. | **COMPLETED.** `docs/NEXTGEN_DEPENDENCY_ISOLATION_V1.md`, AST import guard and evidence note; exact tested head `1234cf92125b21698dff4d5d0d6ea9be558c4ee3`, `dax-bot-1x-ci` #426 GREEN and `research-lab-ci` #1210 GREEN. Formal pointer head after closeout `0af66af8…` also GREEN (#427/#1211). |
| 2154 | Audit remaining documented NextGen compatibility/legacy edges for active and forensic consumers before retirement. | **COMPLETED — 7/7 `RETAIN_WITH_REASON`, 0 `RETIRE_CANDIDATE`.** Added `docs/NEXTGEN_COMPATIBILITY_RETIREMENT_AUDIT_V1.md` and `tests/test_nextgen_compatibility_retirement_audit.py`. Exact technical tested head `df29bb44c919c307eb7fe271e80841e677b97455`: `dax-bot-1x-ci` #429 GREEN and `research-lab-ci` #1213 GREEN. No compatibility file deleted; no strategy, MT5, V11.2, risk, execution or authorization behavior changed. |
| 2155 | Define Canonical Risk Decision V1 between strategy planning and deterministic execution intent. | **IN PROGRESS.** Build broker-neutral, deterministic, fail-closed risk/sizing contracts without adding any broker execution capability or PAPER/LIVE authorization. |

## Step 2154 closeout truth

Step 2154 found no evidence-neutral retirement candidate. The seven audited surfaces remain `RETAIN_WITH_REASON` because each still has an active parity/restart/adapter/research/reference/provenance obligation. Retirement requires a later separate whole-number step with zero active semantic consumers, no unresolved forensic/provenance requirement, evidence-equivalent replacement where applicable, deterministic compatibility/parity proof, and no weakening of Step-2153 dependency isolation.

## Step 2155 active work

**Step 2155 — IN PROGRESS:** define the first canonical broker-neutral Risk Decision V1 boundary between `TradePlan` and `ExecutionIntent`.

Required properties:

1. deterministic request/decision identity;
2. explicit ALLOW/DENY semantics with machine-readable blockers/reasons;
3. quantity is produced only by an ALLOW risk decision, never directly by strategy output;
4. instrument/sizing inputs are canonical data, not direct MT5 SDK objects;
5. finite/positive/unit-step invariants fail closed;
6. risk output does not authorize broker submission;
7. no BASE/BOOST/HIGH legacy research profile becomes product policy automatically;
8. no PAPER/LIVE authorization change.

Architecture basis: `docs/NEXTGEN_GREENFIELD_ARCHITECTURE_V1.md` §5.5 Risk, portfolio and execution domain.

## Binding numbering and handoff rules

1. Every independent concrete work unit consumes exactly one next integer.
2. Immediate tests, fixes, CI correction and documentation needed to prove that same work unit remain inside the same integer step.
3. A different independent deliverable consumes the next integer even if the previous step's CI is still running or an earlier lane is `WAITING_EXTERNAL`.
4. Decimal suffixes, letter suffixes and nested official step IDs are forbidden.
5. A lane marked `WAITING_EXTERNAL` does not consume repeated placeholder steps and does not block independent work.
6. Before reporting a new official step number after resume, read `docs/SESSION_EXECUTION_REFRESHER.md`, pin repo/branch/head, then read this file.
7. `Weiter mit dem DAXBot` triggers the repository-backed recovery protocol in `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md` and continuation without asking for a pasted Masterstand.
8. `Erstelle einen Masterstand` triggers an immediate canonical handover refresh.
9. Every multiple of 250 official steps requires a Masterstand checkpoint. The next is Step 2250. Every 500-step checkpoint also performs the full LEAN/architecture audit; next full audit Step 2500.
10. **Step-Close-Gate:** a new independent official step may not begin until the previous step is either (a) explicitly `COMPLETED` with its required evidence/CI and pointer synchronized, or (b) explicitly `INTERRUPTED`/`WAITING_EXTERNAL`/`BLOCKED` with unfinished scope and unblock/resume provenance recorded. Merely having commits is not completion.
11. **Pointer-before-next-step:** update this canonical pointer before the first substantive action of the next independent step; do not backfill several step numbers after work has already advanced.
12. This numbering/handoff ledger never authorizes PAPER/LIVE, changes VERIFIED evidence, or overrides safety/product contracts.
13. Visible multi-step work must follow: Step N → short activity → normal-text Zwischenstand with ✅/⚠️/❌ → immediate next action. Tool/interface activity alone is not a Zwischenstand, and long tool-call chains without normal-text progress visibility are prohibited.
14. **Visible official step numbering is monotonic.** Once a higher official step number has started or completed, never visibly resume work under a lower step number. Preserve lower steps as historical/interrupted provenance and carry unfinished scope into the next unused whole-number step.
15. Explicit user intervention to stop/review/govern the workflow is a valid sequence interruption. Freeze the active step truth first, then start the governance/review work under the next unused integer.
16. Never claim work continues after a turn-ending/final response. Work may continue only while an active tool/action turn is actually executing; after platform/app/network suspension or a final response, the next turn must re-pin repository/head/pointer before continuation.

## Safety boundary

Current NextGen work remains non-executing product/research architecture:

- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- no broker order submission authorization;
- PAPER not authorized;
- LIVE not authorized;
- `NO_STRATEGY_AUTO_PROMOTION` unchanged;
- frozen V11.2 evidence and verified historical fingerprints remain unchanged.
