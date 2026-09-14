# DAX-BOT MASTERSTAND LATEST — CHAT / WORK / DEMO HANDOVER

Status: **BINDING LATEST HANDOVER / REPOSITORY TRUTH FIRST**  
Updated: **2026-09-14 — Step 2231 / Research Factory 3.0 continuity handoff**  
Repository: `hennebergtoni-lgtm/dax-Day`  
Working branch: `nextgen-bot-line-v1`  
Pull request: `#109` -> `main`

This file is the canonical latest handover overlay for the DAX Daytrading Bot. It supersedes stale chronological statements in older masterstand prose. It does not supersede exact code/tests/machine evidence, `docs/CURRENT_WORK_STEP.md`, binding safety contracts, or fresh runtime/broker evidence.

Truth precedence:
1. exact current code/tests/machine evidence/current runtime and broker evidence;
2. `docs/CURRENT_WORK_STEP.md` for official whole-number step truth;
3. binding safety/governance/authorization contracts;
4. this `docs/MASTERSTAND_LATEST.md`;
5. current Work artifacts / File Library source reports;
6. older repository masterstands and historical docs;
7. chat memory.

---

## 1. New-chat resume procedure — BINDING

Canonical phrases include:

`Weiter mit dem DAXBot`

`Weiter mit DAX Bot`

`Weiter DAX Bot`

On one of these phrases, a new chat MUST recover the project automatically and MUST NOT ask the user to reconstruct the prior chat when repository/File Library access is available.

Mandatory recovery sequence:
1. fetch PR #109 and pin the **fresh exact head SHA**, base/main SHA, PR state and current required CI before any write;
2. read `docs/CURRENT_WORK_STEP.md`;
3. read this `docs/MASTERSTAND_LATEST.md`;
4. read `docs/DAXBOT_CHAT_HANDOFF_PROTOCOL_V1.md`, `docs/WORK_CONTINUITY_PROTOCOL.md`, `docs/SESSION_EXECUTION_REFRESHER.md` and `docs/DAXBOT_WORKFLOW_INTEGRITY_GATE_V1.md` as needed;
5. if File Library is available, search for and load the four Work rescue anchors listed in section 7 below; do not rely on chat recollection when the source artifacts are available;
6. reconcile any branch drift and any out-of-band Work results against repository truth;
7. inspect only the active-step owners/evidence plus directly relevant predecessor evidence;
8. continue the active safe work automatically; do not stop at a status recap when the next safe action is known.

If File Library is unavailable, continue from repository truth and this masterstand, explicitly noting that the original Work artifacts could not be re-opened. Never invent their missing details.

---

## 2. Repository truth at the Research Factory 3.0 anchor

Immediately before this documentation-only continuity update, main chat independently verified:

- PR #109: **OPEN / UNMERGED / mergeable**;
- branch: `nextgen-bot-line-v1`;
- base/main SHA: `e0784ebfc11bee28475fd9c3385be661af58a738`;
- research/hardening anchor head: `0ee0ecac5751cfecdf9cdc59ded356054f6ad2fb`;
- `dax-bot-1x-ci` #649 / run `34780166146`: **SUCCESS**;
- `research-lab-ci` #1433 / run `34780166138`: **SUCCESS**;
- PR Acceptance text remains deliberately stale and MUST NOT be refreshed merely because CI is green;
- no merge is authorized.

This documentation update creates a newer branch head. Therefore every future chat MUST re-pin the actual head and CI rather than treating `0ee0eca...` as a future drift-gate target. It is a research anchor only.

---

## 3. Official work pointer — BINDING

At the pre-update research anchor, `docs/CURRENT_WORK_STEP.md` states:

- last completed whole-number step: **2230**;
- last interrupted step: **2185**;
- active whole-number step: **2231**;
- active state: **PLANNED — WAITING_EXTERNAL / USER_AUTH / NO BROKER SIDE EFFECT**;
- next after successful completion: **2232**;
- Step 2206 remains **WAITING_EXTERNAL / USER_AUTH**;
- active real-host lane 2122 remains **WAITING_EXTERNAL** for market-open clock/GREEN/Candidate/restart evidence;
- next scheduled Masterstand checkpoint: **2250**;
- integer-only official step numbering remains mandatory.

This masterstand update does **not** advance Step 2231 and does not close Step 2206 or lane 2122.

---

## 4. Execution authorization — BINDING

Current safety state:

- SHADOW: **AUTHORIZED** under existing no-order contracts;
- first actual bounded DEMO evidence order: **NOT AUTHORIZED**; separate explicit authorization required;
- normal/continuous DEMO/PAPER broker execution: **NOT AUTHORIZED**;
- LIVE: **NOT AUTHORIZED**;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no `mt5.order_send` call is authorized;
- no cancel/modify side effect is authorized;
- no automatic consumed-slot release;
- no blind retry/resubmit after restart or ambiguous transport outcome;
- fixture/Linux/SHADOW/synthetic evidence never becomes broker truth by inference.

Do not weaken these gates to meet a calendar target.

---

## 5. Immediate Monday / first bounded DEMO path

Research Factory 3.0 found **no new blanket software blocker** that by itself requires postponing one separately authorized, supervised, bounded DEMO evidence order. Pre-first-DEMO status remains **CONDITIONAL**.

Before such an order can even be considered, real evidence must close the current external chain:

1. exact Windows checkout/runtime build/Python environment and correct MT5 terminal instance, including executable/data path/build/runtime owner where available;
2. exact DEMO account/server/symbol and actual account margin-mode semantics (netting/hedging must not be inferred from the word DEMO);
3. market-open fresh tick and genuinely CLOSED-M5 evidence;
4. broker/UTC/session/DST/time semantics and local receive/source time consistency;
5. full-account orders/positions/history inventory and any manual/foreign/unresolved state;
6. broker symbol/economics contract including tick size, digits, point, volume min/step/max, contract/tick values, trade/execution/filling/order mode, relevant stops/freeze/session semantics;
7. reviewed Fixed-Cash Risk, Loss/Exposure and Protection evidence with source provenance;
8. reconciliation of UNKNOWN/partial/delayed/duplicate/out-of-order outcomes;
9. a separately reviewed active submission capability, if one is to be introduced;
10. separate explicit user authorization for the exact bounded DEMO evidence action.

Important research rules for this gate:
- `tick_size != digits`; digits alone do not prove a valid native order-price grid;
- position average price has different semantics from a native order request price;
- `order_check()` success is a preflight result, **not an execution guarantee**;
- `order_calc_margin()` is an isolated operation estimate and **not total account exposure**;
- quote session and trade session are not interchangeable;
- negative evidence such as empty open orders or a short history window is not terminal proof of no venue side effect;
- timeout/transport ambiguity remains `UNKNOWN -> QUERY_REQUIRED`, never blind resubmit.

---

## 6. Continuous DEMO is a later, stricter gate

One bounded evidence order is not autonomous/continuous DEMO.

Before continuous DEMO, Research Factory 3.0 prioritizes:

- startup/reconciliation barrier before strategy execution;
- independent pre-trade controls (PTC) for price/quantity/notional/message/attempt/duplicate/stale-price constraints with reviewed limits;
- explicit return-code/recovery taxonomy: deterministic reject, partial/reconcile, requote/revalidate, unknown/query-required;
- real broker conformance for account mode, symbol precision, session, lifecycle and reconnect;
- independent/out-of-band submission kill or emergency authority that the strategy cannot self-unlock;
- real loss/exposure/equity evidence; missing PnL is never zero;
- semantic/process watchdog and transition-based alerting;
- immutable release bundle, state-preserving rollback, restart/restore/DR and conformance drills.

Rollback is **not** state reset: reservations, consumed slots, unresolved attempts, broker positions/orders and historical evidence must survive code/config rollback.

Strategy research (new filters, VWAP, M1, similarity, macro, Monte Carlo extensions, parameter plateaus) is not a prerequisite for the first bounded evidence order unless new concrete evidence proves otherwise.

---

## 7. Work rescue anchors — MUST REHYDRATE WHEN AVAILABLE

The following original Work artifacts were found in the user's ChatGPT File Library and are the loss-prevention anchors for the two large Work tranches and Research Factory 3.0:

1. `DAX_PRE_DEMO_DRIFT_REVIEW_2026-09-13.md`
   - independent pre-hardening drift/contract review and reproduced gaps;
2. `DAX_PRE_DEMO_HARDENING_2_FINAL_2026-09-13.md`
   - Steps 2217–2230 hardening result, tests, safety and external gates;
3. `DAX_RESEARCH_FACTORY_3_FINAL.md`
   - full read-only Research Factory 3.0 report: 66 source entries, 40 falsifiable hypotheses, 100 deduplicated failure scenarios (not claimed as 100 independently observed incidents), 24 architecture/operations learnings, source-quality matrix and roadmap;
4. `DAX_POST_DEMO_NEXT_WORK.md`
   - prepared A–J Post-DEMO Work assignment, status **PLANNED / NOT EXECUTED**.

New-chat rule: when File Library access exists, search these exact names and read the relevant source artifact before making claims that depend on its detail. Do not ask the user to upload them again unless File Library search genuinely cannot locate them.

---

## 8. Research Factory 3.0 — durable outcome

Research cutoff: 2026-09-13. Read-only; repository unchanged during the Work research itself.

Durable conclusions:

- no newly demonstrated blanket blocker before the first separately authorized bounded DEMO evidence action;
- real host/account/clock/inventory/economics/policy evidence and user authorization remain mandatory;
- broker connection != broker truth;
- reconnect requires inventory/history/unresolved-outcome/local-checkpoint reconciliation;
- negative evidence != proof of flatness/non-execution;
- MT5 event/report ordering/completeness cannot be assumed;
- PTC is independent from strategy risk;
- emergency authority is separate from normal strategy and from the current read-only console;
- same-terminal MT5 history is not an independent drop-copy channel;
- TCA begins at decision/arrival, not merely at fill-slippage;
- data/clock parity must remain dimensional rather than hidden behind one magic score;
- dependent/block/regime/session/cluster-preserving simulation is an extension to existing IID research, not a new runtime risk owner;
- trade-R drawdown != account-equity drawdown;
- parameter plateaus/neighbourhood stability matter more than a single best parameter;
- complete strategy/release identity should bind dataset, engine, costs, risk, session, adapter and execution assumptions;
- more architecture without added broker/risk/profit evidence should be rejected.

Later main-chat research added these durable broker-conformance notes:

- classify MT5 trade results by recovery semantics rather than a simple success/fail boolean;
- `DONE_PARTIAL` requires reconciliation;
- invalid request/volume/stops/no-money is a deterministic reject and not a blind-retry case;
- requote/price-change requires a freshly revalidated intent, not automatic replay;
- timeout/ambiguous transport remains UNKNOWN/QUERY_REQUIRED;
- retain `retcode_external` when present;
- symbol-spec drift includes trade/execution/filling/order modes, stops/freeze levels, swap/session semantics;
- an incident-forced overnight position can make swap/financing economically relevant even for an intraday strategy.

---

## 9. Binding milestone roadmap M01–M12

This is the next-milestone sequence after the current external host gate. It is a roadmap, not an authorization to skip official whole-number governance.

- **M01 — Real-host evidence**
- **M02 — First bounded DEMO evidence** (only separately authorized)
- **M03 — Broker lifecycle truth**
- **M04 — Expected vs Observed**
- **M05 — TCA / latency / cost attribution**
- **M06 — Data / clock parity**
- **M07 — Continuous-DEMO safety / release operations**
- **M08 — Tail / risk survival**
- **M09 — Strategy robustness**
- **M10 — Parameter plateau / multiple testing**
- **M11 — New filters / research efficiency**
- **M12 — Capital scaling / PRE-LIVE**

M01 is the immediate operational lane. M02 cannot be inferred from M01 and requires separate user authorization plus reviewed capability. M07 must be complete before autonomous continuous DEMO. M12 is much later and cannot be inferred from a small DEMO sample.

---

## 10. Prepared Post-DEMO Work A–J — PLANNED / DO NOT START YET

The File Library artifact `DAX_POST_DEMO_NEXT_WORK.md` contains the full prepared assignment:

A. Broker Execution Evidence  
B. Expected vs Observed  
C. TCA / Cost Attribution  
D. Data / Clock Parity  
E. Risk Science  
F. Tail Survival  
G. Strategy Robustness  
H. Release / Operations  
I. Failure Injection  
J. Research Efficiency

It is **PLANNED / NOT EXECUTED**. Before starting it, re-pin actual head/main/pointer/Continuity. `0ee0eca...` is only its research anchor, not a future required head. Missing host/broker/user-authorization evidence remains external. V11.2 and CAND-001 trading logic/costs remain frozen. The assignment itself authorizes no broker order, cancel, modify, blind retry, slot release, PAPER or LIVE action.

---

## 11. Research / strategy backlog — durable ordering

Research decision order remains:

**REGIME -> STRUCTURE -> ENTRY**

Important later tracks include:

- ATR compression/expansion and range relative to higher volatility;
- ADX with hysteresis rather than regime flapping;
- previous-day structure, opening-gap persistence and breakout quality;
- first breakout / first retest / late-entry avoidance;
- rejected-candidate analytics, filter efficiency, overlap and opportunity cost;
- Strategy Specification Fingerprint and immutable hypothesis/trial families;
- profit concentration / top-trade removal;
- Drawdown DNA: depth, duration, recovery, time-under-water;
- dependent Monte Carlo / tail survival / Risk of Ruin under explicit fixed-cash assumptions;
- adaptive risk decay/cooldown only as risk reduction, never Martingale/revenge sizing;
- expected-vs-observed and execution-cost attribution before interpreting forward degradation;
- FAST staged screening / coarse-to-fine rather than blind brute force.

No item above silently promotes CAND-001 or mutates V11.2.

---

## 12. Anti-patterns — binding rejects

Do not silently adopt:

- Martingale / doubling after loss;
- averaging down / unlimited grid / unlimited rescue / hedge escalation;
- blind retry/resubmit after ambiguous transport;
- state reset as incident recovery;
- synthetic evidence promoted to broker truth;
- one-magic-parameter selection;
- AI/profit marketing without reproducible evidence;
- second duplicate store/risk/reconciliation/lifecycle/health framework without a proven owner gap.

---

## 13. Work / chat operating rules — BINDING

- Repository truth > Work prose > chat memory.
- Work is for large high-leverage packages; main chat independently verifies head/diff/CI/safety/pointer afterward.
- When Work is actively writing the branch, main chat must not concurrently write that branch.
- Work orders visibly state model/thinking/credit budget.
- Before user-visible generated files, run the required preflight.
- Visible cadence during long work: `Schritt N -> Tätigkeit -> kurzer Zwischenstand -> ✅/⚠️/❌ -> tatsächliche nächste Aktion`.
- A status update is not a stop. Continue while safe work remains.
- Official project steps are whole integers only.
- Do not fabricate background work. Only scheduled automations genuinely run later.
- Public/open-source scans inform RESEARCH/EXTEND/REJECT decisions but never silently replace VERIFIED local architecture.

---

## 14. Frozen/reference facts

- V11.2 remains the frozen reference baseline.
- Historical 2014–2019 baseline: 1,673 Berlin-session days; 09:00–17:30; 172,319 M5 candles; 103 bars/day; 0 OHLC errors.
- Walk-forward: 81 WFs; Train 45 / OOS 20 / Step 20.
- Static repository OOS truth for V11.2: 856 trades; total normal-cost R approximately `-31.309210619787684`; 37 positive / 44 negative WFs; median PF approximately `0.905769`.
- Normal cost assumptions: spread 0.20 / slippage 0.10 / commission 0.10; existing 1.5x / 2x stress retained.
- CAND-001 is a product candidate, not a profitability proof.
- Engine reconstruction before every backtest and FAST-screening discipline remain binding.

---

## 15. Exact next action after a new-chat recovery

Unless repository/runtime truth has changed materially, the next technical progression is **M01 / active Step 2231 real-host evidence**, not new strategy coding:

Windows checkout/runtime build -> correct MT5 instance -> DEMO account/server/symbol/account mode -> fresh tick/CLOSED-M5 -> broker/UTC/session clock -> full-account inventory/history -> economics/precision/symbol contract -> risk/loss/protection -> reconciliation/restart evidence.

Only after those real facts are reviewed may the project decide whether conditions exist to prepare/request separate authorization for M02.

No repository prose, Work report or green CI can substitute for those external facts.
