# NextGen Broker Economics → Risk Inputs Binding V1

Status: **STEP-2159 PRODUCT / READ-ONLY ADAPTER CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Translate externally verified, normalized broker-symbol economics into canonical NextGen `InstrumentRiskInputs` without promoting research policy, changing strategy semantics, or adding any venue execution capability.

## Reuse / mapping decision

Existing owners remain authoritative:

- `runtime.mt5_readonly.BrokerSymbol` — normalized read-only venue metadata;
- `runtime.broker_economics_readiness.assess_broker_economics()` — completeness/readiness classification;
- `research.broker_risk_sizing` — research evidence for the conservative tick-value sizing equation;
- `domain.risk.InstrumentRiskInputs` — canonical product sizing economics.

Step 2159 adds only `runtime.nextgen_broker_economics.bind_verified_broker_economics_to_risk_inputs()`.

## Economics mapping

For a FULL-trading broker symbol with externally verified economics:

`cash_loss_per_price_unit_per_quantity = risk_tick_value / tick_size`

where `risk_tick_value` is the existing conservative broker-economics readiness value.

Canonical quantity inputs map from broker `volume_min`, `volume_step` and `volume_max`. A positive `volume_limit`, when present, conservatively caps canonical `quantity_max`.

`currency_profit` becomes the canonical risk currency because tick-value cash loss is denominated in profit currency.

## Identity rule

Canonical product identity and broker routing identity remain separate:

- canonical identity: `InstrumentId`, e.g. `DAX40.CFD`;
- broker symbol: venue-specific evidence, e.g. `DE40`.

The binding evidence records both and fingerprints the broker economics used. It never replaces canonical instrument identity with the venue symbol.

## Fail-closed rules

Binding is rejected when:

- external broker-economics verification is false;
- trade mode is not `FULL`;
- readiness reports incomplete economics;
- required numeric economics are non-finite or non-positive;
- profit currency is missing/malformed;
- a supplied volume limit is invalid;
- resulting min/max quantities violate canonical quantity-step alignment.

## Parity proof

Tests verify that the same explicit broker economics produce the same conservative quantity under the existing research sizing equation and canonical Risk V1 fixed-cash sizing. This is semantics parity, not automatic promotion of any BASE/BOOST/HIGH research risk profile.

## Current host/demo evidence note

The manual MetaQuotes-Demo plumbing test performed on 2026-09-12 does **not** set `broker_economics_verified=true` for the bot. The observed `DE40` symbol had trading disabled, while the tradeable MetaQuotes `DAX` symbol had materially different price/instrument characteristics. Therefore neither observation is silently promoted into canonical DAX broker economics.

## Safety boundary

- read-only normalized evidence only;
- no MT5 SDK import in the binding owner;
- no account balance lookup;
- no order submission;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- PAPER/demo broker execution not authorized;
- LIVE not authorized.
