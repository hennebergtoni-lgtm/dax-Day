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

Gate 0 status: **GREEN (2026-09-08)**.

## Gate 1 — frozen V11.2 parity and clean reference
V11.2 is reference-only and immutable. A reconstructed/adapted core must reproduce the established engine surface before research results are accepted.

Clean active reference is `V112_REFERENCE_V1`, fixed rolling 45/20/20, 81 WFs, audited DAX M5 data, normal/1.5x/2x costs. Historical V4.0-FIX1 remains legacy evidence only because `_MALFORMED` serialization/parsing affected part of the old OOS surface.

Gate 1 status: **GREEN — ACTIVE REFERENCE FROZEN.**

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

### BB001 current branch
- alignment gate: GREEN, 856/856 clean OOS trades matched at actual `entry_time`
- descriptive evidence: narrowest bandwidth quartile weak; directional band position promising
- fixed coarse directional-momentum test: +24.37R / PF 1.10 / 432 trades at normal costs, but not yet validated
- temporal stability remains mixed at finer WF resolution; regime explanation and exact cost stress are required before promotion

### EVENT001 — event/news context layer
The event layer is a research tool, not an unverified live override. Candidate inputs include scheduled macro events (ECB, Fed/FOMC, CPI, NFP and other demonstrably DAX-relevant releases), event proximity, event class/importance and later validated market/news context. Event information may become a filter, risk reducer or confidence input only after OOS/WF validation.

## Gate 3A — recurring public-project intelligence milestone
Public GitHub/quant projects must be reviewed throughout research, not only once at the end. The purpose is to reuse already-developed ideas, experimental designs and engineering patterns to reduce duplicated effort while keeping our own evidence independent.

For every major research family (Bollinger, Fibonacci, gaps, OR/retest, volatility/regime, event context, exits/trailing, cross-market context, execution), perform a targeted public-project scan before finalizing its experiment design. Record:
- repository/project and license status
- exact idea or engineering pattern worth testing
- what evidence the donor project actually provides versus what is only a claim
- look-ahead/repainting/data-mining risks
- whether we may reuse code or only reimplement the idea
- mapping into our IDEA -> RESEARCH -> PILOT -> VALIDATED TOOL pipeline

Public-project results never replace our DAX OOS/WF validation. They are an efficiency and hypothesis source.

### Public-project hypotheses already queued
1. **Multi-timeframe Bollinger regime switching** — inspired by `JN842/multitf-bollinger-switching`: investigate whether a completed higher-timeframe Bollinger state can distinguish momentum/breakout from mean-reversion regimes. Must use only completed HTF bars and be independently implemented unless license permits reuse.
2. **Confirmed breakout -> retrace** — inspired by `dws-data/nas-orb-backtester`: investigate close-confirmed OR breakout followed by retracement rather than raw intrabar breakout.
3. **Volume-profile retracement zones** — investigate VAH/POC/VAL or comparable volume-profile structure as retracement context, only after a reproducible DAX volume-data contract exists.
4. **Breakout persistence** — investigate whether persistence/confirmation after an OR break predicts retest quality; candidate confirmations include one/two closes and higher-timeframe close, with volume variants only if data quality supports them.
5. **Efficient precomputation architecture** — retain donor patterns such as daily-context precomputation, vectorized arrays, timestamp lookup and MFE/MAE capture where they preserve exact strategy semantics.

These hypotheses are now milestone items and must not be silently dropped. They are not validated rules and must not be inserted into V11.2.

## Gate 4 — targeted interactions and regime/tool mapping
Interactions are hypothesis-led and limited. No brute-force combinatorial explosion. Existing OR15/retest/OR-mid/RR/OR-ATR findings remain evidence and controls, not automatic strategy replacements.

After isolated evidence exists, explicitly research **which validated tool/filter works in which trading period/regime**. Candidate conditioning dimensions include:
- time-of-day/session phase
- DAX volatility/trend/range/OR state
- completed higher-timeframe state
- scheduled-event proximity
- later cross-market state from DAX-relevant instruments (e.g. European equity context, US futures where contemporaneously available, EUR/USD, rates/Bund, volatility indices)

Cross-market features must be timestamp-causal. No information unavailable at the DAX decision time may be used. The target architecture is regime -> DAX structure -> cross-market context -> eligible validated tools -> setup/entry -> bounded risk, rather than one universal filter stack.

## Gate 5 — candidate bot
A candidate requires robust OOS/WF evidence, cost stress, overfitting diagnostics, stability and independent validation. Ranking alone cannot promote a candidate.

## Gate 5A — confidence and adaptive risk research
Only after validated strategy components exist, research a transparent setup-quality/confidence score. Confidence and risk remain separate; all adaptive sizing stays inside hard account/day/trade limits and must pass OOS/WF and stress validation.

## Gate 6 — execution
Only after candidate validation: MT5 paper/demo execution boundary, operational risk controls, then any later live decision. Research code and broker execution stay separated.

## Gate 7 — operator web interface
Later UI: bot/MT5 state, regime/setup explanation, bounded risk profile, event context, trades and why trade/no trade. UI cannot create arbitrary strategy parameters or bypass risk controls.

# Donor-project integration rule
Public GitHub projects are an engineering/research library, not a new source of truth.

Previously audited donors retained:
- `charlesbx/futures-backtester` (MIT): plugin architecture, grid/WF organization, explicit costs, CLI concepts.
- `DaruFinance/quant-research-framework` (Apache-2.0): no-lookahead discipline, robustness/overfitting statistics, CI/property-test philosophy.
- `asdtroll3/ORB-Backtester` (MIT): conservative ambiguity handling, trade reporting and sensitivity analysis.
- `jimtin/build-your-own-mt5-ea` (MIT): later MQL5/MT5 helper patterns.
- `Sarthaktagra27/orb-futures-backtesting`: previous-day range, CPR, volatility/cross-instrument hypotheses; idea donor only unless licensing permits otherwise.
- `dws-data/nas-orb-backtester`: confirmed breakout/retrace, volume-profile and persistence hypotheses; idea donor unless licensing permits reuse.
- `JN842/multitf-bollinger-switching`: multi-timeframe regime-switching hypothesis; idea donor unless licensing permits reuse.

Every donor-derived idea must enter our normal IDEA -> RESEARCH -> PILOT -> VALIDATED TOOL pipeline and must be tested against our audited DAX data and frozen controls.
