# Public Research Donors V3

Date: 2026-09-08
Purpose: architecture/test/hypothesis donors only. Public performance is never DAX evidence.

## DaruFinance/quant-research-framework
URL: https://github.com/DaruFinance/quant-research-framework
License: Apache-2.0 (verified from repository LICENSE on 2026-09-08)
Role: ARCHITECTURE / TEST-PATTERN DONOR

Useful concepts:
- correctness-first walk-forward research with strict no-look-ahead invariants,
- future-pollution tests that alter later bars and require earlier signals to remain unchanged,
- explicit robustness/stress layers and overfitting diagnostics,
- readable reference implementation plus faster implementation held to parity in CI,
- ATR implementation based on true range and exponential/Wilder-style smoothing,
- run locks to prevent concurrent output corruption.

DAXLAB decision:
- adopt concepts and independent implementations where useful;
- do not import bundled ATR-cross strategy performance or thresholds;
- retain our canonical 45/20/20 WF, V11.2 cost semantics, DAX session rules and frozen baseline;
- direct code reuse would require Apache-2.0 attribution/notice compliance, so ATR001 will initially use an independent small implementation rather than copied donor code.

## Jenak26/event-driven-backtester
URL: https://github.com/Jenak26/event-driven-backtester
Role: CONCEPT DONOR pending license verification before any direct code reuse.

Useful concepts observed publicly:
- point-in-time/event-driven semantics,
- next-bar fills,
- realistic costs,
- walk-forward validation,
- explicit documentation of limitations and regime dependence,
- tests for look-ahead prevention and windowing.

DAXLAB decision: concepts only until license is verified. No performance transfer.

## MT5 public adapter projects
Examples reviewed include PyTrader MT4/MT5 connector, MT5 Python wrappers and pymt5adapter-style wrappers.
Role: EXECUTION-BOUNDARY CONCEPT DONORS only.

Useful concepts:
- connection keepalive/health,
- account/symbol/tick/bar read APIs,
- explicit error translation,
- separation between terminal bridge and strategy,
- symbol metadata discovery.

DAXLAB decision: current MT5 phase remains READ_ONLY_ONLY. No order-send code is imported or enabled. Our own MT5 adapter contract remains authoritative.

## Binding donor rule
A public project may change our test plan or architecture only when it improves correctness, observability, reproducibility or safety. It cannot promote a trading rule. Every trading hypothesis still passes our own causal -> descriptive -> OOS/WF -> cost stress -> stability -> prospective evidence ladder.