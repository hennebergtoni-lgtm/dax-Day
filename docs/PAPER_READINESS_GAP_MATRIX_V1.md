# PAPER Readiness Gap Matrix V1

Status: BINDING PLANNING / EVIDENCE MATRIX — PAPER NOT AUTHORIZED
Updated: 2026-09-11
Branch: `nextgen-bot-line-v1`

Purpose: turn the coarse goal "get to real demo/PAPER quickly" into explicit evidence lanes without creating broker-order capability prematurely. This matrix maps directly to `ReadinessSnapshot` / `RunKind.PAPER` and to `docs/SHADOW_PAPER_ACCEPTANCE_V1.md`.

## Binding safety boundary

- SHADOW is the only currently authorized prospective mode.
- PAPER/demo broker execution is **not authorized**.
- LIVE is **not authorized**.
- `execution_capability=NONE` / `order_execution_enabled=false` remain binding on the current product runtime.
- No item marked IMPLEMENTABLE_BEFORE_PAPER may introduce `mt5.order_send`, a broker-order submission path or an execution-capability inversion.
- Explicit user authorization remains an independent final STOP-gate even after all technical evidence is green.

## Evidence matrix

| Readiness / capability | Current owner/evidence | Current state | Next evidence required | Lane |
| --- | --- | --- | --- | --- |
| CI / engine / DB / technical replay | existing CI, reference/replay/database gates | VERIFIED for repository alpha | maintain exact-head GREEN | REUSE |
| Dataset identity | frozen audited V11.2/reference evidence | HASH_VERIFIED | preserve unchanged | REUSE |
| Audited bundle / full reference replay | frozen/reproduced reference evidence | VERIFIED for current repository milestone | preserve provenance | REUSE |
| Legacy execution boundary | `paper_contracts.py`, Decision→ExecutionIntent separation | IMPLEMENTED / CONTRACT-VERIFIED | retain as coarse compatibility gate only | REUSE |
| ExecutionIntent + deterministic client identity | `paper_contracts.py`, `candidate_execution_intent.py` | IMPLEMENTED / SHADOW-SAFE | future authorized adapter must reuse this identity; do not duplicate | REUSE |
| Fill/same-bar/gap model vocabulary | `paper_contracts.py`, `core/execution.py`, Candidate virtual lifecycle | IMPLEMENTED for simulation | broker execution telemetry must record observed fill/slippage separately | REUSE |
| Stateful virtual lifecycle | `candidate_virtual_lifecycle.py` | VERIFIED for SHADOW simulation | does not satisfy broker order-lifecycle evidence by itself | REUSE AS MODEL ONLY |
| Restart/publication idempotency | Candidate checkpoint/publication journal | VERIFIED for SHADOW | reuse identity/persistence patterns; do not create a second recovery architecture | REUSE PATTERN |
| Current Windows/MT5 read-only health | existing host gate/supervisor + deployment runbook | repository integration VERIFIED; current-branch real host proof pending | run current branch on real Windows/MT5 and capture GREEN evidence | WAITING_EXTERNAL |
| Real DE40 broker economics | extended read-only MT5 symbol probe | collector IMPLEMENTED; current values not yet verified | observe/verify volume/tick/contract/currency/margin metadata on real demo broker | WAITING_EXTERNAL |
| Broker-risk sizing translation | `broker_risk_sizing.py`, `broker_economics_readiness.py` | algorithm/research tests IMPLEMENTED | bind to verified real DE40 economics and validate rounding/cash-at-stop semantics | PARTIAL / WAITING_EXTERNAL |
| BASE/BOOST/HIGH risk profile | `risk_profile_sizing.py` | research policy + lineage IMPLEMENTED | promote explicit validated cash-risk budgets/hard cap; never infer from account-allocation percentages | PARTIAL |
| Loss-cap policy | `loss_cap_gate.py` | research gate IMPLEMENTED | promote validated thresholds and prove interaction with sizing/admission | PARTIAL |
| Broker order lifecycle owner | `broker_order_lifecycle.py`, `tests/test_broker_order_lifecycle.py` | OWNER IMPLEMENTED / REPOSITORY-CI VERIFIED; PAPER evidence still unverified | feed real demo venue observations through the same contract before setting the PAPER readiness boolean | PARTIAL / WAITING_EXTERNAL |
| Broker order lifecycle restart state | no strict serialized BrokerOrderLifecycle restore envelope yet | FIX REQUIRED | add tamper-evident lifecycle payload/parse contract and prove OPEN/ACK/PARTIAL restore continuity without any broker API | IMPLEMENTABLE_BEFORE_PAPER |
| Broker reconciliation owner | `broker_reconciliation.py`, `tests/test_broker_reconciliation.py` | OWNER IMPLEMENTED / REPOSITORY-CI VERIFIED; PAPER evidence still unverified | reconcile real demo local-vs-venue truth including reconnect/restart cases before setting the PAPER readiness boolean | PARTIAL / WAITING_EXTERNAL |
| Execution protection gates / owner | `broker_execution_protection.py`, `tests/test_broker_execution_protection.py` | OWNER IMPLEMENTED / REPOSITORY-CI VERIFIED; non-executable ALLOW_EVIDENCE only | bind to real host/spread/reconciliation/sizing/session evidence and prove fail-closed behavior on the demo venue before setting the PAPER readiness boolean | PARTIAL / WAITING_EXTERNAL |
| Order lifecycle telemetry owner | `broker_execution_telemetry.py`, `tests/test_broker_execution_telemetry.py` | APPEND-ONLY RECORD CONTRACT IMPLEMENTED / REPOSITORY-CI VERIFIED; PAPER telemetry evidence still unverified | capture real demo request/ACK/reject/partial/fill/cancel/reconcile/protection records | PARTIAL / WAITING_EXTERNAL |
| Telemetry restart/idempotency journal | `broker_execution_telemetry_journal.py`, `tests/test_broker_execution_telemetry_journal.py` | IMPLEMENTED / REPOSITORY-CI VERIFIED | later bind the same journal to the authorized demo runtime/export boundary; synthetic CI is not broker evidence | REUSE / WAITING_EXTERNAL FOR BROKER EVIDENCE |
| PAPER telemetry readiness gate | `ReadinessSnapshot.broker_order_telemetry_verified` / `BROKER_ORDER_TELEMETRY_UNVERIFIED` | IMPLEMENTED / FAIL-CLOSED | set true only from complete qualifying broker telemetry evidence; repository CI alone cannot satisfy it | WAITING_EXTERNAL FOR BROKER EVIDENCE |
| Demo broker adapter / order submission | intentionally absent | NOT IMPLEMENTED / NOT AUTHORIZED | only after preceding evidence owners exist, current readiness remains fail-closed, real broker evidence is sufficient and explicit PAPER authorization is given | AUTHORIZATION-GATED |
| User PAPER authorization | `paper_user_authorized` readiness gate | FALSE by default / fail-closed | explicit user STOP-gate review after complete evidence bundle | USER_STOP_GATE |
| LIVE | no authorization/path | BLOCKED | independent future gate after PAPER evidence; not part of current plan | DEFERRED |

## Key conclusion

The core **broker-neutral execution evidence owners now exist**: lifecycle, reconciliation, protection, deterministic telemetry records, a restart-safe telemetry identity journal and an explicit PAPER telemetry readiness gate. This materially reduces the amount of software that must be invented when demo/PAPER becomes authorized.

Their existence does **not** make PAPER ready. Repository CI and synthetic fixtures prove software behavior; broker-facing PAPER readiness still requires real Windows/demo-venue evidence, verified DE40 economics/risk policy, lifecycle restore/reconnect evidence, real reconciliation/telemetry evidence and the independent user STOP-gate.

The next safe repository work is therefore:

1. add strict restart-safe serialization/restoration for the broker order lifecycle itself;
2. prove restored ACK/PARTIAL state continues deterministically and preserves identity;
3. keep real host/economics/reconciliation/telemetry evidence as parallel `WAITING_EXTERNAL` lanes;
4. do not create a broker submission adapter until the authorization-gated boundary is explicitly crossed.

## What does not count as broker evidence

The following must never set `broker_order_lifecycle_verified`, `broker_reconciliation_verified`, `execution_protection_gates_verified` or `broker_order_telemetry_verified` to true by themselves:

- the existence of enum names or dataclasses;
- successful SHADOW virtual fills;
- historical backtest/replay results;
- deterministic client IDs alone;
- a green read-only MT5 feed;
- synthetic/mock broker fixtures alone;
- CI success without the specific real broker evidence required by the gate;
- user authorization by itself.

## Promotion rule

A future evidence bundle may set a PAPER readiness boolean true only when the corresponding owner has a named version/fingerprint, regression proof, and — where the gate is broker-specific — real demo-broker evidence. Readiness booleans are summaries of evidence, not substitutes for evidence.
