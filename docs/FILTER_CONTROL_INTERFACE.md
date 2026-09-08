# Filter Control Interface Contract

Status: architecture contract, not live trading implementation.

## Goal
Expose researched strategy components as modular, explainable capabilities without allowing the UI to bypass evidence, execution, or risk gates.

## UI states per filter
Each filter card exposes:
- key and human-readable label
- evidence status: research / validated / deployable
- current mode: visible-only / manual / regime-automatic
- enabled state when the current mode permits it
- current regime relevance
- short reason: why suggested / why not suggested
- provenance: experiment/module/version
- last validation reference

## Permission model
### RESEARCH
- visible in research/operator UI
- may show current value and historical evidence
- may be suggested as an experiment
- cannot change trade eligibility in live/demo execution
- no manual or automatic live switch

### VALIDATED
- may become manually selectable in demo/restricted operator mode after explicit promotion artifact
- cannot be regime-automatic yet

### DEPLOYABLE
- may be enabled manually if the release policy allows it
- may participate in regime-automatic switching only if a separate regime-map validation exists

## Auto-regime principle
The system may select only among explicitly deployable configurations. It must not invent new thresholds, combine unvalidated filters, or optimize against current live outcomes.

Decision chain:
`market regime -> DAX structure -> validated context -> eligible deployable filters -> setup/entry -> bounded risk`

## Hard boundaries
The following controls are never bypassable by filter switches:
- per-trade risk limit
- daily loss limit
- maximum exposure
- session/trading-state gate
- emergency stop
- data-integrity/no-lookahead gate
- execution/broker health gate

## Current BB001 status
BB001 is a RESEARCH_TOOL only. The interface may display causal M5/HTF Bollinger state, PrevRange/ATR context, and research suggestions, but none of these may alter live/demo order eligibility until promoted through the evidence gates.

## Operator explanation example
`Regime: breakout/retest, prior day extended. BB001 is relevant as a researched quality annotation, but remains observe-only because independent validation is incomplete.`
