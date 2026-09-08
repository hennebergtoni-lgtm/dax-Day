# V6 Screening and Stability Contract

Status: BINDING RESEARCH CONTRACT

## Step 32 — Exact spot-check requirement
Every accelerated/vectorized family must be checked against the exact/non-accelerated implementation on deterministic samples spanning multiple eras. Zero semantic mismatches are required before accelerated results count as research evidence. A family without an exact comparator remains descriptive/engineering-only.

## Step 33 — Minimum trade-count / stability reporting
No fixed universal cutoff is treated as magic. Every result must report trade count, active WF count, positive/negative WF count, broad-era concentration and a low-sample warning. Sparse results can be retained as hypotheses but cannot be promoted on PF alone.

## Step 34 — WF/OOS stability table
Each material hypothesis must report, at minimum:
- total 81-WF coverage or explicit reason for smaller scope
- active WF count
- positive / negative / flat WF count
- median WF PF
- broad-era thirds (WF1–27, 28–54, 55–81) or equivalent dated eras
- trade count and Return-R per era
- concentration warning when one era dominates the result

## Step 35 — Friction stress
Any hypothesis that changes trade selection or execution must report normal, 1.5x and 2x costs using the frozen V11.2 cost definitions. A candidate that only survives the normal model is not considered robust.

## Step 36 — Single-family screening order
1. feature-generation and causality
2. descriptive distribution
3. fixed/predeclared hypothesis
4. OOS/WF stability
5. cost stress
6. neighbourhood / adjacent-bin robustness
7. conditional incremental-information check
8. retain/reject/fresh-validation decision

## Step 37 — Interaction order
Pairwise interaction is allowed only after both components have defensible isolated evidence. Higher-order combinations require explicit rationale and fresh validation. No all-family Cartesian grid.

## Step 38 — Selection-bias warning
Any threshold or interaction discovered from OOS/aggregate diagnostics is labeled `OOS_DIAGNOSTIC_DERIVED`. It may generate the next hypothesis but cannot validate itself on the same sample.

## Step 39 — No-trade impact
Every exclusion/filter result reports:
- baseline trades
- retained trades
- excluded trades
- no-trade increase
- Return-R/PF delta
- whether the improvement comes from removing losses, removing winners, or both
A lower trade count is neither automatically good nor bad.

## Step 40 — Negative-result retention
Rejected, neutral and unstable hypotheses remain versioned with definition, evidence scope and reason for rejection. A failed branch is not retested unless there is a material change in definition, data regime, causal implementation or genuinely new independent evidence.

## Global interpretation
Headline PF or Return-R never overrides causality, sample size, stability, cost stress or provenance. Simpler evidence with broad stability is preferred over a more complex rule with narrow historical gains.
