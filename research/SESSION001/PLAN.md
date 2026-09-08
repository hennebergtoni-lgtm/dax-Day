# SESSION001 — Session / Time Context Research Plan

Status: RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Research question
Does coarse, causally known session timing explain stable differences in V11.2 setup quality without creating a minute-by-minute overfit grid?

## Initial context families
- early / middle / late session coarse buckets
- minutes since Berlin session open
- minutes since OR completion
- day-of-week only as a descriptive/context variable unless predeclared for testing
- proximity to session close where relevant for trade management diagnostics

## Parameter discipline
- no 5-minute bucket optimization across the full day;
- coarse buckets must be predeclared or derived train-only;
- boundaries chosen after OOS inspection become fresh hypotheses;
- no calendar/event assumptions inside SESSION001; EVENT001 remains separate.

## Causality
Time/session fields are inherently known at decision time, but any statistics attached to a time bucket must still be derived only from allowed training information.

## Initial fixed hypotheses
1. setup quality may differ between early and later session phases;
2. retests occurring long after OR completion may behave differently from immediate retests;
3. time effects may proxy volatility or structure, so conditional contribution must be checked before stacking.

## Required reporting
- trades per bucket
- Return-R / PF / DD
- positive/negative WF coverage
- broad-era consistency
- interaction overlap with ATR001 and STRUCT001
- no-trade increase if used as exclusion

## Non-goals
- no minute-level optimization
- no weekday superstition
- no event-calendar leakage
- no automatic time-based shutdown rule
