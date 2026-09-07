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
Each is isolated first; only validated tools reach interaction testing.

## Gate 4 — targeted interactions
Interactions are hypothesis-led and limited. No brute-force combinatorial explosion. Existing OR15/retest/OR-mid/RR/OR-ATR findings remain evidence and controls, not automatic strategy replacements.

## Gate 5 — candidate bot
A candidate requires robust OOS/WF evidence, cost stress, overfitting diagnostics, stability and independent validation. Ranking alone cannot promote a candidate.

## Gate 6 — execution
Only after candidate validation: MT5 paper/demo execution boundary, operational risk controls, then any later live decision. Research code and broker execution stay separated.

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
