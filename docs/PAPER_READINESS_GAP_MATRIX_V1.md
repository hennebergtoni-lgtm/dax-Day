# PAPER Readiness Gap Matrix V1

Status: BINDING PLANNING / EVIDENCE MATRIX — PAPER NOT AUTHORIZED
Updated: 2026-09-13
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
| Broker order lifecycle restart state | `broker_order_lifecycle_state_payload` / `parse_broker_order_lifecycle_state_payload`, `tests/test_broker_order_lifecycle_state.py` | IMPLEMENTED / REPOSITORY-CI VERIFIED | bind to the future authorized demo runtime and reconnect evidence; repository fixtures are not broker evidence | REUSE / WAITING_EXTERNAL FOR BROKER EVIDENCE |
| Broker execution atomic checkpoint | `broker_execution_checkpoint.py`, `tests/test_broker_execution_checkpoint.py` | OWNER IMPLEMENTED / REPOSITORY-CI VERIFIED; PARTIAL→FILLED restart parity proven | qualifying demo-runtime checkpoint/restart evidence before setting PAPER checkpoint readiness true | PARTIAL / WAITING_EXTERNAL FOR BROKER EVIDENCE |
| PAPER checkpoint readiness gate | `ReadinessSnapshot.broker_execution_checkpoint_verified` / `BROKER_EXECUTION_CHECKPOINT_UNVERIFIED` | IMPLEMENTED / FAIL-CLOSED | set true only from qualifying broker checkpoint/restart evidence; repository CI alone cannot satisfy it | WAITING_EXTERNAL FOR BROKER EVIDENCE |
| Broker reconciliation owner | `broker_reconciliation.py`, `tests/test_broker_reconciliation.py` | OWNER IMPLEMENTED / REPOSITORY-CI VERIFIED; PAPER evidence still unverified | reconcile real demo local-vs-venue truth including reconnect/restart cases before setting the PAPER readiness boolean | PARTIAL / WAITING_EXTERNAL |
| Execution protection gates / owner | `broker_execution_protection.py`, `tests/test_broker_execution_protection.py` | OWNER IMPLEMENTED / REPOSITORY-CI VERIFIED; non-executable ALLOW_EVIDENCE only | bind to real host/spread/reconciliation/sizing/session evidence and prove fail-closed behavior on the demo venue before setting the PAPER readiness boolean | PARTIAL / WAITING_EXTERNAL |
| Order lifecycle telemetry owner | `broker_execution_telemetry.py`, `tests/test_broker_execution_telemetry.py` | APPEND-ONLY RECORD CONTRACT IMPLEMENTED / REPOSITORY-CI VERIFIED; PAPER telemetry evidence still unverified | capture real demo request/ACK/reject/partial/fill/cancel/reconcile/protection records | PARTIAL / WAITING_EXTERNAL |
| Telemetry restart/idempotency journal | `broker_execution_telemetry_journal.py`, `tests/test_broker_execution_telemetry_journal.py` | IMPLEMENTED / REPOSITORY-CI VERIFIED | later bind the same journal to the authorized demo runtime/export boundary; synthetic CI is not broker evidence | REUSE / WAITING_EXTERNAL FOR BROKER EVIDENCE |
| PAPER telemetry readiness gate | `ReadinessSnapshot.broker_order_telemetry_verified` / `BROKER_ORDER_TELEMETRY_UNVERIFIED` | IMPLEMENTED / FAIL-CLOSED | set true only from complete qualifying broker telemetry evidence; repository CI alone cannot satisfy it | WAITING_EXTERNAL FOR BROKER EVIDENCE |
| Demo broker adapter / order submission | intentionally absent | NOT IMPLEMENTED / NOT AUTHORIZED | only after preceding evidence owners exist, current readiness remains fail-closed, real broker evidence is sufficient and explicit PAPER authorization is given | AUTHORIZATION-GATED |
| User PAPER authorization | `paper_user_authorized` readiness gate | FALSE by default / fail-closed | explicit user STOP-gate review after complete evidence bundle | USER_STOP_GATE |
| LIVE | no authorization/path | BLOCKED | independent future gate after PAPER evidence; not part of current plan | DEFERRED |

## Key conclusion

The core **broker-neutral execution evidence owners and readiness gates now exist** for lifecycle, lifecycle restore/checkpoint, reconciliation, protection and deterministic telemetry. Repository CI proves those software contracts and their fail-closed behavior, but it does not convert them into broker-facing evidence.

Their existence does **not** make PAPER ready. Broker-facing PAPER readiness still requires real Windows/demo-venue evidence, verified DE40 economics/risk policy, reconnect/reconciliation/telemetry/checkpoint evidence and the independent user STOP-gate.

## Step 2127 repository-owner reassessment — 2026-09-12

Step 2127 re-audited the current branch owner-by-owner against implementation and regression tests rather than relying on this matrix summary alone. The reviewed broker-neutral surfaces were:

- broker order lifecycle + lifecycle state restore;
- atomic broker execution checkpoint;
- local-vs-venue reconciliation;
- execution protection/admission evidence;
- deterministic order/reconciliation/protection telemetry;
- restart-safe telemetry idempotency journal;
- read-only broker economics readiness;
- research-only cash-at-stop sizing translation;
- BASE/BOOST/HIGH explicit cash-risk profile bridge;
- research-only loss-cap admission gate;
- `ReadinessSnapshot` / `RunKind.PAPER` fail-closed gate composition.

Result: **no material missing broker-neutral software evidence owner was identified.** The existing owner set already separates repository/fixture proof from broker-facing proof and keeps broker-order submission intentionally absent. The PAPER readiness evaluator independently requires lifecycle, checkpoint, reconciliation, protection, telemetry, MT5 read-only health, broker economics, broker risk sizing, risk-profile policy, loss-cap policy and explicit user authorization before PAPER can be allowed.

Therefore the remaining gap is **evidence collection and authorization**, not another generic execution scaffold. Real demo-broker observations must populate the existing evidence contracts before their PAPER readiness booleans may become true. Building a broker submission adapter before that evidence exists and before explicit PAPER authorization would be premature overengineering and remains prohibited.

The next safe repository work is therefore:

1. preserve the existing owner set unless new evidence reveals a concrete missing contract;
2. keep real host/economics/reconciliation/telemetry/checkpoint evidence as parallel `WAITING_EXTERNAL` lanes;
3. prefer thin read-only evidence adapters/tests over inventing a broker submission stack prematurely;
4. do not create a broker submission adapter until the authorization-gated boundary is explicitly crossed.

## Step 2188 PAPER readiness evidence ownership reassessment — 2026-09-13

Step 2188 rechecked the current PR head after the atomic local PREPARED checkpoint was completed. The purpose is to prevent the Monday demo target from turning readiness booleans into evidence substitutes or triggering duplicate runtime owners.

### Ownership classes

- **REUSE** — a canonical owner/evidence contract already exists; do not duplicate it.
- **ADAPT** — the semantic owner exists, but a narrow promotion/evidence-binding step is still required before the corresponding PAPER boolean may become true.
- **EXTERNAL** — the owner/collector exists, but current truth requires real Windows, MT5, Neon/database or demo-venue evidence that repository CI cannot invent.
- **USER_AUTH** — only an explicit user STOP-gate decision may satisfy the gate; software evidence must never infer it.

### ReadinessSnapshot ownership map

| PAPER gate | Canonical owner/evidence | Ownership class | Current truth / promotion rule |
| --- | --- | --- | --- |
| `ci_green` | required GitHub checks on the exact PR head | REUSE | exact-head GREEN required; stale runs do not count |
| `dataset_verified` + `dataset_identity` | frozen audited V11.2/reference identity | REUSE | preserve `HASH_VERIFIED`; no research result may rewrite it |
| `engine_verified` | frozen engine/reference gates | REUSE | preserve verified engine identity; no new engine owner |
| `database_verified` | Neon migration/integrity/restore/detail-import gates | EXTERNAL | five Neon/DB gates were skipped on the Step-2187 PR runs and remain `WAITING_EXTERNAL`; prior repository-alpha shorthand must not silently satisfy the current-head PAPER gate |
| `technical_replay_verified` | existing replay/technical gates | REUSE | exact-head regression evidence required |
| `audited_bundle_available` | audited recovery/reference bundle | REUSE | preserve provenance/fingerprint |
| `full_reference_replay_verified` | clean full-reference replay evidence | REUSE | repository/replay evidence may satisfy this non-broker gate when exact-head provenance is preserved |
| `execution_boundary_verified` | legacy `paper_contracts.py` / intent separation | REUSE | compatibility gate only; explicitly insufficient for PAPER by itself |
| `mt5_readonly_health_verified` | current host gate, supervisor, `mt5_windows_probe.py`, `latest_bundle.json` | EXTERNAL | current-branch real Windows/MT5 market-open GREEN/clock/CLOSED-M5 evidence required |
| `broker_economics_verified` | `broker_economics_readiness.py` + read-only DE40 probe | EXTERNAL | must come from verified real demo-broker DE40 economics; synthetic/default values do not count |
| `broker_risk_sizing_verified` | `nextgen_broker_economics.py` / existing broker-risk translation | REUSE | typed owner already fails closed until economics are externally verified; validate concrete cash-at-stop/rounding on the verified symbol before promotion |
| `risk_profile_policy_verified` | `FixedCashRiskPolicy` + existing explicit risk-profile research lineage | ADAPT | promote one explicit validated cash-risk policy with provenance; BASE/BOOST/HIGH research values must not auto-promote |
| `loss_cap_policy_verified` | `LossExposurePolicy` / canonical loss-exposure admission owner | ADAPT | promote explicit validated daily/weekly/consecutive/open-position thresholds and prove policy interaction; do not invent values to clear the gate |
| `broker_order_lifecycle_verified` | `broker_order_lifecycle.py` / `nextgen_broker_lifecycle.py` | EXTERNAL | software owner is REUSED, but PAPER=true requires real demo-venue lifecycle observations after the authorization-gated execution boundary exists |
| `broker_execution_checkpoint_verified` | `broker_execution_checkpoint.py` + Step-2187 PREPARED owner | EXTERNAL | local PREPARED/restart proof is necessary but does not prove broker checkpoint/restart behavior; qualifying demo-runtime evidence required |
| `broker_reconciliation_verified` | `broker_reconciliation.py` | EXTERNAL | reconcile real local-vs-demo-venue truth including reconnect/restart ambiguity; fixtures do not count |
| `execution_protection_gates_verified` | `broker_execution_protection.py` + typed NextGen protection | EXTERNAL | owner is REUSED; PAPER=true requires concrete real host/spread/reconciliation/risk/session evidence, not merely offline `ALLOW_EVIDENCE` tests |
| `broker_order_telemetry_verified` | broker telemetry owner + idempotency journal/checkpoint | EXTERNAL | complete qualifying real demo request/outcome/reconciliation/protection telemetry required |
| `paper_user_authorized` | explicit PAPER STOP-gate | USER_AUTH | remains false until the user reviews the complete evidence bundle and explicitly authorizes demo/PAPER; never infer from technical readiness |

### Evidence-less boolean finding

`ReadinessSnapshot` remains a normalized fail-closed summary and intentionally accepts booleans. The Step-2188 audit does **not** promote a second readiness architecture merely to replace those fields. Instead, every future transition to `True` must cite the owner/evidence named above. A naked caller-supplied `True` without that provenance is not qualifying PAPER evidence.

No generic PAPER-readiness composer is justified before the external evidence exists. Creating one now would mostly wrap unavailable evidence in another object and would not move the Monday target forward.

### Smallest Monday-demo path after this audit

1. keep exact-head CI/replay/reference evidence green;
2. clear the five Neon/database gates using real connected database evidence rather than CI inference;
3. at the next market-open Windows/MT5 window, capture current-branch read-only host/clock/CLOSED-M5 plus DE40 economics through the existing probe/supervisor bundle;
4. bind verified DE40 economics into the existing broker-aware risk translation;
5. promote explicit risk-profile and loss-cap policy values only with named provenance and validation;
6. keep broker lifecycle/checkpoint/reconciliation/protection/telemetry PAPER gates false until qualifying real demo-venue evidence exists;
7. only after the complete evidence bundle is reviewable may the independent `paper_user_authorized` STOP-gate be considered;
8. real-money LIVE remains out of scope.

### Step-2188 product decision

- **REUSE** the existing readiness evaluator and all existing broker-neutral evidence owners.
- **DO NOT BUILD** a generic readiness composer or second evidence stack now.
- **ADAPT NEXT** only the smallest evidence/policy promotion boundary that remains after connected Neon and real MT5 evidence are harvested.
- Treat skipped Neon/DB and unavailable real Windows/MT5/demo-venue observations as `WAITING_EXTERNAL`, never as failures that stop unrelated safe work and never as VERIFIED evidence.

## What does not count as broker evidence

The following must never set `broker_order_lifecycle_verified`, `broker_execution_checkpoint_verified`, `broker_reconciliation_verified`, `execution_protection_gates_verified` or `broker_order_telemetry_verified` to true by themselves:

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
