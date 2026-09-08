# FAIL001 — Why traders and trading systems fail

Status: RESEARCH

## Purpose
FAIL001 studies recurring failure mechanisms in discretionary trading and systematic research so they can be translated into technical controls. Literature and external evidence are context only; they never become trading rules by themselves.

## Binding principle
A valid NO_TRADE decision is a successful system outcome when data, evidence, setup quality, execution state or risk constraints are insufficient.

## Failure families
- overtrading
- forced trades
- overconfidence
- revenge / risk escalation
- transaction-cost neglect
- excess leverage / risk of ruin
- lookahead / repainting
- overfitting
- parameter proliferation
- regime blindness
- data-quality failure
- unrealistic execution / fills
- strategy drift
- changing rules after short losing streaks
- survivorship / selection bias
- no-trade blindness

## Technical translation categories
Every accepted FAIL001 finding must map to one or more of:
- DATA_GATE
- RESEARCH_GATE
- SETUP_GATE
- RISK_GATE
- EXECUTION_GATE
- MONITORING_GATE
- UI_GUARDRAIL

No finding may bypass the normal IDEA -> RESEARCH -> PILOT -> VALIDATED TOOL pipeline.

## Existing empirical context
Research context retained from the project handover includes Barber & Odean on excessive trading, Barber et al. on aggregate investor trading losses and day-trader skill, and Chague et al. on persistent day trading. These papers motivate failure controls; they do not define DAX entries, exits or parameters.

## Planned technical controls
- Overtrading / forced trades -> SETUP_GATE: no setup = no trade; trade count is never a target.
- Overconfidence -> RESEARCH_GATE: no promotion after a few attractive WFs.
- Cost neglect -> RESEARCH_GATE + EXECUTION_GATE: normal / 1.5x / 2x stress and execution-health checks.
- Revenge / risk escalation -> RISK_GATE: no loss-triggered risk increase; hard daily limits later.
- Emotional exits -> EXECUTION_GATE: deterministic exit semantics.
- Regime blindness -> SETUP_GATE: regime determines eligible validated tools, never automatic unvalidated rules.
- Overfitting / parameter proliferation -> RESEARCH_GATE: OOS/WF, neighbourhood stability and independent validation.
- Lookahead / repainting -> RESEARCH_GATE: closed-candle causality and replay parity.
- Excess leverage -> RISK_GATE: independent bounded risk engine before paper/live.
- Data errors -> DATA_GATE: unsafe data forces NO_TRADE.
- Strategy drift -> MONITORING_GATE: warn/block only; never self-optimize.
- Rule changes after short losing streaks -> RESEARCH_GATE + UI_GUARDRAIL: no live self-modification.
- Survivorship / selection bias -> RESEARCH_GATE: retain rejected/blocked evidence and explicit provenance.
- No-trade blindness -> MONITORING_GATE: log NO_TRADE and blocker reasons alongside trades.

## Promotion rule
FAIL001 itself is not a strategy. Its outputs are guardrails and test requirements. Any control that changes execution semantics requires its own validation before deployment.
