# PUBLIC DONOR MAP V4

Status: RESEARCH / ARCHITECTURE INTELLIGENCE — 2026-09-08

Purpose: map useful public projects to DAX Research Lab concerns without treating external projects as DAX performance evidence and without copying code unless license/reuse is explicitly cleared.

## Binding rule
External repositories may contribute architecture ideas, failure modes, test patterns and research ergonomics. They do not validate a DAX trading rule. Independent reimplementation is preferred.

| Donor | License observed | Useful category | Pattern relevant to DAX Lab | Adoption status |
|---|---|---|---|---|
| nautechsystems/nautilus_trader | LGPL-3.0 | REPLAY / OPERATIONS / EXECUTION | event-driven architecture, separation of trading logic from venue/execution concerns, consistent research/live concepts | IDEA / ARCHITECTURE ONLY; no source copied |
| QuantConnect/Lean | Apache-2.0 | DATA / REPLAY / EXECUTION / OPERATIONS | mature brokerage boundary, event-driven backtest/live separation, explicit order lifecycle concepts | IDEA / ARCHITECTURE ONLY; no source copied |
| polakowo/vectorbt | Apache-2.0 + Commons Clause | RESEARCH | fast vectorized research exploration, parameter-surface analysis and research ergonomics | IDEA ONLY; no code reuse planned because of license restriction and because FAST cannot be promotion evidence |
| jefrnc/strategy-orb15-momentum | MIT | RESEARCH / RISK / OPERATIONS | configurable 5–15 minute ORB, real-data backtesting requirement, Paper-first workflow, logging/circuit-breaker concepts | IDEA ONLY; equity/long-only evidence does not validate DAX OR15 or our performance |
| deterministic-market-replay | Apache-2.0 (prior audit) | REPLAY | deterministic event replay and sequence reproducibility | IDEA / TEST-PATTERN DONOR |
| QSTrader | MIT (prior audit) | REPLAY / RESEARCH | event-driven portfolio/backtest decomposition | IDEA DONOR |
| Jenak26 donor | MIT (prior audit) | RESEARCH | strategy/research implementation patterns | IDEA DONOR; no DAX evidence substitution |
| WalllerG donor | MIT (prior audit) | RESEARCH | modular indicator/filter patterns | IDEA DONOR |
| Boutquin.Trading | Apache-2.0 (prior audit) | OPERATIONS / EXECUTION | execution and trading-system decomposition | IDEA DONOR |
| multi-timeframe Bollinger donor | license not verified | RESEARCH | multi-timeframe Bollinger hypothesis | IDEA ONLY; no code reuse |

## Category mapping
### DATA
Useful donor questions:
- Is source provenance explicit?
- Are timestamps monotonic and timezone-aware?
- Are session boundaries modeled rather than repaired silently?
- Can identical normalized data be fingerprinted reproducibly?

Current DAX Lab response: HASH_VERIFIED audited session surface, explicit Berlin session handling, fail-closed quality states, versioned fingerprint contract.

### REPLAY
Useful donor questions:
- Can the same core consume historical and prospective events?
- Is replay deterministic across reruns and restart/resume?
- Are event ordering and state transitions explicit?

Current DAX Lab response: shared V11.2 bridge, run manifests, decision manifests, checkpoint provenance, session-aware sequence classification.

### RISK
Useful donor questions:
- Are hard safety blockers outside strategy discretion?
- Can data/feed/execution faults force NO_TRADE?

Current DAX Lab response: DATA_UNSAFE / FEED_INTERRUPTION / EXTREME_SPREAD / CONTRADICTORY_STATE are non-overridable blockers.

### RESEARCH
Useful donor questions:
- Is fast screening separated from exact validation?
- Are parameter surfaces inspected for stability rather than single-point maxima?
- Are causality and OOS independence tested explicitly?
- Does an ORB donor require real data, realistic costs and prospective paper validation rather than relying on a claimed headline result?

Current DAX Lab response: FAST is screening only; exact/OOS/WF/cost-stress/stability/prospective validation is the promotion path. External ORB parameter choices such as 5–15 minutes are hypothesis context only and never substitute for DAX-specific evidence.

### UI
Useful donor questions:
- Can operator-visible health distinguish GREEN/YELLOW/RED?
- Are blockers and NO_TRADE reasons visible rather than hidden?

Current DAX Lab response: operator health/readiness models and decision logging already separate technical health from promotion readiness.

### OPERATIONS
Useful donor questions:
- Are execution/broker adapters isolated from strategy?
- Can reconnect/resume reconcile state without duplicate orders?

Current DAX Lab response: Shadow/Paper acceptance contract defines a separate execution boundary; implementation remains future work and cannot authorize Paper yet.

## Bias / causality audit before adopting any external idea
Reject or quarantine an external pattern if it relies on any of the following without an explicit causal reformulation:
- centered or future-aware rolling windows;
- future swing highs/lows for current Fibonacci anchors;
- same-bar close information used for an entry that occurs before that close;
- repainting indicators;
- parameter choice made from OOS outcomes and then reported as independent OOS proof;
- survivorship/selection of only successful instruments, sessions or setups;
- vectorized fill assumptions that ignore intrabar ordering, gaps, spread or costs;
- global normalization/statistics that include future data;
- post-event labels leaked into entry features.

## Project decision
No public donor changes V11.2 and no public donor is accepted as DAX alpha evidence. Donors may improve engineering and research discipline only after independent causal implementation and local tests.
