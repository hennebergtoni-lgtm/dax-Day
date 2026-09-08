# V6 Research Evidence Boundaries

Status: BINDING RESEARCH CONTRACT

## Purpose
Keep hypothesis generation, parameter selection, OOS evaluation and diagnostics separate so that evidence strength is not overstated.

## Evidence zones

### 1. Predeclared / independent
A hypothesis, feature definition, threshold or interaction is fixed before observing its evaluation sample.
- strongest research provenance class before prospective testing;
- may proceed to OOS/WF if causal and sufficiently specified;
- public ideas may inspire a hypothesis, but donor performance is not DAX evidence.

### 2. Train-only derived
A threshold or bin boundary may be estimated from the training slice only.
- allowed inside each WF when recomputed strictly from that WF's training data;
- must never use future OOS observations;
- must record the derivation rule, not just the resulting number.

### 3. OOS result
OOS is evaluation evidence, not a parameter-development surface.
- metrics may be read and retained;
- OOS must not be used to tune a threshold and then be counted again as independent proof for that same threshold.

### 4. Diagnostic-derived
A pattern, threshold, filter or interaction discovered by inspecting OOS/aggregate diagnostics is a NEW hypothesis.
- label it `OOS_DIAGNOSTIC_DERIVED`;
- it may be retained for future testing;
- it cannot promote on the same evidence that generated it;
- it requires fresh independent/prospective evidence or a previously untouched holdout.

### 5. Prospective / untouched
Evidence from a future or previously untouched sample under a frozen definition.
- strongest validation class in the Research Lab;
- still does not auto-promote into Paper/Live.

## Walk-forward rule
For every WF window:
1. define/derive parameters from training only;
2. freeze them for that window;
3. evaluate OOS once;
4. retain the result without feeding that OOS back into the same window;
5. if diagnostics create a new hypothesis, record it separately for later independent validation.

## Interaction rule
An interaction is not independent evidence merely because each component existed previously. If the pairwise rule or threshold was chosen after seeing joint OOS diagnostics, the interaction is diagnostic-derived and requires fresh validation.

## Negative evidence rule
Rejected or non-improving hypotheses remain recorded. A negative result may be revisited only when the definition, data regime or causal argument materially changes; otherwise repeated testing is parameter fishing.

## Promotion rule
No combination of historical OOS/WF metrics alone creates automatic deployability. Research status, evidence provenance and readiness gates remain separate from bot promotion.
