# Pre-DEMO Hardening 2.0 — repository-local closeout

Date: 2026-09-13. Repository `hennebergtoni-lgtm/dax-Day`, branch
`nextgen-bot-line-v1`, PR #109 OPEN / UNMERGED.

Start head exactly `ff7f22540d7dee37b0bf2d61e10a339cea90d8cf`.
Main exactly `e0784ebfc11bee28475fd9c3385be661af58a738`, unchanged.
No initial drift. Every publication rechecked exact current PR head before commit
and before fast-forward ref update. Subsequent drift is only this authorized
exclusive write-lane's commits. No parallel/security-relevant drift detected,
no force push, no newer repository truth overwritten. User explicitly authorized
ACTIVE Step2217 takeover. Step2206 and host2122 remain external; no Acceptance refresh.

## Implementation and sequence

| Step | Concrete unit | Published implementation head / validation |
| ---: | --- | --- |
| 2217 | Consolidate original full-account inventory/query owner | original ff7f22540...; 76 focused tests + original CI #635/#1419; takeover docs 18aec152... |
| 2218 | Credential-free structural browser DTO + additional secret rejection | 2d02b26d...; 78 focused tests, Ruff; CI #637/#1421 GREEN |
| 2219 | HTTP/frontend execution contradiction guard | 7b20f85a...; 54 focused socket/credential/UI tests, executed Node validator |
| 2220 | Preserve heartbeat blockers, independent liveness/readiness/safety/truth | d5919a9b...; 76 focused tests |
| 2221 | Pinned operational lookup/result/inventory projection | cde947a7...; 147 inventory/transport/query/socket/credential/UI tests |
| 2222 | Windows/localhost/protected remote/iPhone runbook | 11881e42...; 32 related UI/HTTP tests |
| 2223 | Conservative health/freshness/Monday evidence gate matrices | a2da398a...; 87 focused tests |
| 2224 | Incident timeline from existing snapshots and bounded heartbeat archive | 9341d5a7...; 52 focused tests |
| 2225 | Existing reconciliation comparison, partial/unapplied fills, native precision | 148a8ec6...; 148 adversarial tests |
| 2226 | Empirical historical risk envelope using existing detail/analysis owners | a72b6e6f...; 27 analysis/detail tests |
| 2227 | Primary public-project extraction + research/reject/threat mapping | 4380d2be...; 14 related tests; 24 cases mapped |
| 2228 | Executed DOM/mobile/failure tests and collapsed detailed gate lists | dcaec617...; 26 focused tests; actual browser rendering UNVERIFIED |
| 2229 | Bounded malformed HTTP sources/filter alerts/canonical enum preservation | 2d8b7f14...; 85 focused tests |
| 2230 | Full regression, eight offline gates, source mutation audit and closeout | final code 2d8b7f14165586337f5cab5237fd46aba06511dd; 119 focused / 2619 full passed, six local pwsh skips; CI #648/#1432 GREEN |

Intermediate local unit closure is not a claim that an intermediate CI was already
green: rows with pending CI are covered by final code-head full validation. Final
publication/pointer head must also receive both required workflows; exact final
SHA/run IDs are reported after that publication, avoiding a self-referential CI claim.

## Reproduced bugs, causes and fixes

1. **Credential leakage:** free-form events passed the original pattern filter.
   Original V3 bytes/digest validate first; browser DTO uses closed canonical
   display codes, unknown text redaction and blocker identity digests. Added
   normalized case-insensitive secret keys and Bearer/token/DSN/private-key tests;
   real loopback responses contain no synthetic sentinel. Source snapshots are
   neither rewritten nor re-persisted; provenance explicitly marks the display DTO.
2. **EXECUTION GREEN contradiction:** frontend checked top-level NONE/false but
   trusted a legal GREEN tile. Independent HTTP and JS guards now reject every
   execution tile except BLOCKED/DISABLED. Invalid response cannot retain old GREEN.
3. **Heartbeat blocker loss:** only non-GREEN status carried source blockers.
   All blocker identities survive independently of liveness; readiness remains
   BLOCKED. Unknown provider text retains a digest rather than leaking free text.
4. **Inventory invisible in console:** existing typed full-account export lacked
   a consumer. Strict inverse result codec and original envelope/reservation pins
   bind it into the existing read projection. Foreign orders/positions are visible;
   non-atomic or failed reads never imply flat/current/reconciled/risk-zero.
5. **Remote instructions absent:** concrete runbook added without order steps.
6. **Unapplied venue fills lacked explicit operator contradiction:** existing
   `reconcile_broker_order` now compares the original local lifecycle against venue
   observation. No local lifecycle, fill ledger or consumed guard is mutated.
7. **Native inventory precision:** volume-step/digits from existing observed symbol
   metadata identify contradictions; no rounding/price tolerance is invented.
   Weighted-average fill price is not confused with an individual native tick.
8. **Malformed-resource errors:** heartbeat initial/final reads were unbounded and
   deep JSON could terminate the HTTP request. Existing resource bound now covers
   both reads; recursion/malformed failures return fixed 503, not exception text.
   Credential failures produce a fixed safe alert without raw evidence.
9. **Display enum regression:** strict display allowlist now reuses actual
   VirtualPositionStatus (`PENDING_ENTRY`) and actual CANDIDATE_INPUT source.

## Owner reuse and console architecture

Original OperatorSnapshot V3/digest, candidate_operator_telemetry, candidate current
snapshot, Candidate checkpoint/manifest and mt5_shadow_supervisor remain canonical.
Neon `cand001_operator_current`, migrations0008/0009 and exporter remain unchanged;
no DB connection is needed for the local browser. Existing host/feed/clock/account
normalizer, economics bindings, FixedCashRiskPolicy, LossExposurePolicy/provenance,
NextGen Protection, session guard/PREPARED/reservation, lifecycle/checkpoint/query/
reconciliation owners retain their semantics and fingerprints.

Existing atomic supervisor artifacts and optional existing pinned broker lookup
file -> canonical parsers/pure operator projection -> loopback HTTP GET -> vanilla
mobile browser. HTTP imports no MetaTrader5 SDK/DB client; it reads through the
existing file-store load port and never writes to runtime source. The optional
inventory uses the already established single MT5 query connection in its existing
collector, never a new connection in HTTP/UI.

GET-only fixed routes; POST/PUT/PATCH/DELETE/OPTIONS/HEAD return405 before source
access. Loopback Host/Origin/Sec-Fetch-Site checks, no CORS wildcard, no-store, CSP,
nosniff and frame-deny remain. No broker/Neon credentials in assets or response.
503/background/invalid/fetch failure clears prior evidence. Browser polling/timeout
are UX resource values, never freshness or risk thresholds.

No second store/journal/risk/lifecycle/reconciliation/readiness/health framework,
React rebuild, autonomous repair, messaging provider, cloud infrastructure or
complex authentication platform was justified. A protected external remote
transport remains mandatory.

## Operator behavior and freshness

Fourteen status tiles, safety banner and blockers precede details. Decision is
read-only Regime -> Structure -> Setup/Entry, signal reason, admission/decision
and proposed Entry/Stop/Target/RR. Local intent/guard/reservation bookkeeping and
broker-observed orders/positions/fills are distinct. Timeline display has explicit
source fingerprints and generated/observed timestamps; missing transition times
remain UNKNOWN. Duplicate/reordered display is deterministic, not state replay.

Separate web/backend/Candidate/MT5/feed/clock/account/inventory/reconciliation/
protection/telemetry observations prevent liveness from hiding readiness blockers.
Feed uses its canonical source max-age. Snapshot/host/inventory/economics/current
reconciliation lack reviewed absolute thresholds in this console: UNKNOWN /
UNVERIFIED_THRESHOLD. Existing reserved QUERY host-age/grant preflight is reused
only for its own scoped validity. Browser fetch never renews source facts.

Actual desktop/WebKit/iPhone pixel rendering and protected remote deployment are
UNVERIFIED / WAITING_EXTERNAL. Node executes real validator/render/clear branches,
including long blockers, STALE/UNKNOWN/external inventory/disabled/unreachable;
HTML/CSS contracts verify mobile safe-area, responsive grid/wrapping and touch size.
No screenshot or real-device success is invented.

## Historical risk and external learning

Existing detail loader strictly pins clean trade artifact hash/count and typed
rows; existing failure_analysis now computes empirical MAE magnitude/MFE and
median/P90/P95/P99/worst, duration, side strata, within-nonoverlapping-WF/variant
loss streaks/session/week chains and trade-boundary net-R drawdown distributions.
Zero actual verified source rows were supplied in this checkout. Actual MAE/MFE
quantiles remain null/INSUFFICIENT_SAMPLE; the correct external artifact, not a
synthetic rebuild, is required. No new risk policy or minimum sample criterion.
Tail inference/survival UNVERIFIED_THRESHOLD; missing Regime/Structure/Setup/OR joins
UNKNOWN. Per-trade stress/slippage/gap cannot be inferred from net-R or MAE/MFE.
Unchanged static V11.2 aggregate normal/-31.3092R, 1.5x/-40.9217R, 2x/-48.4246R are
historical summaries, not Candidate runtime or a survival PASS.

Primary NautilusTrader/LEAN/Freqtrade/FreqUI/Hummingbot/Passivbot review mappings,
ADOPT/ALREADY_HAVE/RESEARCH/REJECT and explicitly prohibited Grid/Martingale/AI-
execution ideas are in PRE_DEMO_PUBLIC_EXECUTION_REVIEW_V2.md. Public concepts are
review input; no VERIFIED baseline, strategy or cost model was retroactively changed.
Reconciliation threat matrix covers all24 requested cases in the companion report.

## Verification and remaining gates

Final production-code tests: **119 focused passed**, **2619 full passed / 6 local
PowerShell-unavailable skips** (65 new tests versus starting baseline).
Ruff entire src/scripts/tests GREEN, Node syntax GREEN, all eight offline gates
GREEN: recovery_preflight, research registry, hypothesis ledger, web status,
static_runtime_safety_smoke, probe_v112_engine, v112_replay_smoke, shadow_soak_smoke.
Changed production Python AST has zero order/submission/cancel/modify/resubmit calls.
Frozen subtree `e61a59f9bdc6ba9d108cfae0ea518bd7b990dedc` unchanged; actual strategy/
config/cost/workflow/Acceptance and web/status.json/web/index.html have no mutation.

Code head CI DAX #648/run34779991786 and research #1432/run34779992010 GREEN.
Five PR-only database steps remain skipped, not executed connected-Neon/restore/
import evidence. No database operation or actual Windows/MT5 SDK call was performed.

Remaining: Step2206 USER_AUTH/current host/product policy; host2122 real Windows/
MT5/CLOSED-M5/broker clock/account/server/symbol/inventory/economics/restart evidence;
current reviewed risk/loss/provenance/protection and separately bounded first-DEMO
execution authorization/capability. Freshness criteria, actual protected iPhone
transport/rendering and pinned historical source remain external/policy evidence.
Exact Monday checklist and fail-closed incident response are in
REMOTE_OPERATOR_RUNBOOK_V1.md. This tranche closes the repository-local read-only
hardening scope. **It does not make a first order executable:** after Step2206,
separate bounded authorization and a reviewed active submission capability are
still required; NONE/false remains binding and no adapter is activated here.

## Safety assertion

broker_orders_sent=0; broker_side_effects=0; mt5.order_send_calls=0;
execution_capability=NONE; order_execution_enabled=false;
SHADOW=authorized; DEMO broker execution=unauthorized; PAPER=unauthorized;
LIVE=unauthorized; V11.2=unchanged; CAND-001 strategy=unchanged;
no fabricated broker evidence; no force push; no merge; no Acceptance refresh.
