# DAX-BOT Chat Handoff Protocol V1

Status: **BINDING**  
Updated: **2026-09-14 — Step 2231 supplied Windows closeout / Step 2232 SHADOW E2E continuity**

Purpose: make chat/context handovers deterministic and repository-backed so the DAX-BOT project resumes without asking the user to reconstruct long chats, including after conversation-length saturation. Repository truth and source Work artifacts are preferred over chat memory.

The binding step-closure/workflow-integrity rules remain defined in `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`. If this protocol conflicts with that gate on official step closure, pointer synchronization, interrupted-lane numbering, or claims about ongoing work, the workflow-integrity gate controls.

---

## 1. Resume codewords — BINDING

Canonical phrase:

`Weiter mit dem DAXBot`

Accepted aliases include:

`Weiter mit DAX Bot`

`Weiter mit DAXbot`

`Weiter DAX Bot`

When one of these phrases is used in a new or existing chat, treat it as an instruction to recover the DAX Daytrading Bot automatically. Do not ask the user to paste the prior masterstand, repeat known project facts, or manually re-upload Work artifacts when repository/File Library access is available.

---

## 2. Mandatory recovery sequence — BINDING

Before substantive work or any repository write:

1. read `docs/SESSION_EXECUTION_REFRESHER.md` as needed for active-turn rules;
2. pin repository `hennebergtoni-lgtm/dax-Day`, PR #109, working branch, fresh exact head SHA, base/main SHA, PR state and current required CI;
3. read `docs/CURRENT_WORK_STEP.md`; official whole-number numbering comes from this file, never chat inference;
4. read **`docs/MASTERSTAND_LATEST.md`**; it is the canonical latest handover overlay;
5. read `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md`;
6. read `docs/WORK_CONTINUITY_PROTOCOL.md` for Work delegation/model/thinking/credit-budget/out-of-band reconciliation rules;
7. read `docs/PROJECT_KNOWLEDGE_INDEX.md` and older `docs/MASTERSTAND.md` only when historical context is needed;
8. if ChatGPT File Library is available, search and load the Work rescue anchors in section 3 when their details are relevant;
9. reconcile branch drift, out-of-band Work results, WAITING_EXTERNAL/USER_AUTH/BLOCKED/INTERRUPTED lanes and CI before writing;
10. inspect only the active-step owners/code/tests/evidence plus directly relevant predecessor evidence;
11. continue the next safe action automatically after recovery; a recovered status report is not a stop.

Truth precedence:

1. fresh code/tests/machine/runtime/broker evidence;
2. `docs/CURRENT_WORK_STEP.md`;
3. binding safety/authorization/governance contracts;
4. `docs/MASTERSTAND_LATEST.md`;
5. original Work/File Library source artifacts;
6. historical repository docs;
7. chat memory.

If File Library is unavailable, continue from repository truth and explicitly state that source Work artifacts could not be reopened. Never invent their missing detail.

---

## 3. Work/File-Library rescue anchors — MUST SEARCH WHEN AVAILABLE

The following exact artifacts contain the original high-value Work results and must be treated as recovery sources, not disposable chat attachments:

1. `DAX_PRE_DEMO_DRIFT_REVIEW_2026-09-13.md`
2. `DAX_PRE_DEMO_HARDENING_2_FINAL_2026-09-13.md`
3. `DAX_RESEARCH_FACTORY_3_FINAL.md`
4. `DAX_POST_DEMO_NEXT_WORK.md`

Recovery rule:

- search File Library by exact filename first;
- read the relevant source file before relying on detailed Work claims;
- do not ask the user to upload it again unless File Library search genuinely cannot locate it;
- repository truth overrides Work prose where they disagree;
- Work summaries do not create broker evidence or authorization.

`DAX_RESEARCH_FACTORY_3_FINAL.md` is the canonical original source for the read-only Research Factory 3.0 output, including its 66 source entries, 40 falsifiable hypotheses, 100 deduplicated failure scenarios (not 100 independently observed incidents), 24 architecture/operations learnings, source-quality matrix and M01–M12 roadmap.

`DAX_POST_DEMO_NEXT_WORK.md` is **PLANNED / NOT EXECUTED** and must not be started merely because it exists.

---

## 4. Current milestone recovery — BINDING

Current IG continuation: first load `docs/IG_DEMO_M5_TIMESTAMP_HANDOFF.md`, pin the fresh PR head/main/required CI and `CURRENT_WORK_STEP.md`. Step 2231 is COMPLETED / VERIFIED AS SUPPLIED for the corrected real Windows IG feed slice, with original JSON/time/hash values not supplied to Work; see `STEP_2231_REAL_HOST_CLOSEOUT.md`. Protection/reconciliation UNKNOWN, broader M01 incomplete. Step 2232 is IMPLEMENTED_LOCAL / real Windows SHADOW E2E WAITING_EXTERNAL. Next action is the single IG/CAND-001 invocation and bound operator read in `STEP_2232_IG_REAL_HOST_SHADOW_E2E.md`; no blind MT5 supervisor startup or fabricated MT5 bundle. Step 2206 / USER_AUTH and MT5 lane 2122 stay independent. Next 2233 only after real 2232 source review; no order authorization is implied.

As of the 2026-09-14 continuity update, the latest masterstand records the durable roadmap:

- M01 Real-host evidence
- M02 First bounded DEMO evidence — separately authorized only
- M03 Broker lifecycle truth
- M04 Expected vs Observed
- M05 TCA / latency / cost attribution
- M06 Data / clock parity
- M07 Continuous-DEMO safety / release operations
- M08 Tail / risk survival
- M09 Strategy robustness
- M10 Parameter plateau / multiple testing
- M11 New filters / research efficiency
- M12 Capital scaling / PRE-LIVE

This roadmap does not replace official whole-number governance. On recovery, the active official pointer remains authoritative. At the Research Factory anchor the active pointer was Step 2231, WAITING_EXTERNAL / USER_AUTH / NO BROKER SIDE EFFECT. Re-pin rather than assume that is still current.

---

## 5. Safety boundary — BINDING

This continuity protocol never grants execution.

Unless fresh authorized evidence says otherwise:

- SHADOW only is authorized under no-order contracts;
- first actual bounded DEMO evidence order requires separate explicit authorization;
- continuous DEMO/PAPER is not authorized;
- LIVE is not authorized;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no `mt5.order_send`;
- no cancel/modify;
- no automatic consumed-slot release;
- no blind retry/resubmit after ambiguous transport/restart;
- Linux/fixture/SHADOW/synthetic evidence never becomes broker truth by inference.

Do not weaken safety to satisfy a date or restore progress after a chat switch.

---

## 6. Durable Research Factory 3.0 rules to recover

A new chat should not rediscover these from scratch:

- broker connection != broker truth;
- negative evidence != proof of no execution/flatness;
- `tick_size != digits`;
- native order-price semantics != position average-price semantics;
- correct MT5 executable/data path/build/runtime owner is part of host identity;
- broker/UTC/session/DST/time semantics require real evidence;
- `order_check()` success is preflight, not execution guarantee;
- `order_calc_margin()` is not account exposure;
- quote session != trade session;
- deterministic rejects must not become blind retry;
- partial fill requires reconciliation;
- requote/price change requires revalidation;
- timeout/transport ambiguity -> UNKNOWN/QUERY_REQUIRED;
- PTC is independent from strategy risk;
- emergency/kill authority is separate from strategy and from the current read-only console;
- same-terminal MT5 history is not independent drop-copy;
- Expected-vs-Observed and TCA precede strong interpretation of forward/live drift;
- trade-R drawdown != real account-equity drawdown;
- dependent/block/regime/cluster simulation extends existing IID research;
- parameter plateaus/neighbourhood stability matter more than one best parameter;
- rollback != state reset;
- more architecture without added broker/risk/profit evidence should be rejected.

Research decision order remains:

**REGIME -> STRUCTURE -> ENTRY**

V11.2 remains frozen; CAND-001 is a product candidate, not a profitability proof.

---

## 7. Explicit masterstand command

Canonical phrase:

`Erstelle einen Masterstand`

When used, refresh `docs/MASTERSTAND_LATEST.md` to current repository truth and update other continuity/navigation files when their truth changed materially. Do not wait for the scheduled checkpoint if chat saturation, a major Work tranche, a major Research handoff, or a material execution/governance transition creates new durable knowledge.

The masterstand must preserve at least:

- repository/branch/PR and fresh-head guidance;
- current official pointer;
- current safety/authorization state;
- frozen reference facts;
- current CAND/product evidence maturity;
- important completed milestones since the prior handoff;
- unresolved external/auth/blocker lanes;
- Work/File-Library rescue anchors;
- current M01–M12 or successor roadmap;
- current CI/evidence truth without claiming a newer head green before verified;
- exact next safe action;
- chat/workflow/no-stop/integer-step rules.

---

## 8. Scheduled masterstand checkpoints

A masterstand checkpoint remains mandatory every 250 official whole-number work steps: 2250, 2500, 2750, ...

At each checkpoint:

1. refresh `docs/MASTERSTAND_LATEST.md`;
2. verify pointer/workflow/Work-protocol/Knowledge-Index consistency;
3. record fresh PR/head/CI truth;
4. summarize new durable findings, solved problems and remaining lanes;
5. preserve safety/authorization boundaries;
6. continue after the checkpoint unless a real global stop exists.

Every 500 steps, perform the full Architecture & Learning Review as already governed.

---

## 9. Chat-capacity saturation rule — BINDING

A platform message that the conversation is too long is a continuity interruption, not a DAX-BOT technical failure.

If saturation is approaching while actions still work:

1. stop starting new high-risk substantive work;
2. pin fresh repo/head/CI/pointer;
3. truthfully classify incomplete technical work;
4. refresh `docs/MASTERSTAND_LATEST.md` and continuity navigation if material knowledge changed;
5. ensure Work rescue anchors and exact next action are named;
6. tell the user to open a new chat and use `Weiter mit DAX Bot`.

If the old chat hard-stops first, the new chat performs the mandatory recovery sequence in section 2. Never infer completion from chat memory.

---

## 10. Whole-number / step discipline

- official steps are integers only;
- no decimal or letter suffixes;
- **Step-Close-Gate:** before a new independent whole-number step starts, the previous active step must be explicitly classified `COMPLETED`, `INTERRUPTED`, `WAITING_EXTERNAL`, or `BLOCKED`, with reason/evidence and `docs/CURRENT_WORK_STEP.md` synchronized;
- **Pointer-before-next-step:** the canonical pointer must be synchronized before any new independent official step begins;
- **visible numbering is monotonic**: once an official step number has been visibly used, later continuation must never reuse an older number as if it were current;
- if an interrupted lane later resumes, **resume its unfinished scope under the next unused integer** rather than reviving its old visible number;
- **the old wording `Fortsetzung Schritt N` must not be used** for a resumed interrupted lane;
- `WAITING_EXTERNAL` blocks only its lane unless it is the actual critical path;
- new independent steps require the previous active step to be truthfully classified and pointer synchronized;
- out-of-band Work commits are not retroactively relabeled as an unrelated unfinished step;
- chat audit blocks inside an active step are not new official step numbers;
- a documentation continuity refresh must not fake technical step completion.

---

## 11. Visible work / no-premature-stop contract

Preferred cadence:

`Schritt N -> Tätigkeit -> kurzer Zwischenstand -> ✅ / ⚠️ / ❌ -> tatsächliche nächste Aktion`

A status update is a visibility point, not a stop. If the next safe action can be executed with available tools/files/read-only diagnostics, execute it in the same active turn. Stop only for a real blocker, required user-side action/authorization, explicit user stop/review, milestone handoff, safety issue, or platform limit.

Do not claim autonomous background work unless an actual automation/background mechanism exists.

---

## 12. ChatGPT Work handoff reconciliation

`docs/WORK_CONTINUITY_PROTOCOL.md` remains the canonical Work operating contract.

On resume, if Work commits/results exist beyond the last numbered evidence:

1. pin exact Work commit chain/head/CI;
2. inspect actual changes/results;
3. separate skipped external gates;
4. do not auto-accept Work prose;
5. reconcile out-of-band results without corrupting official numbering;
6. preserve main-chat ownership of independent verification, Acceptance and merge unless explicitly delegated;
7. when source Work artifacts exist in File Library, read them rather than relying on a chat summary.

When Work is actively writing the branch, main chat must not concurrently write that branch.

---

## 13. End-of-recovery rule

A successful new-chat recovery should end its orientation phase with:

- fresh head/main/CI;
- official active step and external/auth lanes;
- whether Work artifacts were successfully rehydrated;
- current safety state;
- exact next action.

Then perform that next safe action if tools/evidence permit. Do not make the user prove that the previous work existed.
