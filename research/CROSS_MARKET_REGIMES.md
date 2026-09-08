# Cross-Market / Regime Research

Status: PLANNED RESEARCH LAYER — not active strategy logic.

## Principle
A filter is not assumed to be globally useful. Its value may depend on the trading period/regime and on the state of related instruments. The future research lab must therefore measure conditional effectiveness, not only full-sample averages.

## Candidate external context
Initial instruments/context to investigate after isolated DAX tools are measured:
- Euro Stoxx 50 / European equity context
- S&P 500 and Nasdaq futures / US risk context
- EUR/USD
- Bund / German rates context
- volatility proxy such as VIX or an appropriate European volatility index
- later other instruments only where a defensible DAX relationship exists

This list is a research universe, not a fixed trading rule.

## Required regime dimensions
Candidate dimensions include:
- time-of-day / session phase
- volatility state
- trend vs range state
- opening-range structure
- event proximity
- external-instrument direction, momentum, volatility and divergence/convergence with DAX

## Research question
For each validated or promising DAX tool/filter, measure whether its effect changes materially by regime and external-market state. Examples: Bollinger momentum may work in one volatility/cross-market regime while a pullback/reversion tool works in another.

## Anti-overfitting rules
- First establish isolated evidence for each DAX tool.
- Define cross-market features using information available at the decision timestamp only.
- No future US-session information may leak into a European-morning DAX decision.
- Do not search arbitrary combinations of instruments, regimes and thresholds.
- Use predeclared coarse states first, then targeted interactions only where evidence exists.
- Require sufficient trades per conditional cell.
- Require rolling WF/OOS stability and normal/1.5x/2x cost stress.
- Retain negative findings.
- Cross-market context may become a filter, confidence input or bounded risk modifier only after validation.

## Intended architecture
Final decision logic should be capable of selecting among validated tools by current regime rather than forcing one universal filter stack. Conceptually:

`market regime -> DAX structure -> cross-market context -> eligible validated tools -> setup/entry -> bounded risk`

No automatic strategy mutation is permitted. Any regime-to-tool mapping must be versioned, auditable and validated before candidate-bot promotion.
