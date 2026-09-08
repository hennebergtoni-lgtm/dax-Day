# V6 DB Evidence Separation Contract

Status: BINDING RESEARCH / DATABASE CONTRACT

## Principle
Research evidence state and database import state are independent dimensions.

A result can be:
- causally valid and reproducible,
- yet still NOT_IMPORTED in the production DB.

Conversely, a row existing in the DB does not by itself make the evidence validated or deployable.

## Research evidence states
Examples:
- PLAN_ONLY
- DESCRIPTIVE
- OOS_TESTED
- WF_TESTED
- COST_STRESSED
- STABILITY_TESTED
- PROSPECTIVE_TESTED

## DB import states
- NOT_IMPORTED
- PARTIAL
- VERIFIED

## Import eligibility
A research artifact becomes import-eligible only when all required provenance, schema, row count, hashes, dataset/engine identity and idempotency rules pass.

Import eligibility does not imply strategy promotion.

## Promotion separation
The following are forbidden shortcuts:
- `VERIFIED` DB row => automatically deployable tool
- positive OOS/WF result => automatically import to active reference
- new reproducible hash => silently replace a historical expected hash
- database presence => evidence independence

## V11.2 binding
V11.2 active-reference aggregate remains immutable. Research-family rows, if later imported, must stay explicitly separated from active-reference truth unless a future explicit promotion process says otherwise.

## Operational display
Web/UI should show both dimensions separately, for example:
- Evidence: COST_STRESSED
- DB: NOT_IMPORTED

This avoids treating storage state as research quality or vice versa.
