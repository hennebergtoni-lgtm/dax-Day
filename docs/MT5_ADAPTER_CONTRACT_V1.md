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

## Future execution boundary
A later execution adapter may expose `order_check` before any `order_send`, but only after explicit Paper-stage authorization and dedicated tests for symbol mapping, volume rounding, stop-distance rules, filling policy, idempotency, duplicate-order prevention, partial fills and broker rejection handling.

## Separation from Web UI
The Web interface may display MT5 adapter health and mapping state. It must not expose an order button or mutable trading control during this preparation phase.

## Promotion
This contract does not authorize Shadow, Paper or Live trading. It only prepares the boundary so later integration can occur without redesigning the Decision Core.
