# Research Module Catalog

This catalog separates code availability from trading permission.

| Module | Purpose | Code status | Evidence status | Live switchable now? | Planned interactions |
|---|---|---|---|---|---|
| V11.2 reference | frozen execution/reference baseline | frozen | active reference | baseline only | controls all research comparisons |
| BB001 | causal Bollinger quality/regime context | implemented + tested | research | no | OR/retest, prior-day regime, later FIB/GAP |
| PrevRange/ATR | prior-day extension context | implemented inside research tooling | research | no | BB001, OR/retest |
| FIB001 | causal retracement depth/zones from defined impulse | implemented feature module + tests | research-started | no | OR/retest first, later BB001/GAP001 |
| GAP001 | opening gap context and normalization | implemented feature module + tests | research-started | no | OR/retest first, later BB001/FIB001 |
| EVENT001 | scheduled macro-event context | planned | planned | no | regime/setup quality after isolated validation |
| Cross-market | external market context | planned | planned | no | only after DAX-internal evidence stabilizes |

## Web-interface principle
A module can exist in code long before it is allowed to affect execution. The interface should expose:
- evidence status
- current observed value/state
- research provenance
- suggested relevance to current regime
- whether manual or automatic control is permitted

## Promotion ladder
`idea -> research code -> isolated evidence -> validated -> deployable -> optional manual switch -> separately validated regime-automatic switch`

## Current decision architecture
`market regime -> DAX structure -> validated context -> eligible deployable filters -> setup/entry -> bounded risk`

## Hard rule
No UI toggle, recommendation engine, or regime selector may bypass risk limits, data-integrity gates, no-lookahead rules, execution health checks, or explicit promotion status.
