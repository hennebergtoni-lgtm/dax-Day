# DAX-BOT MASTERSTAND — NEXT-CHAT HANDOVER

Status: **BINDING HANDOVER / REPOSITORY TRUTH FIRST**  
Updated: **2026-09-13 — Step 2184 chat-capacity continuity handoff**  
Repository: `hennebergtoni-lgtm/dax-Day`  
Working branch: `nextgen-bot-line-v1`  
Pull request: `#109` -> `main`

This is the canonical durable handover for the DAX Daytrading Bot project. It exists specifically so a new ChatGPT conversation can recover the project after conversation-length limits, context compaction, reconnects or ordinary chat changes without relying on conversational memory.

If this prose ever disagrees with fresh repository evidence, precedence is:

1. exact code / tests / machine evidence / fresh runtime telemetry;
2. `docs/CURRENT_WORK_STEP.md` for official step numbering;
3. binding safety/governance contracts;
4. this Masterstand;
5. chat memory.

The previous more verbose Masterstand remains recoverable through Git history. Pre-refresh blob: `d4ca60477e5c5030a44e657527a5559feb053c4f`.

---

## 1. Resume command and mandatory new-chat behavior

Canonical resume codeword:

`Weiter mit dem DAXBot`

Accepted user-friendly alias:

`Weiter mit DAXbot`

On either phrase in a new chat:

1. read `docs/SESSION_EXECUTION_REFRESHER.md`;
2. pin repository, working branch, PR #109, **fresh exact HEAD** and current CI;
3. read `docs/CURRENT_WORK_STEP.md`; it is the only active-step authority;
4. read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`;
5. read this Masterstand;
6. read `docs/PROJECT_KNOWLEDGE_INDEX.md` and the problem/solution registries;
7. inspect only the code/docs/tests needed for the active step;
8. reconcile `WAITING_EXTERNAL`, `INTERRUPTED` and `BLOCKED` lanes separately;
9. continue safe work automatically when the Step-Close-Gate permits it.

Do **not** ask the user to paste the previous chat or reconstruct the project manually when repository access is available.

The user intends to discuss **ChatGPT Work** in the new chat before or around the technical continuation. That product discussion does not itself change repository truth or trading authorization; after it, resume from the fresh pointer rather than from chat memory.

---

## 2. Working style — BINDING

The user wants continuous, visible engineering work with very compact status reports.

Required cadence:

`Step N -> short activity -> 1–2 sentence Zwischenstand -> ✅ / ⚠️ / ❌ -> actual next action`

Binding behavior:

- Repository truth overrides chat recollection.
- Tool/interface status alone is not a visible Zwischenstand.
- Zwischenstände are **visibility points, not stops**.
- While a safe executable next action exists, do not send a turn-ending final/status response merely saying work will continue.
- If one method stalls or repeatedly yields no new evidence, switch to another safe method rather than waiting for the user to restart progress.
- Errors are shown openly and corrected inside the same active work unit when appropriate.
- Official step numbers are whole integers only.
- Pointer-before-next-step and Step-Close-Gate are mandatory.
- Interrupted old work is resumed under the next unused integer with provenance; never roll visible numbering backward.
- Do not claim invisible/background work after a final response.

### 2026-09-13 workflow incident and correction

During the long chat, the assistant repeatedly stopped after progress/status text even though the next safe repository action was already known. This was a **workflow failure**, not a technical DAX-BOT blocker.

Durable correction:

- before any final response during active engineering, apply the end-of-turn guard in `SESSION_EXECUTION_REFRESHER.md`;
- if safe work remains, continue with an actual action;
- a found file, green sub-check, CI poll, warning or partial audit is not a valid stop condition;
- if the platform itself reports that the conversation is too long, execute the controlled chat-capacity handoff instead of stopping ambiguously.

### Chat-capacity saturation rule

The platform message that a conversation is too long is treated as a **context-capacity interruption**, not a project technical failure.

When possible before leaving the old chat:

1. re-pin repo/head/CI/pointer;
2. mark incomplete technical work `INTERRUPTED` truthfully;
3. create a dedicated continuity/Masterstand work unit under the next unused integer;
4. refresh handoff documents;
5. reserve unfinished technical scope for another later integer;
6. start the new chat with `Weiter mit dem DAXBot` or `Weiter mit DAXbot`.

If the platform hard-stops before those writes are possible, the new chat performs this reconciliation first.

---

## 3. Fresh repository truth at start of this handoff block

Before Step-2184 documentation writes:

- PR #109: **OPEN / UNMERGED / MERGEABLE / NOT DRAFT**;
- base: `main`;
- work branch: `nextgen-bot-line-v1`;
- base SHA: `e0784ebfc11bee28475fd9c3385be661af58a738`;
- fresh branch head at handoff preflight: `1540012da9931aab9b726f419d40a5316837ef2f`;
- commit message: `docs: close Step 2182 and open Step 2183 prepared checkpoint`;
- on that head: `dax-bot-1x-ci` #547 **GREEN**;
- on that head: `research-lab-ci` #1331 **GREEN**.

Step-2184 documentation commits create newer heads. Therefore every new chat must re-pin HEAD and CI rather than treating the SHA above as current forever.

`main` remains governed by repository ruleset `Projekt main`: PR required, strict checks `dax-bot-1x-ci` + `research-lab-ci`, deletion and non-fast-forward blocked, bypass list empty. This is governance evidence only; it does not authorize merge or trading.

---

## 4. Safety / execution authorization — BINDING

Current project safety state:

- SHADOW: authorized only inside the existing no-order contract;
- PAPER / demo broker execution: **NOT AUTHORIZED**;
- LIVE: **NOT AUTHORIZED**;
- `execution_capability=NONE` where required;
- `order_execution_enabled=false` where required;
- no broker order-submission path is currently authorized;
- no CI result, backtest result or research promotion grants PAPER/LIVE authority;
- explicit later user authorization is mandatory before PAPER or LIVE;
- `NO_STRATEGY_AUTO_PROMOTION` remains unchanged.

The current goal of reaching a demo milestone does **not** override these gates.

---

## 5. Project destination — DAX Bot 1.0

The user’s product goal is not merely to attach the old V11.2 logic to MT5. The project is building a maintainable **DAX Bot 1.0** with modular components that can be replaced independently.

User’s puzzle principle:

- strategy/entry is one piece;
- filters/regime logic are separate pieces;
- risk sizing/policy is a separate piece;
- session/admission is a separate piece;
- data/feed adapters are separate pieces;
- broker/execution adapters are edge pieces;
- state/recovery/reconciliation are separate infrastructure pieces;
- operator/web presentation is separate from trading authority.

If one piece later proves defective, inefficient or unprofitable, replace that piece rather than discarding the whole bot.

This is now reflected in the NextGen architecture rather than merely being an idea.

---

## 6. Frozen scientific reference — REF-V11.2

V11.2 remains immutable scientific/reference evidence, not the NextGen chassis.

Verified historical reference facts:

- 2014–2019;
- 1,673 valid Europe/Berlin session days;
- 481,824 raw M5 rows;
- 172,319 Berlin-session M5 bars;
- 103 bars/session;
- session 09:00–17:30 Europe/Berlin;
- 0 known OHLC errors;
- 144 variants;
- 81 WF windows;
- Train 45d / OOS 20d / Step 20d;
- 856 OOS trades;
- normal OOS total `-31.309210619787684 R`;
- 37 positive / 44 negative WFs;
- median WF PF `0.905769310256018`.

Never relabel these as NextGen profitability evidence. V11.2 is a frozen comparison/reference baseline.

---

## 7. CAND-001 / DAX-BOT 1.0-alpha compatibility line

Frozen CAND-001 semantics remain available as legacy product/reference/compatibility evidence:

- DE40 M5;
- Europe/Berlin 09:00–17:30;
- OR15;
- closed-M5 confirmed breakout;
- BOTH directions;
- stop = OR opposite;
- target = 1.5R;
- maximum one admitted trade/session.

Repository-side 1.0-alpha is a correctness/control milestone, not a profitability proof.

Legacy/CAND-001 rules must not silently leak into generic NextGen core contracts. Compatibility is explicit through adapters.

---

## 8. NextGen architecture — verified direction

Canonical architecture owner: `docs/NEXTGEN_GREENFIELD_ARCHITECTURE_V1.md`.

Binding architecture rule:

**Legacy is reference, regression evidence and compatibility input — not the NextGen architecture constraint.**

Key implemented/verified building blocks through the current work line include:

- canonical broker-neutral domain and ports;
- immutable Parquet/Arrow historical data catalog direction;
- Strategy Plugin V1;
- explicit CAND-001 compatibility adapter;
- deterministic product replay engine;
- research experiment/promotion artifact and research→product conformance;
- read-only MT5 market-data adapter behind canonical ports;
- generic atomic `StateStorePort` implementation;
- generic operator read model;
- deterministic product checkpoint and restart/resume parity;
- CAND-001 state codec / real Candidate resume parity;
- dependency isolation and compatibility/retirement audit;
- canonical Risk Decision V1;
- Risk→ExecutionIntent bridge;
- reuse of existing broker lifecycle/reconciliation/protection owners;
- PAPER pre-authorization composition audit without granting authorization;
- broker economics→risk-input adapter;
- fixed-cash risk policy;
- canonical loss/exposure admission policy;
- authoritative risk+admission bridge/protection evidence;
- restart-safe loss/exposure checkpoint/freshness;
- canonical session-admission policy;
- authoritative session admission / deterministic consumption state;
- restart-safe session consumption ledger;
- combined atomic SessionAdmissionGuardCheckpoint;
- typed NextGen protection using the authoritative guard;
- protected session-consumption commit-boundary audit selecting fail-safe local write-ahead PREPARED ordering.

The architecture intentionally prefers compatibility-first adaptation over duplicate stacks.

---

## 9. Most recent verified technical sequence

Recent repository truth:

- **2174 COMPLETED** — session-admission consumption transition audit;
- **2175 COMPLETED** — deterministic idempotent session-consumption state;
- **2176 COMPLETED** — restart-safe consumption-state persistence;
- **2177 COMPLETED** — ledger/freshness crash-coherence audit;
- **2178 COMPLETED** — combined atomic SessionAdmissionGuardCheckpoint;
- **2179 COMPLETED** — typed NextGen protection uses that guard as authoritative session evidence;
- **2180 INTERRUPTED** — first commit-boundary audit attempt interrupted by explicit continuity intervention; no technical conclusion claimed there;
- **2181 COMPLETED** — prior Masterstand/Monday-target continuity reconciliation;
- **2182 COMPLETED** — commit-boundary audit continuation selected conservative local PREPARED write-ahead ordering;
- **2183 INTERRUPTED** — atomic local PREPARED checkpoint implementation had only been opened/prepared when the user requested the present chat-capacity/Masterstand intervention; no 2183 implementation completion is claimed;
- **2184** — this chat-capacity continuity hardening + Masterstand refresh.

Step 2182 binding decision:

`protection ALLOW evidence -> deterministic local session consumption using intent_id -> updated authoritative SessionAdmissionGuardCheckpoint + REQUESTED lifecycle/protection provenance bound into one local PREPARED state -> only later may a separately authorized external submission be attempted -> restart must reconcile before retry`

Shared deterministic identity:

`ExecutionIntent.intent_id == lifecycle client_order_id == session consumption_id`

Because broker and local filesystem cannot share one atomic transaction, the product deliberately prefers conservative under-trading over duplicate exposure.

---

## 10. Exact technical continuation after this handoff

After Step 2184 is closed, the unfinished Step-2183 scope must continue under **Step 2185** due monotonic numbering.

Planned Step 2185 scope:

Implement the smallest evidence-neutral atomic local **PREPARED checkpoint/composition** required by Step 2182.

Required properties:

1. reuse `ExecutionIntent.intent_id` as lifecycle `client_order_id` and session `consumption_id`;
2. bind the post-consumption authoritative `SessionAdmissionGuardCheckpoint`;
3. bind existing REQUESTED lifecycle / broker-execution checkpoint semantics, not a second lifecycle;
4. bind typed protection verdict/provenance;
5. deterministic tamper-evident identity/fingerprint;
6. persist all local PREPARED truth under one existing `StateStorePort` key/payload;
7. restart/load preserves original evidence and never invents broker acceptance or freshness;
8. cross-wired identities fail closed;
9. retry/replay of the same deterministic local attempt remains idempotent;
10. no broker API/order submission, PAPER/LIVE authorization, automatic slot release, session reset/timezone derivation or CAND-001 mutation.

The new chat must re-read `CURRENT_WORK_STEP.md` because it is authoritative if the pointer has advanced beyond this snapshot.

---

## 11. MT5 / host integration state

The Python↔MT5 plumbing and read-only integration work exists; NextGen has a read-only canonical MT5 market-data adapter.

Separate current host lane:

- origin Step 2122;
- status `WAITING_EXTERNAL`;
- host wiring/parity/fail-closed evidence is verified;
- market-open clock/GREEN/candidate/restart evidence still requires the real Windows/MT5 host under suitable market conditions.

This lane does not globally block independent repository engineering.

No broker submission is authorized merely because MT5 connectivity works.

---

## 12. Monday demo target

The user wants a meaningful Monday milestone.

Correct interpretation:

- a real **SHADOW** end-to-end milestone on MT5 data is the first preferred target;
- demo/PAPER order submission is only allowed after all required technical readiness gates are verified **and** the user explicitly authorizes PAPER;
- do not weaken protection/restart/idempotency/reconciliation gates just to meet a calendar target.

Priority corridor toward that milestone:

1. finish the PREPARED local commit boundary;
2. prove restart/idempotency/reconciliation behavior around it;
3. verify current Windows/MT5 market-open host evidence;
4. run end-to-end SHADOW;
5. audit PAPER readiness and broker economics;
6. obtain explicit PAPER authorization before any demo order-submission capability is enabled.

---

## 13. Filter database / research governance

The filter/research system must avoid the classic failure mode where accumulated filters suppress virtually all trades or mask one another.

Binding research principles already established:

- filters are research artifacts until promoted;
- measure incremental contribution, not just standalone attractiveness;
- use ablation / overlap / backward-elimination / Pareto-style analysis where applicable;
- measure trade-count loss and interaction effects;
- avoid auto-promoting filters because one backtest looks good;
- preserve OOS/WF and multiple-testing/overfitting discipline;
- filter combinations must be evaluated for redundancy and mutual suppression;
- no `NO_STRATEGY_AUTO_PROMOTION` bypass.

The long-term filter database should record at minimum identity/version, definition, regime/feature family, dependencies, sample/trade counts, overlap/redundancy, incremental contribution, robustness/OOS evidence, interactions, promotion state and retirement reason.

The database is not considered finished merely because many candidate filters exist.

---

## 14. Knowledge / problem-solution database

This is an explicit project pillar, not incidental documentation.

Existing durable mechanisms include:

- `MASTERSTAND.md`;
- `CURRENT_WORK_STEP.md` + archive;
- `PROJECT_KNOWLEDGE_INDEX.md`;
- workflow-integrity gate;
- chat-handoff protocol;
- session execution refresher;
- problem/solution registries;
- topic-specific architecture/evidence/audit contracts;
- CI regression tests that preserve important architectural/governance invariants.

Purpose:

- avoid rediscovering solved failures;
- find ownership quickly;
- distinguish VERIFIED / IMPLEMENTED / RESEARCH / PLANNED / UNVERIFIED;
- record why a design exists, not only what code currently does;
- make chat loss and contributor changes survivable.

Today’s premature-stop/chat-saturation lesson has been added to this continuity layer.

---

## 15. Public / open-source learning

The project deliberately checks established public systems such as:

- NautilusTrader;
- Freqtrade;
- QuantConnect LEAN;
- vectorbt;
- comparable established execution/backtesting systems.

The goal is not to copy strategies or import entire frameworks blindly. The scan is for useful patterns in:

- lifecycle/state machines;
- recovery/reconciliation;
- state persistence;
- forward testing;
- data integrity;
- performance/research efficiency;
- overfitting controls;
- governance/observability/operator design.

Public popularity alone is not evidence to rewrite a working component. Patterns are classified using KEEP / IMPROVE / REFACTOR / RETIRE / DEFER and adapted only when evidence supports them.

A full Architecture & Learning Review is mandatory at Step 2500, but obvious structural problems discovered earlier must not wait until that checkpoint.

---

## 16. Web / operator interface and Boost/Turbo ideas

Operator/read-model groundwork exists, but the visual web/operator product is intentionally behind the execution/recovery core in priority.

Desired eventual UI ideas include:

- obvious SHADOW/PAPER/LIVE mode banner;
- broker/data/clock/market readiness;
- strategy/filter/risk-policy identity;
- current session/trade/admission state;
- lifecycle/reconciliation health;
- restart/checkpoint state;
- warnings/fail-closed reasons;
- performance/evidence views separated from live runtime truth;
- configurable higher-risk modes such as Boost/Turbo only through explicit policy selection and authorization.

Boost/Turbo must **not** be an implicit risk escalation. The canonical core currently uses a simple fixed-cash policy rather than promoting old BASE/BOOST/HIGH research profile names or values. Higher-risk modes are future product policies that must remain replaceable and explicitly authorized.

---

## 17. Checkpoint governance

Next mandatory 250-step Masterstand checkpoint: **2250**.

Next mandatory 500-step full audit: **2500**.

Next mandatory 500-step Architecture & Learning Review: **2500**.

The Step-2500 review must be a real architecture/learning reassessment, not a chronological status summary. It must ask what is known now that was not known when earlier design choices were made, inspect repeated failures/CI friction/runtime cost/duplication/coupling/recovery/test quality/operator usability, refresh relevant public-system knowledge and produce a prioritized post-review plan.

KEEP/no-change is a valid outcome; a checkpoint alone never justifies a rewrite.

---

## 18. New-chat quick start

User opens a new chat and writes:

`Weiter mit DAXbot`

Expected assistant behavior:

- read the refresher;
- re-pin repo/branch/PR/head/CI;
- read `CURRENT_WORK_STEP.md`;
- read workflow integrity + this Masterstand + Knowledge Index;
- report the recovered state briefly;
- do not ask the user to paste this chat;
- if the user wants to discuss ChatGPT Work first, answer that discussion while retaining the recovered DAX-BOT pointer;
- when technical work resumes, continue from the repository’s current whole-number step, expected to be Step 2185 after successful closure of this handoff block.

---

## 19. Non-negotiable truth labels

Maintain the distinction:

- **VERIFIED** — supported by explicit evidence/tests/runtime evidence as applicable;
- **IMPLEMENTED** — code exists, but not automatically equivalent to real-host or profitability proof;
- **RESEARCH** — hypothesis/diagnostic/experiment, not product truth;
- **PLANNED** — intended but not yet implemented;
- **UNVERIFIED** — not yet evidenced sufficiently.

Never convert one category into another merely because a chat summary sounds confident.

---

## 20. Bottom line

The project has moved materially beyond V11.2 toward a modular DAX Bot 1.0 architecture. The current technical frontier is not strategy decoration; it is the safe atomic local PREPARED boundary that connects already-existing canonical risk/admission/protection/session/lifecycle/state/reconciliation pieces without introducing duplicate execution or storage stacks.

The current chat-length problem is handled as a continuity/governance concern. Important project goals, technical state and working style are now repository-backed so starting a new chat is a normal controlled handoff rather than a loss of project memory.
