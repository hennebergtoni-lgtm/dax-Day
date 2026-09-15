# Targeted public donor rescan — 2026-09-14

Primary sources were reopened during this Work. These are architecture/testing donors, not profitability evidence. REUSE/adaptation decisions are ours. No third-party framework is installed.

| Donor | Primary source | Decision and local owner |
| --- | --- | --- |
| NautilusTrader | https://nautilustrader.io/docs/latest/concepts/reconciliation/ | ADAPT bounded history, startup barrier, report dedup and order-origin semantics in broker_reconciliation / restart_reconcile; REJECT inferred terminal outcomes based only on missing reports or timeout. |
| Freqtrade | https://www.freqtrade.io/en/stable/lookahead-analysis/ ; https://www.freqtrade.io/en/stable/recursive-analysis/ | ADAPT prefix and warmup perturbation tests in existing causal research owners. Absence of triggered signals is not full bias coverage. Keep complete trial families and report tested scope. |
| QuantConnect LEAN | https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/reconciliation | ADAPT dimensional data/clock/cost/broker/spec drift and stateful restart; existing conformance/manifests owners. Scheduled time and actual bar availability are different clocks. |
| vectorbt | https://vectorbt.dev/api/portfolio/base/ | ADAPT memory-efficient coarse screening before selected event/lifecycle checks. REJECT a second portfolio engine and simulated records as broker truth. Existing trial registry/statistics retained. |
| Backtrader | https://www.backtrader.com/docu/live/ib/ib/ | ADAPT delayed/backfilled versus current feed distinction and independent cash/value observation; IG feed/operator owners. REJECT provider-specific IB retry/backfill rules as an IG contract. |
| Hummingbot | https://hummingbot.org/connectors/connectors/architecture/order_lifecycle/ | ADAPT start tracking before transport and keep client ID separate from venue acceptance. Existing reservation/lifecycle owners; REJECT self-managing retry/cancel without exact bounded authority and reconciliation. |
| Passivbot | https://github.com/enarjord/passivbot/blob/master/docs/metrics.md | ADAPT realized-PnL versus mark-to-market equity and drawdown duration semantics in failure_analysis. REJECT grid rescue/averaging/exposure escalation and all performance marketing. |
| IG official REST | https://labs.ig.com/rest-trading-api-guide.html ; https://labs.ig.com/reference/positions-otc.html ; https://labs.ig.com/reference/confirms-deal-reference.html | REUSE in-memory V2 session headers for repeated reads. User-defined dealReference and confirmation/affectedDeals require native IG conformance; an HTTP acknowledgement is not fill proof. No undocumented duplicate-reference guarantee. |

IG V2 session documentation describes initial six-hour token validity with usage extension up to72 hours. This does not explain host401 or justify blind relogin. Existing one-owner single-session/no-retry design is retained.

REST M5 timestamp-start/end remains unresolved. No streaming convention substitutes for REST evidence. A few stable later observations cannot establish permanent immutability or a maximum revision duration.
