# Paper Preparation V10

Status: CONTRACTS IMPLEMENTED / PAPER NOT STARTED

V10 prepares deterministic paper-trading data contracts without adding a broker adapter or an order submission function.

Implemented preparation surface:
- `ExecutionIntent` is versioned and has a deterministic `client_order_id` derived from decision/run/time/symbol/side/quantity/prices.
- duplicate intent identity is rejected by a dedicated deduplicator contract;
- lifecycle vocabulary is fixed to ACK / REJECT / PARTIAL / FILLED / CANCELLED;
- fill model V1 records spread, slippage, commission and latency assumptions;
- same-bar ambiguity is conservative stop-first;
- gap-through policy is first-available fill;
- partial fills are explicitly policy-controlled and disabled by default;
- telemetry is `SIMULATION_ONLY` and carries decision/run/client identity, timestamps, prices, costs, feed age, health and reconciliation state.

Hard boundary:
- no MetaTrader order API is present;
- no broker adapter is present;
- no credentials or account identifiers belong in these contracts;
- Paper remains BLOCKED / NOT STARTED;
- LIVE remains NOT AUTHORIZED;
- synthetic SHADOW evidence remains `SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE` and cannot satisfy real-host milestones 102–110.

The historical V11.2 reference remains frozen and is not changed by these execution-preparation contracts.
