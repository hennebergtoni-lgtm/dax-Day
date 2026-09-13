# Step 2190 Closeout / Step 2191 Scope

Status: BINDING MAIN-CHAT CLOSEOUT + NEXT-STEP SCOPE
Updated: 2026-09-13
Branch: `nextgen-bot-line-v1`
PR: #109

## Step 2190 result

Step 2190 is COMPLETED.

Independent Work Red-Team result: `VERIFIED_GAP`.

Main-chat verification independently confirmed on head `29d9edf0c940615a63746d80b995efaeb4b6a6ab`:

- PR #109 remained OPEN / UNMERGED and had no branch drift at verification time;
- `dax-bot-1x-ci` #569: GREEN;
- `research-lab-ci` #1353: GREEN;
- research-lab CI: Ruff GREEN and `2196 passed`;
- Neon/DB workflow steps in that PR CI remained skipped and were not misreported as fresh DB evidence;
- synthetic SHADOW soak explicitly remained `SYNTHETIC_ONLY_NOT_BROKER_EVIDENCE`;
- no broker submission path was added;
- PAPER and LIVE remained unauthorized.

The independently confirmed architecture gap is a bootstrap-cycle problem:

1. normal PAPER readiness requires real broker-facing lifecycle/checkpoint/reconciliation/protection/telemetry evidence;
2. current SHADOW and PAPER-preparation surfaces cannot submit broker orders;
3. `BrokerExecutionProtectionVerdict.ALLOW_EVIDENCE` is deliberately non-executable (`execution_capability=NONE`, `order_execution_enabled=false`);
4. the current PREPARED checkpoint proves local preparation only and forbids venue/fill evidence;
5. therefore the repository currently lacks a rule-compliant transition by which the bot itself can generate its first real demo-broker evidence.

This does NOT invalidate the prior anti-overbuild decision. The missing capability is narrower than a second execution stack: a separately authorized, demo-only evidence-acquisition boundary is required before normal PAPER can be evidence-complete.

## Reuse remains mandatory

Any future implementation must reuse the existing canonical owners wherever applicable:

- `ExecutionIntent` identity and existing risk-to-intent binding;
- broker economics / risk policy / loss and exposure admission;
- session admission consumption and `SessionAdmissionGuardCheckpoint`;
- `nextgen_prepared_checkpoint.py` local PREPARED commit boundary;
- existing broker order lifecycle;
- existing `BrokerExecutionCheckpointState` and codecs;
- existing broker reconciliation;
- existing typed broker execution protection;
- existing broker execution telemetry and telemetry journal;
- existing `StateStorePort` / `AtomicFileStateStore`;
- existing host/clock/CLOSED-M5 safety contracts.

No second lifecycle, state store, reconciliation stack, telemetry stack, or generic execution service is justified.

## Step 2191 — ACTIVE scope

Implement only the smallest software contract needed to separate DEMO evidence-acquisition authorization from final PAPER authorization.

Step 2191 MUST NOT add venue submission or an MT5 order API. It is authorization-contract work only.

Required properties:

1. introduce an explicit demo-evidence authorization type/stage that is semantically distinct from final `paper_user_authorized`;
2. authorization must be tightly scoped and fail closed: intended demo account/server identity, intended symbol/instrument scope, validity window or explicit expiry, permitted action scope, and evidence-only purpose;
3. unknown/REAL/CONTEST account modes must be rejectable by the contract; a generic `trade_allowed=True` must never prove demo status;
4. final PAPER authorization must remain independent and unchanged in meaning;
5. existing SHADOW and PAPER-preparation gates must not be weakened or reinterpreted as executable;
6. `ALLOW_EVIDENCE` must remain evidence-only and non-executable;
7. the new contract must not itself submit an order, call MT5 order APIs, fabricate broker evidence, or auto-promote readiness;
8. no CAND-001, frozen V11.2, cost-model, strategy, timezone/reset or production-risk defaults may be mutated;
9. tests must cover missing/expired authorization, account/server/symbol mismatch, REAL/CONTEST/unknown account mode, confusion with final PAPER authorization, tampering/cross-wiring, and preservation of `execution_capability=NONE` / `order_execution_enabled=false`;
10. repository docs/readiness ownership must clearly state that passing Step 2191 enables no broker execution by itself.

## Deferred beyond Step 2191

Explicitly deferred until a separately reviewed later step:

- MT5/demo venue transport adapter;
- `mt5.order_send` or any equivalent order API;
- post-PREPARED venue-attempt/result checkpoint progression;
- real ACK/FILL/REJECT handling from a venue;
- broker history/open-order querying for bootstrap recovery;
- normal PAPER start authorization;
- LIVE execution.

## Monday target impact

Status after Step 2190: `BLOCKED` for a rule-compliant real demo-broker evidence run at the current head.

The blocker is now isolated and actionable rather than ambiguous. Step 2191 closes only the authorization-contract part. A later transport/checkpoint implementation and external Windows/market-open/broker gates remain necessary before an actual demo-broker evidence run can be authorized.

Safety remains binding:

- SHADOW authorized;
- PAPER/demo execution not authorized;
- LIVE not authorized;
- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- frozen V11.2 unchanged;
- no profitability claim.
