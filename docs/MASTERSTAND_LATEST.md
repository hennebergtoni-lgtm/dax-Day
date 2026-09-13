# DAX-BOT MASTERSTAND LATEST — CHAT HANDOVER

Status: **BINDING LATEST HANDOVER / REPOSITORY TRUTH FIRST**  
Updated: **2026-09-13 — Step 2201 chat-length handoff**  
Repository: `hennebergtoni-lgtm/dax-Day`  
Working branch: `nextgen-bot-line-v1`  
Pull request: `#109` -> `main`

This file is the **latest chat-handover overlay** for the DAX Daytrading Bot project. It supersedes stale chronological statements in `docs/MASTERSTAND.md` where that older file still describes the Step-2186 era. It does **not** supersede repository code/tests/machine evidence, `docs/CURRENT_WORK_STEP.md`, safety/governance contracts or fresh runtime evidence.

Truth precedence:
1. exact current code/tests/machine evidence/current runtime telemetry;
2. `docs/CURRENT_WORK_STEP.md` for official whole-number step truth;
3. binding safety/governance/authorization contracts;
4. this `MASTERSTAND_LATEST.md`;
5. older `MASTERSTAND.md` historical context;
6. chat memory.

---

## 1. New-chat resume procedure — BINDING

Canonical resume phrase:

`Weiter mit dem DAXBot`

On that phrase, the new chat MUST:
1. fetch PR #109 and pin the **fresh exact head SHA** before any write;
2. read `docs/CURRENT_WORK_STEP.md`;
3. read this `docs/MASTERSTAND_LATEST.md`;
4. read `docs/SESSION_EXECUTION_REFRESHER.md`, `docs/WORK_CONTINUITY_PROTOCOL.md` and `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md` as needed;
5. verify current required GitHub CI on the fresh head;
6. inspect only the active-step owner/code/tests plus directly relevant predecessor evidence;
7. continue the active step automatically when safe;
8. do **not** ask the user to reconstruct or paste the prior chat when repository access is available.

If the branch head differs from the handoff head below, reconcile the intervening commits before continuing. Repository truth wins.

---

## 2. Exact repository truth at this handoff

Verified before creating this handoff:

- PR #109: **OPEN / UNMERGED**;
- branch: `nextgen-bot-line-v1`;
- base: `main`;
- base SHA: `e0784ebfc11bee28475fd9c3385be661af58a738`;
- pre-handoff PR head: `2aec07185668ae06f8a0c8a0b5288ffccee36124`;
- `dax-bot-1x-ci` #613: **GREEN**;
- `research-lab-ci` #1397: **GREEN**;
- Acceptance in PR body remains deliberately stale relative to current PR head;
- no merge authorized;
- no Acceptance refresh authorized merely because CI is green.

This handoff commit creates a newer branch head. Therefore the next chat MUST re-pin the actual head and CI rather than assuming `2aec0718...` is still final.

---

## 3. Current official work pointer

At the verified pre-handoff head, `docs/CURRENT_WORK_STEP.md` states:

- last completed whole-number step: **2200**;
- active whole-number step: **2201**;
- active state: **ACTIVE — READ-ONLY / NO BROKER SIDE EFFECT**;
- next successful step: **2202**;
- host-verification lane: **2122 — WAITING_EXTERNAL**;
- next mandatory 250-step Masterstand checkpoint: **2250**;
- next mandatory 500-step full audit / Architecture & Learning Review: **2500**;
- decimal/letter step IDs prohibited.

Step 2201 scope: audit/compose the remaining read-only first-DEMO-order readiness chain after Step 2200: current Windows/MT5 host lane, market-open feed and broker clock/timezone, exact observed DEMO account/server/symbol, real transport-tag lookup support, broker economics, explicit risk/loss/sizing policy and current protection. **REUSE before BUILD.** No actual DEMO order.

---

## 4. Current execution authorization — BINDING

User authorization currently permits:

- technical DEMO-evidence **transport/lookup implementation and tests**;
- read-only broker lookup/query preparation;
- read-only Windows/MT5 account/feed/evidence checks;
- technical local/restart/reconciliation preparation.

User has explicitly **NOT** authorized:

- the first actual DEMO-evidence broker order;
- normal PAPER broker execution;
- LIVE execution.

Binding safety state:

- SHADOW: **AUTHORIZED** inside existing no-order contracts;
- actual DEMO evidence order: **NOT AUTHORIZED — separate explicit authorization required**;
- PAPER: **NOT AUTHORIZED**;
- LIVE: **NOT AUTHORIZED**;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no `mt5.order_send` call is authorized;
- no cancel/modify broker side effect is authorized;
- no automatic consumed-slot release;
- no blind restart retry/resubmit;
- CI/fixtures/Linux evidence never becomes real broker evidence by inference.

Do not weaken these gates to satisfy the Monday target.

---

## 5. Monday target — current interpretation

Target date: **Monday 2026-09-14**.

The practical target is a safe **DEMO/PAPER-oriented milestone**, not Echtgeld-LIVE. The desired path is:

1. finish all repository-local/read-only DEMO readiness work that can be proven without broker side effects;
2. obtain fresh real Windows/MT5 market-open evidence;
3. verify account/server/symbol/clock/feed/broker economics/risk/loss/protection truth;
4. verify lookup/history/fill support and restart/reconciliation behavior with real read-only provider evidence;
5. only after all preconditions are green, separately request explicit authorization for the **first actual DEMO-evidence order**;
6. normal PAPER remains a later separate promotion/readiness decision.

Do not claim Monday success in advance. Prefer a safe blocked state over a calendar-driven safety inversion.

---

## 6. Verified step sequence since prior Masterstand

### 2187 — Atomic local NextGen PREPARED checkpoint — COMPLETED

- Shared identity: `ExecutionIntent.intent_id == lifecycle client_order_id == session consumption_id`.
- Local post-consumption guard + REQUESTED lifecycle + typed protection bound into PREPARED before any future transport.
- Exact retry idempotent; no invented venue/fill evidence; no blind resubmit.
- Implementation/evidence head: `59b7c3f69500c5060431cc5b8fe494ec0c2e9cc7`.
- Focused/relevant/full validation and CI GREEN.

### 2188 — PAPER-readiness evidence ownership audit — COMPLETED

- Gates classified REUSE / ADAPT / EXTERNAL / USER_AUTH.
- No generic readiness composer justified.
- Found real Neon production migration lag 0008/0009.

### 2189 — Connected Neon migration/integrity closure — COMPLETED

- Exact repository migrations 0008/0009 applied to production Neon after explicit approval.
- 9/9 migrations, telemetry tables/view and safety constraints verified.
- Frozen V11.2/dataset/ACTIVE_REFERENCE preserved.
- Separate `step-2189-db-drills` branch used for isolated restore/detail-import conflict drills.
- Direct Neon evidence, not inferred from skipped PR CI DB jobs.

### 2190 — Monday-demo critical-path reassessment — COMPLETED

- Main-chat audit + independent Work Red-Team confirmed a real bootstrap gap: normal PAPER required real broker evidence that existing no-order preparation could not itself produce.
- Missing capability was a narrow separately authorized DEMO-evidence bootstrap path, not a second execution stack.

### 2191 — DEMO-evidence authorization contract — COMPLETED

- Separate DEMO_EVIDENCE authorization from final PAPER authorization.
- Exact account/server/symbol/time/action/submission scope.
- REAL/CONTEST/UNKNOWN and cross-wiring fail closed.
- Still `NONE/false` and non-executable.

### 2192 — Read-only MT5 account observation ownership audit — COMPLETED

- Existing `scripts/mt5_windows_probe.py` reuses the single `mt5.account_info()` observation.
- No second MT5 account reader justified.

### 2193 — MT5 demo-account context normalization — COMPLETED

- Dependency-free DEMO/CONTEST/REAL/UNKNOWN normalization.
- Raw login never serialized; deterministic namespaced SHA-256 account identity instead.
- Runtime constants used; missing/malformed/ambiguous -> UNKNOWN.
- Legacy SHADOW remains compatible.

### 2194 — DEMO pre-transport composition audit — COMPLETED

- Selected one durable one-way local `TRANSPORT_ATTEMPT_RESERVED` phase before any future venue side effect.
- Existing PREPARED/auth/account/bundle/store/lifecycle/reconciliation owners reused.

### 2195–2199 — Large Work recovery/forward tranche — COMPLETED

Independent Work repaired the red Step-2195 line and advanced through Step 2199.

Root cause of red CI: `WindowsMt5Bundle.demo_account_context` was accidentally made mandatory and broke legacy SHADOW constructors. Compatibility restored without weakening DEMO reservation requirements.

Work final head for this tranche: `d7cccf6bacc866669134629ff81cdc0491416a33`.

Key results:
- 2195: restart-safe transport-attempt reservation checkpoint repaired/closed;
- 2196: fingerprint-pinned restart-load + UNKNOWN operator state;
- 2197: shared QUERY preflight + reconciliation input boundary;
- 2198: deterministic local QUERY work-item projection;
- 2199: integrated restart/failure/replay/safety evidence.

Work validation reported local full `2304 passed / 6 pwsh skipped`; final remote research CI reported `2310 passed`; Ruff + eight offline gates GREEN.

Main chat independently re-pinned and verified the Work result before accepting it.

### 2200 — Technical DEMO-evidence transport/lookup implementation — COMPLETED

User explicitly authorized the technical implementation/tests **without any actual broker order**.

Implemented/verified direction:
- deterministic local MT5 correlation identity/transport tag from full intent identity;
- non-executable transport draft/payload preparation;
- read-only MT5 lookup path using account/open-orders/order-history/deal-history surfaces;
- identity checks bind symbol + magic/tag/comment semantics conservatively;
- null result, multiple matches, account mismatch, contradictory quantity/fill, SDK failure or expired history window fail closed;
- restart/query remains `query/reconcile first`, never blind resubmit;
- request-preparation path reuses `AtomicFileStateStore` + reservation + current validated Windows bundle;
- no `mt5.order_send`, cancel or modify path;
- no execution activation.

Final technical candidate head: `4c5f88645d428c30c55eef4a0d56f201f232c24a`.

Validation:
- `dax-bot-1x-ci` #612 GREEN;
- `research-lab-ci` #1396 GREEN;
- research reported **2334 tests passed**;
- Ruff GREEN;
- eight offline/safety gates GREEN;
- static safety remained `Paper/Live BLOCKED | NO_ORDER`.

Pointer closeout then produced pre-handoff head `2aec07185668ae06f8a0c8a0b5288ffccee36124`, with CI #613/#1397 GREEN.

---

## 7. Step 2201 partial audit finding at chat handoff

Step 2201 is **not completed**. Do not retroactively mark it complete.

Main-chat analysis before the chat-length handoff found:

- broker economics already has a canonical owner;
- fixed-cash risk/sizing already has a canonical owner;
- loss/exposure admission already has a canonical owner;
- loss/exposure persistence/restart evidence already has a canonical owner;
- operator risk-profile/readiness surfaces already exist;
- execution protection already has a canonical typed owner;
- a new monolithic “super-risk owner” is **not justified**.

The important remaining gap appears to be **authoritative observation production/evidence**, not basic risk math:
- real current broker time/timezone/session-day/reset semantics;
- current realized/unrealized PnL semantics where required;
- current exposure/loss observation provenance;
- exact broker economics observed on the real DEMO environment;
- fresh market/open feed evidence;
- Windows/MT5 identity-bound real lookup/history/fill evidence;
- promotion of explicit risk/loss/sizing policy values only from evidence — never invented defaults.

This is a **partial audit conclusion**, not yet a committed Step-2201 closeout. New chat must verify concrete owner files/tests before writing the Step-2201 sign-off.

---

## 8. Public/open-source learning — current use

Public projects remain an active cross-check, not a source of automatic design replacement.

Primary references:
- NautilusTrader;
- Freqtrade;
- QuantConnect LEAN;
- vectorbt where research methodology is relevant.

Current relevant lessons:
- keep risk management, protections and brokerage/reconciliation as separate owners rather than a monolithic super-owner;
- preserve client identity across restart/reconciliation;
- reconciliation/query comes before trading/retry after ambiguous restart states;
- “not found in open orders” is not proof that no venue side effect occurred;
- dry-run/simulation is not real broker evidence;
- provider/broker adapter boundaries should remain thin and explicit.

Use public-project scans periodically and at architecture/recovery/execution boundaries. Do not waste time repeatedly scanning when the next local step is already clear.

---

## 9. Chat operating rules — BINDING USER PREFERENCE

The user has repeatedly and explicitly requested **continuous automatic progression**.

### 9.1 Intermediate status is NOT a stop

A Zwischenstand, successful subtest, file discovery, warning, CI poll, public-Git finding or partial conclusion does **not** justify ending the turn while safe work remains.

Do not end a turn with only:
- “Ich mache weiter”;
- “der nächste Schritt ist klar”;
- “jetzt prüfe ich X”;
- a status recap followed by no actual next action.

If the next safe action is known and tools are available, execute it in the same working sequence.

### 9.2 Automatic continuation / stop rules

Continue automatically through whole-number steps until one of these occurs:

1. **error severity >= 3** under the project’s 1–5 operational error classification;
2. material branch/PR drift that cannot be safely reconciled before writing;
3. explicit safety/authorization boundary requiring user approval;
4. required real external evidence is unavailable and no independent repository work remains;
5. Step **2250** Masterstand checkpoint;
6. Step **2500** full audit / Architecture & Learning Review;
7. a genuinely large/high-risk package is identified where Work gives material leverage;
8. explicit user STOP/chat-switch request;
9. product/tool runtime itself times out or the chat reaches a hard platform length limit.

Errors 1–2 are normal fix-and-continue conditions. Do not stop merely because CI is red at levels 1–2; diagnose, fix, rerun and continue.

### 9.3 Reasoning/tool-loop optimization

Recent chat experienced repeated timeouts and unproductive repeated GitHub searches. Corrective rule:

- standard main-chat reasoning effort: **GPT-5.6 Sol MEDIUM** for normal repository inspection, tests, bounded implementation and step progression;
- use HIGH only for cross-cutting architecture, recovery, execution safety, difficult root-cause analysis or major review;
- if the same search/tool approach fails twice or returns no useful information, **change method** rather than repeating it;
- prefer direct exact-file fetch, commit diff, workflow logs, owner docs and known refs over broad repeated searches;
- re-use already verified current-head evidence instead of re-fetching unchanged facts without reason;
- repository truth is a checkpoint after platform timeout; resume from the latest verified head rather than reconstructing hours of chat reasoning.

The screenshot-visible “Reasoning fehlgeschlagen / Zeitüberschreitung” was a platform/tool-run failure, not a DAX-BOT technical blocker.

### 9.4 Visibility cadence

Preferred compact cadence while actively working:

`Schritt N: Tätigkeit -> kurzer Zwischenstand -> ✅ / ⚠️ / ❌ -> tatsächliche nächste Aktion`

Visibility should not become a stream of repetitive status-only messages. Prefer meaningful milestones and actual tool/action progress.

---

## 10. ChatGPT Work strategy — BINDING

Work is valuable and has repeatedly found important errors. It is **not** the default for every 2–3 main-chat steps.

Main chat role:
- architecture/prioritization;
- normal repository inspection;
- small/medium implementation;
- CI diagnosis/fix;
- step sequencing;
- independent verification of Work output;
- Acceptance/merge decisions.

Use Work when there is a **real large/high-leverage package**, especially:
- roughly 10–30 coherent steps or a package that would take ~2–3 hours of main-chat iteration;
- multi-subsystem execution/recovery/reconciliation work;
- CI-recovery + broad regression/hardening tranche;
- pre-DEMO/PAPER Red-Team;
- persistence/restart/recovery/state integrity;
- whole-PR or broad safety audit;
- large multi-file implementation where parallel compute/review materially saves time.

The user is willing to spend additional Work credits/money when the package is genuinely worth it and likely to accelerate progress or improve safety/quality.

Do **not** spend Work on:
- simple file lookup;
- single small test fix;
- routine CI polling;
- obvious pointer edits;
- work main chat can complete cheaply and safely.

Preferred Work header:

`👷 WORK-AUFTRAG — MODELL: GPT-5.6 SOL — DENKSTUFE: HOCH — IMPLEMENTIERUNG ERLAUBT — 💳 CREDIT-BUDGET: HOCH`

Adjust thinking/credit downward for smaller bounded work. For a true “Brett” package, HIGH/HIGH is acceptable.

Every Work task must pin repo/branch/PR/exact starting head and include a mandatory drift gate. Main chat must not write the same branch concurrently during a Work implementation run. Work results are never auto-accepted; main chat independently checks head, commits, diff, tests, CI, safety and skipped external gates.

### Unattended / overnight intent

The user wants long stretches of useful progress without having to watch the phone. Main-chat turns cannot be assumed to execute indefinitely in the background. When a coherent multi-hour unattended block is available, prefer packaging it as a bounded Work assignment rather than pretending the normal chat will continue after the turn/platform limit.

---

## 11. Work package history / lessons

The large Work tranche covering Steps 2195–2199 was a successful example:
- exact head pinned;
- root cause repaired;
- multiple coherent forward steps completed;
- full tests/Ruff/offline gates/remote CI run;
- stopped before first actual broker-side-effect boundary;
- main chat independently verified the result.

This is the preferred pattern for future large packages.

Do not use Work merely because main chat feels slow; first define a coherent scope and leverage case.

---

## 12. Neon / database truth

Connected Neon project: `dax-research-lab`.

Production migration 0008/0009 was explicitly approved, applied and verified in Step 2189.

At Step 2189 direct evidence showed:
- 9/9 migrations;
- required Candidate telemetry table/view;
- safety constraints `execution_capability='NONE'` / `order_execution_enabled=false`;
- frozen V11.2/dataset/ACTIVE_REFERENCE intact;
- no unintended detail import.

A separate `step-2189-db-drills` branch was used for isolated restore/import conflict tests and may remain visible/idle in Neon. This is expected and is not a second production database.

PR CI often skips five DB jobs because they are main/provider-dependent. A skipped PR DB job is not failure, but it also is not fresh DB evidence. Direct connected-Neon evidence remains separate.

---

## 13. GitHub workflow explanation / current governance

The repository exposes separate GitHub Actions workflows. At handoff the important required workflows are:

- `dax-bot-1x-ci` — product/bot CI;
- `research-lab-ci` — research/lab/full-regression CI.

`reference-payload-export` is a separate specialized export workflow and is not a third required CI gate for every PR step.

Workflow run numbers are execution counts, not error counts.

`main` remains protected by repository governance requiring PR + strict required CI. Governance does not itself authorize merge or broker execution.

---

## 14. Frozen scientific/reference truth

V11.2 remains immutable reference evidence and must not be retroactively changed or promoted as proof of NextGen profitability.

Key frozen reference facts remain:
- 2014–2019;
- 1,673 valid Berlin-session days;
- 172,319 M5 session bars;
- 103 bars/session;
- 144 variants;
- 81 WF windows;
- 856 OOS trades;
- V11.2 remains frozen reference baseline.

No profitability claim is authorized from this engineering progress.

---

## 15. Next-chat immediate action — DO THIS, DO NOT DISCUSS IT FIRST

After fresh head/CI re-pin, continue **Step 2201** from repository evidence.

Immediate sequence:

1. fetch concrete owner files/tests for:
   - broker economics;
   - fixed-cash risk/sizing;
   - loss/exposure admission;
   - loss/exposure persistence/current observation;
   - operator risk-profile/readiness;
   - typed execution protection;
2. produce a compact REUSE-vs-GAP matrix based on actual symbols/tests, not filenames alone;
3. determine whether Step 2201 can close as a read-only evidence-owner sign-off or whether one small technical read-only binding is genuinely missing;
4. if small gap: implement/test/CI in main chat and continue;
5. if no gap: commit Step-2201 sign-off + pointer to 2202 and continue automatically;
6. next likely emphasis is authoritative real-host observation/evidence production and Monday readiness, but do not invent reset/timezone/PnL/risk values;
7. keep first actual DEMO evidence order behind separate explicit authorization.

Do not spend the first new-chat turn recapping this document to the user. **Work from it.**

---

## 16. Mandatory no-loss reminders

- Repository truth over chat memory.
- Intermediate status != stop.
- Fix level-1/2 errors and continue.
- No endless repeat searches; switch method after two failed attempts.
- Main chat standard = MEDIUM reasoning; HIGH selectively.
- Work = large coherent leverage package, not default cadence.
- Public Git learning remains periodic and targeted.
- No automatic strategy promotion.
- No fake external evidence.
- No first DEMO order without separate explicit user authorization.
- PAPER/LIVE remain unauthorized.
- PR #109 remains open/unmerged.
- Acceptance remains stale until deliberately reconciled.
- Step 2250 = mandatory Masterstand checkpoint.
- Step 2500 = mandatory full audit + Architecture & Learning Review.

End of latest handoff.