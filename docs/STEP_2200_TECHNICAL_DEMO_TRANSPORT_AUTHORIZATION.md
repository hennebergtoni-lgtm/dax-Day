# Step 2200 — Technical DEMO transport authorization boundary

Status: ACTIVE / TECHNICAL IMPLEMENTATION AUTHORIZED
Date: 2026-09-13
Repository: `hennebergtoni-lgtm/dax-Day`
Branch: `nextgen-bot-line-v1`
PR: #109
Authorization anchor head: `d7cccf6bacc866669134629ff81cdc0491416a33`

## User authorization

The user explicitly authorized Step 2200 for **technical DEMO-evidence transport and lookup implementation including tests**.

The authorization does **not** authorize any actual broker order. The first actual DEMO-evidence order requires a separate explicit user authorization. Normal PAPER and LIVE remain unauthorized.

## Permitted in Step 2200

- implement and test a bounded DEMO-only technical transport contract;
- implement and test read-only MT5 lookup/query surfaces;
- normalize externally returned open-order/history/deal evidence into existing broker-neutral evidence owners;
- derive deterministic local transport identity metadata from the existing canonical `client_order_id` provided the derivation is tamper-evident and never treated as broker proof before real-host verification;
- use dependency injection/fakes for Linux CI and keep MetaTrader5 runtime imports confined to the Windows-facing adapter surface;
- add fail-closed tests for missing, ambiguous, stale, malformed, cross-wired and contradictory evidence;
- retain existing restart/query/reconciliation/telemetry owners and one canonical attempt identity/store.

## Explicitly not authorized

- no call to `mt5.order_send` or any equivalent broker submission function;
- no actual DEMO broker order;
- no PAPER or LIVE authorization;
- no `execution_capability` other than `NONE`;
- no `order_execution_enabled=true`;
- no automatic resubmit, retry, cancel or slot release;
- no fabricated ACK/fill/order ticket/venue observation;
- no Acceptance refresh or PR merge;
- no V11.2, CAND-001 strategy, cost or reference-data mutation;
- no assumption that MT5 `comment`, `magic`, ticket, open orders, history or deals preserve a usable client identity until verified on the real DEMO host.

## MT5 technical facts used by the design

The official MetaTrader5 Python surface provides read-only `orders_get`, `history_orders_get` and `history_deals_get`. `MqlTradeRequest` provides `magic` and `comment` fields, while history/order/deal records expose related metadata. The adapter may therefore implement a deterministic local transport tag and read-only matching policy, but real broker preservation/lookup support remains `WAITING_EXTERNAL` until observed on the actual DEMO account.

An empty open-order result is never sufficient evidence of non-execution. Lookup must include the relevant order history and deal/fill history and must fail closed on ambiguity or SDK/query failure.

## Binding continuation

Step 2199 remains the verified local restart/read-only boundary. Step 2200 may move that boundary forward technically, but it must stop before the first real DEMO order or any other broker-side trading side effect.
