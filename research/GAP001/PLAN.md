# GAP001 — Opening Gap Research Plan

Status: RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Research question
Does the DAX opening gap provide useful causal context for OR/retest quality, direction, or trade exclusion on the audited 2014–2019 session dataset?

## Scope
Opening gap means current Berlin-session open relative to the previous session close. It is distinct from intraday Fair Value Gaps (FVG).

## Public-project intelligence retained
- Separate opening-gap context from intraday displacement/FVG logic.
- Measure gap size, direction, normalized size, and gap-close behaviour before building strategy rules.
- Treat gap-aware fills and non-tradable close-to-open effects carefully.

## Feature set
- signed gap points
- absolute gap points
- up / down / flat
- gap / ATR14
- gap / prior-day range
- previous close inside/outside current OR context
- gap-close occurrence and time, for descriptive analysis only unless causally available before decision time

## Evaluation order
1. Data/feature audit and causality checks.
2. Distribution by broad era and direction.
3. Isolated fixed hypotheses for setup eligibility.
4. OOS/WF stability.
5. Cost stress if execution/trade selection changes.
6. Only then test interaction with OR/retest, BB001 or FIB001.

## Separate later family
Intraday FVG/displacement-retest remains a distinct future hypothesis and must not be mixed into GAP001 results.

## Non-goals
- no assumption that gaps must fill
- no hindsight use of gap-close information at entry
- no large threshold grid
- no automatic strategy promotion
