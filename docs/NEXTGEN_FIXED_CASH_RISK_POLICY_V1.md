# NextGen Fixed-Cash Risk Policy V1

Status: **STEP-2162 PRODUCT / NON-EXECUTING RISK POLICY CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Provide the smallest canonical product risk policy above Risk V1: one explicit risk currency and one explicit positive finite per-trade maximum cash-loss ceiling.

## Canonical owner

`src/daxlab/domain/risk_policy.py`

The owner provides:

- `FixedCashRiskPolicy` — currency + maximum cash loss + deterministic fingerprint;
- `build_risk_request_from_policy()` — binds the policy into the existing canonical `RiskRequest`.

Sizing remains owned exclusively by `evaluate_fixed_cash_risk()` in `domain/risk.py`.

## Fail-closed rules

Policy creation rejects:

- empty or whitespace-normalized currency errors;
- zero, negative, non-finite cash limits;
- schema mismatch;
- fingerprint tampering.

Binding rejects policy/instrument currency mismatch before a Risk V1 request is produced.

## Deliberate exclusions

This product policy contains no:

- `BASE`, `BOOST` or `HIGH` research profile;
- automatic risk escalation;
- account balance or equity-percentage sizing;
- broker/account API access;
- MT5 SDK or order API;
- broker submission path;
- PAPER or LIVE authorization.

Software implementation does not set `risk_profile_policy_verified=true`; readiness evidence remains an independent gate.

## Safety boundary

- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- PAPER not authorized;
- LIVE not authorized;
- `NO_STRATEGY_AUTO_PROMOTION` unchanged;
- frozen V11.2 evidence and verified historical fingerprints remain unchanged.
