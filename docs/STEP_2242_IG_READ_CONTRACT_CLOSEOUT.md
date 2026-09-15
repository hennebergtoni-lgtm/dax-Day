# Step2242 — IG read-contract real-host closeout

Status: COMPLETED / REAL-HOST VERIFIED
Date: 2026-09-15  
Start head: `d7ad273e71a9ae993d8c28031e8c20d3a84e32d2`  
Branch: `nextgen-bot-line-v1`  
PR: #109 OPEN / UNMERGED  
Main at start: `e0784ebfc11bee28475fd9c3385be661af58a738`

Accepted runtime head: `20b1c86b5af771757d3557b6910e26501a419984`.

## Final replacement-contract evidence — authoritative (2026-09-15)

The later exact-Step2244-head Windows/IG-DEMO run used the final replacement
contracts and returned PASS for all eight required raw reads, including both
WORKING_ORDERS rows and ACTIVITY_HISTORY. Cleanup succeeded; the run used one
session, no retry/dealing/order, and retained NONE/false. The Step2242
real-provider recheck is therefore complete. The earlier 5 PASS / 3 HTTP_4XX
result remains historical evidence for the superseded request contracts.

## Real-host finding retained

The user-supplied Windows run is the only real-host/provider evidence for this
step. It proved one authenticated IG DEMO session and an eight-row matrix with
five PASS rows. `WORKING_ORDERS_A`, `ACTIVITY_HISTORY`, and
`WORKING_ORDERS_B` returned HTTP_4XX with no safely recognized provider code.
The matrix remained BLOCKED and the wrapper separately reported
`DEPLOYMENT_CLEANUP_FAILED_RETAINED`. It proved no order and no retry.

This implementation does not claim that the replacement contracts have passed
against the real gateway. That requires one exact-final-head replacement run.

## Contract comparison and decisions

### Working orders

The adapter sent `GET /working-orders` with VERSION 2. The current REST
reference names that hyphenated route, but both official runtime sample clients
use `GET /workingorders` with VERSION 2:

- IG Java sample, pinned commit
  `c9d8bcb6b3dede7657f5689c5f4d76a910494eb5`, `RestAPI.getWorkingOrdersV2`;
- IG .NET sample, pinned commit
  `d19c4b0da435a169f2883627e92570b827ff71a1`,
  `IGRestApiClient.workingOrdersV2`.

The same official sample DTO family retains the top-level `workingOrders` list
and nested `workingOrderData`. The real gateway rejected the hyphenated route
twice while the same session, headers, account context, and other versioned GETs
succeeded. The canonical request is therefore one `GET /workingorders`, VERSION
2. There is no fallback, alternate-path retry, relogin, or dealing call.

### Activity history

The existing v3 endpoint and VERSION header were correct. Its shared serializer
used `datetime.isoformat()` and emitted `+00:00`. The v3 request contract/sample
format is UTC `yyyy-MM-ddTHH:mm:ss`; `Z` and `+00:00` are outside that concrete
wire representation. The canonical serializer now converts aware inputs to UTC,
emits whole seconds without a zone suffix, percent-encodes the colons through
the existing transport, and fixes the collector query to exactly `from`, `to`,
`detailed=true`, and `pageSize`. Optional `dealId` and `filter` are absent.

The common query owner rejects naive times, non-positive intervals, intervals
over seven days, booleans/non-integers, and page sizes outside 10–500. The
response owner requires `activities`, `metadata`, and `metadata.paging`; it does
not follow `paging.next`, so bounded history is never promoted to complete venue
history.

### Safe provider error taxonomy

The old fixed allowlist omitted documented errors relevant to these GET
contracts. It now includes the documented date/page errors, restricted/revoked
API-key errors, account-trading allowance, and the explicit documented
`error.public-api.failure.*` values for encryption, KYC, missing credentials,
pending agreements, preferred-account state, product code, and stockbroking.
Only exact constants are admitted. Unknown codes remain `None`; raw bodies,
free-form text, headers, credentials, and account identifiers remain excluded.

### Deployment cleanup

The wrapper wrote its hash-verified temporary PowerShell module into the runner
owned deployment parent. Before deletion it re-ran `Test-RunnerOwnedDeployment`,
whose allowed child set intentionally contains only the marker, hooks directory,
and repository. Because the module copy was neither allowed nor removed, the
wrapper rejected its own file and retained the deployment.

The module path is now returned with the owner context and deleted after
`Remove-Module`, before the ownership check and recursive deployment deletion.
If that file cannot be removed, the exact owner check still fails closed and the
directory is retained. A primary collector failure continues to outrank the
secondary cleanup code, while both remain visible in wrapper output.

## Bot-Helper dogfood

The real failure shape is represented by a fixed 5-PASS/3-HTTP_4XX regression.
The producer evidence remains one eight-row matrix and one fingerprint.

| Role | Projected result | Preserved truth |
| --- | --- | --- |
| H | PASS | Valid bound runtime/evidence envelope is not relabelled as a broker failure. |
| D | PASS | The valid CLOSED-M5 observation remains usable data evidence. |
| B | BLOCKED | The three non-PASS broker reads produce `BROKER_READ_FAILED`. |
| S | BLOCKED | Any required read failure produces `READINESS_BLOCKED`. |
| O | PASS | The complete eight-row evidence remains referenced and projectable. |
| K | BLOCKED | Deterministic aggregation has no vote count; five PASS rows cannot outvote three required failures. |

The Candidate state is unchanged, no SHADOW step is admitted from the blocked
readiness evidence, and NONE/false remain typed and unchanged. This adds no new
truth, risk, state, execution, broker connection, or console owner.

The existing Operator GET now projects the safe fields `resource`,
`endpoint_family`, `status`, `reason_code`, `http_status_class`,
`provider_error_code`, and `response_shape_status` for every row. Provider codes
pass through the same exact allowlist as the adapter; a resealed unknown code is
dropped. The wrapper summary remains the owner for its primary error and the
secondary deployment cleanup code because deployment cleanup occurs after the
collector evidence has been finalized.

## Internal verification before publication

- focused IG/readiness/Bot-Helper suites: PASS;
- provider taxonomy and unknown-code secrecy cases: PASS;
- Working Orders path/version/response fixtures: PASS;
- Activity UTC serialization, URL encoding, bounds, page size, query and paging
  shape cases: PASS;
- T07/T14 5:3 no-majority dogfood: PASS;
- full local suite: PASS with environment-dependent skips only;
- Ruff full repository: PASS;
- Python syntax: PASS;
- final local two-pass acceptance: 972 PASS / 1 browser SKIP per pass; T01–T11,
  T13 and T15 PASS, T12/T14 locally INCOMPLETE solely because Chromium is not
  installed. CI sets the browser-required contract and must produce zero skips;
- dax-bot-1x-ci #734: PASS; both acceptance passes 973 PASS / 0 SKIP and all
  T01–T15 PASS;
- research-lab-ci #1518: PASS; both acceptance passes 973 PASS / 0 SKIP, all
  T01–T15 PASS, full suite 3472 passed / 1 conditional external skip;
- windows-host-lane-ci #23: PASS; both acceptance passes 973 PASS / 0 SKIP,
  native Windows PowerShell 5.1, PowerShell 7, host-focused tests, Ruff and syntax
  PASS.

The publication path initially based the first remote implementation commit on
an older Step2241 runtime tree, which reverted three accepted Step2241 documents.
The byte comparison caught this before acceptance. A normal fast-forward repair
commit restored those files; the repaired remote tree was proven byte-identical
to the locally accepted tree. No force update or historical rewrite occurred,
and only the later exact-head CIs above count as evidence.

No internal defect is deferred. Historical FOLLOW-UP WORK
DEBT=`EXTERNAL_ONLY` is **CLOSED** by the final replacement-contract evidence
above.
