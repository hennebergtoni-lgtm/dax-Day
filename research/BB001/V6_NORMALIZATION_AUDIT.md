# BB001 V6 Normalization Audit

Status: RETAINED RESEARCH SIGNAL / NO PROMOTION

## Historical preservation
Existing BB001 manifests and result artifacts are retained unchanged. V6 does not rewrite historical evidence. Older pilot alignment issues and same-entry-bar interpretations remain part of provenance but are superseded for strategy conclusions by later causal artifacts where explicitly stated.

## Current causal basis
- 856/856 baseline OOS trades aligned to the last fully completed M5 bar strictly before entry time.
- 0 missing, 0 ambiguous.
- all state times strictly before entry.
- unique lag: 5 minutes.

## Provenance classification
- same-entry-bar Bollinger interpretations: non-causal for current V11.2 entry semantics; not valid strategy evidence.
- full-sample/descriptive bandwidth Q1 or global OOS median thresholds: `OOS_DIAGNOSTIC_DERIVED` / descriptive-derived; not independent promotion proof.
- directional prior-bar position hypothesis: retained research signal, but historical evidence alone is not prospective confirmation.
- train-only/per-WF derived thresholds: eligible research mechanism when recalculated strictly inside each training slice.

## Retained findings
- prior-bar directional position can improve aggregate selection quality.
- causal retest branch survived exact normal/1.5x/2x cost stress in the tested candidate.
- Bollinger appears more useful as a secondary quality/regime selector than as a standalone strategy.

## Negative / limiting findings
- same-entry-bar state is non-causal.
- bandwidth-only filtering is not temporally stable by itself.
- combined filters can look strong in aggregate while failing materially in the middle WF era.
- completed 15m above-mid did not improve the retained candidate.
- completed 15m position >= 0.75 reduced the retained candidate PF.
- tight retest timing is not justified.
- extra OR/ATR threshold is not stable enough to add.
- current strong cost-stressed candidate still uses an evaluation-derived bandwidth cutoff and therefore requires a fresh ex-ante or per-WF-train-only definition before stronger validation.

## V6 state
- family: BB001
- status: RESEARCH / RETAINED SIGNAL
- evidence maturity: COST_STRESSED
- causality: PASS
- promotion_allowed: false
- next valid evidence: fresh validation of a fixed ex-ante or per-WF-train-only Bollinger rule; no threshold optimization on the historical OOS surface.
