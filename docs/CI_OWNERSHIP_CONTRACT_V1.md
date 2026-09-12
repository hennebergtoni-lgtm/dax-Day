# DAX-BOT CI Ownership Contract V1

Status: BINDING CI RESPONSIBILITY CONTRACT
Updated: 2026-09-12

Purpose: keep CI responsibilities explicit without weakening aggregate regression coverage or creating workflows merely for cosmetic separation.

## 1. Governing principle

DAX-BOT uses a deliberate hybrid CI model:

1. one broad integration/regression owner;
2. focused product/runtime owners where fast, narrow evidence is valuable;
3. separate immutable-reference evidence owners where legacy/reference artifacts need different semantics.

A focused workflow does **not** replace the broad integration gate. A broad integration gate does **not** make focused ownership meaningless.

Public-project comparison supports this hybrid model: LEAN separates several responsibility-specific regression/benchmark/research workflows; Freqtrade combines a broad CI workflow with separate operational workflows; NautilusTrader combines broad build/test surfaces with separate performance/security/release owners. DAX-BOT adopts the responsibility-separation principle without copying their workflow count or platform complexity.

## 2. Canonical workflow owners

### `research-lab-ci` — BROAD INTEGRATION / REGRESSION OWNER

Workflow: `.github/workflows/ci.yml`

Primary responsibility:
- repository-wide Python lint/test integration;
- cross-component regression compatibility;
- recovery reconstruction preflight;
- research registry and hypothesis-ledger integrity;
- static web-status integrity;
- static read-only runtime safety smoke;
- V11.2 reference surface/replay regression;
- deterministic offline SHADOW smoke;
- optional main-branch-only Neon/database migration/integrity/restore drills when credentials are available.

Contract:
- keep the broad `pytest` surface unless a later evidence-backed migration explicitly replaces equivalent coverage;
- do not silently remove a subsystem from this workflow merely because it gains a focused workflow;
- main-only database drills remain optional external-service gates and must not be misread as ordinary PR evidence when skipped.

### `dax-bot-1x-ci` — FOCUSED PRODUCT / CANDIDATE SAFETY OWNER

Workflow: `.github/workflows/dax-bot-1x-ci.yml`

Primary responsibility:
- fast focused checks for `candidate_*`, `broker_*` and operator runtime surfaces;
- Candidate correctness, restart/idempotency and broker-neutral safety tests;
- lean Candidate-specific lint surface;
- deterministic Candidate performance observation artifact.

Contract:
- optimized for fast product/runtime feedback;
- must retain `execution_capability=NONE` / no-order assumptions of the current product line;
- benchmark output is observation evidence, not profitability or promotion evidence;
- green focused CI does not replace broad `research-lab-ci` integration evidence when repository-wide compatibility matters.

### `reference-payload-export` — IMMUTABLE LEGACY REFERENCE OWNER

Workflow: `.github/workflows/reference-payload-export.yml`

Primary responsibility:
- hash-verify frozen recovered V11.2 source payloads;
- export only verified reference sources as short-lived CI artifacts.

Contract:
- reference identity is separate from DAX-BOT 1.x product correctness;
- hash mismatch fails closed;
- this workflow must never be interpreted as CAND-001 economic evidence or product acceptance.

## 3. Responsibility matrix

| Evidence / concern | Broad integration | Focused DAX-BOT 1.x | Reference payload |
| --- | --- | --- | --- |
| repository-wide pytest compatibility | PRIMARY | SUPPORTING subset | no |
| repository-wide lint | PRIMARY | SUPPORTING subset | no |
| Candidate/broker-neutral safety | INTEGRATION evidence | PRIMARY | no |
| Candidate benchmark observation | no | PRIMARY | no |
| recovery/reconstruction governance | PRIMARY | indirect | no |
| research registry/hypothesis integrity | PRIMARY | no | no |
| static Web/runtime safety smoke | PRIMARY | indirect | no |
| V11.2 probe/replay regression | PRIMARY | no | SUPPORTING identity |
| frozen recovered-source hash export | no | no | PRIMARY |
| offline synthetic SHADOW regression | PRIMARY | supporting Candidate tests | no |
| Neon/database restore drills on main | PRIMARY when configured | no | no |

## 4. Change-control rules

Before adding, splitting, removing or renaming a CI workflow or major CI gate:

1. identify the current responsibility owner;
2. identify the concrete defect, latency problem or ownership ambiguity being solved;
3. prove where equivalent regression evidence will remain;
4. update this contract in the same work unit;
5. add/update regression coverage when a machine-checkable ownership invariant exists;
6. do not create another workflow solely to make the repository look more modular.

Moving a check from one workflow to another is not complete until aggregate coverage is preserved and the new owner is explicit.

## 5. Safety / authorization

CI ownership never grants execution authorization.

- SHADOW remains no-order under the current product contract.
- `execution_capability=NONE` remains binding where applicable.
- `order_execution_enabled=false` remains binding.
- PAPER is not authorized.
- LIVE is not authorized.

No benchmark, test pass, CI pass, reference hash or workflow name may promote the bot to PAPER/LIVE or prove trading profitability.

## 6. Current decision

**RETAIN HYBRID CI / CLARIFY OWNERSHIP.**

Do not split `research-lab-ci` merely because it contains multiple evidence families. Its broad integration role is intentional. Keep focused `dax-bot-1x-ci` for fast Candidate/runtime safety feedback and `reference-payload-export` for immutable reference-source integrity. Revisit further CI decomposition only when a concrete runtime, latency, reliability or ownership defect appears.
