# DAX-BOT Chat Handoff Protocol V1

Status: BINDING
Updated: 2026-09-12

Purpose: make chat/context handovers deterministic and repository-based so the DAX-BOT project can resume without copy/pasting a large masterstand into every new chat.

## 1. Resume codeword

The canonical resume phrase is:

`Weiter mit dem DAXBot`

When this phrase is used in a new or existing chat, treat it as an instruction to recover and continue the DAX Daytrading Bot project automatically. Do not ask the user to paste the prior masterstand or repeat already-known project facts if the repository is available.

Mandatory recovery sequence:

1. Read `docs/SESSION_EXECUTION_REFRESHER.md`.
2. Pin repository `hennebergtoni-lgtm/dax-Day`, working branch, PR, fresh exact head SHA and current CI state.
3. Read `docs/CURRENT_WORK_STEP.md`; official numbering comes from this file, never from chat-memory inference.
4. Read `docs/MASTERSTAND.md`.
5. Read `docs/PROJECT_KNOWLEDGE_INDEX.md`.
6. Read the problem/solution registry and only the topic-specific code/docs/tests required for the active step.
7. Reconcile any `WAITING_EXTERNAL` lane separately from independent safe work.
8. Continue the next concrete whole-number work unit automatically. A recovered status report is not a stop.

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
- unresolved `WAITING_EXTERNAL` lanes;
- current official step pointer and exact next work;
- current CI/evidence truth without claiming a newer head green before it is verified;
- required no-stop / integer-step / repository-first resume rules.

Also update `docs/PROJECT_KNOWLEDGE_INDEX.md` and `docs/CURRENT_WORK_STEP.md` if their navigation/pointer truth changed materially.

## 3. Scheduled masterstand checkpoints

A masterstand checkpoint is mandatory every 250 official whole-number work steps.

Checkpoint numbers are multiples of 250: `2250`, `2500`, `2750`, ...

Current next scheduled checkpoint: **2250**.

At each checkpoint:

1. refresh `docs/MASTERSTAND.md`;
2. verify `CURRENT_WORK_STEP.md` and Knowledge Index consistency;
3. record fresh PR/head/CI truth;
4. summarize new durable findings, solved problems and remaining lanes;
5. preserve safety/authorization boundaries;
6. continue work after the checkpoint unless a real global stop exists.

The existing full architecture/LEAN audit remains every 500 steps. Therefore every second 250-step checkpoint (e.g. `2500`, `3000`) includes both the masterstand refresh and the full 500-step audit.

## 4. Chat memory boundary

Conversation memory may help orientation, but it is not sufficient evidence for current project truth. The handoff system is deliberately repository-backed so it still works after chat truncation, a new chat, compaction or incomplete conversational memory.

Do not promise autonomous work while no model turn is running. If the app/network/platform interrupts execution, resume at the next available turn by running the recovery sequence automatically; the interruption itself is not a project stop.

## 5. Step-number discipline

- official steps are integers only;
- no `.1`, letter suffix or nested official step number;
- a masterstand refresh at a scheduled checkpoint is itself part of that official whole-number work unit;
- `WAITING_EXTERNAL` blocks only its lane and does not prevent later independent whole-number steps;
- after any handoff, continue from repository truth without inventing skipped work;
- if an older still-open step is resumed after a later independent/governance step has already been completed, label it explicitly as **`Fortsetzung Schritt N`** so the chronology is not mistaken for a numbering rollback;
- intermediate reports inside an active/resumed step are labeled simply **`Zwischenstand`** and must not introduce or repeat a different official step number.

## 6. Visible work / progress-reporting contract

For ongoing multi-step project work, the required visible cadence is binding:

**Step N -> short activity -> visible intermediate report in normal assistant text -> status marker (`✅`, `⚠️`, or `❌`) -> immediate next step.**

Tool activity/status lines shown by the interface do **not** count as the visible intermediate report. Do not run a long chain of tool calls without a normal-text progress report between meaningful checks. The user must be able to see what was checked, the current result, and what will happen next.

A visible intermediate report is a visibility point, not a stop. After reporting, continue immediately when the next safe action is known. Stop only for a real blocker, required user action/decision, milestone stop, or safety-relevant issue.

**No-prompt continuation enforcement:** if the next safe action can be executed with the currently available repository, tools, files, or read-only diagnostics, the assistant must execute it in the same running turn after the intermediate report. The intermediate report must not terminate the work turn merely to wait for another user message, acknowledgement, or `Weiter`. A user reply is required only when the next action genuinely needs user-side execution, missing information, explicit authorization/decision, unavailable access, or a safety gate. If one method stalls or repeats without new evidence, switch to another safe method instead of waiting for the user to restart progress.

**Active-turn final-response prohibition:** while executable safe work remains in the current turn, the assistant must not send a final/turn-ending response that merely says work will continue. Progress updates must be emitted as non-final intermediate text, followed immediately by the next tool/action in the same turn. A final response is permitted only when the current work unit is complete, a genuine blocker has been reached, or user-side action/decision is actually required. Never write phrases such as `läuft automatisch weiter` in a final response unless no further tool/action can be executed in the current turn.

## 7. Safety boundary

This protocol changes only continuity/navigation and visible reporting. It never authorizes PAPER or LIVE trading, never changes VERIFIED evidence, never changes strategy semantics, and never bypasses explicit execution-authorization gates.
