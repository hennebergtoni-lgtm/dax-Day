# Step2243 — IG 8/8 Read Derivation Closeout

Status: COMPLETED / TECHNICALLY VERIFIED

## Pinned truth

- Start head: `5eca87b68b15fa5c82cb1dc1193364f28905bafe`
- Accepted runtime head: `c6c41581fcb6632e89e8d20d264e78756b314f93`
- Accepted runtime tree: `b45dc5261ba10c79e474967c624d8af12245b23b`
- Branch: `nextgen-bot-line-v1`
- PR: #109 OPEN / UNMERGED
- Main: `e0784ebfc11bee28475fd9c3385be661af58a738`

The user-supplied Windows/IG-DEMO result is real-host evidence for precheck
PASS, one login, no retry, no dealing, cleanup success and all eight required
GET rows PASS. It is not evidence that the ten derived stages passed.

## Exact historical failure classification

The supplied terminal envelope contains
`IG_READINESS_DERIVATION_INCOMPLETE`, but no derived-stage ledger. Therefore the
exact historical failed stage is `UNKNOWN_NOT_EMITTED`. Raw 8/8 success cannot
identify whether LOGIN_CONTEXT, INVENTORY, HISTORY, MARKET_ECONOMICS, M5, CLOCK
or another downstream projection failed. Assigning one would manufacture
evidence.

The repository defect was systemic diagnostic aggregation, not an endpoint:

1. the collector calculated ten internal stage outcomes but omitted them from
   its final stdout;
2. the persisted SUMMARY and component set did not carry an independent fixed
   derivation ledger;
3. the Operator GET exposed raw rows but only the generic aggregate derivation
   blocker;
4. runtime coordination treated broker binding blockers as B ambiguity and
   blocked S only for raw-read failures, obscuring Raw-vs-Derived authority.

## Decision: REFACTOR, with one adjacent repair

The existing owners remain canonical. A small composition refactor separates
two ledgers without creating a state engine, database, console or process:

- `authenticated_read_matrix`: eight broker-request outcomes, unchanged;
- `derived_processing`: the fixed ten stages in canonical order;
- `DERIVATION.json`: a hash-manifested component built by the existing evidence
  publisher;
- final Python JSON and PowerShell output: one safe row per derived stage;
- Operator GET: fixed stage/status/reason plus bounded counts and booleans;
- Bot Helper: B observes raw reads; S vetoes incomplete mandatory derivation;
  K cannot majority-vote 8/8 raw success over S; Candidate state stays unchanged.

The adjacent repair builds `DERIVATION.json` only after the
COMPONENT_CONSTRUCTION result is final, so the component and READINESS envelope
cannot disagree in memory. No provider-response data, exception text, URL,
credential or free provider text is projected.

## Ten-stage contract

The required set is owned once by `IG_DERIVATION_STAGES`:

1. MATRIX_CONSTRUCTION
2. LOGIN_CONTEXT
3. INVENTORY
4. HISTORY
5. MARKET_ECONOMICS
6. M5
7. CLOCK
8. DEPENDENT_CONCLUSIONS
9. EVIDENCE_ENRICHMENT
10. COMPONENT_CONSTRUCTION

Missing, malformed or unrecognized rows become safe UNKNOWN/BLOCKED outcomes;
they never become PASS. Every stage has failure injection. Every injected case
retains eight raw rows and the original raw PASS count.

## H/D/B/S/O/K dogfood

- H: runtime evidence remains independent; no derived failure rewrites it.
- D: M5/source truth is evaluated by its existing owner and remains separate
  from the other derived stages.
- B: eight successful GET outcomes remain eight successful broker-read facts;
  no generic broker-read failure is invented from a derived blocker.
- S: any required non-PASS derived stage emits READINESS_BLOCKED; no admission
  promotion occurs.
- O: existing GET projection exposes Raw and Derived separately with safe facts.
- K: no majority rule exists; the S veto blocks the cycle and preserves the
  original Candidate state.

## Acceptance evidence

Required CI on the accepted runtime head is green:

- dax-bot-1x-ci #736, run 34969302484;
- research-lab-ci #1520, run 34969302285;
- windows-host-lane-ci #25, run 34969302286.

Every workflow ran two independent Bot-Helper acceptance processes: 977 PASS,
0 SKIP, 0 FAIL per pass; T01–T15 all PASS. Research full suite: 3476 passed and
one conditional external-service skip. Windows verified native PowerShell 5.1
exact module import and failure injection plus PowerShell 7 compatibility.
Ruff, Python syntax and actual Chromium acceptance passed.

Local focused contract/coordination/operator suites passed. Local full-suite
execution passed with only environment-dependent browser/PowerShell skips; the
required CI supplied those dependencies. A polluted external Python search path
was detected during local full-suite execution; the rerun pinned this checkout's
`src`, verified module origin, and passed without modifying or deleting the
foreign checkout.

## Remaining truth and safety

All ten synthetic derived stages pass. The historical concrete stage cannot be
recovered from an outer payload that never contained it. One final-head real
Windows/provider run is therefore the only remaining Step2243 evidence action;
it will directly emit all eight raw rows and all ten derived rows in the same
invocation. No manual endpoint series or diagnostic commands are needed.

FOLLOW-UP WORK DEBT: EXTERNAL_ONLY.

Execution remains `execution_capability=NONE` and
`order_execution_enabled=false`. No endpoint/request, retry, dealing method,
order, strategy parameter, cost model, risk/loss policy, V11.2 reference or
CAND-001 decision sequence changed. LIVE remains prohibited. This step does not
promote Step2238, Step2239, Step2240, M01 or the 27 readiness gates.
