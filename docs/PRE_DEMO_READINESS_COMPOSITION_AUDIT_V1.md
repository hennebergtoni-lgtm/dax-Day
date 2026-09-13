# Pre-DEMO readiness composition — Step 2201

Audit anchor: `52e2aa0942f20909641be66ddc71845237f5424b`, PR #109,
2026-09-13. Implementation authorization covers local/read-only preparation;
it does not authorize a DEMO order, PAPER or LIVE. No Acceptance is renewed.

## Gate/owner matrix

Status describes the named layer, not an automatic promotion of its consumers.
Existing VERIFIED history remains historical evidence. The current Windows host
and broker facts below were not observed by this Work task.

| Gate | Existing authoritative owner / contract | Software layer | Current external/product layer |
| --- | --- | --- | --- |
| Windows host lane 2122 | `mt5_host_contract`, `mt5_windows_bundle`, Windows SHADOW runbook | IMPLEMENTED; prior wiring/parity/fail-closed VERIFIED | WAITING_EXTERNAL: exact-head real-host GREEN and restart |
| CLOSED-M5 / clock / session | `mt5_feed_payload`, `mt5_probe_payload`, Candidate/session contracts | IMPLEMENTED; bar 0 excluded, finite bars, explicit timezone | WAITING_EXTERNAL: market-open closed bars, clock/timezone and session-day evidence |
| Redacted DEMO account/server/symbol | `mt5_demo_account_context`, same probe/bundle | IMPLEMENTED; DEMO/REAL/CONTEST/UNKNOWN distinct | WAITING_EXTERNAL: current account and exact symbol; no credentials in artifacts |
| Transport tag / open/history/deal lookup | `mt5_demo_evidence_transport`, Step-2200 scripts | IMPLEMENTED; zero/ambiguous lookup blocked | WAITING_EXTERNAL: broker tag preservation and actual venue records |
| Broker economics to Risk V1 | `broker_economics_readiness`, `nextgen_broker_economics`, `domain.risk` | IMPLEMENTED canonical conversion; MISSING source-bundle/account/time binding at adapter boundary | WAITING_EXTERNAL: actual DE40 economics, independent verification and cash-at-stop/rounding validation |
| Fixed cash risk policy | `domain.risk_policy.FixedCashRiskPolicy` | IMPLEMENTED; no default cash budget | USER_AUTH: concrete reviewed cash budget/currency/provenance; BASE/BOOST/HIGH remain RESEARCH |
| Loss/exposure policy | `domain.loss_admission.LossExposurePolicy` | IMPLEMENTED; explicit caps/counters | USER_AUTH: concrete caps, scope, drawdown definition and period/reset policy |
| Loss/exposure observation provenance | `LossExposureObservation`, `state.loss_exposure` checkpoint | IMPLEMENTED values/policy/time; MISSING source/account/period provenance binding | WAITING_EXTERNAL: authoritative realized/unrealized loss and inventory; no synthetic zero-loss observation |
| NextGen protection | `evaluate_nextgen_execution_protection` | IMPLEMENTED; recomputes canonical risk/loss/session decisions and freshness | WAITING_EXTERNAL: actual host/feed/spread/inventory/loss/session facts. ALLOW_EVIDENCE is not execution authorization |
| Lifecycle/checkpoint/reconciliation/telemetry | existing broker owners and journal | IMPLEMENTED; no second lifecycle/store/journal justified | WAITING_EXTERNAL: real ACK/REJECT/PARTIAL/FILLED/CANCELLED, reconnect and telemetry evidence |
| PAPER/DEMO readiness provenance | `readiness`, `demo_evidence_authorization` | IMPLEMENTED summaries and separate scoped authorization; final PAPER booleans default false | USER_AUTH for first actual evidence order and separately normal PAPER; real broker gates WAITING_EXTERNAL |
| Reserved restart / ambiguity | reservation owner, pinned query request, read-only lookup, reconciliation | IMPLEMENTED; immutable attempt, query first, no resubmit or slot release | WAITING_EXTERNAL: broker-side restart/tag/query evidence |

## REUSE before BUILD and bounded local follow-up

The existing readiness evaluator remains the only readiness owner. Its booleans
are evidence summaries, not collection, authentication or order submission APIs.
No additional readiness orchestrator, risk evaluator, PnL calculator, session
reset, lifecycle, reconciliation, store or journal is warranted.

Two narrow adapter/provenance gaps remain locally addressable: (1) bind the
existing economics conversion to an exact, independently reviewed Windows bundle,
account/symbol and observation time; (2) bind an existing loss checkpoint to an
explicit source digest, account and caller-supplied daily/weekly period boundaries.
Fingerprints prove integrity and binding, not broker origin or user authorization.
Both require independent evidence review before any readiness boolean changes.
The loss adapter must not compute drawdown from margin/notional/account allocation
or infer broker timezone/reset boundaries. Product numeric policies require
explicit review; this tranche supplies no product risk values.

Follow-up units: 2202 economics observation binding, 2203 loss observation
provenance, 2204 read-only Windows evidence/preflight instructions and final
composition conformance. Each closes only after local gates and both required
GitHub CIs are green. Further units require a concrete independently useful gap;
step numbers will not be padded to reach an arbitrary target.

## Boundary before the first actual DEMO evidence order

Require exact-head host/market-open/clock/session evidence, exact DEMO context,
verified broker economics and canonical sizing, reviewed fixed cash and
loss/exposure policies, fresh source-bound loss/inventory observations, complete
reconciliation, fresh feed/spread and current typed protection. Preserve one-key
PREPARED/reservation identity and consumed guard. Ambiguous reserved attempts
require query/reconciliation; UNKNOWN/NOT_FOUND never means safe resubmit.

Only a subsequent separately scoped user authorization may permit the first
actual broker side effect, after independent review and an authorized adapter.
Current software contains no trading submission path. Broker acceptance, venue
IDs and fills may never be inferred from PREPARED/reservation/local tags. No
automatic PAPER/LIVE promotion, slot release, retry or refreshed original evidence.
Five main-only PR DB gates and host lane 2122 remain WAITING_EXTERNAL; earlier
VERIFIED Neon evidence is not discarded and is not relabeled as a current full run.
