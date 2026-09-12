# NextGen Risk Policy Promotion Audit V1

Status: **STEP-2160 BINDING PROMOTION AUDIT / NO POLICY VALUES PROMOTED**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Audit the existing research-only risk-profile and loss-cap owners against canonical NextGen Risk V1 and the Step-2159 broker-economics binding before any product-policy promotion.

Allowed classifications:

- `REUSE` — semantics already belong in the canonical product contract or are already represented there;
- `ADAPT` — semantics are useful, but the research owner/name/state must not become the product owner;
- `DEFER` — no evidence-neutral product promotion is justified yet.

## Result

| Research / product semantic | Classification | Product decision |
| --- | --- | --- |
| Explicit cash-at-stop budget | `REUSE` | Already canonical as `RiskRequest.max_loss_cash`; keep explicit, positive and deterministic. |
| Explicit risk currency | `REUSE` | Already canonical as `RiskRequest.loss_currency` and `InstrumentRiskInputs.currency`; mismatch denies. |
| Conservative floor-to-quantity-step sizing | `REUSE` | Already canonical in `evaluate_fixed_cash_risk()` and parity-tested against research sizing. |
| Verified broker economics -> canonical risk inputs | `REUSE` | Step 2159 owner remains the only read-only translation boundary. |
| One explicit per-trade fixed-cash policy | `ADAPT` | A product policy may bind one configured cash-risk ceiling + currency to Risk V1; it must not import research profile identities. |
| Research `BASE` / `BOOST` / `HIGH` profile names | `DEFER` | No automatic product promotion. They remain research hypotheses/configurations only. |
| Research profile cash values | `DEFER` | No numerical value is promoted without separate evidence and governance. |
| Automatic risk escalation / profile switching | `DEFER` | No product mechanism or evidence justifies automatic escalation. |
| Daily and weekly cash drawdown caps | `ADAPT` | Useful product admission semantics, but require a canonical owner and verified product observations. |
| Consecutive-loss cooldown | `ADAPT` | Useful fail-closed admission semantic; research owner/state is not canonical product ownership. |
| Maximum open positions | `ADAPT` | Useful portfolio admission semantic; remains separate from per-trade sizing. |
| Research loss-cap numeric values | `DEFER` | No numeric policy is promoted by this audit. |
| Account-balance / equity percentage sizing | `DEFER` | Not inferred. No account read or percentage policy is introduced. |

## Architecture boundary

`src/daxlab/domain/risk.py` remains independent from `daxlab.research.*`. Product risk must not import `RiskProfile`, `RiskProfileBudgetSpec`, research loss-cap types or their version strings.

The existing research owners remain evidence and hypothesis surfaces:

- `research/risk_profile_sizing.py` proves explicit cash budgets and a hard-cap research relationship;
- `research/loss_cap_gate.py` proves deterministic fail-closed cap semantics;
- neither file is a product policy owner.

## Separation of responsibilities

Per-trade risk sizing and portfolio/session admission are deliberately separate:

1. canonical Risk V1 decides quantity from one explicit maximum cash loss and verified instrument economics;
2. loss/drawdown/cooldown/open-position gates decide whether a new trade may be admitted at all;
3. neither layer may silently increase the other's limits;
4. readiness evidence for risk policy and loss-cap policy remains explicit and false until separately verified.

## Next safe product step

The smallest evidence-neutral implementation after this audit is a canonical **single fixed-cash risk policy** that binds one explicit currency + per-trade maximum cash loss to Risk V1. It must contain no BASE/BOOST/HIGH concept and no broker/account API.

Loss-cap product adaptation remains a separate later work unit because it consumes different state and admission evidence.

## Safety / non-change statement

Step 2160 promotes no numerical risk value, broker economics observation, research profile or loss-cap configuration. It adds no MT5 SDK/order API, no account balance read, no broker submission and no PAPER/LIVE authorization.

Current safety remains:

- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- PAPER not authorized;
- LIVE not authorized;
- `NO_STRATEGY_AUTO_PROMOTION` unchanged.
