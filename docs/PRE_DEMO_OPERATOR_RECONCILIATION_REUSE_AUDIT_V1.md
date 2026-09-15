# Pre-DEMO operator / reconciliation REUSE audit

Step 2207. Pinned input: `96c22897194015a7b25e8f6894b932552b641c06`.
Base/main: `e0784ebfc11bee28475fd9c3385be661af58a738`. No start drift.
This is repository architecture/test evidence, not real Windows or broker evidence.
Step 2206 and host lane 2122 remain WAITING_EXTERNAL / USER_AUTH.

## REUSE decision

| Surface | Existing canonical owner | Decision |
| --- | --- | --- |
| Current strategy, plan, virtual position and runtime context | runtime.operator_snapshot.OperatorSnapshot, build_operator_snapshot | REUSE; add observation projection here, not another readiness orchestrator |
| Credential-free Candidate validation and current observation | candidate_operator_telemetry.validate_candidate_operator_snapshot; candidate_operator_query.build_candidate_operator_current | REUSE / harden finite values and observation times |
| Durable source files | scripts/mt5_shadow_supervisor.py: heartbeat.json, latest_bundle.json, candidate_operator_snapshot.json, candidate_checkpoint.json | REUSE read-only; no new store or aggregate journal |
| Database mirror | export_mt5_shadow_telemetry.py; migrations 0008/0009; cand001_operator_current; read_candidate_operator_runtime.py | REUSE; local console needs no database connection, migration or browser DSN |
| Host, feed, clock and redacted account | mt5_windows_bundle, mt5_feed_payload, mt5_host_contract, mt5_demo_account_context | REUSE strict parsers; clock_ok is an observation, not proof of reviewed broker timezone |
| Risk / loss / economics | domain.risk, risk_policy, loss_admission; nextgen_broker_economics; nextgen_loss_exposure_provenance | REUSE; absent observed policy/provenance remains unknown, never invented |
| Protection / consumed guard / local PREPARED | broker_execution_protection; nextgen_prepared_checkpoint | REUSE typed checkpoints; ALLOW_EVIDENCE is not order authorization |
| Reserved attempt / restart | demo_transport_attempt_reservation | REUSE pinned parse and demo_transport_restart_status; always query first, never resubmit/release |
| Broker lifecycle / checkpoint / order reconciliation / telemetry | broker_order_lifecycle; broker_execution_checkpoint; broker_reconciliation; broker_execution_telemetry_journal | REUSE; no second lifecycle or reconciliation engine |
| Targeted read-only lookup | mt5_demo_evidence_transport; scripts/mt5_demo_evidence_lookup.py | REUSE; targeted intent lookup does not prove complete account inventory/history |
| Static research website | web/index.html, web/status.json; check_web_status.py | KEEP STATIC; separate local operator page and explicit local GET-only endpoint boundary |

Minimal justified addition: a loopback-only HTTP read adapter and mobile page over
these existing files/read contracts. The existing supervisor remains the sole
writer/process owner. The console must not mutate checkpoints, publish intents,
read secrets into the browser or import MT5. No second state store/export journal.

## Reproduced input gaps

1. candidate_operator_query.build_candidate_operator_current validates the bar
   against queried_at but not snapshot generated_at. A payload dated 2099 with
   runtime.freshness_seconds=NaN is accepted at a 2026 query. Existing validator
   only checks number type and `< 0`. Fix finite/time validation at existing owner;
   preserve valid original snapshot bytes/fingerprint and original measured age.
2. BrokerOrderLifecycle and VenueOrderObservation accept requested_quantity=+Inf.
   With both quantities +Inf, reconcile_broker_order returns CONSISTENT. Direct
   constructors and lifecycle parser need finite canonical number validation.
   Valid finite equality/fingerprints must remain unchanged.
3. No browser runtime endpoint exists. Existing static website correctly refuses
   runtime health claims. Missing data, source failures and a stale Candidate
   behind a running host need explicit projection, not an inferred GREEN.
4. Snapshot/host maximum observation age is not a reviewed console policy.
   Show age and UNVERIFIED_THRESHOLD / UNKNOWN; do not invent a timeout.
   Feed has an authoritative per-bundle max_age_seconds: reuse it at query time.
5. Targeted reservation lookup is NOT an account-wide positions/orders inventory
   or proof that a bounded history window is complete. Console must display this
   boundary as UNKNOWN/BLOCKED, including when targeted open orders are empty.
   True account inventory scope/completeness and PnL calculation remain external
   evidence/contracts; do not promote summary booleans from fixtures.

## Public-project review input (retrieved 2026-09-13)

Primary documentation, no strategy transplant or copied numeric thresholds:

- NautilusTrader: https://nautilustrader.io/docs/latest/concepts/reconciliation/
  and https://nautilustrader.io/docs/latest/how_to/configure_live_trading/ .
  Startup and continuous reconciliation are separate. In-flight requests,
  external orders, partial fills and positions require venue reports. Missing
  reports and bounded history need explicit completeness, not absence inference.
  Its active reconciliation/repair behavior is NOT added to this observation-only
  tranche. https://nautilustrader.io/docs/latest/developer_guide/adapters/ documents
  distinct tracked/external/suppressed updates and one history cutoff.
- Freqtrade/FreqUI: https://www.freqtrade.io/en/stable/rest-api/ and
  https://www.freqtrade.io/en/stable/freq-ui/ . Remote monitoring can use a small
  client separate from the trading process; prefer loopback and protected tunnel.
  FreqUI also has controls, which this console deliberately does not implement.
  https://www.freqtrade.io/en/stable/advanced-setup/ distinguishes dry-run/live
  persistence. Here existing SHADOW stores remain unchanged.
- QuantConnect LEAN: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/brokerages
  documents disconnect/reconnect state synchronization, including fills observed
  after reconnect without assuming a fresh order callback. Reconciliation and
  existing account holdings must be considered:
  https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/reconciliation .
  https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/algorithm-control
  warns about external/manual interference. Here it is blocking evidence; no
  liquidation, cancellation, account claiming or automatic state repair.

## Adversarial coverage / evidence boundary

| Case | Existing contract / planned narrow test | Current evidence |
| --- | --- | --- |
| Existing position/order or manual order at startup | targeted lookup is insufficient; no complete inventory => UNKNOWN/BLOCKED | WAITING_EXTERNAL account inventory |
| Reserved attempt, lost connection after transport, reconnect finds fill | demo_transport_restart_status + reconcile_broker_order state/ID/fill mismatch | IMPLEMENTED; no blind retry, venue drill WAITING_EXTERNAL |
| Partial fill / local-venue quantity or price mismatch | broker lifecycle PARTIAL semantics; exact reconciliation comparison | IMPLEMENTED; finite input hardening required |
| Duplicate/out-of-order event | apply_order_event + telemetry journal duplicate keys/time order | IMPLEMENTED; relevant regression suite required |
| Incomplete/short history, empty orders with contrary deals | lookup blocks missing/ambiguous/contradictory results; completeness not inferred | IMPLEMENTED targeted lookup; complete scope WAITING_EXTERNAL |
| Symbol/account/server mismatch | strict DEMO account context + reservation/lookup preflight | IMPLEMENTED; real account WAITING_EXTERNAL |
| Clock drift/timezone mismatch | host clock_ok + explicit feed/host timestamp contract | IMPLEMENTED; real broker/session review WAITING_EXTERNAL |
| Web alive but snapshot stale / source unavailable | query-time bar age; no snapshot threshold => UNKNOWN, never cached healthy | local projection required |
| Runtime alive MT5 down / MT5 alive Candidate stale | bundle/heartbeat blockers independently override Candidate display | local composition tests required |
| Browser alive, API/source down | discard old green display; fixed safe error, no exception/DSN text | local HTTP/UI tests required |

## Rejected overengineering

No cloud dashboard platform, second readiness composer, live control API, second
PnL/risk/lifecycle engine, account claiming/repair loop, new persistent journal,
automatic restart resubmission, generated risk values or guessed freshness limits.
A runtime commit is a supervisor startup observation, NOT the webserver's current
checkout or a manually supplied expected SHA. Legacy heartbeats without build
observation remain parseable and display UNKNOWN.

Execution remains NONE / disabled. SHADOW only is authorized. DEMO/PAPER/LIVE are
not authorized. V11.2, CAND-001 strategy, costs, Acceptance and main are unchanged.

## Step 2210 boundary correction from new regression evidence

The initial placement preference above was tested against
`tests/test_candidate_hot_path_boundary.py`: operator_snapshot is a protected
Candidate hot-path owner and cannot import MT5 evidence modules. The outer
projection therefore belongs to the ALREADY EXISTING candidate_operator_query
read-model. operator_snapshot only reconstructs/verifies its own V3 contract.
No boundary test is weakened, no second read-model/MT5 connection is introduced.
This prospective decision follows new evidence and preserves historical results.

## Additional red-team evidence — Steps 2215 / 2216

Read-only in-memory SDK fixtures at `d7854e47cbc00c2843971760f1db72397bff4007`:

- VERIFIED P1: `mt5_demo_evidence_transport.query_mt5_demo_evidence` summed
  duplicate deal rows before deduplicating ticket IDs. Requested quantity 2.5,
  one unique ticket 501 with volume 1.25 delivered twice, history order FILLED
  with remaining 0: actual MATCHED / fill 2.5. Expected BLOCKED because unique
  fill evidence is only 1.25. Step 2215 deduplicates immutable deal evidence by
  positive ticket before deterministic aggregation; conflicting duplicate ticket
  fields and missing ticket fail closed. Existing unique fill/venue fingerprints
  remain unchanged; raw transport row counts remain honest. No venue repair.
- VERIFIED P1: the same owner checked the normalized DEMO account only before
  the three SDK reads. A fixture changing its account to REAL during deal-history
  read still returned MATCHED for the bound DEMO request. Expected BLOCKED with
  no venue observation. Step 2216 must check the normalized context again before
  interpreting any query results. This cannot make multiple SDK reads an atomic
  broker snapshot or detect an account switching away and back between checks;
  exclusive terminal/account operation and real-host evidence remain mandatory.

Neither reproduction sent an order or used a real broker/MT5 connection. The
existing REQUESTED lifecycle comparison still blocks ACK/fill mismatch. These
findings therefore concern evidence integrity, not execution authorization.

## Step 2217 — open inventory observation, not account reconciliation

The REUSE search found no `positions_get` collection owner in the runtime/Windows
lookup surface; loss admission accepts already-normalized observation counts but
is not a collector. `mt5_demo_evidence_transport` now owns an optional typed,
redacted full-account open-order/position read observation. The existing Windows
lookup runner can embed it in the same output envelope using
`--include-account-open-inventory`. Default lookup result bytes are unchanged.
There is no second store/journal, risk calculation or account reconciliation owner.

Both SDK legs must succeed and the normalized account must remain the bound DEMO
context before/after. Unknown enums, invalid finite quantity/price, contradictory
object duplicates or failed legs block; absence is not inferred from failure.
Any existing position or open order is explicit blocking evidence even if its
transport tag matches this attempt. No external object is claimed or repaired.
Local collection start/end is distinct from broker event time, feed/snapshot time
and browser fetch. Reads are explicitly NON-ATOMIC; an empty successful open
observation proves neither complete history nor resolved submission outcome.
Current scope/freshness is rechecked with the existing reserved QUERY validator
before and after optional collection. Real account inventory, broker precision,
broker-side history completeness and exclusive-terminal operation remain external.
