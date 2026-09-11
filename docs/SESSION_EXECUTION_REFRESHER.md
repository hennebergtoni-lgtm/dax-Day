# SESSION EXECUTION REFRESHER — READ BEFORE CONTINUING WORK

Status: BINDING
Updated: 2026-09-11

Purpose: prevent avoidable project stops and step-number drift during long DAX-BOT engineering sessions.

## Mandatory 15-second preflight

Before the first concrete tool/code action after any `weiter`, `fortsetzen`, resume, context reconstruction, reconnect, tool disruption or new work turn, verify these seven items:

1. **Integer step only.** Official visible work steps are whole numbers only: `2039 -> 2040 -> 2041`. Never use `.1`, letters, nested official numbering or pseudo-substeps.
2. **Intermediate update != stop.** A Zwischenstand, successful test, warning, recovered context, CI state, found file or partial result is visibility only. Continue concrete work immediately afterward.
3. **Stop reason test.** Before ending a work sequence, explicitly check whether one of the five stop reasons in `WORK_CONTINUITY_PROTOCOL.md` is actually true. If none is true, ending is a process defect: continue.
4. **Repo truth first.** Re-pin repo/branch/head/CI after disruption. Do not ask the user to repeat known information.
5. **Canonical step pointer.** Read `docs/CURRENT_WORK_STEP.md` after repo/head pinning and use its current whole-number pointer. Reconstruct from commit evidence only if that file is missing/inconsistent; do not infer the step number from chat memory or raw commit count.
6. **Next integer is consumed by the next independent work unit.** Do not hide several independent deliverables inside one step and do not split one tightly coupled implementation/test into decimal substeps.
7. **Lane blocker != project blocker.** If one step needs external hardware, a Windows/MT5 host, a user action, later market time, or another unavailable dependency, mark only that dependency lane `WAITING_EXTERNAL`. Immediately continue with the next independent safe whole-number work units. A global stop is allowed only when no useful independent work remains or another binding stop condition applies.

## End-of-turn guard

Immediately before producing a final/status-only response during an active engineering sequence, ask internally:

`Is there a real global stop condition, and are there truly no independent safe work units left?`

- **NO** -> do not finalize; execute the next concrete work item.
- **YES** -> state the exact stop condition and what evidence makes it global rather than lane-local.

The user being away from the foreground, a temporary disconnect, context compaction, CI still running, a tool miss, a completed intermediate check, or one externally blocked dependency lane are not valid global stop conditions.

## Navigation

Current whole-number pointer: `docs/CURRENT_WORK_STEP.md`.
Authoritative detail: `docs/WORK_CONTINUITY_PROTOCOL.md`.
This refresher is deliberately short and must be read first on resume before the longer protocol/navigation files when work continuity is relevant.
