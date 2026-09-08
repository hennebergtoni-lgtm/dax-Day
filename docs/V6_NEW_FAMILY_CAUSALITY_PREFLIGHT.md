# V6 New-Family Causality Preflight

Status: PRELIMINARY PASS / NO PROFITABILITY CLAIMS

Reviewed families: ATR001, LIQ001, STRUCT001, MOM001, SESSION001, ENTRY001, EXIT001.

## ATR001
PASS at specification level.
- ATR inputs must be completed before decision.
- OR/ATR only after OR completion.
- train-only boundaries required for adaptive bins.
Main risk: full-sample quantile leakage.

## LIQ001
PASS at specification level.
- reference level must pre-exist sweep.
- wick rejection known only at sweep candle close.
- break/reclaim known only at reclaim close.
Main risk: hindsight swing/pivot levels and backdated confirmation.

## STRUCT001
PASS at specification level.
- structure state becomes valid only at actual confirmation time.
Main risk: pivot/BOS labels backdated to turning candle.

## MOM001
PASS at specification level.
- only completed bars before entry.
Main risk: using same-entry-bar close/body for next-open semantics incorrectly.

## SESSION001
PASS at specification level.
- clock/session fields known causally.
- statistics associated with buckets still need train-only provenance.
Main risk: minute-level overfitting rather than timestamp leakage.

## ENTRY001
PASS as diagnostics only.
- current V11.2 next-open entry remains frozen.
- discovered timing/distance thresholds are diagnostic-derived until fresh validation.
Main risk: converting hindsight entry-quality diagnostics directly into rules.

## EXIT001
PASS as diagnostics only.
- MFE/MAE and residual excursion are outcome diagnostics, not causal exit inputs.
Main risk: designing exits from future excursion then claiming same-sample validation.

## Global blocked patterns
- future-confirmed pivots backdated to historical timestamp
- same-bar information unavailable at entry open
- global/full-sample quantiles treated as ex-ante thresholds
- outcome fields such as eventual gap close, MFE or MAE used retrospectively at entry
- OOS-discovered threshold validated on the same OOS sample

## Preflight conclusion
All seven families may proceed to feature-generation/testing under the V6 contracts. This is a specification-level causality pass only. Each implementation still requires automated no-lookahead/property tests and exact spot checks before its numerical results count as research evidence.
