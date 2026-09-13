# Monday pre-DEMO evidence — Step 2205

Date: 2026-09-13. Target observation window: Monday, 2026-09-14.
This is an evidence handoff, not a PAPER/DEMO/LIVE execution authorization.
Reuse `CAND001_WINDOWS_SHADOW_DEPLOYMENT_RUNBOOK_V1.md` for host lane 2122.
Its historical real-host findings remain intact, including configured but not
yet market-open-verified broker timezone. No commands here were run on a real
Windows/MT5 host by this Work tranche.

## Exact-head and isolated SHADOW evidence

First read PR #109's current head and required-check results; compare the host
checkout using the existing parity script. Do not change an unsynced/dirty host
or start another scheduled runtime. Retain full Git SHA, interpreter/environment,
parity output and observation times. Follow the existing isolated one-shot and
scheduled restart instructions; do not mix scheduled and preflight state folders.

Required real results: host GREEN, current market-open DE40 CLOSED-M5 (bar 0
excluded), supported broker clock/timezone/DST interpretation and session date,
Candidate manifest/checkpoint/operator evidence and non-regressing overlap/restart.
Configuration alone, weekend ticks, another symbol or Linux PowerShell tests are
insufficient. No reset or timezone is inferred by the new source bindings.

Reuse the existing probe with the *independently supported* timezone, exact
configured symbol and existing reviewed freshness configuration. For example:

```powershell
& '<EXISTING_MT5_PYTHON>' scripts\mt5_windows_probe.py --symbol '<EXACT_SYMBOL>' --broker-timezone '<VERIFIED_BROKER_TIMEZONE>' --bars 20 --max-age-seconds '<REVIEWED_FEED_LIMIT>' --timestamped --output '<NEW_EVIDENCE_PATH>\probe.json'
```

These placeholders must be resolved from actual reviewed host configuration;
they are not defaults or new risk policies. The existing probe can select a
market-data symbol; it has no trading API. Preserve its credential-free original
bundle, SHA256, redacted account fingerprint, server, symbol and observation time.
DEMO must be observed from exact MT5 runtime account-mode constants. REAL,
CONTEST, UNKNOWN, ambiguous symbol, shifted/stale clock or missing feed stops this
lane. Broker `trade_allowed` is an observation, not bot execution authorization.

## Economics, product policy and loss source packets

Economics: retain the original probe and independently review its exact DEMO
account/server/symbol, currencies, contract/tick values and volume constraints.
Record the verification artifact digest and the bundle digest it verifies.
`bind_verified_windows_broker_economics_to_risk_inputs()` consumes the exact pinned
bundle/context, original observation time and review digest, then delegates to
the existing economics conversion. It requires GREEN/current source and consistent
explicit timezone; it does not authenticate the review or set PAPER readiness.
Validate canonical Risk V1 quantity rounding and cash-at-stop on real economics.
Margin, notional and capital allocation are not cash loss at stop; cash-at-stop
sizing is not a guarantee against costs/gaps/slippage. Costs remain unchanged.

Product review must explicitly supply currency/per-trade fixed cash risk and
daily/weekly drawdown caps, consecutive-loss/open-position limits, account versus
instrument scope, drawdown calculation definition, period/reset boundaries and
freshness/spread limits. Use existing `FixedCashRiskPolicy`, `LossExposurePolicy`
and session policy owners. No BASE/BOOST/HIGH research value, fixture budget or
synthetic zero inventory/loss may become a product value automatically.

Loss source: obtain actual read-only account/position/history evidence, redact
personal identifiers and retain source digests and timestamps. Independently
validate the already-computed canonical observation against those records and
the approved drawdown/scope definition. Observation production/calculation and
reset semantics remain explicitly deferred by Step 2166 until reviewed; the new
adapter implements **no** PnL calculator, default reset or missing-data-to-zero
conversion. An MT5 profit field alone is not daily/weekly drawdown.

Build the existing `LossExposureObservationCheckpoint`; attach
`LossExposureObservationProvenance` with exact account context, source digest,
calculation-contract and policy-review digests, and explicit aware daily/weekly
intervals. Its strict codec preserves original checkpoint bytes. Check
`assert_loss_exposure_provenance_compatible()` against independently pinned
source/account/policy and current time before existing protection composition.
Digests bind content; they do not prove broker origin, review issuance or approval.
Do not allocate another store/journal or replace the authoritative guard/attempt.

## Reserved attempt read-only lookup

Only use an independently valid existing reservation, exact attempt key/pin and
new same-context Windows bundle. Do not create a reservation from fixture
Protection/authorization merely to run this command. The existing preparation
script accepts an explicit history window; cover the requested observation time.

```powershell
& '<EXISTING_MT5_PYTHON>' scripts\prepare_mt5_demo_evidence_lookup.py --state-dir '<EXISTING_ATTEMPT_STORE>' --attempt-key '<EXACT_KEY>' --reservation-fingerprint '<PINNED_SHA256>' --bundle '<CURRENT_PROBE_JSON>' --history-from '<EXPLICIT_AWARE_START>' --history-to '<EXPLICIT_AWARE_END>' --output '<NEW_REQUEST_JSON>'
& '<EXISTING_MT5_PYTHON>' scripts\mt5_demo_evidence_lookup.py --state-dir '<EXISTING_ATTEMPT_STORE>' --attempt-key '<EXACT_KEY>' --reservation-fingerprint '<PINNED_SHA256>' --bundle '<CURRENT_PROBE_JSON>' --request '<NEW_REQUEST_JSON>' --output '<NEW_RESULT_JSON>'
```

The operational runner now revalidates the pinned reservation, request identity/
quantity, current host/feed and QUERY authorization before SDK initialization
and again before reading. A history window never extends grant/freshness validity.
The injected low-level lookup remains a technical API, not an authorization owner.
Retain the runner envelope, request/result digests and current-bundle/preflight
provenance. Queries may be repeated; they never save state or submit an order.
NOT_FOUND/UNKNOWN/AMBIGUOUS/error/stale/contradictory evidence cannot free the slot
or permit resubmit. Feed returned observations through existing reserved-query
reconciliation and broker telemetry owners; no synthesized ACK/venue ID/fill.
Local magic/comment derivation is not proof of actual broker tag preservation.

## First-side-effect STOP

After independent exact-head/diff/CI/safety review, require real current host,
clock/feed/session/account/economics evidence; reviewed concrete risk/loss policies;
fresh source-bound loss/inventory, complete reconciliation and typed protection;
one deterministic intent/client/consumption identity with durable authoritative
guard/PREPARED/reservation. Restart/uncertain state means query/reconcile first.

The first actual DEMO evidence order still needs a **separate explicit bounded
user authorization** and a separately authorized submission implementation.
Its scope must name DEMO account/server/symbol, purpose, validity, attempts and
risk/loss constraints. Existing scope-valid/ALLOW_EVIDENCE records do not authorize
execution. Normal PAPER requires its own real broker gates and independent user
authorization; LIVE stays unauthorized. No cancel/modify/blind retry/slot release.

Current truth: broker orders NONE; SHADOW authorized; DEMO/PAPER execution NOT
AUTHORIZED; LIVE NOT AUTHORIZED; `execution_capability=NONE`;
`order_execution_enabled=false`. Host lane 2122 and real venue/economics evidence
remain WAITING_EXTERNAL. Main-only PR DB steps remain skipped/WAITING_EXTERNAL.
