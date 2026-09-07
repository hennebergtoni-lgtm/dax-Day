# Research Gates and Milestone Discipline

The new infrastructure accelerates work; it does not change the scientific order of the project.

## Gate 0 — audited data basis
Required before historical parity/research claims:
- 2014–2019 basis identified by manifest/fingerprint
- 1,673 valid Europe/Berlin session days
- 172,319 M1 candles
- 103 M5 session bars/day
- 09:00–17:30 Europe/Berlin session contract
- zero known OHLC integrity errors

## Gate 1 — frozen V11.2 parity
V11.2 is reference-only and immutable. A reconstructed/adapted core must reproduce the established reference surface before research results are accepted.
Required checks include:
- 144-variant grid contract
- 81 WF schedule, 45 train / 20 OOS / 20 step
- known trade-bearing pre-gate: 14 trades, 3.9351648669R, PF 1.5556035886
- broader parity surface: 144/144, 114 trade-bearing cases where the reference fixture is available
- reference OOS aggregate: 1,384 trades, -68.1095R, 36 positive / 45 negative WFs

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
