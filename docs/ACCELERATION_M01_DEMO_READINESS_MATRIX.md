# M01 and bounded IG DEMO readiness — current acceleration matrix

## Step2244 real-host evidence recount — authoritative (2026-09-15)

This section supersedes every lower current-status/count/next-run statement. The
lower sections remain immutable chronology for the failures and repairs that led
to this result.

The exact-Step2244-head Windows/IG-DEMO recheck on
`ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2` completed the one-session
read-only lane: preflight 50/52 PASS, zero required failures, one UNKNOWN and
one NOT_REQUIRED; one login; all eight raw reads PASS; all ten derived stages
PASS; all five required MARKET_ECONOMICS subchecks PASS; cleanup successful.
There was no retry, dealing call or order. Effective safety remained
`execution_capability=NONE` and `order_execution_enabled=false`.

Step2238 is therefore **COMPLETED / REAL-HOST VERIFIED** for its bounded
read-only evidence-acquisition contract. This does not mean every value carried
by the resulting components is execution-ready. A successful projection proves
that the source/shape/derivation contract ran; it does not convert absent
provider-native economics into verified risk inputs.

### M01 evidence recomputation

| M01 requirement | Status | Current evidence / remaining limit |
| --- | --- | --- |
| Exact runtime head | VERIFIED | The supplied recheck was explicitly bound to `ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2`. The later closeout commit is documentation/test continuity only. |
| Windows runtime | VERIFIED | The one-command Windows lane reached authenticated READ and cleanup after the 50/52 preflight. |
| IG DEMO environment | VERIFIED | One authenticated session used the hard-pinned IG DEMO endpoint. |
| Account-context projection | VERIFIED | ACCOUNTS and LOGIN_CONTEXT completed in the same authenticated session. This is scoped projection evidence, not disclosure of an account identifier. |
| Exact DEMO account identity/binding | WAITING_EXTERNAL | The supplied closeout facts do not include the pseudonymous account-context fingerprint/value needed to audit exact selected-account binding. |
| Server/environment identity | VERIFIED | The provider environment is the hard-pinned IG DEMO API; no LIVE endpoint or account switch was used. |
| Instrument identity | VERIFIED | MARKET_IDENTITY PASS binds the response `instrument.epic` to the requested DAX EPIC. |
| MARKET_V4 read/shape | VERIFIED | MARKET_V4 raw PASS and MARKET_SHAPE PASS were observed. |
| Market status contract | VERIFIED | Required MARKET_STATUS subcheck PASS proves a recognized provider v4 status, not necessarily TRADEABLE at every later instant. |
| Price precision representation | VERIFIED | Required PRICE_PRECISION PASS proves valid decimal/scaling representation; it is not native tick size. |
| Finalized M5 contract | VERIFIED | Existing Step2237 real-host INTERVAL_START/true-close evidence remains valid; M5_PRICES and M5 derivation also passed in this run. |
| Feed freshness | VERIFIED | The prior accepted Step2237 real-host true-close freshness evidence remains the authority; this recount does not broaden its time scope. |
| Broker/server clock provenance | VERIFIED | CLOCK derivation completed and the real bundle contains clock provenance. This does not prove the session calendar or a DST boundary. |
| Timezone/session/DST semantics | WAITING_EXTERNAL | No exact current session-calendar/DST policy binding was supplied by the closeout facts. |
| Positions A/B read contract | VERIFIED | Both bracketed position reads passed in the same session. Read success alone is not a flatness claim. |
| Working orders A/B read contract | VERIFIED | Both bracketed working-order reads passed in the same session. Read success alone is not a zero-order claim. |
| Inventory state/foreign-manual clearance | WAITING_EXTERNAL | The supplied closeout facts do not state the counts, stable-bracket verdict or foreign/manual-inventory verdict. |
| Bounded activity-history derivation | VERIFIED | ACTIVITY_HISTORY and HISTORY derivation passed for the collector's bounded scope. Absolute venue-history completeness is not claimed. |
| Market-economics projection | VERIFIED | MARKET_ECONOMICS plus all five required subchecks passed. Provider-dependent/canonical economics remain separate. |
| Minimum deal-size rule | VERIFIED | DEALING_RULES PASS proves a positive provider minimum with a recognized unit; it does not prove the full quantity grid. |
| Native tick size | WAITING_EXTERNAL | Deliberately not inferred from decimal/scaling factors. |
| Quantity increment | WAITING_EXTERNAL | No provider-native `quantity_step` evidence was supplied. |
| Maximum size | WAITING_EXTERNAL | No provider-native `quantity_max` evidence was supplied. |
| Margin/canonical economics | WAITING_EXTERNAL | MARGIN_OR_SIZE_RULES and CANONICAL_ECONOMICS_CONSTRUCTION may honestly remain UNKNOWN; complete cash-loss/margin semantics are absent. |
| Stop/protection semantics | WAITING_EXTERNAL | The supplied facts do not prove complete native stop-distance, controlled-risk or request-time protection semantics. |
| Fixed-cash risk | WAITING_EXTERNAL | The canonical owner exists but cannot run broker-bound admission without tick/quantity/value semantics. |
| Loss/exposure/session policy | WAITING_EXTERNAL | Existing policy owners still need the exact account, inventory, economics and session bindings. |
| Attempt reservation | BLOCKED | The durable reservation is not yet bound to a native IG submission/deal-reference lifecycle. |
| Native reconciliation | BLOCKED | No IG submit/confirm/order/deal/position reconciliation path or real lifecycle evidence exists. |
| Restart/resume | BLOCKED | Read-only Candidate resume is VERIFIED historically; unresolved native IG execution-attempt recovery remains unimplemented/unproved. |
| Telemetry/operator evidence | VERIFIED | Existing real-host Operator/telemetry evidence remains valid; this run additionally emitted the raw, derived, economics and component evidence surfaces. |
| Unexpected inventory handling | IMPLEMENTED | Fail-closed handling exists and is synthetically tested; the supplied run does not provide the inventory values needed for a real-host verdict. |
| Execution remains disabled | VERIFIED | The real run retained NONE/false and used only GET/session cleanup. |

**M01 status: IN_PROGRESS / NOT READY.** The read-only acquisition lane is
closed, but broker-bound admission and native lifecycle readiness are not.

### Recomputed 27 Pre-DEMO gates

| Gate | Requirement | Status | Current evidence / remaining limit |
| ---: | --- | --- | --- |
| 1 | Exact final runtime head | VERIFIED | Real-host run bound to `ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2`; later closeout is non-runtime. |
| 2 | IG DEMO environment | VERIFIED | Successful authentication/read-only session on the hard-pinned DEMO API. |
| 3 | DEMO account identity | WAITING_EXTERNAL | Account-context projection passed, but the exact pseudonymous binding/value is not present in the supplied closeout facts. |
| 4 | Instrument identity | VERIFIED | Required MARKET_IDENTITY PASS for the requested DAX EPIC. |
| 5 | Finalized market-data contract | VERIFIED | Historical real-host INTERVAL_START/true-close contract remains verified; current M5 read/derivation passed. |
| 6 | Feed freshness | VERIFIED | Retained Step2237 real-host true-close freshness evidence; no broader timeless claim. |
| 7 | Clock/session | WAITING_EXTERNAL | Clock provenance exists, but current timezone/session/DST binding is not fully supplied. |
| 8 | Understood inventory | WAITING_EXTERNAL | Position reads A/B passed; counts, stable-bracket result and foreign/manual clearance are not stated. |
| 9 | Working-order truth | WAITING_EXTERNAL | Working-order reads A/B passed; exact current counts/history completeness are not stated. |
| 10 | Economics | WAITING_EXTERNAL | Required market projection passed, but canonical tick/value/quantity/margin/cost binding is explicitly incomplete. |
| 11 | Tick size | WAITING_EXTERNAL | Native tick size is absent and is not inferred from price precision. |
| 12 | Quantity increment | WAITING_EXTERNAL | Native quantity step is absent. |
| 13 | Min/max size | WAITING_EXTERNAL | Minimum dealing rule passed; full min/max/grid binding is incomplete because maximum/step are absent. |
| 14 | Stop/target constraints | WAITING_EXTERNAL | Full native distance/control/request-time semantics are not established by DEALING_RULES alone. |
| 15 | Fixed-Cash Risk | WAITING_EXTERNAL | Canonical owner lacks complete broker-native economics. |
| 16 | Loss/exposure admission | WAITING_EXTERNAL | Requires reviewed account, inventory, exposure, economics and policy inputs. |
| 17 | Session guard | WAITING_EXTERNAL | Requires exact broker clock/calendar/DST/session binding. |
| 18 | One-trade-per-session guard | WAITING_EXTERNAL | Durable owner exists but final IG session identity/policy binding is not verified. |
| 19 | Attempt reservation | BLOCKED | No native IG submission/deal-reference binding. |
| 20 | Idempotency | BLOCKED | No-blind-resubmit policy exists; native IG submission/idempotency lifecycle is absent. |
| 21 | Reconciliation | BLOCKED | No native IG order/deal/position/history lifecycle conformance or real DEMO evidence. |
| 22 | Protection | BLOCKED | Independent PTC exists; native request-time enforcement is absent. |
| 23 | Telemetry | VERIFIED | Existing real-host telemetry plus current raw/derived/component evidence surfaces. |
| 24 | Operator visibility | VERIFIED | Existing real-host Operator proof remains valid; current code projects the new fixed ledgers. |
| 25 | Restart/recovery | BLOCKED | Read-only resume is verified; unresolved native execution-attempt recovery is not. |
| 26 | Explicit DEMO_ONLY capability | BLOCKED | Capability deliberately remains NONE/false; no bounded native transport is activated. |
| 27 | Hard LIVE block | VERIFIED | The real run used only the DEMO read-only boundary; LIVE remains unauthorized. |

**Recomputed tally: 8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL /
6 BLOCKED / 0 UNKNOWN = 27.** No gate is newly promoted solely from successful
transport/derivation. The newly verified facts live inside Gates 3 and 7–14 but
do not complete those compound gates. Synthetic/CI is not real host, real-host
read is not execution, and readiness is not dealing authorization.

### Smallest remaining work

1. Step2239: acquire/review the exact account/inventory/session fields and the
   missing native tick/quantity/value/margin/stop semantics, then bind them to
   the existing Risk/Loss/Session owners.
2. Step2240: implement and independently verify the native IG reservation,
   submit/confirmation/query/reconciliation/protection/restart path while
   capability remains NONE.
3. Only after every gate is VERIFIED may a separate bounded NONE-to-DEMO_ONLY
   authorization package be reviewed. No order is authorized by this recount.

## Step2238 V3 eight-row availability overlay — 2026-09-15

The latest real host proved the lane through authenticated READ but did not emit
the promised matrix because one exception could escape before V2 list
construction completed. No account, inventory, economics, history or M5 gate is
promoted from an absent matrix.

V3 preallocates and preserves exactly eight raw rows after every successful
login, with one outer guard per GET and independent guards around all derived and
publication work. This is repository implementation evidence only. Counts remain
**8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL / 6 BLOCKED**; Step2238 is
IMPLEMENTED/WAITING_EXTERNAL, M01 IN_PROGRESS and DEMO NOT READY. NONE/false;
no order and LIVE prohibited.

## Step2238 authenticated-read matrix overlay — 2026-09-15

The real run at `98de1476cde6667ee07f5fbc97d52de0f6da7dcd`
proved host/precheck/auth entry and cleanup but stopped on an unnamed READ
failure. The v2 collector now aggregates all eight required resource outcomes in
one authenticated session. It corrects the official `/working-orders` v2 path,
keeps independent known failures observable, blocks only lost-auth dependents,
and publishes incomplete evidence with a fixed sanitized code.

No gate advances without the new real bundle. Counts remain **8 VERIFIED / 0
IMPLEMENTED / 13 WAITING_EXTERNAL / 6 BLOCKED**. Step2238 is
IMPLEMENTED/WAITING_EXTERNAL, Step2239 remains evidence-dependent, Step2240
remains repository-partial, and DEMO readiness is NOT READY. NONE/false; no order.
See `STEP_2238_IG_READINESS_MATRIX.md`.

## Step2238 collector-head overlay — 2026-09-15

Head `9ae082ce094967cedc3ab6525173a68041f76965` supplied real host
preflight truth but authenticated collection did not begin: the preserved
`HEAD_MISMATCH` came from an unbound process-CWD Git query. The corrected
collector checks its resolved exact-clone root with `git -C` and performs this
plus runtime/namespace/credential shape before AUTH wording.

No broker-readiness gate advances until the replacement evidence bundle exists.
Counts remain **8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL / 6 BLOCKED**;
M01 IN_PROGRESS, DEMO NOT READY, NONE/false, no order, LIVE prohibited.

## Step2238 collector-contract overlay — 2026-09-15

Real-host preflight is now materially proven: head
`ecd029924af4cd949676dace039c330fff31e12d` reported 50/52 PASS, zero required
failures, then began AUTH READ-ONLY. Its structured collector outcome was masked
by the wrapper exit contract. The corrected owner preserves allowlisted domain
errors, validates NONE/false and separates primary broker/read truth from
secondary cleanup/exit diagnostics.

This supplies host-lane evidence but not the missing account/inventory/economics
bundle. Gate counts remain **8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL /
6 BLOCKED**; M01 IN_PROGRESS; DEMO NOT READY; no order; LIVE prohibited.

## Step2238 IG HTTP semantics overlay — 2026-09-15

Real-host head `8defee400ccb40f8bde379f0d3acfed316f9d07c` produced
49/51 PASS. The sole required failure was the prior combined IG HTTPS check
observing HTTP 5xx; DNS/TLS passed and no authenticated phase ran. Preflight V2
now separates required `NETWORK_IG_HTTPS_TRANSPORT` from optional
`IG_PROVIDER_HEALTH`. A received status proves transport only; provider health
stays UNKNOWN absent a documented anonymous IG health endpoint and must be
observed during authenticated read-only collection. A no-response remains
BLOCKED and is attributed to NETWORK.

This corrects evidence semantics but adds no broker truth. Gate counts remain
**8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL / 6 BLOCKED**; Step2238 is
IMPLEMENTED/WAITING_EXTERNAL, M01 IN_PROGRESS, DEMO NOT READY, NONE/false, no
order, LIVE prohibited.

## Step2238 canonical Python selection overlay — 2026-09-15

Implementation head: `30d9575fc8b8526e281a86c9717d19e9dda6b71b`;
all three mandatory CI lanes are GREEN.

The real `PYTHON_COMMAND_RESULT_MULTIPLE` block is pre-authentication host-lane
evidence only. The runtime owner now probes and collapses actual interpreter
identities rather than blocking on command count, while keeping the existing 51
checks. This changes no broker gate: **8 VERIFIED / 0 IMPLEMENTED / 13
WAITING_EXTERNAL / 6 BLOCKED** remains authoritative. Step2238 remains
IMPLEMENTED/WAITING_EXTERNAL; M01 IN_PROGRESS; DEMO NOT READY; NONE/false; no
order; LIVE prohibited.

## Step2238 host-lane audit overlay — 2026-09-15

The repository-owned Step2238 lane now has a reusable Windows runtime owner, 51
aggregate preflight checks, 38 deterministic failure scenarios, a shared
credential-shape contract, staged/hash-bound evidence publication and dedicated
Windows CI. These are implementation and parity improvements, not new broker
truth. No exact-head Step2238 account/inventory/economics bundle exists yet.

Therefore the matrix remains **8 VERIFIED / 0 IMPLEMENTED / 13
WAITING_EXTERNAL / 6 BLOCKED**: VERIFIED 1, 2, 4, 5, 6, 23, 24, 27;
WAITING_EXTERNAL 3 and 7–18; BLOCKED 19–22, 25, 26. M01 remains IN_PROGRESS and
DEMO readiness NOT READY. Step2238 and Step2239 are
IMPLEMENTED/WAITING_EXTERNAL; Step2240 is IN_PROGRESS/BLOCKED. Linux is
NOT_REQUIRED for the Windows lane. NONE/false, no order and LIVE prohibition
remain binding. See `STEP_2238_WINDOWS_HOST_LANE_AUDIT.md`; all prior gate rows
remain historical truth until new real evidence is reviewed.

## Step2238 total Python-boundary normalization — authoritative (2026-09-15)

The immutable-head Windows run on
`bbd1d29671f8d275179a38d04681dfdfca3fc248` reached deployment and WAIT, then
failed closed with `RUNNER_UNEXPECTED_FAILURE`. No Step2238 evidence bundle was
accepted; `legacy_partial_state=NONE_DETECTED`, host state/evidence stayed
intact, execution stayed disabled and no broker side effect occurred.

The replacement provides exhaustive fixed-code normalization around PowerShell,
.NET paths, command-result cardinality, Python version/executable identity,
import JSON/origins and collector bootstrap, with injection tests and stderr
secrecy. This is implementation evidence only. M01 stays **IN_PROGRESS** and the
27-gate tally stays **8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL / 6
BLOCKED** pending a successful real run. NONE/false; no DEMO order; LIVE
prohibited.

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


## Step2238–2240 pre-DEMO program — authoritative (2026-09-15)

The exact-head one-session Step2238 collector, hash-bound credential-free
bundle, native IG v4 market/rule parser, bounded activity-history scope,
bracketed inventory truth, server-clock provenance and fail-closed Step2239/2240
provider bindings are implemented. No exact-head Windows Step2238 bundle exists
yet. Therefore M01 remains **IN_PROGRESS**, DEMO readiness is **NOT READY**, and
the gate tally remains **8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL / 6
BLOCKED**.

Step2238 and Step2239 are **IMPLEMENTED / WAITING_EXTERNAL**. Step2240 is
**IN_PROGRESS / BLOCKED** because the durable attempt reservation is still
MT5-bundle-bound and no native IG submit/confirm/reconciliation adapter has real
DEMO conformance evidence. See `STEP_2238_2240_PREDEMO_PROGRAM.md`. NONE/false
remains effective; no order; LIVE prohibited. Lower sections are historical.


## Step2233/2237 real-host closeout — authoritative (2026-09-15)

**Formal decision:** Step2233 and Step2237 are **COMPLETED / VERIFIED** on the
accepted runtime-evidence head
`62029df3353b74cc58884f06cd0c296ddd8d73cc`.

The user-supplied real Windows console record is:

- START: isolated exact-head local clone; existing checkout untouched;
- WAIT: one IG read-only session; Fresh Start; next true M5 close; Resume;
  Operator;
- SUMMARY: `SUCCESS / error_code=NONE`;
- namespace:
  `.runtime/ig_m5_contract_2237_interval_start_v2_attempt_03`;
- deployment cleaned; `execution_capability=NONE`;
  `order_execution_enabled=false`; no broker order and no LIVE authorization;
- `legacy_partial_state=DETECTED_RETAINED`.

This is sufficient for the two step closeouts because the exact runner emits
SUCCESS only after the published-head and isolated deployment gates, Windows and
import-parity checks, canonical INTERVAL_START contract check, an exclusive
fresh namespace, one login, two complete authenticated read-only probe cycles,
true-close freshness, strict unchanged-overlap and resume-anchor validation,
current Operator projection/fingerprint validation, one logout and
ownership-bound clone cleanup. The detected legacy partial worktree was
correctly retained and is **non-blocking contained technical debt**; it was not
pruned, deleted, migrated or used by the successful clone.

This closes the repeated market-data/session/state-resume evidence cycle. It
does **not** prove account identity, atomic flat inventory, broker/server clock,
DST/session policy, quote status, economics, native tick/quantity grids,
stop/target rules, broker history, execution reconciliation or dealing
lifecycle. M01 therefore advances to **IN_PROGRESS**, not COMPLETED. The current
27-gate result is **8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL /
6 BLOCKED**. Effective execution remains NONE/false; no DEMO order; LIVE
prohibited.

The accepted runtime commit and runner blobs remain immutable evidence:
PowerShell `cfad3ca6b4effb24fdd6dc0fa7ef0d7cb9fae63b`; Python
`8274ac096f33c8c2f2321964352e68ba3a59fb10`. A later documentation-only
closeout commit does not claim a different host run and does not alter these
runner blobs.

**Next work package:** Step2238 — M01 native IG read-only account, inventory,
clock, market-rules and economics evidence. Repository owners must first be
extended to validate and hash-bind those dimensions; afterwards exactly one new
Windows runner is required for that new evidence package. Re-running the
Step2237 runner is not required. Sentinel, Helperbot and Multi-Market expansion
remain deferred.

All lower sections that still describe Step2233/2237 as WAITING_EXTERNAL are
historical and superseded by this section.


## M01 current evidence

| M01 requirement | Status | Current evidence / remaining limit |
| --- | --- | --- |
| Exact code head | VERIFIED | Real wrapper proved deployed HEAD `62029df3353b74cc58884f06cd0c296ddd8d73cc` and a clean isolated tree before Python. |
| Windows runtime identity | VERIFIED | SUCCESS required Windows, exact Git identity and daxlab import parity from the isolated clone. Detailed OS/Python version remains useful release metadata but is not needed to re-open Step2237. |
| IG DEMO environment/account/server | WAITING_EXTERNAL | Real authentication to the hard-pinned IG DEMO endpoint is verified. The credential-free evidence deliberately omits account identifiers and does not bind a selected account/server context. |
| EPIC/instrument/symbol mapping | VERIFIED | Both real cycles required `/markets/IX.D.DAX.IFMM.IP` to return that exact EPIC and processed it through the pinned DE40/M5 mapping. |
| Market status/fresh quote | WAITING_EXTERNAL | Market detail was fetched twice, but SUCCESS does not require non-null TRADEABLE/bid/offer/update-time values or prove quote-time freshness. |
| Finalized M5 | VERIFIED | Real Fresh Start and Resume validated INTERVAL_START, true close, active-tail exclusion, continuity, uniqueness and no mutable finalized overlap. |
| Broker/UTC/session clock | WAITING_EXTERNAL | Local UTC ordering, monotonic wait and discontinuity guards passed. Independent broker/server clock and session binding were not established. |
| DST/session semantics | WAITING_EXTERNAL | No real session-calendar/DST boundary evidence was captured. |
| Full inventory/working orders/positions | WAITING_EXTERNAL | Both GET families succeeded, but inventory is explicitly non-atomic, history-incomplete and the reported SUMMARY contains no reviewed counts. Negative evidence is not flatness proof. |
| History scope | WAITING_EXTERNAL | No complete IG activity/deal/order-history scope was validated. |
| Economics/precision/min size/margin | WAITING_EXTERNAL | Market detail was read, but optional values were neither required nor bound to a reviewed broker economics contract. |
| Stops/freeze/protection | WAITING_EXTERNAL | Native dealing-rule values and request-time protection binding remain unverified. |
| Feed freshness | VERIFIED | Both cycles required finalized M5 age between 0 and 600 seconds from true `close_time`. |
| Risk/loss/session policy | WAITING_EXTERNAL | Existing policy owners are not yet bound to reviewed IG account/economics values. |
| Reconciliation | BLOCKED | Candidate overlap/resume is verified; native IG order/deal/position/history reconciliation is not integrated. |
| Restart/resume | VERIFIED | Real durable Fresh Start → later true close → state readback → exact anchor resume → Operator flow succeeded. Unresolved execution-attempt recovery remains Gate25, not this read-only M5 proof. |

**M01 status: IN_PROGRESS.** Six rows are VERIFIED, nine remain
WAITING_EXTERNAL and native execution reconciliation is BLOCKED. M01 is not
closed.

## 27 Pre-DEMO gates

| Gate | Requirement | Status | Evidence / remaining limit |
| --- | --- | --- | --- |
| 1 | Exact final runtime head | VERIFIED | Real exact-head isolated run on `62029df3353b74cc58884f06cd0c296ddd8d73cc`; subsequent closeout publication is documentation-only and retains the tested runner blobs. |
| 2 | IG DEMO environment | VERIFIED | Successful real authentication and reads through the client hard-pinned to the IG DEMO API endpoint. |
| 3 | DEMO account identity | WAITING_EXTERNAL | Account identifiers are intentionally excluded; no pseudonymous account-context fingerprint or selected-account binding exists. |
| 4 | Instrument identity | VERIFIED | Real market detail returned the configured DAX EPIC exactly; DE40/M5 mapping was consumed by both cycles. |
| 5 | Finalized market-data contract | VERIFIED | INTERVAL_START V2, `event_time=T`, `close_time=T+5m`, no extra grace and strict overlap all passed on the real host. |
| 6 | Feed freshness | VERIFIED | True-close-based maximum age 600 seconds passed twice. |
| 7 | Clock/session | WAITING_EXTERNAL | Local UTC/monotonic checks passed; broker/server clock, DST and session-calendar truth remain external. |
| 8 | Understood inventory | WAITING_EXTERNAL | Positions were queried twice, but values/atomicity/history were not reviewed; no flatness claim. |
| 9 | Working-order truth | WAITING_EXTERNAL | Working orders were queried twice, but values/history completeness were not reviewed. |
| 10 | Economics | WAITING_EXTERNAL | Point value, currency, margin and cost binding remain unverified. |
| 11 | Tick size | WAITING_EXTERNAL | No required native tick-size value was proven; digits are not a substitute. |
| 12 | Quantity increment | WAITING_EXTERNAL | No required native increment was proven. |
| 13 | Min/max size | WAITING_EXTERNAL | Broker minimum/maximum and policy bounds remain unbound. |
| 14 | Stop/target constraints | WAITING_EXTERNAL | Native minimum distances, controlled/guaranteed/trailing rules and price geometry remain unbound. |
| 15 | Fixed-Cash Risk | WAITING_EXTERNAL | Canonical owner exists but lacks a reviewed IG economics/account binding. |
| 16 | Loss/exposure admission | WAITING_EXTERNAL | Requires reviewed equity, inventory and exposure inputs plus policy binding. |
| 17 | Session guard | WAITING_EXTERNAL | Owner exists; real IG clock/session/calendar binding remains missing. |
| 18 | One-trade-per-session guard | WAITING_EXTERNAL | Durable guard exists but is not verified against the final IG session identity. |
| 19 | Attempt reservation | BLOCKED | Native IG attempt/deal-reference context is not integrated. |
| 20 | Idempotency | BLOCKED | No blind resubmit remains enforced, but native IG submission/idempotency semantics are not integrated. |
| 21 | Reconciliation | BLOCKED | Native IG orders/deals/positions/history conformance is absent. |
| 22 | Protection | BLOCKED | Independent PTC exists; native IG request-time enforcement is absent. |
| 23 | Telemetry | VERIFIED | Real fresh/resume evidence, fingerprints, current runtime health and credential-free persisted summary validated. |
| 24 | Operator visibility | VERIFIED | Real Operator snapshot and browser projection validation succeeded on the resumed current bar. |
| 25 | Restart/recovery | BLOCKED | Read-only Candidate resume is verified; process restart with unresolved native reservation/outcome is not. |
| 26 | Explicit DEMO_ONLY capability | BLOCKED | Conditional authorization exists, but capability remains deliberately NONE/false and no bounded transport is activated. |
| 27 | Hard LIVE block | VERIFIED | Hard DEMO endpoint/read-only boundary remained active on the real run; no order or LIVE call occurred. |

**Current tally: 8 VERIFIED / 0 IMPLEMENTED / 13 WAITING_EXTERNAL /
6 BLOCKED.** Readiness is not complete. There is no DEMO_ONLY promotion and no
order authorization is exercised.

## Smallest coherent remaining work packages

| Package | Gates / M01 dimensions | Deliverable | Windows requirement |
| --- | --- | --- | --- |
| Step2238 — native IG read-only readiness evidence | 3, 7–14 and evidence inputs for 16 | One canonical credential-free, hash-bound account-context/inventory/clock/market-rules/economics/history bundle using the existing session, probe and market owners. | **Exactly one new runner after repository implementation.** |
| Step2239 — broker-bound risk and session admission | 15–18 and completion of 16 | Bind Fixed-Cash, loss/exposure, session and one-trade owners to reviewed Step2238 values; deterministic policy tests. | No Windows run until the repository binding is complete; one combined verification can follow if needed. |
| Step2240 — native IG transport/lifecycle safety | 19–22, 25–26 | Existing reservation/PTC/reconciliation/protection owners adapted to IG; unknown outcome → QUERY_REQUIRED; partial/duplicate/out-of-order/restart tests; capability remains NONE. | Read-only conformance runner later; no order in these packages. |

## Roadmap impact

| Milestone | Status | Current truth |
| --- | --- | --- |
| M01 Real-host evidence | IN_PROGRESS | Step2233/2237 data/session/resume evidence closed; broker context/economics/inventory/history remain. |
| M02 First bounded DEMO | BLOCKED | Requires all 27 gates VERIFIED; no order now. |
| M03 Broker lifecycle truth | IN_PROGRESS | Local generic owners exist; native IG integration and real DEMO lifecycle evidence remain. |
| M04–M11 | IN_PROGRESS / PLANNED | Unchanged by this closeout. Reuse existing acceleration work. |
| M12 PRE-LIVE | PLANNED | No scaling or LIVE promotion. |

Sentinel, Helperbot and Multi-Market work are explicitly deferred.
