# ATR001 — V8 OOS Diagnostic Findings

Status: RESEARCH ONLY. OOS_DIAGNOSTIC_DERIVED. NOT PROMOTION PROOF.

## Scope
This note records diagnostic findings from the reproduced clean V11.2 normal-cost OOS ledger. V11.2 remains immutable. No finding below is deployable or eligible for Paper/Live.

## Train-only regime construction
For every canonical 45/20/20 WF window, ATR and OR/ATR regime boundaries were fitted on training dates only, separately for OR5 and OR15, then frozen before application to OOS trades. 162 boundary rows were produced (81 WFs × 2 OR families). All 856 reproduced OOS trades were classified.

## Broad ATR result
ATR HIGH: 340 trades, +7.3244R, PF 1.0371. This broad effect is unstable: WF1-27 +17.1591R, WF28-54 -1.7911R, WF55-81 -8.0436R. Therefore `ATR HIGH` alone is not retained as a selector.

## Diagnostic interaction
The diagnostic cell ATR HIGH × OR/ATR MID contained 112 trades and +11.3665R, PF 1.1806. Structural split:
- OR5: 38 trades, -7.5228R, PF 0.7039.
- OR15: 74 trades, +18.8893R, PF 1.5035.

The OR15 cell was positive in all six calendar-year summaries and all three broad WF eras. Both entry modes were positive: breakout +11.7919R, retest +7.0974R.

## Anti-duplication check
The OR15 diagnostic cell exists across all frozen V11.2 OR/ATR filter labels, so it is not merely identical to one legacy filter label. However this remains an OOS diagnostic observation and cannot establish incremental causal alpha.

## Binding interpretation
`OR15 × ATR HIGH × OR/ATR MID` is retained only as an OOS-diagnostic research candidate. It MUST NOT be promoted, tuned further on the same OOS evidence, or added to V11.2. A valid next proof requires independent/prospective evidence or a predeclared fresh evaluation protocol.

## Negative control
The same ATR/OR-ATR cell under OR5 is negative and is retained as a useful structural negative control.

## Next research action
Freeze this candidate definition exactly as discovered. Stop threshold refinement. Continue other independent research families and later test the frozen candidate on genuinely new/prospective evidence. This prevents repeated mining of the same 2014-2019 OOS ledger.
