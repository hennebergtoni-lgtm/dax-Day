# DAX-BOT 1.x Migration Safety Gate

Status: PLANNED MIGRATION GOVERNANCE / NO EXECUTION AUTHORIZATION

Purpose: protect the accumulated project work while creating the DAX-BOT 1.x product line. A cleaner bot architecture must not erase verified evidence, useful research, working observability or already-tested runtime safety.

## 1. Non-destructive migration rule

The DAX-BOT 1.x line begins alongside the existing verified project state.

Until a component has passed this gate:
- do not delete it;
- do not silently replace it;
- do not redirect the Windows/MT5 host to a new path;
- do not change broker execution safety;
- do not reinterpret historical evidence;
- do not promote research into runtime by naming alone.

`main` remains the stable project truth. Next-generation work is isolated on a branch until CI, replay and compatibility checks pass.

## 2. Classification vocabulary

Each existing component receives exactly one migration classification:

- `PRESERVE` — authoritative evidence or contract remains unchanged.
- `REUSE` — directly reused by the new bot because semantics already match.
- `ADAPT` — retained behind a thin adapter; business logic is not duplicated.
- `RESEARCH_ONLY` — valuable evidence/tooling remains available but stays outside the bot hot path.
- `REPLACE_AFTER_PARITY` — replacement is allowed only after deterministic parity/compatibility evidence.
- `RETIRE_AFTER_AUDIT` — removable only after consumer/test/CI/runtime analysis proves it obsolete.
- `FIX_REQUIRED` — known ambiguity or defect must be resolved before use in the new hot path.

## 3. Initial protected inventory

| Area | Current asset / evidence | Initial classification | DAX-BOT 1.x rule |
|---|---|---|---|
| Frozen reference | `REF-V11.2`, clean 856-trade evidence, hashes, WF evidence | PRESERVE | Immutable negative comparison/regression anchor; never rewritten as the new strategy. |
| Historical dataset | audited 2014–2019 M5/session identity and hashes | PRESERVE | Continue as historical evidence; newer data may be added as separate versioned evidence. |
| Candle/data contracts | canonical runtime Candle/closed-bar identity/data-quality checks | REUSE | One canonical data boundary for replay, SHADOW and PAPER_SIM where semantics match. |
| Closed-bar causality | closed M5 only, chronological processing, duplicate handling | REUSE | Mandatory invariant for 1.x. |
| Decision audit | `DecisionRecord`, deterministic decision IDs, reason/setup fields | REUSE/ADAPT | Extend only if required; do not create parallel decision objects without proof. |
| Safety gates | `execution_capability=NONE`, `order_execution_enabled=false`, readiness gates | PRESERVE/REUSE | Alpha cannot bypass these. |
| MT5 read-only adapter | broker symbol/timezone/feed/closed-bar acquisition | REUSE/ADAPT | Preserve working Windows path; strategy product change alone does not require host reinstall/reconfiguration. |
| SHADOW runtime | supervisor/integration/watchdog/health/cross-cycle integrity | REUSE/ADAPT | Keep proven observability/reconciliation; attach new strategy only through tested contract. |
| Neon SHADOW telemetry | heartbeat, bars, decisions and idempotent outbox behavior | PRESERVE/ADAPT | Existing NO_ORDER SHADOW semantics remain intact; do not overload with incompatible PAPER lifecycle records. |
| Paper contracts | ExecutionIntent, fill/cost/same-bar/gap/simulation-only contracts | REUSE | Use existing contracts before creating a second simulator. |
| Paper outcome/ledger | virtual outcome, R/cash ledger, performance views | REUSE/ADAPT | Use for 1.x PAPER_SIM after strategy decision adapter is proven. |
| Recovery | restart/reconcile plus current recovery modules | FIX_REQUIRED | Resolve duplicate `recovery.py` vs `recovery_bundle.py` consumer/test/runtime matrix before choosing hot-path implementation. |
| Context resume governance | deterministic project resume/reconciliation policy | PRESERVE | Mandatory work-recovery rule. |
| Research registry | 17 research families and evidence maturity | PRESERVE / RESEARCH_ONLY | All knowledge remains available; nothing becomes a runtime filter without candidate promotion evidence. |
| Filter/feature code | ATR, Bollinger, Fibonacci, Gap, Structure, Momentum, Session, Entry/Exit, TWAP, etc. | RESEARCH_ONLY initially | Promote one at a time through candidate/config/version lineage; do not preload all into alpha. |
| Robustness tooling | WF/OOS, degradation, backward elimination, overlap/ablation, multiple testing, DSR/MinTRL/PBO-related tooling | RESEARCH_ONLY / REUSE in validation | Mandatory validation toolkit, not runtime hot path. |
| Operator views | forward monitoring view + view models | ADAPT | Reuse as operator-facing model boundary where practical. |
| Web UI | `web/index.html` + status model | PRESERVE/ADAPT | Keep user-facing observability; evolve from research-only dashboard toward bot status without losing evidence views. |
| CI | Ruff, pytest, recovery preflight, registry/ledger/web checks, reference/replay/shadow smokes, DB drills | PRESERVE/EXTEND | Existing checks must stay green; new 1.x compatibility/replay tests are additive before any removal. |
| Database | research schema + SHADOW telemetry | PRESERVE | No schema removal as part of version renaming; new runtime persistence only after reuse/schema gate. |
| Windows host | clean git clone + existing MT5/Python runtime arrangement | PRESERVE | No manual user changes until repository-only path proves stable and a host migration is explicitly required. |

## 4. Research knowledge preservation

The next-generation bot must not discard the accumulated research simply because the runtime becomes simpler.

Research remains versioned evidence, including but not limited to:
- OR5 / OR15 behavior;
- breakout / retest differences;
- stop logic and RR;
- previous-range and OR/ATR filtering;
- ATR regimes / ATR25 concepts;
- Bollinger research;
- Fibonacci/retracement research;
- gap behavior;
- liquidity / failure / momentum / market-structure research;
- session effects;
- entry and exit diagnostics;
- TWAP/anchored-price research;
- ADX/BODY/COMP/STALE findings;
- ablation, overlap, backward elimination and Pareto analysis;
- multiple-testing and overfitting-protection methods;
- forward degradation/stability evidence.

Preservation does not equal activation. A DAX-BOT release uses an explicit promoted candidate/config snapshot.

## 5. Web and observability protection

The web/operator surface is a first-class capability, not decoration.

DAX-BOT 1.x must expose enough state to answer:
- Is the bot alive and healthy?
- Which product version and strategy candidate/config is active?
- Which data bar was last processed?
- What REGIME and STRUCTURE were identified?
- Was there a setup?
- Why TRADE or NO_TRADE?
- If TRADE: LONG/SHORT, planned entry, stop, target, RR and reason codes.
- Is a virtual trade open?
- What is the virtual outcome / R after closure?
- Are any blockers, stale data, duplicate bars, recovery/reconciliation events or safety violations present?

Existing research/evidence views remain available; bot-operation views are added rather than replacing them blindly.

No database credential may be exposed in a static browser client.

## 6. Migration test gates

Before DAX-BOT 1.x can replace any existing operational path, all applicable gates must pass:

1. **Repository isolation** — only intended files changed.
2. **Existing CI preservation** — all pre-existing checks remain green.
3. **Contract tests** — Candle, DecisionRecord, Safety, Paper contracts remain compatible.
4. **Deterministic replay** — identical persisted input produces identical decisions/outcomes/config fingerprints.
5. **Causality** — closed bars only; no future-bar access; no same-bar lookahead beyond explicitly defined conservative policy.
6. **Duplicate safety** — repeated bar/restart does not create duplicate decision/intent/outcome.
7. **Restart/reconcile** — state can be reconstructed/reconciled without hidden process memory.
8. **No broker execution** — import/static/runtime tests prove no MT5 `order_send` path in alpha.
9. **Observability** — operator/web-facing state exposes version/config/decision/health safely.
10. **Backward evidence access** — V11.2/reference/research artifacts remain available and unchanged.
11. **Host non-regression** — no Windows/MT5 manual migration until repository and PAPER_SIM evidence justify it.

## 7. Definition of a safe first alpha

`DAX-BOT 1.0-alpha` is not accepted merely because code runs.

It must demonstrate a small end-to-end vertical slice with:
- real or deterministic replay closed M5 input;
- one explicit strategy candidate/config;
- deterministic REGIME -> STRUCTURE -> ENTRY evaluation;
- auditable TRADE/NO_TRADE;
- deterministic virtual intent for trades;
- later-bar-only virtual outcome progression;
- stable state across restart/replay;
- operator-visible health and decision state;
- all execution safety invariants intact.

Performance/profitability is evaluated later and separately. The first alpha proves controllability, correctness and observability.

## 8. No-manual-host-work principle

Repository-side evolution should be completed and tested before asking the user to touch the Windows machine.

User interaction with the host is required only when a real host-only fact cannot be validated elsewhere or when a tested migration is ready to be activated. Avoid repeated manual command entry for work that can be proven by CI/replay/repository tests first.