# V12 Feature Hardening — Milestones 239–240

Date: 2026-09-09
Status: IMPLEMENTED, pending PR CI verification

Four research-only OHLC candidates are implemented as causal closed-bar primitives in `src/daxlab/research/v12_prepaper_features.py`:
- ADX001: Wilder-style ADX / +DI / -DI with explicit warm-up.
- BODY001: breakout-bar body fraction, close location, and direction.
- COMP001: current true range relative to prior mean true range.
- STALE001: closed-bar age since a confirmed breakout.

Safety properties:
- Every feature is evaluated at an explicit `asof_index`.
- Bars after `asof_index` are sliced away before calculation.
- Future-bar mutation tests prove the feature value at the same as-of bar does not change.
- Same-bar or future breakout indices are rejected for staleness.
- Insufficient ADX/compression warm-up returns `None` rather than inventing a value.
- Invalid OHLC and invalid as-of indices fail closed.
- Repeated evaluation over identical input is deterministic.

These tests are engineering gates only. They do not establish profitability, OOS robustness, broker equivalence, Paper readiness, or LIVE readiness.
