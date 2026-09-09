# V12 REJECTION DISCIPLINE — MILESTONE 247

Status: IMPLEMENTED RESEARCH GOVERNANCE CONTRACT

## Purpose
Prevent descriptive/OOS-diagnostic discoveries from becoming production logic through hindsight, threshold shopping, or selective reporting.

## Binding rules
1. V11.2 remains frozen and unchanged.
2. A feature family may be screened descriptively on the frozen evidence surface.
3. Numerical cutoffs discovered after viewing results are classified `OOS_DIAGNOSTIC_DERIVED` unless they were explicitly predeclared before evaluation.
4. `OOS_DIAGNOSTIC_DERIVED` cells cannot receive `ROBUST_CANDIDATE` status from the same evidence surface.
5. No candidate becomes Paper/LIVE logic from historical screening alone.
6. Missing stress-cost parity, weak trade count, unstable years/WFs, or dependence on one narrow slice blocks promotion.

## Candidate outcomes
### REJECTED
Use when the isolated feature has no useful signal, materially worsens outcomes, is unstable, leaks future information, or cannot survive the evidence gates.

### RETAINED_RESEARCH
Use when there is a potentially useful pattern but it is diagnostic, mixed, confounded, or lacks fresh proof. This is the default state for promising hindsight-discovered cells.

### FROZEN_FOR_FRESH_TEST
Use only when a single bounded diagnostic cell is selected for one future/fresh proof test. The selected rule must be frozen before the fresh evidence is observed.

### ROBUST_CANDIDATE
Requires all of the following:
- predeclared or previously frozen rule;
- causal closed-bar computation;
- adequate trade count;
- acceptable PF/Return-R/Drawdown under normal and stress 1.5x/2x costs;
- stability across multiple years and WF epochs;
- fresh evidence not used to choose the rule;
- explicit later promotion decision.

## Current V12 interpretation
- ADX001: `RETAINED_RESEARCH`; ADX >=20 and >=40 observations are diagnostic, with mixed year effects.
- BODY001: `RETAINED_RESEARCH`; body 0.40-0.70 plus direction agreement is diagnostic and not predeclared.
- COMP001: `RETAINED_RESEARCH`; TR-ratio 1.25-2.00 is diagnostic and has negative years.
- STALE001: `RETAINED_RESEARCH`; 2-bar retest slice is interesting but mixed and stress parity is pending.

No family is promoted to `ROBUST_CANDIDATE` by milestone 247.

## Fresh-proof rule
A future fresh-proof test must freeze exactly one bounded rule per selected family before observing the fresh dataset/period. If no genuinely fresh evidence exists, the family remains research-only rather than being self-validated on the same 2014-2019 OOS surface.

## Safety
This contract contains no order capability and does not authorize Paper or LIVE execution.
