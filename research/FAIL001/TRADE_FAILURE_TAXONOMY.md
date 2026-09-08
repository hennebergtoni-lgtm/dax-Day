# FAIL001 — Trade failure taxonomy

Status: RESEARCH CONTRACT

Negative outcomes are evidence, not rows to discard.

## Unit of analysis
Every completed trade, blocked setup and NO_TRADE observation may be assigned zero or more causal tags. Tags describe observable conditions; they must not be invented from hindsight.

## Primary tags
- DATA_UNSAFE
- REGIME_MISMATCH
- STRUCTURE_WEAK
- FALSE_BREAKOUT
- RETEST_FAILED
- STOP_TOO_TIGHT_CANDIDATE
- TARGET_TOO_FAR_CANDIDATE
- COST_SENSITIVE
- ADVERSE_GAP
- VOLATILITY_SHOCK
- LOW_VOL_CHOP
- LATE_SESSION
- EXECUTION_DEGRADED
- FILTER_FALSE_POSITIVE
- FILTER_FALSE_NEGATIVE
- NO_TRADE_CORRECT
- NO_TRADE_MISSED_WINNER
- UNCLASSIFIED

## Required context
Where available, retain: experiment/version, WF, trade date/time, side, normalized R, MFE-R, MAE-R, regime, OR duration/range, ATR context, previous-range context, entry/stop/RR, enabled research annotations, cost model, exit reason and causal-data timestamp.

## Anti-hindsight rule
A tag is descriptive unless a predeclared hypothesis says otherwise. A losing trade does not prove its filter was wrong; a winning trade does not validate its setup. Candidate causes are tested on independent samples.

## Analysis views
1. loss concentration by regime/structure
2. MFE before stop-out
3. MAE before winners
4. cost-sensitive flips
5. false-breakout vs failed-retest clusters
6. time/session concentration
7. OR/ATR and previous-range interaction
8. NO_TRADE opportunity-cost and protection value
9. consecutive-loss and drawdown episodes
10. differences between train, OOS and stress

## Promotion rule
A failure pattern can create a new research hypothesis, never an immediate live filter. It enters the normal research pipeline and must survive OOS/WF and stress gates.
