# DAX-BOT Chat Handoff Protocol V1

Status: BINDING
Updated: 2026-09-12

Purpose: make chat/context handovers deterministic and repository-based so the DAX-BOT project can resume without copy/pasting a large masterstand into every new chat.

The binding step-closure and workflow-integrity rules are defined in `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`. If older wording conflicts with that gate on step closure, pointer synchronization, interrupted-lane numbering or claims about ongoing work, the workflow-integrity gate controls.

## 1. Resume codeword

The canonical resume phrase is:

`Weiter mit dem DAXBot`

When this phrase is used in a new or existing chat, treat it as an instruction to recover and continue the DAX Daytrading Bot project automatically. Do not ask the user to paste the prior masterstand or repeat already-known project facts if the repository is available.

Mandatory recovery sequence:

1. Read `docs/SESSION_EXECUTION_REFRESHER.md`.
2. Pin repository `hennebergtoni-lgtm/dax-Day`, working branch, PR, fresh exact head SHA and current CI state.
3. Read `docs/CURRENT_WORK_STEP.md`; official numbering comes from this file, never from chat-memory inference.
4. Read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`.
5. Read `docs/MASTERSTAND.md`.
6. Read `docs/PROJECT_KNOWLEDGE_INDEX.md`.
7. Read the problem/solution registry and only the topic-specific code/docs/tests required for the active step.
8. Reconcile any `WAITING_EXTERNAL`, `INTERRUPTED` or `BLOCKED` lane separately from independent safe work.
9. Continue the next concrete whole-number work unit automatically only after the current pointer and Step-Close-Gate are consistent. A recovered status report is not a stop.

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
- current official step pointer and exact next work;
- current CI/evidence truth without claiming a newer head green before it is verified;
- required workflow-integrity / no-stop / integer-step / repository-first resume rules.

Also update `docs/PROJECT_KNOWLEDGE_INDEX.md` and `docs/CURRENT_WORK_STEP.md` if their navigation/pointer truth changed materially.

## 3. Scheduled masterstand checkpoints

A masterstand checkpoint is mandatory every 250 official whole-number work steps.

Checkpoint numbers are multiples of 250: `2250`, `2500`, `2750`, ...

Current next scheduled checkpoint: **2250**.

At each checkpoint:

1. refresh `docs/MASTERSTAND.md`;
2. verify `CURRENT_WORK_STEP.md`, workflow-integrity gate and Knowledge Index consistency;
3. record fresh PR/head/CI truth;
4. summarize new durable findings, solved problems and remaining lanes;
5. preserve safety/authorization boundaries;
6. continue work after the checkpoint unless a real global stop exists.

The existing full architecture/LEAN audit remains every 500 steps. Therefore every second 250-step checkpoint (e.g. `2500`, `3000`) includes both the masterstand refresh and the full 500-step audit.

## 4. Chat memory boundary

Conversation memory may help orientation, but it is not sufficient evidence for current project truth. The handoff system is deliberately repository-backed so it still works after chat truncation, a new chat, compaction or incomplete conversational memory.

Do not promise autonomous work while no model turn is running. A final/turn-ending response ends the active work turn. If the app/network/platform interrupts execution, do not claim that work continued invisibly; resume at the next available turn by re-pinning repo/branch/head/CI and the current pointer first.

## 5. Step-number discipline

- official steps are integers only;
- no `.1`, letter suffix or nested official step number;
- a masterstand refresh at a scheduled checkpoint is itself part of that official whole-number work unit;
- `WAITING_EXTERNAL` blocks only its lane and does not prevent later independent whole-number steps;
- after any handoff, continue from repository truth without inventing skipped work;
- **Step-Close-Gate:** a new independent step starts only after the previous step is explicitly `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL` or `BLOCKED`, with the reason/evidence and pointer synchronized;
- **pointer-before-next-step:** `docs/CURRENT_WORK_STEP.md` must name the new active step before its first substantive action;
- visible numbering is monotonic: an older still-open lane is never resumed under its old step number after a higher number has started; preserve its provenance and resume its unfinished scope under the next unused integer, e.g. `Step 2140 — continuation of the lane originating in Step 2122`;
- the old wording `Fortsetzung Schritt N` must not be used as the current official number after later steps have begun;
- intermediate reports inside the active step are labeled simply `Zwischenstand` and must not introduce a different official step number.

## 6. Visible work / progress-reporting contract

For ongoing multi-step project work, the required visible cadence is binding:

**Step N -> short activity -> visible intermediate report in normal assistant text -> status marker (`✅`, `⚠️`, or `❌`) -> actual next tool/action.**

Tool activity/status lines shown by the interface do **not** count as the visible intermediate report. Do not run a long chain of meaningful tool calls without a normal-text progress report between meaningful checks. The user must be able to see what was checked, the current result, and what will actually happen next.

A visible intermediate report is a visibility point, not a stop. After reporting, continue immediately when the next safe action is known. Stop only for a real blocker, required user action/decision, explicit user intervention, milestone stop, or safety-relevant issue.

**No-prompt continuation enforcement:** if the next safe action can be executed with the currently available repository, tools, files, or read-only diagnostics, the assistant must execute it in the same running turn after the intermediate report. The intermediate report must not terminate the work turn merely to wait for another user message, acknowledgement, or `Weiter`. A user reply is required only when the next action genuinely needs user-side execution, missing information, explicit authorization/decision, unavailable access, safety gate, or the user explicitly stopped/reviewed the sequence. If one method stalls or repeats without new evidence, switch to another safe method instead of waiting for the user to restart progress.

**Active-turn final-response prohibition:** while executable safe work remains in the current turn, the assistant must not send a final/turn-ending response that merely says work will continue. Progress updates must be emitted as non-final intermediate text, followed immediately by the next tool/action in the same turn. A final response is permitted only when the current work unit is complete, a genuine blocker has been reached, user-side action/decision is actually required, or the user explicitly instructed a stop/review. Never write phrases such as `läuft automatisch weiter` in a final response unless a real scheduled automation/background mechanism has actually been created.

## 7. User intervention / governance correction

An explicit user instruction to stop, audit, review or correct the workflow is a valid sequence interruption.

Before starting the governance/review work:
1. stop substantive work on the active technical step;
2. inspect its actual repo/CI/evidence state;
3. mark it truthfully `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL` or `BLOCKED`;
4. synchronize `CURRENT_WORK_STEP.md`;
5. start the governance/review under the next unused integer;
6. resume unfinished technical scope later only under a later unused integer.

## 8. Safety boundary

This protocol changes only continuity/navigation and visible reporting. It never authorizes PAPER or LIVE trading, never changes VERIFIED evidence, never changes strategy semantics, and never bypasses explicit execution-authorization gates.
