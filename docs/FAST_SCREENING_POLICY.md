# FAST screening policy

Status: IMPLEMENTED RESEARCH POLICY

## Purpose
FAST execution is a research accelerator only. It may reduce the number of exact evaluations, but it may not change the frozen V11.2 semantics or replace exact-parity evidence.

## Allowed uses
- rank or shortlist research candidates;
- eliminate clearly weak parameter neighborhoods;
- run cheap sensitivity checks;
- target a smaller set of exact OOS/WF evaluations;
- estimate whether a hypothesis is worth a full exact run.

## Forbidden uses
- declaring a new validated tool from FAST-only evidence;
- changing the active V11.2 reference;
- promoting a filter, strategy or risk rule directly to paper/live;
- accepting a candidate when FAST and exact results materially disagree;
- changing exact-engine semantics merely to improve FAST agreement.

## Required promotion path
FAST SCREENING -> EXACT ENGINE/PARITY -> OOS/WF -> COST STRESS -> STABILITY/NEIGHBORHOOD -> PROSPECTIVE VALIDATION.

Any material FAST/exact mismatch is a STOP condition. The mismatch must be explained before the candidate can advance.

## Runtime principle
Research speed is subordinate to reproducibility. The exact SHA-verified engine remains the final measurement surface for reference-level claims.
