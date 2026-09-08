# V6 Findings and Next Evidence-Producing Run

Status: V6 CLOSURE CANDIDATE / PAPER-LIVE BLOCKED

## Consolidated findings
- V11.2 remains immutable and fully reproducible under the canonical rolling-fixed 45/20/20 reference path.
- Existing research families are normalized without rewriting historical artifacts.
- BB001 retains a causal, cost-stressed research signal, but evaluation-derived thresholds are not independent promotion proof.
- FIB001 now has an explicit causal anchor contract; the math core remains intentionally simple and does not discover swings.
- GAP001 remains opening-gap research only and is explicitly separated from intraday FVG.
- FAIL001 remains a guardrail/control-objective taxonomy and must not duplicate runtime enforcement.
- BOOST001 remains downstream sizing/risk simulation and cannot alter signal semantics.
- ATR001, LIQ001, STRUCT001, MOM001, SESSION001, ENTRY001 and EXIT001 have isolated V6 specifications and a specification-level causality preflight.
- Research-family registry, common result schema, evidence-boundary contract, timestamp contract, interaction budget, screening/stability contract and recovery contract are now explicit.
- Web observability is bound to the canonical research registry and remains read-only.
- Productive DB import state remains separate from research evidence quality.
- Duplicate recovery implementations remain a compatibility-first migration candidate; no deletion is authorized yet.

## Next evidence-producing run
The next Research Lab run is **FIB001 causal anchor-generation pilot**, not a Paper/Live stage.

### Scope
1. implement or exercise causal anchor generation using already-known levels/confirmed-breakout structure only;
2. prove `anchor_confirmation_time < retracement_observation_time <= entry_time` for eligible observations;
3. run prefix-stability / future-pollution tests where applicable;
4. produce descriptive retracement-depth distribution across the audited 2014–2019 surface;
5. do not optimize zones or select a profitability threshold in this first run;
6. retain fixed natural zones 33.3–38.2, 38.2–50, 50–61.8, 61.8–66.7 for later predeclared testing;
7. no BB/GAP/ATR interaction until isolated FIB evidence is complete.

## Why FIB001 first
- feature math and tests already exist;
- the main unresolved risk is causal anchor construction, which can be tested cleanly before profitability selection;
- this produces new evidence without mutating V11.2 or multiplying grid dimensions;
- it is the smallest next step with high information value.

## Explicit non-starts
- no Shadow start
- no Paper start
- no Live start
- no V11.2 mutation
- no automatic promotion of any research family
