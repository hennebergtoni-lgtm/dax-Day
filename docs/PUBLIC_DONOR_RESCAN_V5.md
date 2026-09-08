# Public architecture donor rescan — V5

Purpose: architecture/research ideas only. No foreign strategy result is evidence for DAX and no foreign source is copied into the frozen V11.2 engine.

## Rechecked donors

### QuantConnect/Lean
- Public, active repository.
- License observed: Apache-2.0.
- Useful donor categories: event-driven engine separation, research/backtest/live mode boundaries, brokerage/execution abstractions, result/statistics surfaces.
- V5 use: architecture ideas only; our Decision Core and frozen V11.2 remain independent.

### nautechsystems/nautilus_trader
- Public, active repository.
- License observed: LGPL-3.0.
- Useful donor categories: event-driven architecture, deterministic backtest/live parity concepts, execution/risk separation, persistence/operations patterns.
- V5 use: architecture ideas only; do not copy code into the project without an explicit dependency/license decision.

### polakowo/vectorbt
- Public repository.
- Current license observed: Apache-2.0 with Commons Clause restriction.
- Useful donor category: high-throughput vectorized research/screening concepts.
- V5 decision: IDEA ONLY. Do not copy/integrate code. FAST remains screening-only and may never independently promote a strategy.

### kernc/backtesting.py
- Public repository.
- Current license observed: AGPL-3.0.
- Useful donor categories: compact research UX, result visualization, optimization surfaces.
- V5 decision: IDEA ONLY for UI/research ergonomics. Do not copy/integrate source.

## Binding conclusions
1. Event-driven deterministic replay remains the correct production/replay architecture.
2. Vectorized methods remain useful only as bounded research accelerators.
3. Research UX should expose assumptions, parameters, costs, OOS/WF and stability rather than only headline return.
4. Execution/risk boundaries must remain separate from strategy research.
5. License must be checked at the time of any future code/dependency adoption; this document does not authorize code copying.
