# DAX-BOT MASTERSTAND — NEXT-CHAT HANDOVER

## Current override — Step2245 Turbo V1.1 (2026-09-15)

The authoritative current handoff is `MASTERSTAND_LATEST.md` together with
`CURRENT_WORK_STEP.md` and `BOT_HELPER_TURBO_V1_1_CLOSEOUT.md`. Turbo V1.1 is
development-only and currently awaiting final CI acceptance. The start anchor
is `9491a5922eac4abc6984618585778317dd249600`; the real-host evidence head remains
`ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2`. No second real-host run or productive
risk/strategy/execution change. Step2239 remains waiting external, Step2240
blocked, M01 not ready; 27 gates remain 8/0/13/6/0. Older status snapshots below
remain historical; they do not override this current pointer or authorize work.

Status: **BINDING HANDOVER / REPOSITORY TRUTH FIRST**  
Updated: **2026-09-13 — Step 2186 Work/chat-capacity handoff**  
Repository: `hennebergtoni-lgtm/dax-Day`  
Working branch: `nextgen-bot-line-v1`  
Pull request: `#109` -> `main`

This is the canonical durable handover for the DAX Daytrading Bot project. It exists so a new ChatGPT conversation can recover the project after chat-length limits, context compaction, reconnects or ordinary chat changes without relying on conversational memory.

If this prose disagrees with fresh evidence, precedence is:
1. exact code/tests/machine evidence/current runtime telemetry;
2. `docs/CURRENT_WORK_STEP.md` for official numbering;
3. binding safety/governance contracts;
4. this Masterstand;
5. chat memory.

---

## 1. Resume command — BINDING

Canonical codeword:

`Weiter mit dem DAXBot`

Alias:

`Weiter mit DAXbot`

On either phrase in a new chat:
1. read `docs/SESSION_EXECUTION_REFRESHER.md`;
2. pin repo, branch, PR #109, **fresh exact HEAD** and current CI;
3. read `docs/CURRENT_WORK_STEP.md`;
4. read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`;
5. read this Masterstand;
6. read `docs/PROJECT_KNOWLEDGE_INDEX.md`, `docs/WORK_CONTINUITY_PROTOCOL.md` and the problem/solution registries;
7. reconcile `WAITING_EXTERNAL`, `INTERRUPTED`, `BLOCKED` and out-of-band Work evidence separately;
8. inspect only active-step code/docs/tests;
9. continue automatically when Step-Close-Gate permits it.

Do not ask the user to paste the old chat when repository access is available.

---

## 2. Working style and explicit chat-handoff rule

Required visible cadence:

`Step N -> short activity -> 1–2 sentence Zwischenstand -> ✅ / ⚠️ / ❌ -> actual next action`

Intermediate reports are visibility points, not stops. A file discovery, warning, CI poll, partial result or green sub-check does not justify ending the turn while safe executable work remains.

The repeated premature-stop incidents in the preceding chat were workflow failures, not DAX-BOT technical blockers. `WORK_CONTINUITY_PROTOCOL.md` and `SESSION_EXECUTION_REFRESHER.md` contain the durable correction.

Exception: an **explicit user STOP/chat-switch request** is a valid sequence interruption. In that case, reconcile pointer/Masterstand/CI first when possible, then actually stop. This Step-2186 handoff exists because the user explicitly requested a new chat due conversation length.

---

## 3. Exact repository truth entering Step 2186

Verified Work/base head before handoff documentation:

`76251e0e52567f61d3c6015d22266be4bc977395`

At that head:
- PR #109: **OPEN / UNMERGED**;
- base: `main`;
- branch: `nextgen-bot-line-v1`;
- `dax-bot-1x-ci` #555: **GREEN**;
- `research-lab-ci` #1339: **GREEN**;
- no Acceptance refresh by Work;
- no merge;
- `main` unchanged by the Work task.

Step-2186 documentation commits create newer heads. Therefore the next chat MUST re-pin the fresh branch head and CI rather than treating `76251e0e...` as the final handoff commit.

`main` remains protected by ruleset `Projekt main`: PR required, strict checks `dax-bot-1x-ci` + `research-lab-ci`, deletion/non-fast-forward blocked, bypass list empty. This governance never authorizes trading or merge by itself.

---

## 4. Safety / execution authorization — BINDING

- SHADOW: authorized only inside existing no-order contracts;
- PAPER/demo broker execution: **NOT AUTHORIZED**;
- LIVE: **NOT AUTHORIZED**;
- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- no broker order-submission path is authorized;
- CI/backtest/research results never grant PAPER/LIVE authority;
- explicit later user authorization is required before PAPER/LIVE;
- `NO_STRATEGY_AUTO_PROMOTION` unchanged;
- frozen V11.2 evidence/fingerprints unchanged.

The Monday demo goal does not override these gates.

---

## 5. Product destination — modular DAX Bot 1.0

The product is not “V11.2 directly attached to MT5”. It is a maintainable modular DAX Bot 1.0 built like a puzzle so one weak piece can be replaced without discarding the system.

Replaceable boundaries include:
- strategy/entry;
- filters/regime logic;
- risk sizing/policy;
- loss/exposure/session admission;
- data/feed adapters;
- broker/execution adapters;
- lifecycle/state/recovery/reconciliation;
- operator/web presentation.

Legacy/V11.2/CAND-001 remain reference, evidence and compatibility inputs rather than architecture constraints. Canonical owner: `docs/NEXTGEN_GREENFIELD_ARCHITECTURE_V1.md`.

---

## 6. Frozen scientific reference — REF-V11.2

V11.2 remains immutable reference evidence:
- 2014–2019;
- 1,673 valid Europe/Berlin session days;
- 172,319 Berlin-session M5 bars;
- 103 bars/session;
- session 09:00–17:30;
- 144 variants;
- 81 WF windows;
- Train 45d / OOS 20d / Step 20d;
- 856 OOS trades;
- OOS total `-31.309210619787684 R`;
- 37 positive / 44 negative WFs;
- median WF PF `0.905769310256018`.

Never relabel these as NextGen profitability evidence.

---

## 7. Implemented NextGen foundation through the current line

Major verified/implemented blocks include:
- canonical broker/storage-neutral domain + ports;
- immutable Parquet/Arrow catalog direction;
- Strategy Plugin V1 + CAND-001 compatibility adapter;
- deterministic product replay and restart/resume;
- research experiment/promotion + product conformance;
- read-only MT5 market-data adapter;
- atomic generic `StateStorePort`;
- operator read model;
- canonical Risk Decision V1 and fixed-cash risk policy;
- broker economics→risk inputs;
- Risk→ExecutionIntent;
- lifecycle/reconciliation/protection reuse;
- canonical loss/exposure admission + restart/freshness evidence;
- canonical session admission;
- deterministic session-consumption ledger;
- atomic `SessionAdmissionGuardCheckpoint`;
- typed NextGen protection bound to authoritative guard;
- Step-2182 commit-boundary audit selecting conservative local write-ahead PREPARED ordering.

Architecture rule: reuse/adapt existing owners before creating duplicate lifecycle, state, broker or recovery stacks.

---

## 8. Official step state at this handoff

Recent sequence:
- 2174–2179: completed session-admission/guard/protection chain;
- 2180: **INTERRUPTED**, later completed through 2182;
- 2181: Masterstand/Monday-target reconciliation **COMPLETED**;
- 2182: commit-boundary audit continuation **COMPLETED**;
- 2183: atomic PREPARED checkpoint **INTERRUPTED** immediately after pointer preparation;
- 2184: chat-capacity continuity hardening **COMPLETED**;
- 2185: PREPARED checkpoint continuation **INTERRUPTED before substantive implementation** because Work/out-of-band hardening and then explicit chat-switch intervention took precedence;
- 2186: current handoff/Work-evidence reconciliation;
- 2187: reserved continuation of the interrupted PREPARED-checkpoint scope after successful 2186 close.

`CURRENT_WORK_STEP.md` is authoritative if this summary becomes stale.

---

## 9. Step-2182 binding commit-boundary decision

Required future ordering:

`typed protection ALLOW evidence -> deterministic local session consumption using intent_id -> post-consumption authoritative SessionAdmissionGuardCheckpoint + REQUESTED lifecycle/protection provenance bound into one local PREPARED state -> only later may a separately authorized external submission be attempted -> restart/reconciliation before retry`

Shared identity:

`ExecutionIntent.intent_id == lifecycle client_order_id == session consumption_id`

Because broker and local filesystem cannot share one transaction, the product prefers conservative under-trading over duplicate exposure.

Step 2187 must implement the smallest evidence-neutral atomic PREPARED checkpoint over existing owners. It must not submit broker orders, infer broker acceptance, auto-release consumed slots, derive session reset/timezone semantics or authorize PAPER/LIVE.

---

## 10. VERIFIED out-of-band ChatGPT Work hardening after Step 2184

Four Work commits landed on PR #109 while the official pointer still named unfinished Step 2185. They are repository-verified evidence but are **not retroactively relabeled as Step 2185**.

1. `643e6741da601cce708fa301a90664e4a5137149` — finite market-data, recovery-integrity and required-CI hardening. Remote CI: DAX #552 GREEN / Research #1336 GREEN.
2. `2e60cd7d3966754ee6e67637c3d01774d24c41ab` — reject non-finite persisted Candidate state before restore. DAX #553 GREEN / Research #1337 GREEN.
3. `7281bc489c15a7c75c7a0cb7d2e590a094aaca34` — coherent restored CAND-001 session state, canonical session/admission behavior. DAX #554 GREEN / Research #1338 GREEN.
4. `76251e0e52567f61d3c6015d22266be4bc977395` — lifecycle semantic restore hardening. DAX #555 GREEN / Research #1339 GREEN.

Latest lifecycle Work result VERIFIED:
- existing `filled_at >= requested_at`;
- existing `closed_at >= filled_at`;
- OPEN: existing `last_close_time >= filled_at`;
- CLOSED: existing `last_close_time >= closed_at`;
- equality remains allowed;
- shared `_validate_intent_geometry()`:
  - BUY: `stop_price < requested_price < target_price`;
  - SELL: `target_price < requested_price < stop_price`;
- checks apply to direct construction and restore envelopes;
- focused 157 passed, expanded Candidate 552 passed, local full pytest 2,159 passed with 6 missing-pwsh skips, remote research 2,165 passed; Ruff/diff/offline gates passed;
- no strategy/cost/V11.2/order-authority changes.

External evidence NOT supplied by these Work runs:
- five Neon/DB gates were skipped where the environment lacked them;
- real Windows/MT5 host evidence was not executed.

These remain `WAITING_EXTERNAL`, not green-by-inference.

---

## 11. ChatGPT Work / “WERKS” operating contract — BINDING

Canonical owner: `docs/WORK_CONTINUITY_PROTOCOL.md` sections 12–16.

Roles:
- **main chat** = architect, prioritizer, task decomposer, reviewer, acceptance/merge owner;
- **ChatGPT Work** = bounded independent audit/Red-Team/implementation workbench.

Use Work mainly at high-leverage boundaries: CI/truth layers, persistence/restore/recovery, execution safety, pre-merge and pre-PAPER. Avoid uncontrolled parallel Work jobs.

Every Work task should state:
- repo / branch / PR / exact starting HEAD and mandatory re-pin;
- READ-ONLY versus IMPLEMENTATION permission;
- exact scope/non-goals/forbidden actions;
- safety/frozen-reference constraints;
- validation/CI/evidence requirements;
- branch-drift behavior;
- expected final report.

Preferred header format:

`👷 WORK-AUFTRAG — MODELL: GPT-5.6 SOL — DENKSTUFE: MITTEL — IMPLEMENTIERUNG ERLAUBT — 💳 CREDIT-BUDGET: NIEDRIG–MITTEL`

Use current available model/configuration rather than inventing an unavailable one. Thinking level is task-driven:
- LEICHT/LOW: narrow/mechanical/isolated;
- MITTEL/MEDIUM: bounded multi-file implementation or focused architecture audit;
- HOCH/HIGH: cross-cutting Red-Team, recovery/safety, pre-merge/pre-PAPER review.

Credit discipline:
- NIEDRIG: narrow fix/audit;
- MITTEL: focused multi-file/composition work;
- HOCH: whole-PR/cross-cutting hardening and independent high-risk review;
- ranges allowed;
- use the smallest Work assignment that buys meaningful independent evidence;
- do not spend Work credits on repetitive status polling or cheap main-chat steering;
- never substitute simulated/missing external evidence for real host/provider evidence.

Work results are not auto-accepted. Main chat re-pins exact repo truth, validates diff/CI/skips, classifies evidence, and owns Acceptance/merge decisions. Work must not merge or refresh Acceptance unless explicitly authorized.

If Work lands commits outside the currently active numbered step, record them as out-of-band evidence and reconcile prospectively with the next unused whole integer rather than falsifying history.

---

## 12. Acceptance and PR state

`docs/DAX_BOT_1X_ALPHA_ACCEPTANCE_STATUS.md` is **stale relative to current PR head**. Work explicitly did not refresh Acceptance.

Therefore:
- do not claim current head accepted merely because CI is green;
- do not merge PR #109 during this handoff;
- a deliberate future Acceptance reconciliation against the then-current exact head is required before any merge decision.

PR #109 remains open/unmerged at the verified Work head.

---

## 13. MT5 / external host lane

Python↔MT5 plumbing and read-only integration exist; NextGen has a read-only MT5 market-data adapter.

Host lane originating at Step 2122 remains `WAITING_EXTERNAL`:
- host wiring/parity/fail-closed repository evidence exists;
- market-open clock/GREEN/candidate/restart evidence still requires the real Windows/MT5 host under appropriate conditions.

This lane does not block independent repository engineering. MT5 connectivity alone does not authorize broker submission.

---

## 14. Monday demo target

Preferred milestone corridor:
1. finish atomic PREPARED local boundary;
2. prove restart/idempotency/reconciliation around it;
3. obtain current Windows/MT5 market-open evidence;
4. run end-to-end SHADOW;
5. audit PAPER readiness and broker economics;
6. obtain explicit PAPER authorization before any demo order submission.

A meaningful SHADOW milestone is preferred over weakening safety just to satisfy the calendar.

---

## 15. Filter database / research governance

Filters must not accumulate until they suppress almost every trade or mask each other.

Binding principles:
- filters remain research artifacts until promoted;
- measure incremental contribution, not only standalone performance;
- use ablation, overlap, backward elimination and Pareto-style analysis where applicable;
- measure trade-count loss and interaction effects;
- test redundancy/mutual suppression;
- preserve OOS/WF/multiple-testing/overfitting discipline;
- no automatic promotion from a good-looking backtest.

Long-term filter records should carry identity/version, definition, family/regime, dependencies, sample/trade counts, overlap/redundancy, incremental contribution, robustness/OOS evidence, interactions, promotion state and retirement reason.

---

## 16. Knowledge / error database

This is a core project pillar. Durable owners include:
- this Masterstand;
- `CURRENT_WORK_STEP.md` + archive;
- `PROJECT_KNOWLEDGE_INDEX.md`;
- `WORK_CONTINUITY_PROTOCOL.md`;
- workflow-integrity and chat-handoff contracts;
- session refresher;
- problem/solution registries;
- architecture/evidence/audit docs;
- regression tests preserving important invariants.

Every non-obvious solved problem should leave:

`Problem -> Root Cause -> Fix/Decision -> Regression Evidence -> Reuse Rule`

Purpose: avoid rediscovery, find ownership quickly and maintain VERIFIED / IMPLEMENTED / RESEARCH / PLANNED / UNVERIFIED distinctions.

---

## 17. Public/open-source learning

Regularly compare relevant architecture/methodology patterns from established systems such as NautilusTrader, Freqtrade, QuantConnect LEAN and vectorbt.

Focus on lifecycle/state machines, recovery/reconciliation, persistence, forward testing, data integrity, research efficiency, overfitting control, governance and operator design. Do not copy strategies blindly and do not rewrite working components merely because an external project is popular.

Step 2500 is the next mandatory full Architecture & Learning Review; obvious structural problems discovered earlier must still be addressed earlier.

---

## 18. Web/operator and Boost/Turbo ideas

Operator/read-model foundations exist; the visual web product intentionally trails execution/recovery core work.

Desired UI eventually shows mode banner, broker/data/clock readiness, strategy/filter/risk identities, session/lifecycle/reconciliation/checkpoint state, fail-closed reasons and evidence/performance views separated from live runtime truth.

Boost/Turbo is a future explicit replaceable risk policy/mode, not an implicit escalation. Current canonical product logic intentionally does not auto-promote old BASE/BOOST/HIGH research names/values.

---

## 19. Checkpoint governance

- Next 250-step Masterstand checkpoint: **2250**.
- Next 500-step full audit: **2500**.
- Next 500-step Architecture & Learning Review: **2500**.

Step 2500 must critique architecture/process using new evidence, repeated failures, runtime/research cost, duplication/coupling, recovery/test/operator quality and refreshed public knowledge. Outcomes: KEEP / IMPROVE / REFACTOR / RETIRE / DEFER. KEEP/no-change is valid; the checkpoint itself never justifies a rewrite.

---

## 20. Next-chat quick start

User writes:

`Weiter mit dem DAXBot`

Expected behavior:
- re-pin repo/branch/PR/fresh head/CI;
- read refresher, current pointer, workflow gate, Masterstand, Knowledge Index and Work protocol;
- report recovered state briefly;
- do not ask for old-chat paste;
- continue from the pointer, expected after successful Step-2186 close to be **Step 2187: atomic local NextGen PREPARED checkpoint continuation**;
- preserve stale Acceptance and all `WAITING_EXTERNAL` lanes separately.

---

## 21. Truth labels

- **VERIFIED** — explicit supporting evidence/tests/runtime evidence as applicable;
- **IMPLEMENTED** — code exists, not automatically host/profitability proof;
- **RESEARCH** — experiment/hypothesis, not product truth;
- **PLANNED** — intended, not implemented;
- **UNVERIFIED** — insufficient evidence;
- **WAITING_EXTERNAL** — repository work cannot manufacture the required external evidence.

---

## 22. Bottom line

The project has materially moved beyond V11.2 toward a modular DAX Bot 1.0. The next technical frontier remains the safe atomic local PREPARED boundary connecting canonical protection/session/lifecycle/state/reconciliation pieces without a duplicate stack.

The four recent Work hardening commits materially strengthen restore semantics, finite-value handling, session coherence, recovery/CI integrity and lifecycle geometry/time invariants, but they do not constitute Acceptance refresh, broker execution authorization or Windows/MT5 proof.

This Step-2186 handoff deliberately stops technical progression after continuity is green because the user requested a new chat. The next chat resumes from repository truth with `Weiter mit dem DAXBot`.
