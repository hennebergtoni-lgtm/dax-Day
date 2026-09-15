# M01 and bounded IG DEMO readiness — current acceleration matrix

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
