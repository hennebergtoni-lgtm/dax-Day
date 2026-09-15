# NextGen Session Observation Checkpoint V1

Status: **STEP-2172 PRODUCT CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Persist exact canonical `SessionAdmissionObservation` evidence across restart without deriving any session semantics.

## Contract

`SessionAdmissionObservationCheckpoint` binds:

- exact session policy fingerprint;
- exact canonical session observation;
- caller-supplied timezone-aware `observed_at`, normalized to UTC;
- deterministic checkpoint fingerprint;
- `execution_capability=NONE`;
- `order_execution_enabled=false`.

The checkpoint supports strict deterministic UTF-8 JSON bytes roundtrip, save/load through existing `StateStorePort`, and explicit policy compatibility checking.

## Not owned here

This owner does not derive session keys, dates, timezones, calendars, reset transitions or admitted-trade changes. It does not read broker/account state and cannot authorize PAPER or LIVE execution.

Freshness evaluation is deliberately separate and must use explicit evaluation time and maximum age before typed protection trusts restored evidence.
