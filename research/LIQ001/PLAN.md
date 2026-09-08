# LIQ001 — Causal Liquidity Sweep Research Plan

Status: RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Research question
Do causally confirmed sweeps of pre-existing liquidity/reference levels improve DAX setup selection, especially around OR/retest structures?

## Core definition
A liquidity sweep requires:
1. a reference level that existed before the sweep bar;
2. price trades beyond that level;
3. a predeclared confirmation rule showing rejection/reclaim or failure to continue;
4. all information required for classification available before any entry decision using the sweep.

## Allowed reference levels
Initial isolated families are limited to levels known in advance:
- previous session high/low
- previous session close
- completed opening-range high/low
- other previously completed session/reference levels only if declared before testing

## Pivot restriction
Hindsight swing highs/lows are not valid initial reference levels. A pivot requiring future bars for confirmation may only become usable at its actual later confirmation time.

## First confirmation variants
Keep the first pilot coarse:
- wick beyond known level + completed-bar close back inside
- completed-bar close beyond level followed by completed reclaim before entry

These are separate hypotheses, not one flexible rule chosen after results.

## Required evidence fields
- reference_level_id
- reference_price
- reference_known_time
- sweep_bar_time
- extreme_price
- reclaim_confirmation_time
- direction
- excursion_points
- causality_pass
- entry_time when linked to a V11.2 setup

## Evaluation order
1. causal feature-generation tests;
2. descriptive incidence by level/direction/era;
3. isolated fixed confirmation hypotheses;
4. OOS/WF stability and trade-count impact;
5. cost stress if selection changes;
6. pairwise interaction only after isolated evidence.

## Non-goals
- no hindsight pivot mining
- no dense wick-size grid
- no automatic ICT/FVG assumptions
- no claim that every sweep reverses
- no automatic strategy promotion
