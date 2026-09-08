# Public Architecture Donors V2

Status: RESEARCH / ARCHITECTURE INPUT ONLY

No donor project is evidence that a DAX trading rule works. No strategy is promoted from public code. Foreign code is not copied into the frozen V11.2 reference.

## QuantConnect LEAN
- Repository: `QuantConnect/Lean`
- License observed: Apache-2.0
- Useful donor areas: deterministic algorithm lifecycle, event-driven separation, backtest/live interface discipline, result surfaces, operational state boundaries.
- DAX Lab use: architecture comparison only unless a separately reviewed implementation decision is made.

## NautilusTrader
- Repository: `nautechsystems/nautilus_trader`
- License observed: LGPL-3.0
- Useful donor areas: event-driven trading architecture, backtest/live parity concepts, explicit execution/risk boundaries, stateful engine design.
- DAX Lab use: concepts only by default; licensing implications must be reviewed before any direct code reuse.

## Binding donor rules
1. Public-project architecture may inspire tests, interfaces and failure controls.
2. License is checked before any code-level reuse.
3. Public strategy performance is never imported as DAX evidence.
4. Any adopted concept must pass DAX Lab's own deterministic replay, OOS/WF, cost stress and stability gates.
5. V11.2 remains immutable.

## Current V5 priority
The most valuable donor lesson for the current phase is not another indicator. It is operational reproducibility: deterministic run identity, persistent checkpoints, recoverable state, explicit execution boundaries and a UI that reads verified state rather than becoming a second source of truth.
