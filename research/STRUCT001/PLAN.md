# STRUCT001 — Causal Market Structure Research Plan

Status: RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Research question
Can causally confirmed DAX market-structure state improve V11.2 setup selection or explain why some OR/retest setups fail?

## Initial structure families
- break of a previously known session/OR structure level
- higher-high / higher-low and lower-high / lower-low sequences only when their confirmation timing is explicit
- BOS-style confirmation using completed candles
- compression vs expansion around completed structure levels

## Causality rule
A structure label becomes available only when the rule that proves it has completed. If a pivot needs future bars, its usable state time is the confirmation time, not the turning-bar timestamp.

## Initial fixed hypotheses
1. retest quality differs when entry direction agrees with causally confirmed structure;
2. failed structure continuation may identify poor breakout follow-through;
3. structure state may overlap with momentum and volatility, so incremental contribution must be measured before stacking.

## Required evidence fields
- structure_rule_id
- reference_level
- reference_known_time
- confirmation_time
- direction
- state_label
- source_timeframe
- entry_time when linked to a setup
- causality_pass

## Evaluation order
1. no-lookahead property tests;
2. descriptive distribution;
3. fixed isolated hypotheses;
4. WF/OOS stability;
5. cost stress when trade selection changes;
6. conditional/incremental tests against MOM001 and ATR001 before any combination.

## Non-goals
- no hindsight zig-zag optimization
- no visual/manual structure relabeling
- no dense pivot-length sweep
- no automatic trend regime switch
