# Step2238–2240 pre-DEMO readiness program

## Decision

Repository implementation is complete for the Step2238 read-only evidence
collector and the fail-closed IG bindings added in this tranche. Real IG values
have not yet been collected with this exact head, so Step2238 is
**IMPLEMENTED / WAITING_EXTERNAL**, Step2239 is **IMPLEMENTED /
WAITING_EXTERNAL**, and Step2240 is **IN_PROGRESS / BLOCKED**. M01 remains
**IN_PROGRESS**. Readiness is **NOT READY**.

The implementation commit is

`2e01303befe70b3720d9ed5b370aa03624b7599f`.

Effective safety state is unchanged:

- `execution_capability=NONE`;
- `order_execution_enabled=false`;
- no DEMO order in this program;
- LIVE is prohibited.

Step2233 and Step2237 remain **COMPLETED / VERIFIED**. Sentinel, Helperbot and
Multi-Market expansion remain queued.

## Step2238 — one-session IG read-only evidence

`scripts/run_ig_predemo_readiness_2238.py` and its exact-head isolated Windows
wrapper collect, in one authenticated session and with one cleanup:

1. pseudonymous active-account context from the login response;
2. account balance/currency context;
3. positions and working orders before and after all other reads;
4. IG market v4 instrument, quote, margin and native dealing rules;
5. a bounded seven-day detailed account-activity scope with paging truth;
6. canonical finalized M5 history and true-close freshness;
7. HTTP server-date/request timing provenance when supplied.

The bundle contains `READINESS.json`, `ACCOUNT.json`, `INVENTORY.json`,
`MARKET.json`, `CLOCK.json`, `HISTORY_SCOPE.json`, `MANIFEST.json` and
`SUMMARY.json`. Deal and account identifiers are represented only by SHA-256
context fingerprints. Request IDs are hashed. Tokens, headers and credential
values are never emitted. Files are written only into a new namespace and are
hash-bound by the manifest; a partial publication is retained on failure and is
never overwritten.

The client remains pinned to `demo-api.ig.com`; outside login/logout, only GET
is allowed. The new reads are `/markets/{epic}` v4 and bounded
`/history/activity` v3. No dealing method exists. IG documents that session v2
binds CST to the client and X-SECURITY-TOKEN to the current account, and that
positions, working orders and activity history have read endpoints. The same
official reference distinguishes acknowledgement from later confirmation,
which is retained for Step2240 rather than treated as immediate fill truth:

- <https://labs.ig.com/rest-trading-api-guide.html>
- <https://labs.ig.com/rest-trading-api-reference.html>
- <https://labs.ig.com/reference/session.html>
- <https://labs.ig.com/trading-basics.html>

## Step2239 — broker-bound risk/session admission

`src/daxlab/runtime/ig_predemo_safety.py` is a provider binding, not a new risk
engine. It delegates completed numeric inputs to canonical
`InstrumentRiskInputs`, after verifying the Step2238 envelope, environment,
fingerprint, account-context fingerprint, stable bracketed inventory, bounded
history scope, currency, native size bounds/grid, tick/value semantics and stop
rules.

Missing values produce explicit blockers. In particular, `tick_size` is not
derived from `decimalPlacesFactor` or `scalingFactor`; `quantity_step` and
`quantity_max` are not defaulted; `valueOfOnePip` alone is not promoted to
cash loss per price unit. A stable pair of inventory reads is interval-bound
evidence, not an absolute historical flatness claim. Any foreign/manual position
or order blocks admission.

The existing Fixed-Cash Risk, loss/exposure, durable session-admission and
one-trade-per-session owners remain authoritative. They cannot be evaluated as
real-broker VERIFIED until the exact-head Step2238 bundle supplies all required
native values and session context.

## Step2240 — IG lifecycle safety

The provider binding codifies these transitions around the existing reservation,
lifecycle, reconciliation, checkpoint and protection owners:

| Observation | Required next action | Terminal truth |
| --- | --- | --- |
| PREPARED | reserve before transport | no |
| missing reservation | block | no |
| REQUEST_SENT / TIMEOUT / UNKNOWN | `QUERY_REQUIRED` | no |
| PARTIAL / DUPLICATE / OUT_OF_ORDER | reconcile | no |
| ACK | wait or query | no |
| REJECT / FILLED with incomplete query scope | `QUERY_REQUIRED` | no |
| REJECT / FILLED with complete broker scope | reconcile terminal evidence | only after reconciliation |

Every directive hard-codes no resubmit and no session-slot release. The generic
local owners already cover durable reservation, duplicate/out-of-order events,
partial fills, tamper-evident restart state, reconciliation and independent PTC.
However, the current reservation builder is still bound to the legacy MT5 bundle
type and no native IG submit/confirm/inventory-history adapter exists. Gates
19–22 and 25 therefore remain BLOCKED rather than being cosmetically promoted.
Gate26 remains BLOCKED until all other gates are real-evidence VERIFIED and a
separate bounded `NONE → DEMO_ONLY` package is reviewed.

## Exact 27-gate state before the Windows run

| Status | Gates | Count |
| --- | --- | ---: |
| VERIFIED | 1, 2, 4, 5, 6, 23, 24, 27 | 8 |
| IMPLEMENTED | — | 0 |
| WAITING_EXTERNAL | 3, 7–18 | 13 |
| BLOCKED | 19–22, 25, 26 | 6 |

The new code materially narrows the blockers but cannot change a gate to
VERIFIED without its required real-host or real-broker evidence. Gate status is
therefore unchanged until the Step2238 bundle is returned and reviewed.

## One remaining host action

Exactly one Windows runner is required for Step2238. It uses the proven isolated
local-clone deployment owner, exact published-head and ancestry gates, external
credentials/runtime storage, a new namespace, fixed credential-free error codes,
and ownership-token cleanup. It does not mutate the existing checkout, delete
legacy evidence, retry authentication or access a dealing endpoint.

After the bundle is reviewed, Step2239 can either bind the observed values or
name the smallest missing native-economics evidence gap. Step2240 proceeds only
after that decision; no second Windows command is currently justified.
