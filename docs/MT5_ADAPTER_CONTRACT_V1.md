# MT5 Adapter Contract V1

Status: ARCHITECTURE PREPARATION / NO ORDER EXECUTION
Date: 2026-09-08

## Purpose
Prepare a future MetaTrader 5 integration without coupling MT5-specific behavior into the frozen V11.2 reference or the canonical Decision Core.

## Architectural rule
MT5 is an external execution/data adapter, not a strategy engine.

Canonical flow:
1. MT5/data source -> normalized runtime Candle / account observations
2. Data-quality gate
3. Decision Core
4. execution-intent boundary
5. MT5 execution adapter

No MT5-specific symbol, ticket, filling-mode or broker rule may leak into strategy logic.

## Phase 1 — read-only adapter
Allowed capabilities:
- terminal/version health
- symbol metadata
- tick snapshot
- closed-bar retrieval
- account snapshot
- positions snapshot
- broker/server time observation

Forbidden capabilities:
- order_send
- position modification
- position close
- pending-order placement/cancellation
- live risk mutation

## Closed-candle rule
The current/open MT5 bar is never decision-safe merely because it is returned by the terminal. The adapter must normalize only fully closed bars into the runtime Candle contract and must preserve event_time, close_time, received_at, source and quality state.

## Symbol mapping
Broker symbols are configuration, not strategy constants. A mapping layer must resolve canonical instrument `DAX` to broker-specific symbols such as GER40/DE40/DAX40 variants without changing research logic.

Required mapping metadata:
- canonical_symbol
- broker_symbol
- point_size / digits
- contract_size
- minimum_volume
- volume_step
- trade_mode
- session metadata
- source broker/server

The resolver must prefer tradeable exact/configured matches and fail closed on ambiguous aliases. It must never guess a broker symbol solely from a partial string match.

## Time contract
All incoming timestamps must be made timezone-aware and normalized before entering the Decision Core. Broker/server time must not be assumed to equal Europe/Berlin. DST handling remains explicit.

## Health/fail-closed
Adapter health must expose at least:
- TERMINAL_CONNECTED
- ACCOUNT_CONNECTED
- SYMBOL_AVAILABLE
- MARKET_DATA_FRESH
- CLOCK_OK
- READ_ONLY_MODE

Any unknown/stale/disconnected state blocks prospective decisions that depend on that source.

## Operator-safety requirements carried forward from public architecture review
These are architecture patterns only; no foreign strategy performance is imported.

### Single-instance protection
Before any later Paper/Live execution capability exists, one account/symbol execution identity may have only one active writer. A second process must fail closed instead of creating duplicate orders.

### Why-no-trade diagnostics
Every blocked prospective decision should expose the first decisive gate and relevant observed values. The Web interface may display this read-only. It must not convert diagnostics into manual order controls.

### Connection watchdog
The adapter must distinguish terminal connected, account connected, symbol available, market-data fresh and engine-loop healthy. The Web UI must never report a healthy trading state merely because the HTTP process is alive.

### Atomic state persistence
Any future mutable execution state must be written atomically and recoverably so interruption cannot leave a partially written order/idempotency state. Research artifacts and canonical DB evidence remain separate from execution state.

### One-action-per-closed-bar identity
A later execution boundary must preserve deterministic decision/order identity so a persistent signal cannot re-fire repeatedly on the same closed candle. This complements, but does not replace, broker-side duplicate prevention and idempotency checks.

## Future execution boundary
A later execution adapter may expose `order_check` before any `order_send`, but only after explicit Paper-stage authorization and dedicated tests for symbol mapping, volume rounding, stop-distance rules, filling policy, idempotency, duplicate-order prevention, partial fills and broker rejection handling.

Required future progression remains:
1. READ_ONLY
2. SHADOW intent generation with no broker mutation
3. PAPER execution boundary after explicit authorization
4. LIVE only after separate readiness evidence and explicit authorization

No phase may be skipped by changing a Web status flag.

## Separation from Web UI
The Web interface may display MT5 adapter health and mapping state. It must not expose an order button or mutable trading control during this preparation phase.

Recommended read-only fields:
- adapter phase
- terminal/account connectivity
- canonical and resolved broker symbol
- ambiguity/mapping state
- latest closed-bar age
- server-clock offset/health
- engine-loop heartbeat
- first blocking gate / why-no-trade reason
- single-instance lock state
- execution capability (must remain disabled in Phase 1)

## Public donor boundary
Current public donor review contributed architecture ideas only. Code reuse requires a separately verified license and compatibility review before any direct import. Foreign backtest or trading performance never constitutes DAX evidence.

## Promotion
This contract does not authorize Shadow, Paper or Live trading. It only prepares the boundary so later integration can occur without redesigning the Decision Core.
