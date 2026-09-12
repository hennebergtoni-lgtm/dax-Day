# Current Work Step — DAX Daytrading Bot

Status: BINDING NUMBERING POINTER
Updated: 2026-09-12
Branch: `nextgen-bot-line-v1`

Purpose: preserve one unambiguous whole-number work sequence across chat/context loss while keeping the active pointer compact. Repository code, tests, evidence, safety contracts and verified runtime evidence remain authoritative for technical truth.

## Current pointer

- Last completed whole-number step: **2162**
- Active whole-number step: **2163**
- Next step after successful completion: **2164**
- Active Step 2163 scope: **Implement the smallest canonical product loss/exposure admission policy separated from per-trade Risk V1 sizing. Adapt only explicit daily/weekly drawdown caps, consecutive-loss cooldown and maximum-open-position limits from the Step-2160 audit. Promote no research numeric values, calculate no PnL, read no account/broker API, and add no broker submission or PAPER/LIVE authorization.**
- Active host-verification lane: **2122 — WAITING_EXTERNAL / current-branch CAND-001 Windows/MT5 SHADOW real-host verification; host wiring/parity/fail-closed evidence VERIFIED, market-open clock/GREEN/candidate/restart evidence still WAITING_EXTERNAL**
- Stable-branch governance lane: **2136 — VERIFIED PROTECTED / repository ruleset `Projekt main` is active on `refs/heads/main`; pull request required; strict required checks `dax-bot-1x-ci` + `research-lab-ci`; deletions and non-fast-forward pushes blocked; bypass list empty. Verified 2026-09-12 via GitHub ruleset API.**
- Historical interrupted scopes retained in archive: **2116 / 2123 / 2131 / 2137**
- Next mandatory 250-step Masterstand checkpoint: **2250**
- Next mandatory 500-step full audit: **2500**
- Next mandatory 500-step Architecture & Learning Review: **2500**
- Decimal or letter step IDs: **PROHIBITED**

## Ledger archive

The exact prior full ledger has been preserved without rewriting at:

- `docs/CURRENT_WORK_STEP_ARCHIVE_THROUGH_2154_PRE_CLOSE.md`
- archived blob SHA: `4d96586f85cf32f2e726080cf728837ea6dd20ef`
- archive state: full historical pointer through Step 2154 while 2154 was still marked `IN PROGRESS`.
- reconstruction anchor `199e6bf073da1a717839b37e70a314f203e9ffa4` remains the canonical reconstruction anchor; detailed reconstructed history is preserved in the archive.
- reconstructed Steps **2081** through **2089** remain preserved in that archive and are intentionally not duplicated into the compact active ledger.

## Recent verified sequence

| Step | Work unit | Evidence / state |
| ---: | --- | --- |
| 2156 | Canonical Risk-to-ExecutionIntent Bridge V1. | **COMPLETED.** Tested head `1f3a5f819ed115501c8c0902c73903b4a2f2e6e2`; CI #435/#1219 GREEN. |
| 2157 | Broker lifecycle/reconciliation/protection reuse for canonical intent. | **COMPLETED.** Tested head `e65ad2994a6d8e243ef984b75a4724209df1a38a`; CI #437/#1221 GREEN. |
| 2158 | PAPER pre-authorization composition / LEAN audit. | **COMPLETED.** Tested head `8a0052c71a284ab8b94dc5e7dafebf04d10af77a`; CI #439/#1223 GREEN. No new runtime orchestrator; PAPER/LIVE remain unauthorized. |
| 2159 | Canonical read-only broker-economics → Risk Inputs adapter. | **COMPLETED.** Final tested head `6f782e3d14754a744232ae1094a9b4534f767fcb`; CI #442/#1226 GREEN. |
| 2160 | Risk-profile / loss-cap product-promotion audit. | **COMPLETED.** Final tested head `fecff1962ce7e3c7c869dc49cd45b3bfbd5a145a`; CI #445/#1229 GREEN. |
| 2161 | 500-step Architecture & Learning Review governance. | **COMPLETED.** Final tested head `fbc04354ef7e5b209bc3759309561b5d5974d5ed`; CI #449/#1233 GREEN. |
| 2162 | Canonical single fixed-cash risk policy. | **COMPLETED.** Added `domain/risk_policy.py`, canonical export, contract and deterministic/fail-closed/Risk-V1 delegation tests. Final tested head `e72a1fc8000f5966048f1cfe3cac654a43368099`; `dax-bot-1x-ci` #455 GREEN and `research-lab-ci` #1239 GREEN. No research profile values, broker/account API or execution authorization added. |
| 2163 | Canonical loss/exposure admission policy. | **IN PROGRESS.** Adapt explicit cap semantics only; no research numeric-value promotion, PnL calculation or broker/account capability. |

## Step 2162 closeout truth

Step 2162 adds one canonical fixed-cash product policy with explicit currency, positive finite per-trade maximum cash loss and deterministic fingerprint. The policy delegates sizing to existing Risk V1 and fails closed on malformed values, tampering and currency mismatch. BASE/BOOST/HIGH, automatic escalation, account/equity percentage sizing and broker/account access remain absent. Readiness verification remains separate from software existence.

## Step 2163 active work

**Step 2163 — IN PROGRESS:** adapt the separately audited loss/exposure admission semantics into a canonical product owner.

Required properties:

1. explicit currency plus positive finite daily and weekly drawdown caps;
2. explicit integer limits for consecutive losses and open positions;
3. explicit observation input only; no PnL/account computation inside the policy;
4. equality at a cap blocks new admission fail-closed;
5. currency mismatch blocks;
6. deterministic policy/observation/decision identity;
7. no research policy version or research numeric default is promoted;
8. no per-trade quantity sizing duplicated here;
9. no account/broker API, MT5 SDK/order API, broker submission or PAPER/LIVE authorization;
10. readiness verification remains independent from implementation.

## Binding numbering and handoff rules

1. Every independent concrete work unit consumes exactly one next integer.
2. Immediate tests, fixes, CI correction and documentation needed to prove that same work unit remain inside the same integer step.
3. A different independent deliverable consumes the next integer even if an earlier lane is `WAITING_EXTERNAL`.
4. Decimal suffixes, letter suffixes and nested official step IDs are forbidden.
5. **Step-Close-Gate:** a new independent official step may not begin until the previous step is `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL` or `BLOCKED` with evidence/pointer synchronized.
6. **Pointer-before-next-step:** this file must name the new active step before substantive work starts.
7. **Visible official step numbering is monotonic.** Once a higher official step has started, unfinished older scope is preserved as provenance and may continue only under the next unused whole-number step.
8. `Weiter mit dem DAXBot` triggers repository-backed recovery; `Erstelle einen Masterstand` triggers canonical handover refresh.
9. Next Masterstand checkpoint: **2250**; next 500-step full audit and Architecture & Learning Review: **2500**.
10. Visible work remains short: Step N → activity → ✅/⚠️/❌ Zwischenstand → immediate next action.
11. Never claim work continues after a turn-ending response.

## Safety boundary

- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- no broker order submission authorization;
- PAPER not authorized;
- LIVE not authorized;
- `NO_STRATEGY_AUTO_PROMOTION` unchanged;
- frozen V11.2 evidence and verified historical fingerprints remain unchanged.
