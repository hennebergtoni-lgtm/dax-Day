# Public Execution Review — 2026-09-13

Public projects are REVIEW INPUT only. The mappings below are our architectural
inferences from current primary documentation; they do not retroactively change
VERIFIED local baselines. Stable Freqtrade documentation and Nautilus `latest`
(non-nightly) concepts were used; no third-party code was copied or installed.
Passivbot master advertises a tagged release but includes unreleased changes;
only its documented general monitoring/config-separation concepts are review input,
not a claim that an unreviewed master implementation is a stable local contract.

| Primary project/source | Extracted concept | Classification / local mapping |
| --- | --- | --- |
| [Nautilus reconciliation](https://nautilustrader.io/docs/latest/concepts/reconciliation/) | Startup and continuous orders/fills/positions comparison; bounded history may recover order facts without proving portfolio economics; failed position query is not flat. | ADOPT observational inventory/history scope; ALREADY_HAVE pinned reservation, reconciliation, durable checkpoint and duplicate-safe lookup. |
| [Nautilus node](https://nautilustrader.io/docs/latest/how_to/configure_live_trading/) | Continuous checks follow startup reconciliation; venue identity and precision matter. | ADOPT operator-visible query/contradiction; REJECT a second engine, synthetic venue truth and timeout-to-terminal assumptions for this SHADOW lane. |
| [LEAN live concepts](https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/key-concepts) | Brokerage holdings/open orders initialize live portfolio; algorithm must not assume empty startup; stateful strategy restoration is separate. | ALREADY_HAVE local StateStore/guard/checkpoint; ADOPT full-account startup visibility; real retained broker-state reconciliation still external. |
| [LEAN reconciliation](https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/reconciliation) | Restart state and timing can diverge from a backtest. | ALREADY_HAVE causal CLOSED-M5/resume pins; REJECT deriving broker fills or runtime performance from research. |
| [Freqtrade stable API](https://www.freqtrade.io/en/stable/rest-api/) | Bind-local-first, protected SSH/VPN access, minimal ping separated from sensitive API. | ADOPT loopback and protected transport; ALREADY_HAVE GET-only console, no credentials/control coupling. Do not copy its trading/control routes. |
| [FreqUI](https://www.freqtrade.io/en/stable/freq-ui/) | Dedicated operator view above API. | ADOPT thin mobile projection; REJECT a SPA/auth-platform rewrite or exposing database credentials. |
| [Hummingbot GridExecutor](https://hummingbot.org/strategies/v2-strategies/executors/gridexecutor/) | Separate open/filled/close/completed states, bounded position/open-order exposure and failure/cost monitoring. | ALREADY_HAVE lifecycle/protection owners; ADOPT separate inventory/incident visibility; REJECT automatic grid cancellation/recovery/control. |
| [Passivbot](https://github.com/enarjord/passivbot) | Configuration/credentials separated, persistent logs/monitoring and version/migration review; configurable exposure controls. | ADOPT explicit runtime fingerprint and credential separation; ALREADY_HAVE single-instance supervision. REJECT martingale/re-entry/unstucking execution patterns for CAND-001. |

Hummingbot and Passivbot provide multiple established grid/execution examples;
no performance claims are adopted. OctoBot-specific source retrieval was unavailable
and no correctness claim relies on it. No identifiable primary ThunderGrid source
was supplied; its name describes the user's inspiration, not verified performance.

## Threat-to-owner matrix

| Threat | Existing authority / review outcome |
| --- | --- |
| startup with open order / position, manual/external inventory | Existing full-account MT5 query owner; typed inventory optional existing lookup export, separate console panel; never claim ownership from shortened tag. |
| reserved or ambiguous transport outcome; disconnect before ACK | Original durable attempt/consumed guard retained; query/reconcile required; no release/retry. |
| reconnect with missed/partial fill | Existing lookup aggregates unique deal evidence; existing `reconcile_broker_order` exposes unapplied local/venue mismatch; no repair. |
| duplicate / out-of-order report | Unique stable deal IDs, contradictory duplicates block; incident display sorting is not execution-state replay. |
| incomplete / short history; empty open orders but deals contradict | Scope/history completeness UNKNOWN; owner compares requested/remaining/cumulative fill; never infer flat or reconstruct economics. |
| quantity / precision mismatch | Existing request/venue quantity checks; native inventory volume-step/digits checked from observed canonical symbol metadata; unsupported symbols remain external economics gaps. |
| local versus broker clock / timezone | Existing host clock and explicit broker-wall-clock feed binding; broker tick clock absent means UNKNOWN, not browser time. |
| stale feed / Candidate / runtime snapshot | Existing feed source limit; exact Candidate/feed/heartbeat cycle mismatch STALE; snapshot/host absolute thresholds UNVERIFIED_THRESHOLD. |
| alive UI/backend with MT5 down or stale Candidate | Separate transport liveness / readiness / safety / broker truth; no GREEN aggregation that hides blockers. |
| remote UI / credentials / process supervision | Loopback/same-origin GET routes, structural redaction, no SDK/DB in HTTP, existing Windows Task Scheduler + single-instance lock. |

## Research-only backlog

Every item below is RESEARCH, without CAND-001 mutation or auto-promotion:

- ATR adaptive thresholds; consolidation detection; breakout and retracement quality.
- Entry delay; momentum and trend confirmation; session-specific behavior.
- Volatility circuit breaker; tail-risk regimes; MAE-informed stop and MFE-informed exit research.
- Adaptive-risk research; bounded hedge/recovery research.

Any later experiment requires causal evidence, independent provenance, OOS/WF and
explicit review. No unreviewed BASE/BOOST/HIGH promotion is permitted.

## Explicitly rejected patterns

Unbounded Martingale, unlimited averaging down, blind grid expansion, unlimited
rescue levels, doubling until recovered, automatic hedge escalation, autonomous
AI orders, strategy switching without OOS/WF, unknown-order blind retry/resubmit,
consumed-slot release and public unauthenticated control APIs are REJECT.

No second database/store/journal/risk/lifecycle/readiness/reconciliation/health
framework, cloud infrastructure or React migration was justified. Thin display
projections use the existing canonical owners and preserve NONE/false.
