# Problem / Solution Registry — DAX Daytrading Bot

Status: BINDING ENGINEERING MEMORY
Updated: 2026-09-11

Purpose: preserve solved engineering reasoning so the same problem is not rediscovered and re-solved hundreds of steps later. This registry records problem -> root cause -> accepted solution -> proof -> reuse rule. It is not a substitute for code/tests; it points back to them.

## Mandatory use

Before designing a fix for a recurring technical problem:
1. search this registry by component, symptom and failure mode;
2. inspect the referenced code/tests at the pinned commit;
3. reuse the accepted solution when the same semantics apply;
4. if the old solution no longer applies, record why and add a superseding entry rather than silently replacing history.

When a non-trivial defect is solved, add or update an entry if the reasoning is likely to matter again. Do not record trivial typos or one-off tool glitches.

## Entry format

Each durable entry contains:
- ID and status;
- component/topic;
- observed symptom/problem;
- root cause;
- accepted solution/decision;
- proof/evidence;
- reuse rule / what not to do;
- supersession link when relevant.

---

## PSR-001 — GitHub code-search zero hits are not absence proof

**Status:** VERIFIED / BINDING
**Component:** repository navigation / context recovery

**Problem:** Code search can return zero hits even when a file/function exists on the active PR head, especially because search may reflect the default branch/index rather than the exact pinned commit.

**Root cause:** Search index scope/freshness is not equivalent to authoritative repository contents at a specific SHA.

**Accepted solution:** Pin branch/SHA, then use direct file paths, Repository Contents, or small Git trees at that SHA. Treat zero search hits only as a weak discovery signal.

**Proof/evidence:** `docs/CONTEXT_RESUME_RECOVERY_POLICY.md`; repeated recovery during PR #109 where direct tree/file reads found contracts/tests after search returned zero.

**Reuse rule:** Never claim a component/test is absent from code-search zero hits alone. Do not restart architecture because search failed.

---

## PSR-002 — Context loss must reconstruct, not redesign

**Status:** VERIFIED / BINDING
**Component:** project continuation

**Problem:** After chat/tool context loss, prior work can appear unfamiliar and invite duplicate design or repeated investigation.

**Root cause:** Conversational/process memory is transient; repository/evidence is durable but was previously not indexed strongly enough.

**Accepted solution:** Resume from pinned repo/branch/SHA, read `MASTERSTAND.md`, then `PROJECT_KNOWLEDGE_INDEX.md`, then this registry, then only topic-specific files/tests; reconcile runtime claims against fresh telemetry.

**Proof/evidence:** `docs/CONTEXT_RESUME_RECOVERY_POLICY.md`; `docs/PROJECT_KNOWLEDGE_INDEX.md`.

**Reuse rule:** Do not infer project state from recollection. Do not redo completed architecture/research merely because a prior tool response expired.

---

## PSR-003 — Candidate restart fingerprint changed after JSON restore

**Status:** VERIFIED / FIXED
**Component:** DAX-BOT 1.x candidate state persistence

**Problem:** Continuous processing and save/load/resume produced different downstream identities/fingerprints for otherwise identical state.

**Root cause:** Numeric representation drift across JSON restore (integer-like versus float values in opening-range price state) changed canonical serialized identity.

**Accepted solution:** Normalize price/numeric state to canonical float representation at the persistence/state boundary before deterministic identity calculation.

**Proof/evidence:** Candidate state persistence/restart parity tests on PR #109; continuous vs save/load/resume identity is now verified for Signal IDs, TradePlan IDs, Decision IDs and OperatorSnapshot identity.

**Reuse rule:** Any persisted numeric field participating in deterministic identity must have an explicit canonical type/representation. Never trust JSON round-trip representation implicitly.

---

## PSR-004 — Recovery implementations must not silently multiply

**Status:** VERIFIED / ARCHITECTURE DECISION
**Component:** recovery

**Problem:** `src/daxlab/runtime/recovery.py` and `src/daxlab/runtime/recovery_bundle.py` can look like competing recovery implementations and invite a third recovery path.

**Root cause:** Different historical recovery concerns accumulated in separate files without one obvious canonical routing statement.

**Accepted solution:** `recovery_bundle.py` is canonical for material-run recovery. `recovery.py` is legacy / retirement candidate. Candidate state persistence and active SHADOW/replay restart/reconcile remain separate concerns and must not be collapsed blindly.

**Proof/evidence:** `docs/RECOVERY_CANONICALIZATION_AUDIT_V1.md`; Step-2000 migration backlog; `MASTERSTAND.md`.

**Reuse rule:** Before adding recovery code, classify the recovery domain first. Reuse the domain's canonical path; never create a generic parallel recovery subsystem by default.

---

## PSR-005 — DUAL_COMPARE cannot compare unlike decision domains

**Status:** VERIFIED / FIXED
**Component:** DAX-BOT 1.x migration / DUAL_COMPARE

**Problem:** Legacy SHADOW and CAND-001 outputs could be incorrectly labelled MATCH/MISMATCH despite representing different semantic domains.

**Root cause:** Legacy current record represents `SHADOW_ORDER_SAFETY -> NO_ORDER`; CAND-001 represents `STRATEGY_DECISION -> TRADE/NO_TRADE`. Same bar does not imply same decision meaning.

**Accepted solution:** Comparison is semantics-aware. When domain/granularity differs, emit `UNAVAILABLE_DOMAIN_MISMATCH`; do not fabricate parity. Legacy remains authoritative while CAND-001 is observation-only.

**Proof/evidence:** PR #109 DUAL_COMPARE tests and CI head `18fab6cbbfd6228dbb4b9e5b42b85ee58e70f423`; dax-bot-1x-ci run #6 and research-lab-ci #790 were GREEN at that head.

**Reuse rule:** Every dual-compare contract must compare semantic domain and granularity before values. "Same timestamp" is insufficient evidence of comparable outputs.

---

## PSR-006 — Static web status must not masquerade as current runtime truth

**Status:** VERIFIED ISSUE / FIX REQUIRED
**Component:** web / observability

**Problem:** `web/status.json` and older status validation contain pre-host claims such as awaiting real Windows host / no real forward evidence, which became stale after real SHADOW evidence existed.

**Root cause:** Stable/versioned evidence and fresh runtime state were mixed in one static status model.

**Accepted solution:** Separate (1) stable/reference evidence from (2) fresh read-only operator/runtime snapshot. Preserve the small web shell; do not use GitHub as a live telemetry relay; do not expose Neon credentials to browser.

**Proof/evidence:** `MASTERSTAND.md`; `docs/WEB_INTERFACE_CONTRACT_V1.md`; `DAX_BOT_OPERATOR_SNAPSHOT_V1` implementation; Step-2000 backlog.

**Reuse rule:** Any field that can become stale by the minute/hour belongs to a fresh runtime source, not a versioned static truth file.

---

## PSR-007 — ExecutionIntent quantity needed explicit simulation semantics

**Status:** VERIFIED / RESOLVED FOR SIMULATION
**Component:** paper contracts / CAND-001 sizing

**Problem:** `ExecutionIntent` requires positive `quantity`, and tests often instantiated `quantity=1.0`, which could be mistakenly treated as a verified DE40 lot/contract sizing rule.

**Root cause:** The existing Paper contract defined deterministic intent identity and validation but did not define the economic unit of `quantity`. Existing R/cash simulation operated separately from intent quantity.

**Accepted solution:** Introduce `Cand001SimulationSizingPolicy` with exactly `quantity=1.0` and semantic `NORMALIZED_SIMULATION_UNIT`. The policy explicitly sets `broker_volume_semantics=False` and `account_risk_semantics=False`. The value 1.0 is therefore a newly defined normalized simulation unit, not an inferred broker lot or risk amount. The policy has its own deterministic fingerprint and is bound into the `RunManifest` config used by the CAND-001 intent adapter.

**Proof/evidence:** `src/daxlab/runtime/candidate_sizing.py`; `tests/test_candidate_sizing.py`; `src/daxlab/runtime/paper_contracts.py`; `tests/test_paper_quantity_identity.py`; product CI on PR #109 after the sizing implementation.

**Reuse rule:** Example values in tests are not economic policy. Any quantity used in an execution/simulation contract must have an explicit unit/semantic and provenance. Do not reinterpret `NORMALIZED_SIMULATION_UNIT` as broker volume.

---

## PSR-008 — Public-project findings need a canonical donor map

**Status:** VERIFIED STRUCTURE ISSUE / FIXED BY INDEXING
**Component:** open-source research

**Problem:** Useful patterns from LEAN, NautilusTrader, Freqtrade/vectorbt and other donors were recorded across multiple audit/rescan files, creating risk of later rediscovery or inconsistent recall.

**Root cause:** Historical donor research was durable but distributed across several generations without a mandatory navigation order.

**Accepted solution:** `PROJECT_KNOWLEDGE_INDEX.md` establishes donor precedence: read `PUBLIC_DONOR_MAP_V4.md`, then latest `PUBLIC_DONOR_RESCAN_*.md`, then supporting audit files only for additional detail. New durable donor findings must update the current donor map/rescan or a clearly superseding file.

**Proof/evidence:** `docs/PUBLIC_DONOR_MAP_V4.md`; `docs/PUBLIC_DONOR_RESCAN_V5.md`; `docs/OPEN_SOURCE_AUDIT.md`; `docs/PROJECT_KNOWLEDGE_INDEX.md`.

**Reuse rule:** Before scanning a donor again, review what we already learned and identify the genuinely new question. Do not repeatedly rediscover the same architecture lesson.

---

## PSR-009 — Broker sizing remains a separate evidence-gated problem

**Status:** OPEN / NOT REQUIRED FOR CURRENT SHADOW SIMULATION
**Component:** broker economics / future Paper-Live sizing

**Problem:** A normalized simulation unit cannot safely be converted into a broker order quantity without explicit broker volume constraints and an approved economic/risk policy.

**Root cause:** Current verified DE40 evidence establishes digits=2, point=0.01, contract_size=1 and profit currency EUR, while the current canonical project state does not establish `volume_min` and `volume_step` as verified sizing inputs. There is also no authorized account-risk sizing rule for PAPER/LIVE.

**Current decision:** Keep broker sizing completely outside the current SHADOW-only intent adapter. Before any future broker-like sizing, verify symbol volume constraints from the read-only MT5 probe, define the unit conversion, define approved risk/capital semantics, and bind all of those assumptions into versioned config/evidence. PAPER and LIVE remain unauthorized.

**Proof/evidence:** `src/daxlab/runtime/mt5_readonly.py`; `scripts/mt5_windows_probe.py`; `docs/MASTERSTAND.md`; `src/daxlab/runtime/candidate_sizing.py`.

**Reuse rule:** Never derive broker lots/contracts from simulation quantity by convention. Broker sizing requires its own explicit evidence and authorization gate.

---

## PSR-010 — Candidate strategy core and simulation intent boundary must stay separate

**Status:** VERIFIED / ARCHITECTURE DECISION
**Component:** DAX-BOT 1.x runtime boundaries

**Problem:** Mapping an admitted CAND-001 decision into the existing `ExecutionIntent` contract could accidentally pull Paper dependencies into the pure candidate hot path or appear to authorize PAPER.

**Root cause:** Strategy and simulation/execution contracts are adjacent in the event chain but have different dependency and authorization boundaries.

**Accepted solution:** Keep `candidate_config/signal/trade_plan/admission/decision/sizing/pipeline` pure and Paper-free. Place the mapping in the outer `candidate_execution_intent.py` adapter. The current adapter accepts only `RuntimeMode.SHADOW`, requires `FinalAction.TRADE`, verifies plan/decision provenance, and requires a RunManifest whose config fingerprint binds both Candidate config and sizing policy. It creates the existing `ExecutionIntent` only; it creates no broker adapter/order capability.

**Proof/evidence:** `src/daxlab/runtime/candidate_execution_intent.py`; `tests/test_candidate_execution_intent.py`; `tests/test_candidate_hot_path_boundary.py`; current `dax-bot-1x-ci`.

**Reuse rule:** Future PAPER authorization must change the outer boundary explicitly; never loosen the pure candidate core or infer authorization from the existence of an ExecutionIntent.

---

## Maintenance rule

At each mandatory 500-step audit:
- review this registry for stale/open entries;
- verify accepted solutions still match current code/tests;
- mark superseded decisions explicitly;
- promote important newly solved recurring problems into the registry;
- remove no historical entry merely because the implementation changed — mark it superseded and link the replacement.

The objective is not documentation volume. The objective is to make prior engineering reasoning reusable and falsifiable.
