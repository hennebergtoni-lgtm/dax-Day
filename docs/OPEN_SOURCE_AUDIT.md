# Open-Source Donor Audit

Goal: benefit from existing work without importing hidden assumptions, overfit claims or code without permission.

## Strong architecture/methodology donors

### charlesbx/futures-backtester — MIT
Useful concepts:
- strategy-agnostic backtest core
- strategy plugin boundary
- grid optimization
- rolling walk-forward validation
- explicit slippage/commission
- unified CLI and modular metrics/data loader
Adoption rule: adapt architecture; retain our exact V11.2 execution semantics and 45/20/20 WF schedule.

### DaruFinance/quant-research-framework — Apache-2.0
Useful concepts:
- strict no-lookahead/property tests
- IS/OOS/WFO discipline
- robustness/stress tests
- DSR/PSR/MinTRL/MinBTL and PBO/CSCV concepts
- regime segmentation and second OOS concepts
- Python/reference parity philosophy and CI
Adoption rule: use validation methodology; do not replace the frozen V11.2 engine with an unrelated framework.

### asdtroll3/ORB-Backtester — MIT
Useful concepts:
- self-contained ORB experiment design
- per-trade outputs/reporting
- sensitivity analysis
- conservative stop-before-target ambiguity handling
Adoption rule: use conservative execution/reporting ideas where they match our data resolution.

### jimtin/build-your-own-mt5-ea — MIT
Useful concepts for later execution layer:
- MQL5 helper patterns
- indicator helpers including Bollinger-related logic
- new-candle detection
Adoption rule: later MT5 adapter/EA work only; keep research core independent.

## Idea donors — do not copy source unless license is confirmed

### Sarthaktagra27/orb-futures-backtesting
Relevant because it includes DAX/NQ ORB research and hypotheses around:
- 15-minute OR
- close-confirmed breakout / next-bar entry
- OR-mid stop
- previous-day range
- CPR
- volatility/cross-instrument filters
Warnings:
- README-described full-dataset grid search creates overfitting risk.
- no license was identified during our audit.
- observed same-bar stop/target ambiguity logic is not acceptable as our default.
Rule: hypotheses only; independently implement and validate.

### dws-data/nas-orb-backtester
Useful hypotheses:
- confirmed breakout followed by retracement into OR
- volume-profile context (VAH/POC/VAL)
Rule: idea donor until license/reuse rights are confirmed.

### jimtin/python_trading_bot
Useful high-level modular MT5/indicator architecture and indicator catalogue including Bollinger/Fibonacci.
Rule: no source reuse until exact repository license is confirmed.

## Other projects worth monitoring
- sam-bateman/trading-orb — long-horizon ORB validation / walk-forward / paper-trading methodology
- algotrade-plutus/MVP-DaybreakMomentum — explicit TRAIN/VALID/OOS separation and reproducible outputs
- ml4t/backtest — event-driven execution/risk architecture ideas
- QuantConnect/Lean — mature research/backtest/live architecture, but likely too heavyweight to replace our frozen custom core
- lamtrinhthong/Trading-Bot, ilcardella/TradingBot, ArthurBernard/Trading_Bot — modular live-process/software-engineering ideas subject to license verification

## Non-negotiable reuse rules
1. Record repository, license and borrowed concept before copying/adapting code.
2. Never copy code from a repository with no confirmed compatible license.
3. Never import reported performance as evidence for our DAX strategy.
4. Reimplement hypotheses against our audited data and frozen controls.
5. Every imported execution concept must pass parity/intrabar/no-lookahead tests.
6. Preserve attribution/license notices where required.
7. Prefer small, auditable concepts over wholesale framework replacement.
