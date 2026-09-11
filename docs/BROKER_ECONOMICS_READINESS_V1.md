# Broker Economics Readiness V1

Status: IMPLEMENTED READ-ONLY CONTRACT / REAL DE40 VALUES WAITING_EXTERNAL / NO PAPER OR LIVE AUTHORIZATION
Updated: 2026-09-11

## Purpose

Define the minimum broker-symbol evidence required before a separate future demo-sizing research step may begin.

This contract does **not**:
- calculate lots/contracts/order quantity;
- inspect or allocate account balance;
- define account risk percentage;
- authorize PAPER/demo execution;
- authorize LIVE execution;
- call an order API.

The current CAND-001 sizing policy remains `NORMALIZED_SIMULATION_UNIT` with quantity `1.0` and explicitly has no broker-volume or account-risk semantics.

## Existing read-only evidence owner

The existing Windows MT5 probe remains the source. No second broker adapter is introduced.

`BrokerSymbol` / probe evidence can carry:
- broker symbol;
- digits / point;
- trade mode;
- contract size;
- volume minimum;
- volume step;
- volume maximum;
- volume limit when supplied;
- tick size;
- generic tick value;
- profit tick value;
- loss tick value;
- profit currency;
- margin currency;
- initial margin metadata;
- maintenance margin metadata.

All values are observations only. A field being present does not make it valid for sizing.

## Readiness owner

`src/daxlab/runtime/broker_economics_readiness.py`

The pure function `assess_broker_economics()` classifies one resolved `BrokerSymbol` as:
- `READY_FOR_SIZING_RESEARCH`; or
- `INCOMPLETE` with explicit blockers.

The result always preserves:
- `execution_capability=NONE`;
- `order_execution_enabled=false`.

## Minimum positive evidence

Sizing research cannot start unless these are positive / valid:
- contract size;
- volume minimum;
- volume step;
- volume maximum;
- tick size;
- at least one positive tick-value observation;
- non-empty profit currency;
- non-empty margin currency;
- internally consistent volume range.

For risk-side conservatism, the readiness owner selects the maximum positive value observed across loss/profit/generic tick-value fields as `risk_tick_value`. This is still evidence selection, not a final sizing formula.

## Zero / unavailable values

MT5 may expose `0` for some economics fields when the broker does not provide a meaningful value through that field.

Rules:
- zero tick value does **not** satisfy tick-value readiness;
- zero initial/maintenance margin may be retained as observation but is not interpreted as positive margin evidence;
- missing volume maximum blocks readiness;
- negative economics values are invalid at the payload boundary;
- no zero/default value may silently become a broker sizing assumption.

## Real-host evidence lane

Repository code/tests can prove parsing and fail-closed behavior, but cannot prove the user's broker-specific DE40 economics.

Current real-host dependency:
`WAITING_EXTERNAL`

Required later evidence from the current Windows/MT5 host:
1. run the updated credential-free read-only probe against resolved DE40;
2. persist the exact symbol-economics observations;
3. pass them through `assess_broker_economics()`;
4. record blockers or `READY_FOR_SIZING_RESEARCH` without enabling execution;
5. only after that design and validate a separately versioned broker-aware sizing policy.

## Promotion boundary

`READY_FOR_SIZING_RESEARCH` means only that enough venue metadata exists to research sizing semantics.

It does **not** mean:
- PAPER ready;
- demo order ready;
- execution adapter ready;
- account risk policy approved;
- profitability proven;
- LIVE eligible.

PAPER remains behind the existing acceptance and user stop-gate. LIVE remains unauthorized.
