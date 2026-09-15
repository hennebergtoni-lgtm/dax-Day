# Step2238 IG authenticated read matrix

Status date: 2026-09-15

## Real-host input retained

The real Windows run at `98de1476cde6667ee07f5fbc97d52de0f6da7dcd`
proved the host preflight, collector precheck, single login entry, structured
process exit and cleanup contracts. The authenticated phase then stopped at the
first read with `IG_SESSION_READ_FAILED_NO_RETRY`. That historical result is not
rewritten and does not prove which IG resource failed.

Step2238 therefore remains **IMPLEMENTED / WAITING_EXTERNAL**. M01 and the 27
pre-DEMO gates do not advance from this repository-only change. Effective safety
remains `execution_capability=NONE`, `order_execution_enabled=false`; no dealing
route, retry, relogin or order is present.

## Canonical authenticated-read contract

After exactly one successful IG DEMO login, the collector invokes these resources
in order. Each eligible GET is attempted once and never retried:

| Resource | Official REST contract | Required top-level shape |
|---|---|---|
| `ACCOUNTS` | `GET /accounts`, v1 | `accounts[]` |
| `POSITIONS_A` | `GET /positions`, v2 | `positions[]` |
| `WORKING_ORDERS_A` | `GET /working-orders`, v2 | `workingOrders[]` |
| `MARKET_V4` | `GET /markets/{epic}`, v4 | `instrument`, `dealingRules`, `snapshot` |
| `ACTIVITY_HISTORY` | `GET /history/activity`, v3 | `activities[]`, `metadata` |
| `M5_PRICES` | `GET /prices/{epic}`, v3 | `prices[]`, `metadata` |
| `POSITIONS_B` | `GET /positions`, v2 | `positions[]` |
| `WORKING_ORDERS_B` | `GET /working-orders`, v2 | `workingOrders[]` |

The prior `/workingorders` spelling was a repository mismatch and is replaced by
the documented `/working-orders` route. Activity history uses the documented
10–500 page-size range. Prices retain `resolution=MINUTE_5`, bounded `max`, and
`pageSize=0`, which the v3 contract defines as paging disabled.

Each matrix row publishes only `PASS`, `FAIL`, `BLOCKED` or `UNKNOWN`, endpoint
family, HTTP status class, an explicitly allow-listed provider error code,
response-shape status, UTC request/response timestamps, request-ID fingerprint
and fixed reason code. It never publishes raw headers, tokens, account IDs,
request IDs, credentials or raw response payloads.

Known HTTP failure and invalid response shape affect only that resource. A
transport exception is `UNKNOWN` and does not trigger a retry. A 401 or a safely
recognized invalid/missing session-token error changes the session precondition
to query-required; subsequent rows are `BLOCKED` without issuing another GET.
All previously attempted reads remain visible. Logout is attempted exactly once.

## Evidence and dependent conclusions

Schema `DAXLAB_IG_PREDEMO_READINESS_V2` publishes `READ_MATRIX.json` alongside
the existing sanitized components in a new, non-overwriting v2 namespace. An
incomplete matrix is still hash-bound, read back and published with
`IG_READINESS_MATRIX_INCOMPLETE`, after cleanup. This is evidence of the read
failure, not acceptance evidence.

Inventory stability requires both position and working-order brackets. History
scope requires the activity result. Economics requires the market result and
remains `UNKNOWN` where native tick/quantity/value semantics are absent. M5
freshness requires a valid prices result. No negative result is treated as proof
of flat inventory, complete history, usable economics or fresh data.

## Next acceptance action

Run the one exact-head Windows wrapper once. If all eight rows pass, review the
hash-bound v2 evidence before Step2239 bindings. If one or more rows do not pass,
the single published matrix is the complete sanitized diagnosis for the next
repository decision; do not run manual endpoint commands.
