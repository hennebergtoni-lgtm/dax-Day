# EXIT001 — Descriptive Run 2026-09-08

Status: RESEARCH ONLY / POST-TRADE DIAGNOSTIC / NOT SELECTOR PROOF.

## Scope
All 856 reproduced clean-reference normal-cost OOS trades were analyzed after trade completion only. MFE/MAE and holding-time fields are explicitly forbidden from pre-entry decision logic.

## Descriptive summary
- median holding time: 65 minutes
- median MFE: 0.9112R
- median MAE: 1.0313R

Exit reasons:
- stop: 468 trades, -472.2307R, median MFE 0.4451R, median MAE 1.1439R, median hold 45 minutes
- target: 245 trades, +437.2301R, median MFE 2.1009R, median MAE 0.3496R, median hold 70 minutes
- session_close: 121 trades, +23.4354R, median MFE 0.9641R, median MAE 0.5769R, median hold 460 minutes
- gap_stop: 18 trades, -24.1696R
- gap_target: 3 trades, +5.4353R
- stop_and_target_same_bar: 1 trade, -1.0097R

## Binding interpretation
The ledger shows substantial favorable excursion in several trades that later exit by stop or session close, which makes trailing/swing/ATR exit research reasonable as a fresh hypothesis. It does NOT prove that any specific trailing rule would improve results because MFE/MAE are hindsight diagnostics. No exit rule is promoted from this run.

## Next valid work
Predeclare a very small exit family (fixed stop baseline vs ATR trailing vs confirmed-swing trailing vs bounded combination), implement it causally, then evaluate exact OOS/WF and cost/stability evidence. No threshold mining from MFE/MAE distributions.
