# Research Gates and Milestone Discipline

The new infrastructure accelerates work; it does not change the scientific order of the project.

## Evidence hierarchy
Three evidence levels are binding:
1. **Legacy evidence** — historical Colab/notebook outputs. Preserve them for provenance, comparison and hypothesis generation, but do not use them as pass/fail targets when their exact implementation cannot be reproduced cleanly.
2. **Reproducible evidence** — results generated from versioned code, audited/fingerprinted data, explicit methodology and passing automated tests.
3. **Active reference** — reproducible evidence formally frozen as the current comparison surface for subsequent research.

If legacy evidence conflicts with a clean reproducible run, the discrepancy must be documented and investigated, but the new pipeline must not recreate a known legacy defect merely to hit an old aggregate. Legacy values may generate hypotheses; they do not dictate current methodology.

## Gate 0 — audited data basis
Required before historical parity/research claims:
- 2014–2019 basis identified by manifest/fingerprint
- 1,673 valid Europe/Berlin session days
- 481,824 raw M5 rows
- 172,319 M5 Berlin-session bars
- 103 M5 session bars/day
- 09:00–17:30 Europe/Berlin session contract
- zero known OHLC integrity errors
- zero duplicate UTC timestamps
- session OHLC SHA256 `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`

Gate 0 status: **GREEN (2026-09-08)**. The migration bundle was independently re-read and re-fingerprinted after creation. The earlier label “172,319 M1 candles” was an audit-label error; the number is the M5 Berlin-session bar count and no strategy/result values changed.

## Gate 1 — frozen V11.2 parity and clean reference
V11.2 is reference-only and immutable. A reconstructed/adapted core must reproduce the established engine surface before research results are accepted.

Two historically different WF surfaces must not be mixed:
- **Engine/FAST parity surface**: later exact-vs-FAST runner with the known trade-bearing pre-gate and 144/144 broader parity checks. This surface has been re-run on the audited dataset and is GREEN: 1,673/1,673 daily contexts exact, 14 trades / 3.9351648669R / PF 1.5556035886, 144/144 parity with 114 trade-bearing cases, and the 34,992-evaluation normal-cost matrix sum reproduces -1122.231646R.
- **Historical V11.2 OOS legacy surface**: `V11_2_FULL_WF_SESSION_DAY_V4_FIX1/FULL_WF_SUMMARY.csv`, release `V4.0-FIX1`, engine SHA `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`. Its heartbeat records `FULL_WF_COMPLETE` with WF1–WF81. This run uses a fixed rolling 45-train / 20-OOS / 20-step schedule, not the later expanding-training FAST schedule.

Historical legacy aggregate from that 81-row summary:
- 81 WFs exactly, WF1–WF81
- 1,384 OOS trades
- total OOS return -68.10950257808015R
- 36 positive WFs / 45 negative WFs / 0 flat WFs

These values are retained as **legacy evidence only**, not as targets for the clean reference rerun.

### Legacy `_MALFORMED` finding
The WF1–WF6 comparison exposed a concrete legacy implementation artifact: some historical selected variants serialize OR/ATR filters with a `_MALFORMED` suffix, including examples corresponding to `('between', 0.2, 0.6)` and `('above', 0.2)`. The clean runner uses the intended tuple filter representation directly and must not deliberately recreate malformed parsing/serialization behavior merely to match historical totals.

The small clean comparison produced exact agreement on unaffected WFs (including WF3, WF4 and WF6) while affected WFs diverged. This is evidence that the historical aggregate contains implementation-specific legacy behavior. The discrepancy remains documented for provenance; it is not a reason to mutate frozen V11.2 strategy semantics or corrupt the new runner.

Required checks for the new reference therefore include:
- 144-variant grid contract
- fixed rolling 45/20/20 WF methodology
- known trade-bearing engine pre-gate: 14 trades, 3.9351648669R, PF 1.5556035886
- broader engine parity surface: 144/144, 114 trade-bearing cases
- explicit normal / 1.5x / 2x cost models
- deterministic selection/tie-breaking
- versioned output and provenance hashes
- comparison to legacy aggregates as diagnostic information only, never as a pass/fail target

Gate 1 status: **ENGINE PARITY GREEN; HISTORICAL PROVENANCE RESOLVED; CLEAN V11.2 REFERENCE RERUN IN PROGRESS.**

## Gate 2 — research correctness
Before a tool can become VALIDATED TOOL:
- no-lookahead/prefix-stability checks
- deterministic execution and conservative unresolved intrabar ambiguity
- explicit normal / 1.5x / 2x cost stress
- reproducible experiment manifest
- sufficient trade counts and WF/OOS distribution, not aggregate PF alone
- parameter-neighbourhood stability

## Gate 3 — isolated tools
Order begins with the existing research matrix, not donor-project popularity:
1. BB001 Bollinger
2. FIB001 Fibonacci
3. GAP001 close gaps
4. volatility / time / entry / exit / market-structure tools
5. EVENT001 event/news context layer
Each is isolated first; only validated tools reach interaction testing.

### EVENT001 — event/news context layer
The event layer is a research tool, not an unverified live override. Candidate inputs include scheduled macro events (ECB, Fed/FOMC, CPI, NFP and other demonstrably DAX-relevant releases), event proximity, event class/importance and later validated market/news context. Research must measure whether setup behaviour before/after event classes changes trade quality. Event information may become a filter, risk reducer or confidence input only after OOS/WF validation. No statement such as “this trade can only win” is permitted.

## Gate 4 — targeted interactions
Interactions are hypothesis-led and limited. No brute-force combinatorial explosion. Existing OR15/retest/OR-mid/RR/OR-ATR findings remain evidence and controls, not automatic strategy replacements.

## Gate 5 — candidate bot
A candidate requires robust OOS/WF evidence, cost stress, overfitting diagnostics, stability and independent validation. Ranking alone cannot promote a candidate.

## Gate 5A — confidence and adaptive risk research
Only after validated strategy components exist, research a transparent setup-quality/confidence score. Potential validated inputs may include regime, volatility, OR/market structure, setup type, historical behaviour of comparable setups, event/news context, spread/liquidity and cross-market context.

Confidence and risk remain separate concepts:
- confidence estimates setup quality; it never guarantees an outcome
- position sizing remains bounded by hard risk limits
- high-confidence setups may qualify for a prevalidated bounded risk multiplier
- weak conditions may reduce size or prohibit a trade
- all adaptive sizing must be tested OOS/WF and under cost/stress conditions before demo use
- hard account/day/trade loss limits cannot be bypassed by confidence, UI controls or discretionary risk mode

Initial UI concepts such as Defensive / Standard / Offensive are product controls only. Exact percentages and multipliers are not fixed until separately researched and validated.

## Gate 6 — execution
Only after candidate validation: MT5 paper/demo execution boundary, operational risk controls, then any later live decision. Research code and broker execution stay separated.

Before live consideration, the execution/risk layer must support hard limits for per-trade risk, daily loss, exposure, trading/session state and emergency stop. Adaptive sizing remains bounded by those limits.

## Gate 7 — operator web interface
A later web interface should expose, without changing frozen research evidence:
- bot/MT5 connection and trading state
- current market regime and setup-quality/confidence explanation
- active risk profile and hard limits
- event/news risk context
- open/recent trades and bot decision rationale (“why trade / why no trade”)
- optional approval workflow when a validated high-confidence setup qualifies for a larger but still bounded order size

The UI must not create arbitrary strategy parameters or bypass risk controls. Configuration changes must be explicit, auditable and versioned. Automatic higher sizing may only be enabled after the same logic has passed research validation and demo/paper observation.

# Donor-project integration rule
Public GitHub projects are an engineering/research library, not a new source of truth.

Adopt where useful:
- `charlesbx/futures-backtester` (MIT): plugin architecture, grid/WF organization, explicit costs, CLI concepts.
- `DaruFinance/quant-research-framework` (Apache-2.0): no-lookahead discipline, robustness/overfitting statistics, CI/property-test philosophy.
- `asdtroll3/ORB-Backtester` (MIT): conservative ambiguity handling, trade reporting and sensitivity analysis.
- `jimtin/build-your-own-mt5-ea` (MIT): later MQL5/MT5 helper patterns.

Research independently, no code copying without confirmed license:
- `Sarthaktagra27/orb-futures-backtesting`: previous-day range, CPR, volatility/cross-instrument hypotheses; reject its full-dataset-grid-search evidence as validation and do not inherit ambiguous same-bar heuristics.
- `dws-data/nas-orb-backtester`: confirmed breakout/retrace and volume-profile hypotheses.
- other ORB/live-bot projects remain idea/architecture donors subject to license audit.

Every donor-derived idea must enter our normal IDEA -> RESEARCH -> PILOT -> VALIDATED TOOL pipeline and must be tested against our audited DAX data and frozen controls.
