# NextGen Execution Protection Evidence Binding V1

Status: **STEP-2165 PRODUCT / NON-EXECUTING PROTECTION BINDING**  
Date: **2026-09-12**  
Branch: `nextgen-bot-line-v1`

## Purpose

Harden the existing broker-neutral `broker_execution_protection.py` owner so the NextGen path consumes canonical product risk and loss/exposure evidence instead of passing only coarse untyped booleans and placeholder fingerprints.

## Compatibility decision

The existing generic `evaluate_execution_protection()` contract remains available for active legacy/synthetic consumers. Step 2165 does not introduce another protection owner.

The same module now also provides `evaluate_nextgen_execution_protection()` for canonical NextGen evidence.

## Canonical NextGen binding

The typed path requires and verifies:

- `FixedCashRiskPolicy`;
- canonical `RiskRequest`;
- exact canonical `RiskDecision` from Risk V1;
- `LossExposurePolicy`;
- `LossExposureObservation`;
- exact canonical `LossExposureAdmissionDecision`.

It fails closed when:

- RiskRequest identity is not canonical;
- RiskRequest currency/cash ceiling does not match the fixed-cash policy;
- RiskDecision differs from canonical Risk V1 evaluation;
- Loss/Exposure Admission differs from canonical evaluation;
- product risk and loss/admission policy currencies disagree.

## Protection provenance

The resulting existing `BrokerExecutionProtectionVerdict` binds separately:

- per-trade sizing evidence: canonical `RiskDecision.decision_id`;
- fixed-cash product policy: `FixedCashRiskPolicy.policy_fingerprint`;
- loss/exposure admission evidence: `LossExposureAdmissionDecision.decision_fingerprint`.

The new loss-admission fingerprint is optional on the legacy generic verdict surface for compatibility, but the typed NextGen path always supplies it.

A blocked canonical RiskDecision becomes `SIZING_BLOCKED`; a blocked canonical Loss/Exposure decision becomes `LOSS_CAP_BLOCKED`. The protection owner still combines host, feed, spread, reconciliation, duplicate-ID and session-admission evidence as before.

## Readiness separation

Repository implementation and synthetic tests do **not** set any PAPER readiness booleans true. In particular, this step does not infer:

- `risk_profile_policy_verified=true`;
- `loss_cap_policy_verified=true`;
- `execution_protection_gates_verified=true`;
- `paper_user_authorized=true`.

Those remain separately evidenced gates.

## Safety boundary

- no account/broker API added;
- no MT5 SDK/order API added;
- no broker submission path;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- PAPER not authorized;
- LIVE not authorized.
