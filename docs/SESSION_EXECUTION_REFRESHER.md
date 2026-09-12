# SESSION EXECUTION REFRESHER — READ BEFORE CONTINUING WORK

Status: BINDING
Updated: 2026-09-12

Purpose: prevent avoidable project stops, step-number drift, pointer lag and chat-handoff loss during long DAX-BOT engineering sessions.

Canonical workflow-integrity owner: `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`.

## Canonical chat commands

### `Weiter mit dem DAXBot`

Treat this phrase as the canonical repository-backed resume codeword. Do not ask the user to paste the previous Masterstand when the repository is available. Execute the recovery sequence from `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`, reconstruct current truth from the repository and continue the next safe whole-number work unit automatically only after the workflow-integrity gate is consistent.

### `Erstelle einen Masterstand`

Treat this phrase as an immediate handover command. Refresh `docs/MASTERSTAND.md` and the related navigation/pointer truth according to `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`.

### Scheduled checkpoints

A Masterstand refresh is mandatory every 250 official whole-number work steps. The next scheduled checkpoint is **2250**. Every second checkpoint is also the existing 500-step full audit, so **2500** includes both Masterstand refresh and full audit.

## Mandatory preflight before substantive work

Before the first concrete tool/code action after any `weiter`, `fortsetzen`, `Weiter mit dem DAXBot`, resume, context reconstruction, reconnect, tool disruption or new work turn, verify these ten items:

1. **Repo/head truth first.** Re-pin repository, branch, exact head SHA, PR and relevant CI. Do not work from a stale remembered head.
2. **Canonical step pointer.** Read `docs/CURRENT_WORK_STEP.md`; official numbering comes from that file, never from chat memory or raw commit count.
3. **Workflow-integrity gate.** Read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md` and ensure the previous step satisfies the Step-Close-Gate before a new independent step begins.
4. **Integer step only.** Official visible work steps are whole numbers only. Never use `.1`, letters, nested official numbering or pseudo-substeps.
5. **Pointer-before-next-step.** The current pointer must name the active new integer before the first substantive action of that independent work unit.
6. **Intermediate update != stop.** A Zwischenstand, successful test, warning, recovered context, CI state, found file or partial result is visibility only. Continue concrete work immediately afterward when safe work remains.
7. **Visible report != tool log.** Tool/interface activity does not count as the required normal-text progress report. During long work, state what was checked, the result and the actual next action.
8. **Lane blocker != project blocker.** If one dependency needs external hardware, Windows/MT5, user action, later market time or another unavailable dependency, mark only that lane `WAITING_EXTERNAL`/`BLOCKED`; continue independent safe work under the next unused integer when permitted by the Step-Close-Gate.
9. **Monotonic carry-forward.** Never visibly resume an older step number after a higher one has started. Preserve provenance and carry unfinished scope into the next unused integer.
10. **Checkpoint discipline.** At every multiple of 250, refresh the Masterstand before moving beyond it; every multiple of 500 also performs the full architecture/LEAN audit.

## User-intervention guard

If the user explicitly stops, audits, reviews or corrects the workflow:

1. stop further substantive work on the active technical step;
2. inspect its real repo/CI/evidence state;
3. mark it `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL` or `BLOCKED` truthfully;
4. synchronize `CURRENT_WORK_STEP.md`;
5. only then start the governance/review work under the next unused integer;
6. resume unfinished technical scope later under another new integer, never by rolling the visible step number backward.

## End-of-turn guard

Immediately before producing a final/status-only response during an active engineering sequence, ask internally:

`Is there a real stop condition, explicit user stop/review, or no executable safe work left in this turn?`

- **NO** -> do not finalize; execute the next concrete work item.
- **YES** -> state the exact stop/interruption condition.

A final/turn-ending response ends the active work turn. Never claim or imply that repository work keeps running afterward unless a real scheduled automation/background mechanism was actually created. If app/network/platform suspension ends the turn, re-pin repo/head/CI/pointer on the next turn before continuing.

The user being away from the foreground, a temporary disconnect, context compaction, CI still running, a tool miss, a completed intermediate check, or one externally blocked dependency lane are not by themselves valid global stop conditions.

## Navigation

Canonical chat-handoff protocol: `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`.
Workflow integrity gate: `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`.
Current whole-number pointer: `docs/CURRENT_WORK_STEP.md`.
Authoritative continuity detail: `docs/WORK_CONTINUITY_PROTOCOL.md`.
Canonical project handover: `docs/MASTERSTAND.md`.

This refresher is deliberately short and must be read first on resume before the longer protocol/navigation files when work continuity is relevant.
