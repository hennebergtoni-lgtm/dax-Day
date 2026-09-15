# Step2238–2240 pre-DEMO readiness program

## IG HTTP transport/provider-health contract — authoritative (2026-09-15)

On real Windows head `8defee400ccb40f8bde379f0d3acfed316f9d07c`,
49/51 checks passed. The old combined IG HTTPS check alone failed on HTTP 5xx
after DNS and TLS succeeded. No login or broker call occurred.

The V2 preflight expands to 52 checks and models four layers independently:
DNS, TLS, required HTTP response transport, and optional IG provider health.
Because IG documents no anonymous health endpoint, the base response can prove
transport but leaves provider health UNKNOWN. Authenticated read-only Phase C
is the first valid application observation. No response still blocks before
login; an authenticated failure remains fail-closed with no retry. Failure
phase is derived from required failed dimensions.

Step2238 remains IMPLEMENTED/WAITING_EXTERNAL for one final-head run. Step2239,
Step2240, M01 and the 27 gates do not advance from this semantic correction.
NONE/false, no order and LIVE prohibition remain binding.

## Canonical Windows Python runtime selection — authoritative (2026-09-15)

Runtime-selection code head:
`30d9575fc8b8526e281a86c9717d19e9dda6b71b`; native Windows #8, DAX #719 and
research #1503 CI are GREEN.

The latest real Step2238 attempt stopped before authentication with
`PYTHON_COMMAND_RESULT_MULTIPLE`. The shared host owner now separates resolver
cardinality from interpreter identity and deterministically selects one runtime
only after version, architecture and exact project-origin parity. Equal
identities collapse, Store aliases are not started, invalid candidates are
excluded, configured `python` outranks the `py -3` fallback, and genuine
same-rank ambiguity blocks with a sanitized matrix. The 51-check preflight is
unchanged.

Step2238 remains IMPLEMENTED/WAITING_EXTERNAL pending exactly one final-head
Windows run. Step2239/2240, M01 and all 27 gates remain unchanged; NONE/false,
no order and LIVE prohibition remain binding.

## Full Windows host-lane audit — authoritative (2026-09-15)

Code head `6bf1a6bbbcc0af24ba35a6c8397a614f241013fe` supersedes the
earlier step-specific Python bootstrap. The current lane reuses the
Step2237-proven isolated local clone and direct script start, has one reusable
PowerShell runtime/process/output owner, one shared credential-shape owner and a
51-check aggregate preflight before authentication. The `-I -S`/runpy workaround
and `ig_predemo_python_runtime.psm1` are retired.

The audit fixed two latent contract divergences: canonical `IG_USERNAME` is now
shared by preflight and collector, and the exact local clone origin is verified
against its source checkout after the source checkout's GitHub origin/head gate.
Windows CI covers native PowerShell and path semantics but is not real-host
evidence. Linux is NOT_REQUIRED. Step2238 remains IMPLEMENTED/WAITING_EXTERNAL;
Step2239 IMPLEMENTED/WAITING_EXTERNAL; Step2240 IN_PROGRESS/BLOCKED; NONE/false,
no order and LIVE prohibition remain binding. Full architecture, preflight,
failure and evidence-transfer decisions are in
`STEP_2238_WINDOWS_HOST_LANE_AUDIT.md`. Lower sections retain the actual earlier
failure history but no longer describe the active runner.

## Step2238 total Python-boundary normalization — authoritative (2026-09-15)

The real Windows run on immutable head
`bbd1d29671f8d275179a38d04681dfdfca3fc248` reached deployment and WAIT but
returned `RUNNER_UNEXPECTED_FAILURE`. `legacy_partial_state=NONE_DETECTED`;
checkout/evidence were retained, execution remained disabled and no broker side
effect occurred. Because stderr is deliberately secret, the leaf cause is
UNKNOWN and must not be invented.

The successor uses `ig_predemo_python_runtime.psm1` as the sole owner for Python
discovery, version/executable identity, isolated import-origin checks and
collector bootstrap/result validation. Native PowerShell/.NET exceptions,
Get-Command null/array results, path failures, malformed JSON/property/type
shapes, import anomalies and collector failures have fixed credential-free
codes and failure-injection tests. No retry or broker action was added. Step2238
remains **IMPLEMENTED / WAITING_EXTERNAL**; Step2239/2240, M01 and the 27 gates
do not advance; NONE/false and the LIVE block remain binding.

## Step2238 Python-start hardening — authoritative (2026-09-15)

The real Windows run on `60539746383cbf0753d282f149d447d6e63c1130`
passed exact-head isolated deployment and reached WAIT, then stopped fail-closed
with `PYTHON_START_FAILED`. `legacy_partial_state=NONE_DETECTED`; existing
checkout and evidence were retained; execution remained disabled. Because STDERR
was intentionally suppressed, this record proves only that failure occurred at
the former undifferentiated Python launch boundary. It does not prove a Python
version, import failure, credential failure or IG failure. No login, broker read
or side effect is claimed.

The hardened wrapper now resolves exactly one application executable, verifies
Python 3.11+, checks executable identity, verifies that both `daxlab` and the
Step2238 collector import from the isolated exact-head clone, and launches the
collector through an isolated `-I -S` bootstrap with explicit clone-owned
`src` and `scripts` roots. All checks run before the credentials file is
consumed by the collector or any IG login occurs. STDERR remains suppressed.

The former umbrella codes are retired. Discovery, ambiguity, executable,
version, identity, missing script, import, import-origin, collector start,
missing/multiline/invalid result and exit-status mismatch each have a fixed
credential-free code. Step2238 remains **IMPLEMENTED / WAITING_EXTERNAL** until
the replacement exact-head run succeeds. M01, the 27 gates and NONE/false do not
advance. No DEMO order; LIVE prohibited.


## Decision

Repository implementation is complete for the Step2238 read-only evidence
collector and the fail-closed IG bindings added in this tranche. Real IG values
have not yet been collected with this exact head, so Step2238 is
**IMPLEMENTED / WAITING_EXTERNAL**, Step2239 is **IMPLEMENTED /
WAITING_EXTERNAL**, and Step2240 is **IN_PROGRESS / BLOCKED**. M01 remains
**IN_PROGRESS**. Readiness is **NOT READY**.

The implementation commit is

`29805ca7aa7d8bb3695846aa9db9a247b27e7fda`.

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
