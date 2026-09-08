# LIQ001 V6 Sweep Confirmation Contract

Status: BINDING RESEARCH SPEC

## Variant A — Wick rejection
A known reference level is exceeded intrabar and the completed sweep candle closes back on the pre-sweep side of the level.

Required timing:
- reference_known_time < sweep_bar_close_time
- sweep state becomes known only at sweep_bar_close_time
- any entry using this state must occur after that close

## Variant B — Break then reclaim
A completed candle closes beyond the known reference level. A later completed candle reclaims the level. The sweep/reclaim state becomes known only at the reclaim candle close.

Required timing:
- reference_known_time < break_close_time < reclaim_close_time < entry_time

## Separation rule
Variant A and Variant B remain separate hypotheses. Results may not be combined after evaluation simply because one definition performs better in one era and the other in another.

## Direction
- sweep above resistance/high-side liquidity and reclaim downward = high-side sweep candidate
- sweep below support/low-side liquidity and reclaim upward = low-side sweep candidate

No reversal assumption is embedded. Directional outcome is evaluated separately.

## Optional descriptive fields
- overshoot points
- overshoot / ATR
- bars-to-reclaim
- later MFE/MAE

Overshoot or timing thresholds discovered from OOS diagnostics become new hypotheses and require fresh validation.

## Fail-closed cases
- reference level not known before sweep
- reference timestamp missing
- pivot level backdated from future confirmation
- reclaim only known after entry
- ambiguous bar ordering
- same-bar fill semantics that cannot be resolved conservatively
