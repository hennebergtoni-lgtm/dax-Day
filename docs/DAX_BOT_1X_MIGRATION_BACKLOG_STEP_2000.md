# DAX-BOT 1.x Migration Backlog — Step 2000 Audit

Status: VERIFIED AUDIT SNAPSHOT / PLANNED MIGRATION BACKLOG / NO EXECUTION AUTHORIZATION

Purpose: preserve the findings of the mandatory 500-step audit at step 2000 and turn them into a controlled migration map for DAX-BOT 1.0-alpha and later 1.x versions. This document is not permission to rewrite the current system or enable broker execution.

## 1. Audit anchor

Repository truth at this audit:
- repository: `hennebergtoni-lgtm/dax-Day`
- stable branch: `main`
- main commit: `e0784ebfc11bee28475fd9c3385be661af58a738`
- main message: `Add deterministic context resume recovery policy (#108)`
- next-generation PR: `#109`
- PR branch: `nextgen-bot-line-v1`
- audited PR head before this backlog commit: `9cd59badb0e830ac725c8f581e014eb331d7fcf3`
- PR is mergeable
- `research-lab-ci` run for that head completed successfully
- no Python/runtime/DB/web/MT5/Windows-host code had been changed by PR #109 before this backlog file

Safety remains unchanged:
- `execution_capability=NONE` on the real host-facing SHADOW path
- `order_execution_enabled=false`
- no broker order authorization
- REF-V11.2 remains frozen reference evidence, not the DAX-BOT 1.x product

## 2. Audit mode

Step 2000 is used primarily to classify and preserve findings for migration.

Do not repair the old system wholesale merely because an issue is found.

Immediate fixes are required only for defects that threaten current repository truth, current SHADOW safety, data integrity, or evidence integrity.

All other findings enter one of:
- `PRESERVE`
- `1.0_ALPHA`
- `1.X_CLEANUP`
- `2.0_DEFER`
- `RETIRE_AFTER_AUDIT`
- `FIX_REQUIRED`

## 3. Product migration principle

DAX-BOT 1.x is not a rewrite of REF-V11.2.

The preferred path is modular migration with explicit component routing.

A component may be in one of these transition modes:
- `LEGACY` — current proven component remains authoritative for that responsibility.
- `DUAL_COMPARE` — legacy and 1.x component both process the same canonical input; only comparison/evidence is produced.
- `BOT_1X` — the tested 1.x component is authoritative for that responsibility after its migration gate passes.

The routing mode is not a safety authorization.

Safety, readiness and execution gates remain independent and can always block downstream action.

A component transition must be reversible until the replacement has passed deterministic replay, restart/reconcile, observability and compatibility gates.

## 4. Recommended component boundaries

The first 1.x generation should keep the hot path intentionally small:

`CLOSED M5 DATA -> REGIME -> STRUCTURE -> ENTRY -> DECISION -> EXECUTION_INTENT -> PAPER OUTCOME -> TELEMETRY`

Recommended independently routable components:
1. Data / closed-bar normalization
2. Regime
3. Structure
4. Entry/setup
5. Filter snapshot
6. Decision assembly
7. Paper intent
8. Virtual lifecycle/outcome
9. Telemetry/operator state
10. Web/operator presentation

Do not make Safety/Authorization a switchable strategy component.

Do not make broker execution part of the 1.0-alpha transition mechanism.

## 5. Current assets and migration classification

### PRESERVE

#### Frozen reference
- REF-V11.2 immutable hashes, recovered engine sources and clean reference evidence.
- 2014–2019 audited historical dataset evidence.
- clean 856-trade reference evidence.
- 81 historical walk-forward windows and their verified negative baseline metrics.

Role in 1.x: regression/comparison anchor only.

#### Reference payload export
`.github/workflows/reference-payload-export.yml`

Classification: `PRESERVE / LEGACY_REFERENCE`.

Reason: verifies frozen recovered V11.2 engine payloads by SHA before exporting them. It is intentionally separate from the new product hot path.

#### V11.2 engine surface probe
`scripts/probe_v112_engine.py`

Classification: `PRESERVE / LEGACY_REFERENCE_DIAGNOSTIC`.

Reason: reproducibly exposes the SHA-verified V11.2 public engine surface without modifying the engine.

#### V11.2 replay smoke
`scripts/v112_replay_smoke.py`

Classification: `PRESERVE / LEGACY_REFERENCE_REGRESSION`.

Reason: fixture-only parity/determinism protection around the frozen engine. Keep it as a reference test, but do not mistake it for product-bot acceptance.

#### Existing reusable contracts
Preserve/reuse where semantics already match:
- canonical closed Candle/data-quality contract
- bar identity / duplicate suppression
- `DecisionRecord`
- deterministic decision IDs
- safety/readiness gates
- `ExecutionIntent`
- paper cost/fill/same-bar/gap policy
- simulation-only telemetry
- virtual outcome / R / cash-ledger views
- MT5 read-only feed acquisition
- watchdog/supervisor/cross-cycle integrity
- Neon outbox/idempotency patterns
- restart/reconcile patterns
- research registry and evidence governance

## 6. 1.0-alpha mandatory work

The first alpha is accepted for controllability before profitability.

Must provide one small end-to-end vertical slice that proves:
- canonical closed M5 input
- explicit `DAX-BOT 1.0-alpha` product identity
- one candidate/config snapshot with deterministic fingerprint
- visible `REGIME -> STRUCTURE -> ENTRY` decision chain
- deterministic `TRADE` or `NO_TRADE` with reason/blocker codes
- if TRADE: LONG/SHORT, planned entry, stop, target and RR
- mapping into the existing `ExecutionIntent` contract
- virtual lifecycle on causal later bars
- deterministic outcome under versioned fill/cost policy
- duplicate-safe restart/replay
- observable runtime health/freshness/last bar/config/decision state
- no broker order API
- host-facing `execution_capability=NONE`
- `order_execution_enabled=false`

Performance gates remain separate.

## 7. 1.x cleanup backlog

### A. Web runtime truth is stale
Current `web/status.json` / `scripts/check_web_status.py` still encode historical pre-host assertions even though real MT5 SHADOW evidence now exists.

The validator currently requires values including:
- Forward state awaiting real forward evidence
- `real_forward_evidence_present=false`
- host state `AWAITING_REAL_WINDOWS_HOST`
- external MT5 milestones 102–110 incomplete
- next external milestone 102

Classification: `FIX_REQUIRED / 1.X_CLEANUP`.

Migration rule:
- preserve stable research/evidence status separately
- create a fresh operator-runtime status contract separately
- do not expose Neon/database credentials to a static browser
- do not use GitHub as a runtime telemetry relay
- CI should validate stable evidence independently from time-sensitive runtime freshness

### B. Historical pre-host smoke remains in main CI
`scripts/v11_prehost_smoke.py` actively asserts the old pre-host milestone state.

Classification: `1.X_CLEANUP / HISTORICAL_PRE_HOST`.

Do not delete immediately.

First replace its still-useful invariants elsewhere:
- checkpoint identity
- duplicate safety across changed safety state
- order execution disabled

Then move/rename/archive the historical milestone assertions away from the primary product CI.

### C. Synthetic SHADOW smoke has stale operator wording
`scripts/shadow_soak_smoke.py` remains a useful deterministic synthetic no-order regression test, but its printed text says real MT5 broker evidence is not present.

Classification: `PRESERVE_TEST / STALE_OPERATOR_TEXT / 1.X_CLEANUP`.

Keep the deterministic synthetic test; update wording/status separation during migration.

### D. CI mixes research/reference/product concerns
`.github/workflows/ci.yml` currently runs one `research-lab-ci` job containing:
- package/test/lint
- recovery preflight
- research registry/hypothesis checks
- web status integrity
- V11 pre-host smoke
- V11.2 engine probe
- V11.2 replay smoke
- synthetic SHADOW soak
- Neon research DB gates/drills on main

Classification: `1.X_CLEANUP`.

Target direction without needless workflow proliferation:
- shared core quality/test gate
- legacy reference/evidence gate
- research integrity gate
- DAX-BOT 1.x product/runtime gate
- database gates only where database evidence is actually required

The objective is clearer responsibility, not more YAML for its own sake.

### E. Package metadata still names only the research lab
`pyproject.toml` currently declares:
- project name `dax-day-research-lab`
- package version `0.1.0`
- description centered on frozen V11.2 research baseline

Classification: `1.X_CLEANUP`.

Do not blindly rename the Python package during alpha creation.

First define the distinction between:
- Python distribution/package version
- DAX-BOT product version
- strategy candidate/config ID
- research/evidence schema versions

Avoid another ambiguous global `Vxx` namespace.

### F. main branch is not branch protected
Audit observation: `main` reports branch protection disabled.

Classification: `GOVERNANCE_RISK / 1.X_CLEANUP`.

Desired rule: protect the stable branch against accidental direct pushes once the available GitHub account/repository controls support the intended workflow. Do not block current development solely on this item.

### G. Recovery duplicate boundary
Known files:
- `src/daxlab/runtime/recovery.py`
- `src/daxlab/runtime/recovery_bundle.py`

Existing evidence already marks `recovery_bundle.py` as canonical for new material-run production imports; `recovery.py` is legacy.

Classification:
- `recovery_bundle.py`: `PRESERVE / CANONICAL_MATERIAL_RUN_RECOVERY`
- `recovery.py`: `RETIRE_AFTER_AUDIT`

Important distinction:
Historical/SHADOW replay has operational checkpoint/restart state that is not automatically the same contract as material-run recovery bundles.

Do not merge these semantic responsibilities merely to reduce file count.

Before deleting `recovery.py`, retain the matrix:
`Consumer -> Module -> Test -> CI -> Runtime Contract`.

## 8. Research/filter migration rule

The accumulated research is preserved in full, but is not preloaded wholesale into the product hot path.

Existing useful governance includes:
- filter registry
- activation/evidence gating
- candidate readiness
- overlap/efficiency/ablation
- feature bundles
- market structure
- momentum
- ATR/regime work
- Bollinger/Fibonacci/gap/session/TWAP and other research families

Initial classification: `PRESERVE / RESEARCH_ONLY`, with promoted pieces entering 1.x only through explicit candidate/config snapshots.

For pandas/DataFrame-oriented research implementations:
- preserve causal semantics and reference definitions
- do not recalculate full historical DataFrames on every M5 runtime bar
- implement incremental runtime form only when needed
- parity-test the runtime form against the causal research definition

## 9. Transition/Component Registry — planned contract

Do not overload `FilterRegistry`, safety gates or readiness gates for version routing.

Plan one small independent transition contract whose only job is component routing/comparison.

Suggested minimum fields:
- component ID
- component contract version
- routing mode: `LEGACY | DUAL_COMPARE | BOT_1X`
- legacy provider ID/version
- 1.x provider ID/version
- canonical input fingerprint
- active config fingerprint
- comparison policy/version
- last comparison status
- transition evidence ID

The registry must not contain broker credentials or execution authorization.

`DUAL_COMPARE` must not double-publish external side effects. For PAPER/telemetry paths, define one authoritative writer or deterministic namespaced comparison records.

## 10. Public-project lessons intentionally adopted

The audit compared engineering patterns from established public systems. We copy principles, not strategies or platform complexity.

### QuantConnect LEAN
Useful pattern:
- separation of concerns
- pluggable signal/portfolio/risk/execution modules
- swap one module without requiring stateful coupling to every other module

Adopt:
- explicit contracts and replaceable responsibilities

Do not adopt:
- unnecessary multi-asset/portfolio/platform complexity for a single DE40/M5 product

### NautilusTrader
Useful pattern:
- same core strategy/execution code across simulation and live environments
- persistence/reconciliation matters when leaving simulation

Adopt:
- one strategy semantics path where possible
- reconciliation instead of trusting process memory

Do not adopt:
- broad multi-venue architecture not required by this project

### Freqtrade
Useful pattern:
- backtest first, then real-time dry-run/forward test without exchange trades
- compare entry/exit signal candles when backtest and forward differ
- treat backtest profitability cautiously

Adopt:
- DUAL_COMPARE / PAPER_SIM before stronger readiness claims
- explicit backtest-vs-forward parity diagnostics

### vectorbt
Useful pattern:
- close-derived signals must not be executed as if known earlier in the same bar

Adopt:
- closed-bar causality
- later-bar execution/progression unless an explicit conservative same-bar policy is versioned and tested

## 11. Things deliberately deferred to 2.0

Do not burden generation 1 with:
- generic multi-asset universe framework
- multiple brokers/venues
- large portfolio-construction abstraction
- real broker execution architecture
- advanced order-routing framework
- generalized plugin marketplace
- broad distributed/event-bus platform rewrite

Revisit only when 1.x experience provides concrete evidence that these are needed.

## 12. Step-2000 completion criteria

The audit is considered complete when:
- repository/main/PR/CI truth has been rechecked
- public architecture comparison has been completed
- current Web/CI/Recovery/Versioning drift has been classified
- useful Legacy-reference tools have been separated from cleanup candidates
- transition/component routing principle is recorded
- migration backlog is committed to the next-generation branch
- no unreviewed runtime rewrite has occurred
- execution safety remains unchanged

After this document is committed and CI returns GREEN, work may proceed to step 2001: define the minimal Transition/Component Registry contract and tests, then build the first DAX-BOT 1.0-alpha vertical slice incrementally.

## 13. DAX-BOT 1.0 closeout report — required deliverable

When DAX-BOT 1.0 reaches its defined completion gate, produce one evidence-linked closeout report before any stronger execution-readiness claim.

The report must state separately:
- architectural advantages versus the legacy/reference line
- concrete defects, false assumptions and knowledge gaps discovered during migration
- which fixes are VERIFIED versus merely IMPLEMENTED or PLANNED
- measured performance/runtime improvements, including benchmark before/after values where comparable evidence exists
- remaining bottlenecks and unresolved risks
- SHADOW readiness
- broker-demo/PAPER readiness and the explicit authorization state
- real-money/LIVE readiness and every remaining gate before it can be considered
- which public-project patterns were adopted and why
- which legacy components were preserved, retired or replaced

The report must not equate software correctness with trading profitability.

## 14. Planned operator risk profile / aggressiveness control

Classification: `PLANNED / POST-CORE-RISK-CONTROL`.

Desired operator concept: a clear selectable risk profile such as `DEFENSIVE`, `BALANCED`, and `AGGRESSIVE` so the operator can intentionally choose lower-risk continuity or higher-risk/high-return-seeking behavior without editing strategy code.

Design constraints:
- risk profile must never silently change strategy signal semantics
- profile changes must be explicit, versioned and fingerprinted
- the active profile must be visible in telemetry/operator state
- profile should govern risk-budget dimensions such as simulation/account sizing, exposure caps, daily/session loss limits, trade admission/risk limits and other validated risk controls
- broker-specific quantity/contract conversion must remain separate from normalized simulation sizing until the broker economics are explicitly verified
- changing the profile must not bypass safety/readiness/execution-authorization gates
- `AGGRESSIVE` means a controlled higher risk budget, not disabled limits or unconstrained leverage
- every profile requires backtest/OOS/forward evidence before stronger readiness claims

Do not implement this operator control prematurely inside CAND-001 signal logic. First finish the deterministic 1.0 core, outcome/ledger path, persistence/restart safety and forward/demo readiness gates.