# DAX-BOT Chat Handoff Protocol V1

Status: BINDING
Updated: 2026-09-13

Purpose: make chat/context handovers deterministic and repository-based so the DAX-BOT project can resume without copy/pasting a large masterstand into every new chat, including after platform conversation-length saturation.

The binding step-closure and workflow-integrity rules are defined in `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`. If older wording conflicts with that gate on step closure, pointer synchronization, interrupted-lane numbering or claims about ongoing work, the workflow-integrity gate controls.

## 1. Resume codeword

The canonical resume phrase is:

`Weiter mit dem DAXBot`

Accepted user-friendly alias:

`Weiter mit DAXbot`

When either phrase is used in a new or existing chat, treat it as an instruction to recover the DAX Daytrading Bot project automatically from repository truth. Do not ask the user to paste the prior masterstand or repeat already-known project facts if the repository is available.

Mandatory recovery sequence:

1. Read `docs/SESSION_EXECUTION_REFRESHER.md`.
2. Pin repository `hennebergtoni-lgtm/dax-Day`, working branch, PR, fresh exact head SHA and current CI state.
3. Read `docs/CURRENT_WORK_STEP.md`; official numbering comes from this file, never from chat-memory inference.
4. Read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`.
5. Read `docs/MASTERSTAND.md`.
6. Read `docs/PROJECT_KNOWLEDGE_INDEX.md`.
7. Read `docs/WORK_CONTINUITY_PROTOCOL.md`; its Work-delegation, model/thinking, credit-budget and out-of-band Work-reconciliation sections are binding.
8. Read the problem/solution registry and only the topic-specific code/docs/tests required for the active step.
9. Reconcile any `WAITING_EXTERNAL`, `INTERRUPTED`, `BLOCKED` lane and any out-of-band ChatGPT Work commits separately from independent safe work.
10. Continue the next concrete whole-number work unit automatically only after the current pointer and Step-Close-Gate are consistent. A recovered status report is not a stop.

Repository truth overrides chat recollection. Exact code, tests, hashes, evidence and fresh runtime telemetry override prose summaries if they disagree.

## 2. Explicit masterstand command

The canonical handover-preparation phrase is:

`Erstelle einen Masterstand`

When used, update `docs/MASTERSTAND.md` to the current repository truth and ensure it contains at least:

- repository/branch/PR and fresh-head guidance;
- current safety/authorization state;
- frozen reference facts that must not be rewritten;
- current DAX-BOT/CAND candidate architecture and evidence maturity;
- completed milestone summary since the prior masterstand;
- unresolved `WAITING_EXTERNAL`, `INTERRUPTED` and `BLOCKED` lanes;
- any out-of-band ChatGPT Work evidence since the prior handoff and its exact classification;
- current official step pointer and exact next work;
- current CI/evidence truth without claiming a newer head green before it is verified;
- current Acceptance/merge freshness rather than assuming CI implies Acceptance;
- required workflow-integrity / no-stop / integer-step / repository-first resume rules;
- current chat-capacity/handoff state when the command is used because the conversation is approaching or has reached a platform length limit.

Also update `docs/PROJECT_KNOWLEDGE_INDEX.md`, `docs/WORK_CONTINUITY_PROTOCOL.md` and `docs/CURRENT_WORK_STEP.md` when their navigation/pointer/Work truth changed materially.

## 3. Scheduled masterstand checkpoints

A masterstand checkpoint is mandatory every 250 official whole-number work steps.

Checkpoint numbers are multiples of 250: `2250`, `2500`, `2750`, ...

Current next scheduled checkpoint: **2250**.

At each checkpoint:

1. refresh `docs/MASTERSTAND.md`;
2. verify `CURRENT_WORK_STEP.md`, workflow-integrity gate, Work protocol and Knowledge Index consistency;
3. record fresh PR/head/CI truth;
4. summarize new durable findings, solved problems and remaining lanes;
5. preserve safety/authorization boundaries;
6. continue work after the checkpoint unless a real global stop exists.

The existing full architecture/LEAN audit remains every 500 steps. Therefore every second 250-step checkpoint (e.g. `2500`, `3000`) includes both the masterstand refresh and the full 500-step audit.

## 4. Chat memory boundary

Conversation memory may help orientation, but it is not sufficient evidence for current project truth. The handoff system is deliberately repository-backed so it still works after chat truncation, a new chat, compaction, incomplete conversational memory or an explicit platform message that the conversation is too long to continue.

Do not promise autonomous work while no model turn is running. A final/turn-ending response ends the active work turn. If the app/network/platform interrupts execution, do not claim that work continued invisibly; resume at the next available turn by re-pinning repo/branch/head/CI and the current pointer first.

### Chat-capacity saturation rule — BINDING

A platform message such as `Dieses Gespräch ist zu lang, um fortzufahren` is a **conversation-capacity interruption**, not evidence that the repository/project is technically blocked.

When saturation is detected while the current chat can still execute actions:

1. stop new substantive technical work;
2. pin fresh repository/head/CI/pointer truth;
3. truthfully close or mark the current technical step `INTERRUPTED` if its evidence is incomplete;
4. start a dedicated continuity/Masterstand work unit under the next unused whole integer;
5. refresh `docs/MASTERSTAND.md`, this protocol, `WORK_CONTINUITY_PROTOCOL.md` when relevant, and any materially changed navigation/pointer truth;
6. preserve unfinished technical scope explicitly for the next unused integer;
7. provide the user the resume codeword and open the new chat.

If the platform hard-stops the old chat before these writes can happen, the **new chat** must perform the same reconciliation first: re-pin repository truth, inspect whether the previously active step actually completed, mark it truthfully, then continue under monotonic whole-number numbering. Never invent completion from chat memory.

Chat saturation is therefore treated like a controlled handoff event. It must not erase goals, architecture decisions, evidence status, Work delegation rules, safety boundaries or working-style agreements.

## 5. Step-number discipline

- official steps are integers only;
- no `.1`, letter suffix or nested official step number;
- a masterstand refresh at a scheduled checkpoint is itself part of that official whole-number work unit;
- `WAITING_EXTERNAL` blocks only its lane and does not prevent later independent whole-number steps;
- after any handoff, continue from repository truth without inventing skipped work;
- **Step-Close-Gate:** a new independent step starts only after the previous step is explicitly `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL` or `BLOCKED`, with the reason/evidence and pointer synchronized;
- **pointer-before-next-step:** `docs/CURRENT_WORK_STEP.md` must name the new active step before its first substantive action;
- visible numbering is monotonic: an older still-open lane is never resumed under its old step number after a higher number has started; preserve its provenance and resume its unfinished scope under the next unused integer;
- out-of-band Work commits are never retroactively relabeled as the unfinished official step; reconcile them under the next unused continuity step and carry unfinished technical scope prospectively;
- the old wording `Fortsetzung Schritt N` must not be used as the current official number after later steps have begun;
- intermediate reports inside the active step are labeled simply `Zwischenstand` and must not introduce a different official step number.

## 6. Visible work / progress-reporting contract

For ongoing multi-step project work, the required visible cadence is binding:

**Step N -> short activity -> visible intermediate report in normal assistant text -> status marker (`✅`, `⚠️`, or `❌`) -> actual next tool/action.**

Tool activity/status lines shown by the interface do **not** count as the visible intermediate report. Do not run a long chain of meaningful tool calls without a normal-text progress report between meaningful checks. The user must be able to see what was checked, the current result, and what will actually happen next.

**Compact-reporting rule:** intermediate reports should normally be only **1–2 short sentences** containing the result/status and the immediate next action. Do not repeat the full project context, safety baseline, prior findings, long rationale or already-known repository facts unless they materially changed or are required to explain an error. Prefer concise `✅/⚠️/❌` progress markers so the chat remains usable over long project runs.

A visible intermediate report is a visibility point, not a stop. After reporting, continue immediately when the next safe action is known. Stop only for a real blocker, required user action/decision, explicit user intervention, milestone stop, safety-relevant issue or a platform-enforced conversation-capacity handoff.

**No-prompt continuation enforcement:** if the next safe action can be executed with the currently available repository, tools, files, or read-only diagnostics, the assistant must execute it in the same running turn after the intermediate report. The intermediate report must not terminate the work turn merely to wait for another user message, acknowledgement, or `Weiter`. A user reply is required only when the next action genuinely needs user-side execution, missing information, explicit authorization/decision, unavailable access, safety gate, or the user explicitly stopped/reviewed the sequence. If one method stalls or repeats without new evidence, switch to another safe method instead of waiting for the user to restart progress.

**Active-turn final-response prohibition:** while executable safe work remains in the current turn, the assistant must not send a final/turn-ending response that merely says work will continue. Progress updates must be emitted as non-final intermediate text, followed immediately by the next tool/action in the same turn. A final response is permitted only when the current work unit is complete, a genuine blocker has been reached, user-side action/decision is actually required, the user explicitly instructed a stop/review, or a controlled chat-capacity handoff has been completed. Never write phrases such as `läuft automatisch weiter` in a final response unless a real scheduled automation/background mechanism has actually been created.

### Repeated premature-stop incident — 2026-09-13

During the long engineering chat, the assistant repeatedly produced final/status responses even though the next safe repository action was already known. This was **workflow failure, not technical project blocking**. The durable correction is:

- progress text never substitutes for the next action;
- a successful sub-check, CI wait/poll point, found file or partial audit is not a valid turn-ending condition;
- before finalizing, apply the end-of-turn guard from `SESSION_EXECUTION_REFRESHER.md`;
- if the platform itself is approaching/hitting capacity, transition deliberately through the chat-capacity saturation rule rather than silently stopping mid-step.

## 7. User intervention / governance correction

An explicit user instruction to stop, audit, review, create a Masterstand or correct the workflow is a valid sequence interruption.

Before starting the governance/review work:
1. stop substantive work on the active technical step;
2. inspect its actual repo/CI/evidence state;
3. mark it truthfully `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL` or `BLOCKED`;
4. synchronize `CURRENT_WORK_STEP.md`;
5. start the governance/review under the next unused integer;
6. resume unfinished technical scope later only under another new integer.

## 8. ChatGPT Work handoff reconciliation

`docs/WORK_CONTINUITY_PROTOCOL.md` is the canonical Work operating contract. It defines main-chat versus Work ownership, Work-order headers, model/thinking selection, credit classes, branch drift, Acceptance/merge ownership and external-evidence rules.

On resume, if Work commits exist beyond the last numbered project evidence:
1. pin the exact Work commit chain and CI;
2. inspect what actually changed;
3. classify skipped external gates separately;
4. do not auto-accept Work prose or relabel out-of-band commits as an unrelated active numbered step;
5. reconcile them through the next unused whole-number continuity step;
6. carry interrupted technical work prospectively;
7. keep Acceptance and merge ownership in the main chat unless explicitly delegated.

## 9. Safety boundary

This protocol changes only continuity/navigation and visible reporting. It never authorizes PAPER or LIVE trading, never changes VERIFIED evidence, never changes strategy semantics, and never bypasses explicit execution-authorization gates.
