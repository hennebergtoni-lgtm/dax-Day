# IG session and dimensional evidence hardening — Step2236

## One existing session owner

IgDemoReadOnlyClient consumes exactly one login per instance. Successful repeated GETs reuse the same CST/security tokens. HTTP rejection, malformed response, missing token, or unknown transport exception latches QUERY_REQUIRED; no further GET or relogin is allowed. Existing tokens permit one DELETE cleanup and are discarded even if cleanup fails. No dealing route is added. Credential-free session_health reports local lifecycle/read count and leaves feed/inventory truth UNKNOWN. A new owner instance is not automatic recovery authorization: the existing runner aborts; separately reviewed acquisition/reconciliation remains necessary.

Official IG V1/V2 session documentation supports token reuse and expiry handling; it does not explain the host401 cause. The precise cause remains UNKNOWN. Safe transport errors suppress injected exception text. Finite timeouts are required. Tests cover401/429/503/None/empty array/malformed objects, login ambiguity, no replay, cleanup, pagination and health separation.

## Full Expected vs Observed identity

The existing research conformance owner gains compare_full_evidence_identity, requiring semantic component SHA256 pins for dataset/data contract, engine/strategy/code, risk/execution assumptions, cost, session/timezone, adapter/broker context, lifecycle. Dimensional DATA/CLOCK/SIGNAL/EXECUTION/COST/BROKER/LIFECYCLE drift is explicit. A missing component is UNKNOWN. This diagnostic cannot replace frozen expected-decision conformance, the existing RunManifest, trial registry, release bundle or readiness owner. Component manifests must contain actual complete semantic identities; hashes alone are not proof.

## TCA starts before request

The existing failure_analysis research diagnostic owner gains observed_execution_costs. Its closed schema requires source/broker-context pins, reference price, arrival bid/ask/time, request/response times, desired native quantity and explicit tick size. Fill price/time/native quantity must be observed together. Decimal strings preserve native precision; native price-grid mismatch is visible using tick size. Metrics distinguish reference shortfall, arrival slippage, spread, explicit cost and cash conversion when economics is supplied. Missing costs/economics stay unknown. Client request-response time is not broker-internal latency.

A single fill below desired quantity is not proof of terminal partial fill or cumulative quantity. Missing fill remains UNRESOLVED. No invented broker IDs/history, opportunity movement, account-equity series or synthetic real-broker assertion. Broker raw evidence integration remains WAITING_EXTERNAL. Existing broker lifecycle/reconciliation remain the cumulative truth owners.

## Validation and safety

New focused tests plus full mandatory CI validate this tranche. Runtime remains NONE/false, hard DEMO endpoint only, no LIVE/dealing/slot-release/retry/state reset. Source snapshot and Candidate finalization semantics remain unchanged and quarantined pending six Attempt03 originals.
