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

### nautechsystems/nautilus_trader — LGPL-3.0
Useful architecture concepts:
- deterministic event-driven core
- same-strategy-code philosophy across backtest and live execution
- explicit data, execution and portfolio boundaries
- high-integrity production runtime design
Adoption rule: architecture donor only unless LGPL-3.0 obligations and NautilusTrader trademark/attribution requirements are explicitly reviewed for any source reuse. Do not replace the frozen V11.2 research core.

### BullTrading/deterministic-market-replay — Apache-2.0
Useful concepts:
- deterministic MT5-oriented market replay
- timestamp/session normalization
- replay validation and auditability
- execution-event reconstruction
Adoption rule: use replay-engineering concepts where independently implemented and verified against our V11.2 causality/parity contract.

### quantstart/qstrader — MIT
Useful concepts:
- event-driven separation of market data, strategy, portfolio and execution
- explicit simulation boundaries
- modular backtest architecture
Adoption rule: architecture reference only; preserve our V11.2 strategy semantics and data contracts.

### Jenak26/event-driven-backtester — MIT
Useful concepts:
- point-in-time bar cursor
- next-bar fill discipline
- realistic cost handling
- open reporting of negative strategy results
Adoption rule: borrow methodology/engineering ideas only; never import reported performance as evidence.

### WalllerG/Automated-paper-trading-bot — MIT
Useful concepts:
- independent risk engine
- event-driven paper-trading boundary
- no-lookahead execution discipline
- operational separation between signal and order handling
Adoption rule: later Shadow/Paper architecture donor only; hard risk gates remain independent and non-overridable.

### boutquin/Boutquin.Trading — Apache-2.0
Useful concepts:
- event-driven trading architecture
- composite risk-manager patterns
- circuit-breaker style controls
- backtest/execution separation
Adoption rule: use risk/control architecture ideas only after independent implementation and tests.

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

### JN842/multitf-bollinger-switching — license not re-verified on 2026-09-08
Previously noted useful hypotheses/concepts:
- shifted higher-timeframe features to avoid same-bar leakage
- regime switching between breakout and mean-reversion behavior
- explicit cost-aware evaluation
Rule: IDEA ONLY until the exact repository and license are independently re-grounded. No source reuse and no external performance claim may enter DAX evidence.

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
8. Public/open-source material enters the project through IDEA -> RESEARCH -> PILOT -> VALIDATED TOOL; it never bypasses DAX OOS/WF evidence.
