# SESSION EXECUTION REFRESHER — READ BEFORE CONTINUING WORK

Status: BINDING
Updated: 2026-09-12

Purpose: prevent avoidable project stops, step-number drift and chat-handoff loss during long DAX-BOT engineering sessions.

## Canonical chat commands

### `Weiter mit dem DAXBot`

Treat this phrase as the canonical repository-backed resume codeword. Do not ask the user to paste the previous Masterstand when the repository is available. Execute the recovery sequence from `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`, reconstruct current truth from the repository and continue the next safe whole-number work unit automatically.

### `Erstelle einen Masterstand`

Treat this phrase as an immediate handover command. Refresh `docs/MASTERSTAND.md` and the related navigation/pointer truth according to `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`.

### Scheduled checkpoints

A Masterstand refresh is mandatory every 250 official whole-number steps. The next scheduled checkpoint is **2250**. Every second checkpoint is also the existing 500-step full audit, so **2500** includes both Masterstand refresh and full audit.

## Mandatory 15-second preflight

Before the first concrete tool/code action after any `weiter`, `fortsetzen`, `Weiter mit dem DAXBot`, resume, context reconstruction, reconnect, tool disruption or new work turn, verify these eight items:

1. **Integer step only.** Official visible work steps are whole numbers only. Never use `.1`, letters, nested official numbering or pseudo-substeps.
2. **Intermediate update != stop.** A Zwischenstand, successful test, warning, recovered context, CI state, found file or partial result is visibility only. Continue concrete work immediately afterward.
3. **Stop reason test.** Before ending a work sequence, explicitly check whether one of the five stop reasons in `WORK_CONTINUITY_PROTOCOL.md` is actually true. If none is true, ending is a process defect: continue.
4. **Repo truth first.** Re-pin repo/branch/head/CI after disruption. Do not ask the user to repeat known information.
5. **Canonical step pointer.** Read `docs/CURRENT_WORK_STEP.md` after repo/head pinning and use its current whole-number pointer. Reconstruct from commit evidence only if that file is missing/inconsistent; do not infer the step number from chat memory or raw commit count.
6. **Next integer is consumed by the next independent work unit.** Do not hide several independent deliverables inside one step and do not split one tightly coupled implementation/test into decimal substeps.
7. **Lane blocker != project blocker.** If one step needs external hardware, a Windows/MT5 host, a user action, later market time, or another unavailable dependency, mark only that dependency lane `WAITING_EXTERNAL`. Immediately continue with the next independent safe whole-number work units. A global stop is allowed only when no useful independent work remains or another binding stop condition applies.
8. **Handoff checkpoint discipline.** When an official step reaches a 250-step checkpoint, refresh the Masterstand before moving beyond that checkpoint. A user-requested Masterstand refresh can happen earlier and does not replace the next scheduled checkpoint unless it occurs exactly at that checkpoint.

## End-of-turn guard

Immediately before producing a final/status-only response during an active engineering sequence, ask internally:

`Is there a real global stop condition, and are there truly no independent safe work units left?`

- **NO** -> do not finalize; execute the next concrete work item.
- **YES** -> state the exact stop condition and what evidence makes it global rather than lane-local.

The user being away from the foreground, a temporary disconnect, context compaction, CI still running, a tool miss, a completed intermediate check, or one externally blocked dependency lane are not valid global stop conditions.

## Navigation

Canonical chat-handoff protocol: `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`.
Current whole-number pointer: `docs/CURRENT_WORK_STEP.md`.
Authoritative continuity detail: `docs/WORK_CONTINUITY_PROTOCOL.md`.
Canonical project handover: `docs/MASTERSTAND.md`.
This refresher is deliberately short and must be read first on resume before the longer protocol/navigation files when work continuity is relevant.
