# Step2245 — Bot-Helper Collective Turbo V1.1

Status: IMPLEMENTED; acceptance/publication status is owned by
`BOT_HELPER_TURBO_V1_1_CLOSEOUT.md` and `CURRENT_WORK_STEP.md`.
Design confirmed against the supplied prior meta-design and current code; this
is the implementation contract, not a new request to execute broker activity.

## Identity and preserved truth

- Start/continuity anchor: `9491a5922eac4abc6984618585778317dd249600`.
- Real Windows/IG-DEMO evidence head: `ae0efbcaff5650f9e8a8f31bc8fd603cfae212a2`.
- Main: `e0784ebfc11bee28475fd9c3385be661af58a738`; PR #109 stays open/unmerged.
- The initially available local alternate closeout commit `e8a67e6da3d5e0c2e1fa139880cbde59cc080f19`
  had the exact same tree `910751f0d27979530f9e730f0ebcd8c22f8fea38` and parent as
  the remote anchor. Implementation used a detached checkout of the actual
  authoritative remote SHA. No reset, stash, clean, merge or force operation.
- Historical 8/8 raw, 10/10 derived and 5/5 required economics remain proven for
  the real-host head. No second host run is attributed to a documentation SHA.
- Step2238 limited acquisition is complete; Step2239 partially verified/waiting
  external; Step2240 blocked; M01 not ready; gates remain 8/0/13/6/0 of 27.

## Reuse map and architecture decision

| Responsibility | Existing owner retained | Additive implementation |
|---|---|---|
| H/D/B/S/O/K runtime | `runtime/bot_helper*.py`, candidate pipeline | No runtime behavior change |
| Subject/hash/time | `runtime/bot_helper_contract.py` | `research/turbo_contract.py` |
| Composite readiness | `runtime/readiness.py`, authoritative M01 closeout | Read-only partial-dimension projection only |
| L: incidents, lessons, autopsy | `no_trade_analysis`, engineering PSR, failure analysis | `turbo_learning.py` typed analysis |
| E: experiments/filters | `filter_registry`, efficiency, stack, overlap, variant trial registry, WF, PBO/DSR/SPA | `turbo_experiment.py` composition |
| E: risk research | `boost001` fixed-cash/tail model, `failure_analysis` | `turbo_risk.py`; no sizing/order adapter |
| G: independent judgment | existing promotion/conformance | `turbo_judge.py`; additive REVIEW_READY entrance |
| Persistence | existing `research/registry.py`, `atomic_json` | specialized immutable TurboLedger records |
| Operator | existing `operator/read_model.py` | optional read-only card; no new UI/server |
| Acceptance | V1 runner/JUnit sanitation; existing CIs | `run_turbo_acceptance.py` |

KEEP runtime H/D/B/S/O/K. MERGE proposed R/T into L and F/X/adversarial work into
E. KEEP G separate from the proposer. ADD typed contracts and a small journal,
not six services. REJECT second broker/engine/gate/database/dashboard, background
agents, runtime LLM and auto-deployment. Existing Neon runtime persistence and
migrations are untouched; research does not get a runtime database credential.

## Authority and trust

L/E/G are logical development modules, not autonomous agents or a security
sandbox. All can read, suggest, run bounded synthetic/replay checks and publish
their own development evidence. L can propose hypotheses; E owns hypothesis,
trial, challenger and donor records; G owns independent judgment and veto.
G cannot create a challenger. L/E cannot write G records. `authorize` denies
PROMOTE, DEPLOY, MUTATE_RUNTIME, CHANGE_RISK, CHANGE_FILTERS and EXECUTE_ORDER
for every learning role. There is no broker port in the development APIs.

The trusted runner must use reviewed pure evaluators, source-pinned checkout and
no credentials/network. Arbitrary hostile Python with filesystem access could
bypass any in-process library; we do not claim otherwise. Hashes prove integrity
relative to a trusted checkpoint, not author identity or original observation.
Reviewer identity must differ from proposer identity; independent checks are
recomputed from pinned inputs, with distinct evidence references, not vote counts.

## Evidence and partial gates

`Provenance` binds EVIDENCE_HEAD, CONTINUITY_ANCHOR, RUNTIME_BUILD,
CONFIG_FINGERPRINT, DATA_CONTRACT, EVIDENCE_SCOPE, OBSERVED_AT, GENERATED_AT,
SUBJECT, validity and supersession. V1 `HelperSubject` carries instrument,
provider/environment, account/market/session, configuration and code identity.
SYNTHETIC, REPLAY, CI, LOCAL_TEST, REAL_HOST, REAL_BROKER_READ and
REAL_BROKER_EXECUTION are separate classes, never a promotion ladder.

Current reuse requires the exact expected head/build/config/contract/subject,
explicit scope, known validity and no supersession/future observation or future
generation. A later continuity anchor alone does not invalidate an unchanged
source proof. Contradictory matching observations block reuse. Every observation
remains visible, including stale or wrong-scope ones.

`project_partial_evidence` accepts the current owner's composite status and a
closed dimension catalog. It never writes or recomputes that composite. There
is no existing universal executable 27-gate reducer to duplicate: the formal
27-gate matrix remains the authoritative closeout document. A complete dimension
set can request owner reassessment, never promote itself.

Historical operator-reported closeout claims with missing original timestamp,
account/config/build remain explicit `HistoricalClaim` records. Their historical
VERIFIED truth is preserved, current reuse remains false, and unknown current
freshness is not fabricated. Missing structural/economics dimensions are shown
before rereading already documented acquisition. This separates permanent
historical proof from fresh eligibility without losing either.

## Lessons and root-cause model

Typed Incident separates symptom, immediate/root/systemic cause, failure class,
owners, evidence and triggers. Repetition, cross-owner impact, special cases,
contract/fixture drift, masking, conflicting evidence, unclear ownership and
host loops require architecture review. Review does not force a refactor:
bounded sufficient repairs remain REPAIR; justified composition changes use
REFACTOR; inadequate contracts can justify REDESIGN; unsupported benefit or
unknown root cause uses NO_CHANGE. No automatic code repair is exposed.

Lesson includes alternative fixes, rejected alternatives, decision, chosen
solution, tests, real-evidence refs, generalized lesson/rule, introduced head,
last seen and supersession. Reconstruction is not mislabeled real evidence.
Lookup returns candidate prior lessons, never suppresses a new incident because
it resembles an old one. New scope/head/subject/time observations remain new.

TurboLedger uses immutable numbered JSON records and a hash chain, single-writer
exclusive lock, expected predecessor pin and existing atomic publication.
Typed lesson/hypothesis payloads are validated both on append and restart. Keep
the returned head in the existing handoff/checkpoint: without an external pin,
suffix truncation of any hash chain cannot be detected. A leftover crash lock
fails closed; no automatic stale-lock stealing. Windows handles close before
lock deletion. Records are bounded/sanitized, not provider-payload storage.

## Filter governance and causal autopsy

`decision_rule_inventory` composes the current research registry, all immutable
CAND-001 config fields, signal/admission/data-quality enums and risk/loss policy
fields. Every card is TUNABLE_RESEARCH_FILTER, FROZEN_STRATEGY_RULE or
PROTECTED_INVARIANT. Admission/risk are protected; frozen/protected rules cannot
enter PnL ablation. No current productive risk field is classified as soft.

Cards retain purpose/owner/layer/parameters/introduction evidence/dependencies
and review status. Unknown introduction history remains unknown, not invented.
Audit envelopes bind case universe, causal cutoffs, strategy/market/data scope
and trial family. Existing efficiency/stack/overlap owners produce marginal
value, veto/overlap, survival/DD, regime/cost effects, false-rejection proxies,
bad-trade pass-through and top-trade removal. Parameter stability and OOS/WF
stay UNKNOWN until separately evaluated; no proxy is a real fill/PnL claim.

One DecisionCase covers TRADE/NO_TRADE/REJECTED_CANDIDATE. Decision-time features
must precede knowledge cutoff; MFE/MAE/later path/outcome are a separately timed
research zone. ACTUAL requires execution evidence and a real trade case.
Hypothetical fills remain SIMULATED/OPPORTUNITY. Normal losses produce NO_CHANGE.
A candidate avoidable-loss hypothesis needs an earlier available causal
alternative, a pinned replay reference, mechanism and falsifier. Positive
rejected outcomes request review, not filter removal or certainty of a fill.

Research order is REGIME → STRUCTURE → ENTRY. Safety invariants are not PnL
filters. Exploratory and confirmatory experiments are distinct. Predeclared
families count every trial, including failed/abandoned trials. Content-bound
holdout windows cannot be reused by renaming a dataset; overlapping periods for
the same instrument are blocked in the persistent ledger.

## Challenger, G and adversarial research

ChampionIdentity is immutable commit/config/strategy/data/cost/risk identity.
Challenger stages require sequential evidence receipts through data/causality,
backtest, OOS, WF, cost stress, robustness, shadow/dark and champion comparison.
Dark evaluators use detached inputs/states; original hashes must remain equal.
Actual CAND-001 replay uses the existing pure pipeline; no second execution engine.

G validates sealed identities, all-trial accounting reference and complete named
checks. Independent raw-input reproduction covers OOS, 2x costs, prefix causality
and champion binding. Disagreement/source mismatch vetoes. All other required
checks remain mandatory; missing evidence yields MORE_EVIDENCE_REQUIRED.
The durable `publish_judgment` entrance reloads the pinned journal and recomputes
family accounting; an arbitrary accounting hash is insufficient. The existing
promotion adapter returns REVIEW_READY plus the new journal checkpoint, never
product acceptance. A rejected review is also retained in the journal.
Synthetic/exploratory success never produces a promotion candidate. Even an
eligible confirmatory replay can only create REVIEW_READY metadata via the
existing promotion owner, bound to the exact experiment fingerprint. No alias,
runtime strategy or risk policy changes. Independent risk/quality review
recomputes reports and cannot approve risk actuation.

Adversarial plans are bounded and declared before running. Per-attack exceptions
produce retained UNKNOWN rows; they do not hide other failures. Prefix future
perturbation detects exercised look-ahead; differing history/warmup detects
recursive instability. Missing/duplicate/corrected bars, timestamps, sessions,
regimes, costs, delays, top trades, filter removals and parameter perturbations
can use the same plan. Untested branches remain unproved. Existing PBO/DSR/SPA
owners are reused; prerequisites are never fabricated and p-values do not vote.

## Economic objective and Turbo-risk research

NORMAL/BOOST/TURBO are research labels only. Opportunity requires causal quality
dimensions REGIME/STRUCTURE/ENTRY plus sample/OOS/WF/cost/tail evidence. Unknown
hard categories block regardless of score. Contradictions expose uncertainty.
Loss streak/DD cannot raise opportunity mode. Outputs carry falsifiers, scope,
sample adequacy and blockers; confidence never maps to position size.

RiskResearchSpec predeclares bounded cash-risk hypotheses, capital floor, cap,
DD/floor-hit/sample limits, bootstrap budget and seed. There is no privileged
5x multiplier. `execute_risk_trial_family` journals hypotheses and all trials
before calculation; interruption leaves visible UNKNOWN, with no automatic
retry. Existing fixed-cash tails compare identical return/cost streams and
paired resampling across baseline/candidates. OOS and WF each need sample and
positive net evidence; 1.5x/2x costs, tail/floor/DD, top-trade dependence and
incremental return versus added drawdown can reject a candidate.

These are conditional trade-boundary simulations, not proof of edge, account
survival, intrabar margin/liquidity or broker-native cash-loss semantics. Costs
scale linearly in R by explicit research assumption. Higher cash risk alone
does not demonstrate better setup selection. G risk review can REJECT or request
more evidence, not promote a policy. No actual broker quantity is calculated.

Hard categories: survival, exposure, day/week loss, hard DD, margin, protection,
account/instrument binding, stale data, inventory, unresolved transport,
reconciliation, kill switch, LIVE block, PTC and economics. Soft research knobs
exist only in declared research specs; current productive limits remain frozen.
Future TURBO_ARMED vocabulary always projects effective TURBO_OFF in V1.1.
Future actuation requires a separate risk promotion, Step2239/2240 readiness,
native economics, independent judgment, explicit human authorization, TTL,
bounded scope/maximum and all hard vetoes. This build provides no actuation path.

## Cost, complexity and reaction horizons

Ordinal assessment records severity/frequency/blast radius/recurrence/strategy/
learning/economic value/cross-owner gaps and implementation/test effort. No
credit/euro forecasts. RUN_NOW/CHEAP_SCREEN_FIRST/DEFER/STOP support a cheap-to-
expensive funnel. Safety overrides cheapness; external gaps or decision-insensitive
experiments stop/defer. Complexity explicitly compares NO_CHANGE, owner/store/
dependency growth, code/contracts/failure surface, operator burden and research
degrees of freedom. Benefit must justify complexity.

Technical/safety incidents are immediate; similar observations accumulate at
pattern level; multi-period evidence feeds research cycles. A few losses do not
trigger strategy changes. Deterministic clustering is a retrieval aid, not
automatic causal proof or a learned runtime policy.

## Bounded donor decisions (official sources reviewed 2026-09-15)

| Problem | Donor / principle | Local decision, cost and risk |
|---|---|---|
| Hidden future dependency | [Freqtrade lookahead](https://www.freqtrade.io/en/stable/lookahead-analysis/) compares changed runs | ADAPT prefix perturbation in E/G; small adapter, no framework. Unexercised signals remain unproved. Do not copy disabled protection settings. |
| History-dependent indicators | [Freqtrade recursive](https://www.freqtrade.io/en/stable/recursive-analysis/) compares warmup lengths | ADAPT bounded terminal comparisons; small cost, tolerance predeclared. Not a full-strategy correctness proof. |
| Warmup versus tradable state | [LEAN warmup](https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/warm-up-periods) | REUSE existing causal replay/state; no engine migration. More history is not a guarantee of data completeness. |
| Champion alias drift | [MLflow registry](https://mlflow.org/docs/latest/ml/model-registry/) provides version/alias lineage | ADAPT immutable identity; REJECT mutable production alias and MLflow deployment dependency. Existing registry is sufficient. |

Nautilus execution/reconciliation ideas and platform migration are DEFERRED to
the separate Step2240 tranche. No external strategy was copied. No framework,
new database or runtime dependency was installed for Turbo implementation.

## Acceptance and red-team repairs

Frozen U01–U40: `BOT_HELPER_TURBO_V1_1_ACCEPTANCE.md`.
Runner: `python scripts/run_turbo_acceptance.py --output-dir <new-path> --pass-name pass1`
and a separate invocation with `--pass-name pass2`. Different namespace/time/
regime/sequence/fault ordering; actual JUnit outcomes, no skip-as-pass.
The second pass uses independently fixed negative/property/raw-input oracles,
not a claim of a separate human reviewer or statistically independent market data.

This build's review closed: Windows open-handle cleanup, incomplete typed ledger
payloads, generated-in-future reuse, untimed MFE/MAE, mixed/unordered filter
universes, rehashed OOS reuse, unrelated G-to-Operator binding, omitted independent
reproduction and pooled sample insufficiency. Historical dogfood retains all 15
required cases in `tests/fixtures/turbo_dogfood_v1.json` and persists/restores each
lesson. Historical exact MARKET_ECONOMICS throwing value stays unknown.

Non-goals: productive filter/strategy/risk changes, runtime LLM/self-patching,
multi-market implementation, broker connection, order/cancel/modify/retry, slot
release, native Step2239/2240 completion, NONE→DEMO_ONLY, autonomous promotion or
deployment. UI cost decision: read-model only; no second dashboard or button.
