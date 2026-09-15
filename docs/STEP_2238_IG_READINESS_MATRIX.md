# Step2238 IG authenticated read matrix

Status date: 2026-09-15

## Final real-host closeout — authoritative

The exact-Step2244-head Windows/IG-DEMO run on
`ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2` satisfied the V3 availability and
read contracts: one authenticated session, exactly eight rows, 8/8 PASS,
10/10 derived stages PASS, successful evidence construction and cleanup, with
no retry/dealing/order and NONE/false. Step2238 is **COMPLETED / REAL-HOST
VERIFIED** for this bounded read-only acquisition contract.

All lower WAITING_EXTERNAL/next-run wording is historical. The raw PASS result
does not prove flat inventory, full history, canonical broker economics or any
execution lifecycle. Those limits are counted in the current M01 matrix.

## V3 availability closeout

The subsequent real host reached successful login and authenticated READ but a
Python exception between login and matrix construction bypassed the entire V2
matrix. That absence carries no endpoint classification. V2 remains historical.

V3 creates the raw eight-row ledger before login. Each ordered resource is
called through a collector-level outer guard in addition to adapter
normalization. Unexpected exceptions become `UNKNOWN` with
`IG_READ_<RESOURCE>_UNCLASSIFIED`; they never expose exception text. Remaining
independent GETs run once unless the authenticated client definitively changes
to a non-authenticated state, in which case unattempted rows become BLOCKED.

The raw matrix is independent of login-context projection, matrix decoration,
inventory/history/market/M5/clock derivation, dependent conclusions, evidence
enrichment, component construction, cleanup, hashing and publication. A failure
in any of those stages can block acceptance but cannot remove raw rows from the
single structured stdout result. The acceptance invariant is:

`login_success == true  =>  readiness_matrix_row_count == 8`

Failure injection covers every resource, invalid resource result types, lost or
unreadable auth state, each derived stage, cleanup, finalization and publication.
New artifacts use `DAXLAB_IG_PREDEMO_READINESS_V3`, manifest V3 and default
`.runtime/ig_predemo_readiness_2238_v3_attempt_01`; V2 artifacts are retained.

## Real-host input retained

The real Windows run at `98de1476cde6667ee07f5fbc97d52de0f6da7dcd`
proved the host preflight, collector precheck, single login entry, structured
process exit and cleanup contracts. The authenticated phase then stopped at the
first read with `IG_SESSION_READ_FAILED_NO_RETRY`. That historical result is not
rewritten and does not prove which IG resource failed.

Historically Step2238 therefore remained **IMPLEMENTED / WAITING_EXTERNAL**. M01 and the 27
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
| `WORKING_ORDERS_A` | `GET /workingorders`, v2 | `workingOrders[]` |
| `MARKET_V4` | `GET /markets/{epic}`, v4 | `instrument`, `dealingRules`, `snapshot` |
| `ACTIVITY_HISTORY` | `GET /history/activity`, v3 | `activities[]`, `metadata` |
| `M5_PRICES` | `GET /prices/{epic}`, v3 | `prices[]`, `metadata` |
| `POSITIONS_B` | `GET /positions`, v2 | `positions[]` |
| `WORKING_ORDERS_B` | `GET /workingorders`, v2 | `workingOrders[]` |

The earlier `/working-orders` route was rejected by the real gateway. The final
contract uses `/workingorders` v2, matching the official IG Java/.NET runtime
samples and the successful final real-host run. Activity history uses the
documented 10–500 page-size range. Prices retain `resolution=MINUTE_5`, bounded
`max`, and `pageSize=0`, which the v3 contract defines as paging disabled.

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

Historical schema `DAXLAB_IG_PREDEMO_READINESS_V2` publishes `READ_MATRIX.json`
alongside the existing sanitized components in its non-overwriting v2 namespace. An
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
