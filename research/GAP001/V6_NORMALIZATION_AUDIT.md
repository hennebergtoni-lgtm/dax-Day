# GAP001 V6 Normalization Audit

Status: RESEARCH / PLAN-ONLY / NO PROMOTION

## Canonical definition
Opening gap = current Europe/Berlin session open minus previous completed session close.

This family is explicitly distinct from intraday FVG/displacement/imbalance research.

## Causal features eligible at/after session open
- signed gap points
- absolute gap points
- gap direction
- gap / ATR14 using only prior-known ATR inputs
- gap / prior-day range using completed prior-day data
- previous close relative to current OR only once the relevant OR state is causally available

## Diagnostic-only unless known before decision
- whether the gap eventually closes
- time of eventual gap close
- maximum later excursion toward/away from the close

These later outcomes may describe regimes but cannot be used retrospectively as entry-time features.

## First fixed hypotheses
1. gap direction may condition long/short setup quality;
2. normalized gap magnitude may identify materially different OR/retest regimes;
3. very large opening gaps may change the value of prior-close/OR context;
4. no assumption that a gap must fill.

## Parameter discipline
- no dense gap-size grid;
- use coarse fixed hypotheses or per-WF train-only boundaries;
- any threshold discovered from OOS diagnostics becomes a new hypothesis requiring fresh validation.

## Interaction discipline
Isolated GAP001 evidence precedes interaction with OR/retest, BB001, FIB001 or future FVG research.

## V6 state
- evidence maturity: PLAN_ONLY
- causality: SPECIFIED
- promotion_allowed: false
- next evidence: feature-generation audit + broad-era descriptive distribution.
