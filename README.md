# DAX Daytrading Research Lab

Central source of truth for the DAX intraday research and trading-system project.

## Three-layer architecture
1. **Bot / Strategy Core** — deterministic strategy and execution semantics; V11.2 remains frozen as the reference baseline.
2. **Data Layer / Research Database** — validated historical data, feature/cache contracts, experiment metadata and reproducible results.
3. **Research & Test Lab** — isolated hypotheses, walk-forward/OOS, cost stress, robustness, no-lookahead and overfitting gates.

GitHub is the central code/version-control layer. Large historical datasets belong in reproducible data/object storage rather than being duplicated through notebooks. Google Drive may remain backup/document storage, but it is no longer the development architecture.

## Binding baseline
- Historical research period: 2014–2019
- 1,673 valid Europe/Berlin session days
- 172,319 M1 candles
- 103 M5 research bars/day
- Session: 09:00–17:30 Europe/Berlin
- 0 known OHLC integrity errors in the audited basis
- V11.2: 144 frozen variants
- Walk-forward: 81 windows; Train 45 days / OOS 20 days / Step 20 days
- Full V11.2 OOS: 1,384 trades; -68.1095R; 36 positive / 45 negative WFs
- Exact/FAST parity validated on the established surface
- Exact engine SHA256: `9561b9089c57c543798dc587ce240a729b7995230dd5d665a1bdd029f3990887`

## Research evidence retained
Current clues are research evidence, not automatic strategy promotion:
- OR15 stronger than OR5 in aggregate
- Retest slightly stronger than breakout
- OR-mid stop stronger than OR-opposite
- RR 1.5 often stronger than RR 2.0
- OR/ATR filtering is the strongest current structural clue
- V2.8.21 produced multiple stress-positive candidates, led by V47/V48; all remain research candidates

## Research backlog
High priority: Bollinger Bands, Fibonacci retracement, close gaps, volatility filters, entry/exit logic. Medium priority: time/session and other market-structure filters.

## Promotion pipeline
`IDEA -> RESEARCH -> PILOT -> VALIDATED TOOL -> COMBINATION TEST -> CANDIDATE BOT -> WF/OOS -> NEW BOT VERSION`

No single WF, ranking result or attractive equity curve can bypass this pipeline.

## Open-source policy
We actively study and reuse useful **licensed** architecture and methodology from public projects rather than rebuilding solved infrastructure unnecessarily. Unlicensed repositories may inspire independently implemented hypotheses, but their source code is not copied. See `docs/OPEN_SOURCE_AUDIT.md`.

## Security
This repository is public. Never commit broker credentials, API keys, tokens, account IDs, passwords, private licensed market data or other secrets.

## Immediate engineering milestone
Build the durable repository skeleton and validation contracts first. Then import/reconstruct the proven V11.2 reference interfaces behind parity tests. Only after parity is green does BB-001 become the first isolated tool experiment.
