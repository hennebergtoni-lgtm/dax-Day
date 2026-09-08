# Public MT5 / Trading Architecture Donor Scan — 2026-09-08

Status: ARCHITECTURE INTELLIGENCE ONLY

## Rule
Public projects may contribute architecture ideas, testing patterns and interface concepts. Their performance claims are never DAX evidence. Direct code reuse requires verified compatible licensing and a separate provenance record.

## Official MetaTrader 5 Python surface
Source: official MQL5 Python Integration documentation.
Observed capabilities include:
- initialize/login/shutdown
- terminal/account/symbol information
- bars/ticks retrieval
- orders/positions/history
- order_check
- order_send

Important DAXLAB interpretation:
- current bar (`start_pos=0`) is not automatically decision-safe;
- closed-candle normalization must occur before Decision Core use;
- `order_check` and `order_send` belong behind a future execution boundary, not inside strategy logic.

## akivajp/mt5-bridge
License observed: MIT.
Architecture idea retained:
- Windows-side MT5 server/adapter;
- platform-independent client over HTTP;
- guarded MT5-specific handler;
- health/data/account/order surfaces separated from strategy process.

Use in DAXLAB:
- concept donor for remote adapter topology;
- do not import implementation at this stage;
- future Paper stage may evaluate a local/remote bridge after security and idempotency review.

## monki103/pyMt5Bridge
Architecture idea retained:
- small FastAPI facade over official MetaTrader5 package;
- bridge runs in the same Windows runtime as the terminal;
- supports read-only startup mode.

Use in DAXLAB:
- strengthens read-only-first adapter design;
- concept donor only until license/provenance are independently frozen.

## huy-bui-tech/mt5_api
Architecture idea retained:
- Python server + MT5 EA client over sockets for cross-platform operation.

Use in DAXLAB:
- useful alternative topology if the official Python package cannot fit the desired hosting environment;
- higher operational complexity than same-host official Python SDK, so not preferred by default.

## SaadHassanFaisal/MT5-Trading-Bot architecture
Architecture idea retained:
- structural capability separation: market-reading modules should not possess order-placement capability merely by convention.

Use in DAXLAB:
- aligns with existing Decision Core / execution boundary separation;
- reinforces capability-based safety rather than UI-only or policy-only safety.

## BorjaGomezSolorzano/Metatrader-Bridge
License observed: BSD-3-Clause.
Architecture idea retained:
- decoupled Python/MQL communication layer.

Use in DAXLAB:
- historical alternative concept only;
- file-mediated messaging is less attractive for our primary path than a typed local adapter/HTTP/socket boundary with explicit health and idempotency.

## DAXLAB decision
Preferred future path:
1. read-only official MetaTrader5 adapter on Windows/terminal host;
2. normalize MT5 data into canonical DAXLAB runtime contracts;
3. expose adapter health to Web UI;
4. no order capability until explicit Paper-stage authorization;
5. if remote hosting is required, place a narrow authenticated bridge around the adapter rather than moving strategy logic into MT5/MQL.

No public donor changes V11.2, research evidence, Paper readiness or Live readiness.
