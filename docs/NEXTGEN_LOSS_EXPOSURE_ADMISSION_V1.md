# NextGen Loss / Exposure Admission V1

Status: **STEP-2163 PRODUCT / NON-EXECUTING ADMISSION CONTRACT**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Provide one canonical product owner that decides whether a new trade may be admitted from explicit already-computed loss/exposure observations.

## Canonical owner

`src/daxlab/domain/loss_admission.py`

It owns:

- `LossExposurePolicy` — explicit currency, daily/weekly drawdown caps, consecutive-loss limit and maximum-open-position limit;
- `LossExposureObservation` — explicit current observations only;
- `LossExposureAdmissionDecision` — deterministic ALLOW/BLOCK result with reason codes;
- `evaluate_loss_exposure_admission()` — pure fail-closed evaluation.

## Boundary semantics

Equality at any configured limit blocks a new admission. Currency mismatch blocks. Invalid/tampered policy or observation identities fail closed.

The module does not calculate PnL or derive observations. Observation production remains outside this policy boundary.

## Deliberate separation from Risk V1

Per-trade quantity sizing remains owned by canonical Risk V1. Loss/exposure admission does not import `RiskRequest`, does not calculate quantity and cannot increase a per-trade risk ceiling.

## No research-value promotion

Step 2163 adapts only the audited semantics from Step 2160. It promotes no research numeric values and imports no research policy owner/version.

## Safety boundary

- no account/broker API read;
- no MT5 SDK/order API;
- no broker submission path;
- `execution_capability=NONE` where applicable;
- `order_execution_enabled=false`;
- PAPER not authorized;
- LIVE not authorized;
- readiness verification remains independent from software implementation.
