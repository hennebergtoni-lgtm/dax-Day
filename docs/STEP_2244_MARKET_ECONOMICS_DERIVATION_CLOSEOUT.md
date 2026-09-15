# Step2244 — MARKET_ECONOMICS Derivation Closeout

Status: COMPLETED / TECHNICALLY VERIFIED

## Pinned truth

- Start head: `9f8c34adc6e359ea314a7051dffcc256efad7ba2`
- Accepted runtime head: `e10065c1c0008173118c894e40a8c88aed2a43bc`
- Accepted runtime tree: `88733f151d8540043bd9fd573805857e6264f4f3`
- Branch: `nextgen-bot-line-v1`
- PR: #109 OPEN / UNMERGED
- Main: `e0784ebfc11bee28475fd9c3385be661af58a738`

The supplied exact-Step2243 Windows/IG-DEMO run is real-host evidence for one
login, no retry/dealing, successful cleanup, 8/8 raw reads and 9/10 successful
derived stages. MARKET_V4 is PASS. MARKET_ECONOMICS is the sole derived blocker
with the legacy aggregate reason MARKET_DERIVATION_FAILED.

## Root cause and evidence boundary

The successful provider GET is not defective and was not changed. The defect is
the former projection boundary after raw shape validation:

1. v4 top-level shape, provider EPIC identity, optional quote timestamp parsing,
   enum normalization and economics extraction ran in one function;
2. one broad exception handler converted every failure into the same aggregate
   MARKET_DERIVATION_FAILED code;
3. neither terminal output nor Operator evidence retained a safe substage;
4. processing success was named MARKET_ECONOMICS even though the result
   deliberately kept `economics_verified=false` because v4 does not supply all
   canonical Risk V1 quantity-grid and tick-value semantics.

Given the retained evidence, the historical throwing value is not recoverable.
After the raw adapter's valid top-level shape, the old code could still fail on
its EPIC/marketId identity assumption or unbounded numeric/time conversion. A
specific one is not guessed. The repair covers and diagnoses both classes.

The official IG v4 reference states that `instrument.epic` is the instrument
identifier while `marketId` is a distinct market identifier. It also defines
the broader market-status and instrument-type enums and describes
`updateTimestampUTC` as seconds since epoch. The implementation follows those
fixed structural contracts without treating provider-optional economics as
canonical execution truth.

## Decision: REFACTOR

No new Economics Engine or instrument owner was created. The existing collector
now owns one fixed, credential-free subcheck ledger:

| Subcheck | Stage requirement | Meaning |
| --- | --- | --- |
| MARKET_SHAPE | REQUIRED | instrument/dealingRules/snapshot object boundary |
| MARKET_IDENTITY | REQUIRED | exact response `instrument.epic` equals requested EPIC |
| MARKET_STATUS | REQUIRED | documented v4 status enum |
| PRICE_PRECISION | REQUIRED | finite non-negative integral decimal factor and positive scaling factor |
| CURRENCY | PROVIDER-DEPENDENT | one safe default three-letter provider currency when present |
| CONTRACT_ECONOMICS | PROVIDER-DEPENDENT | positive contractSize/lotSize/valueOfOnePip when all present |
| DEALING_RULES | REQUIRED | positive minDealSize with documented unit |
| MARGIN_OR_SIZE_RULES | PROVIDER-DEPENDENT | margin metadata remains UNKNOWN when v4 omits it |
| CANONICAL_ECONOMICS_CONSTRUCTION | NOT DERIVED FROM V4 | Risk V1 quantity step/max/tick-value semantics remain UNKNOWN |

Required non-PASS rows block MARKET_ECONOMICS with their exact fixed reason.
Provider-dependent absence remains UNKNOWN and does not manufacture a derived
failure. No decimal/scaling, marketId, spelling, MT5 or broker-limit inference is
used to fill canonical Risk V1 fields.

The numeric adapter now safely rejects booleans, null, non-finite and oversized
values. Optional invalid provider time is bounded instead of throwing. All
documented v4 status and instrument enums are normalized through fixed lists.

## Evidence and Operator

The safe nine-row ledger is available in:

- final Python JSON output;
- PowerShell 5.1/7 terminal rows;
- SUMMARY.json;
- existing MARKET.json component;
- existing Operator GET and mobile helper panel.

Only fixed subcheck names, REQUIRED flags, PASS/BLOCKED/UNKNOWN and fixed reason
codes are projected. Provider bodies, free exception text, URLs, credentials and
unknown keys are excluded.

## H/D/B/S/O/K dogfood

- H preserves the supplied real-host/runtime facts.
- D keeps MARKET_V4 raw source/shape truth separate from economics derivation;
  M5 remains independently PASS.
- B retains 8/8 successful broker reads as PASS evidence.
- S remains BLOCKED for a mandatory MARKET_ECONOMICS subcheck failure.
- O exposes the exact safe subreason and preserves all raw/other-derived rows.
- K has no majority rule; S veto prevents Candidate processing and state change.

## Acceptance evidence

Required CI on the accepted runtime head:

- dax-bot-1x-ci #738, run 34974483054;
- research-lab-ci #1522, run 34974483236;
- windows-host-lane-ci #27, run 34974483127.

Each workflow passed two independent Bot-Helper acceptance processes with 992
PASS, 0 SKIP and all T01–T15 PASS. Research full suite: 3491 passed and one
conditional external-service skip. Windows verified native PowerShell 5.1,
PowerShell 7, parser parity, module import and host-lane failure injection.
Ruff, Python syntax and actual Chromium passed.

Focused acceptance covers the successful v4 projection, every fixed subcheck,
required versus provider-dependent absence, bool/null/empty-list/enums,
NaN/Inf/overflow, explicit EPIC binding, 8/8 raw plus one Economics blocker,
preservation of the other nine derived stages, safe Operator projection and
T07/T14 H/D/B/S/O/K behavior.

## Remaining truth and safety

Remaining internal Step2244 defects: NONE.

The concrete historical subcause remains unavailable because the previous run
did not emit it. One final-head Windows/provider run is the only remaining
evidence action. It will either prove MARKET_ECONOMICS projection PASS or expose
the exact fixed subcheck in the same invocation; no manual endpoint series is
needed.

FOLLOW-UP WORK DEBT: EXTERNAL_ONLY.

Execution remains `execution_capability=NONE` and
`order_execution_enabled=false`. No endpoint/request, retry, dealing method,
order, strategy parameter, cost model, risk/loss policy, V11.2 reference or
CAND-001 sequence changed. LIVE remains prohibited. Step2238, Step2239,
Step2240, M01 and the readiness gates are not promoted.
