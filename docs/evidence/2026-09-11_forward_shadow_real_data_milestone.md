# Forward SHADOW real-data milestone — 2026-09-11

Status: **VERIFIED** for the stated read-only forward observations.  
Scope: **SHADOW / NO_ORDER / execution_capability=NONE**.  
Profitability: **NOT PROVEN**.  
Paper trading: **NOT AUTHORIZED**.  
Live trading: **NOT AUTHORIZED**.

## What was verified

As of `2026-09-11T07:15:42.139224Z`, the DE40 MT5 SHADOW pipeline was GREEN and processing real closed M5 broker bars.

Latest heartbeat:

- `status=GREEN`
- `closed_m5_bars=40`
- `single_instance_lock_held=true`
- `processed_total=342`
- `cross_cycle_status=GREEN`
- `cross_cycle_overlapping_bars=39`
- `cross_cycle_identical_overlaps=39`
- `cross_cycle_mutated_overlaps=0`
- `blockers=[]`
- `history_archive_status=OK`
- `execution_capability=NONE`
- `order_execution_enabled=false`

## First Berlin-session data block

Session start used for this integrity check: `09:00 Europe/Berlin = 07:00 UTC` on 2026-09-11.

Three closed M5 session bars were present at capture time:

- 07:00 UTC
- 07:05 UTC
- 07:10 UTC

Integrity results:

- duplicate open timestamps: `0`
- OHLC violations: `0`
- non-5-minute gaps: `0`
- safety violations: `0`
- distinct bar fingerprints: `3/3`

## Real bar -> SHADOW decision linkage

Four sequential closed bars were checked against SHADOW decisions. Every decision:

- referenced `V112_REFERENCE_V1`
- referenced engine SHA256 `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`
- matched its closed bar fingerprint
- used `action=NO_ORDER`
- used `execution_capability=NONE`
- used `order_execution_enabled=false`
- recorded broker timezone `Europe/Helsinki`
- recorded timestamp interpretation `EXPLICIT_BROKER_WALL_CLOCK`

This verifies the narrow claim that real closed broker M5 bars are reaching the SHADOW path and are being deterministically linked to observation-only V11.2-reference decisions while execution remains disabled.

## Mini-test #1 — exploratory only

This is **RESEARCH**, not a strategy test and not evidence of profitability.

First 15 minutes of the Berlin session, using the three closed M5 bars from 09:00 through 09:15 local time:

- high: `25497.6`
- low: `25437.1`
- range: `60.5` points
- first open: `25461.1`
- last close: `25453.1`
- net move: `-8.0` points
- bullish bars: `2`
- bearish bars: `1`
- next two bars broke first-bar high: `false`
- next two bars broke first-bar low: `true`

No OR5/OR15 strategy semantics are inferred from this probe. The frozen V11.2 strategy definition remains unchanged and must be verified separately from repository code/tests before any strategy-specific live interpretation.

## Evidence files

Machine-readable companion snapshot:

`docs/evidence/2026-09-11_forward_shadow_real_data_milestone.json`
