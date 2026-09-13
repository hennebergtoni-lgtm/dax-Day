# Reconciliation Red-Team — repository-local read-only evidence

All cases are offline fixtures, not real MT5/broker evidence. Default is BLOCK /
QUERY / RECONCILE; no ASSUME / RETRY / RELEASE. Existing owners remain authoritative.

| Case | Concrete test evidence / fail-closed outcome |
| ---: | --- |
| 1 open broker position at startup | `test_mt5_demo_open_inventory`: existing full-account position rows retained, ACCOUNT_HAS_OPEN_POSITIONS. |
| 2 open broker order at startup | same suite: ACCOUNT_HAS_OPEN_ORDERS; no empty-account assumption. |
| 3 manual order | `test_operator_console_inventory`: foreign symbol/tag visible; BLOCKED. |
| 4 manual position | same: full-account POSITION row; no ownership claim. |
| 5 reservation, venue unknown | `test_demo_transport_query`, `test_operator_console_reconciliation`: QUERY_REQUIRED; original state unchanged. |
| 6 hypothetical disconnect after future transport / before ACK | `test_demo_transport_attempt_reservation`, `test_demo_transport_restart_integration`: durable reservation survives; no submission is performed. |
| 7 reconnect fill, local fill missing | `test_reconnect_fill_observed_but_unapplied_local_checkpoint_is_contradiction`: actual fixture report separate from local REQUESTED; CONTRADICTION. |
| 8 partial fill | same parametrized test; existing unique-deal lookup checks partial quantities. |
| 9 duplicate reports | transport suite duplicate-half-fill test; no fabricated complete fill. |
| 10 out-of-order reports | transport suite reordered unique deals; same venue facts/fingerprint. |
| 11 empty open orders, contradictory history | existing order/deal remaining/cumulative mismatch blocks; no assume-flat. |
| 12 history order without deal | FILLED/PARTIAL without required fill evidence BLOCKED. |
| 13 history window too short | `test_short_history_and_empty_inventory_never_assume_flat`: NOT_FOUND + UNKNOWN history completeness; QUERY_REQUIRED. |
| 14 expired QUERY grant | lookup-script/reserved-query suites plus console expired query; scope veto before SDK query, browser cannot renew it. |
| 15 wrong account | inventory/transport account-before/after switch tests; fail closed. |
| 16 wrong server | transport normalized account mismatch and query recheck tests. |
| 17 wrong symbol | transport order/deal identity checks; console reservation/current context mismatch. |
| 18 quantity mismatch | transport request/fill/remaining checks; codec pins original requested quantity. |
| 19 native price precision mismatch | `test_native_inventory_precision_mismatch_blocks_without_rounding`; no invented rounding/tolerance. Weighted average fill price is not treated as a native tick price. |
| 20 broker clock / timezone mismatch | console projection host clock/timezone-cycle tests; missing tick clock UNKNOWN. |
| 21 stale inventory | console inventory old-bundle test: STALE; absent absolute reviewed inventory limit remains UNVERIFIED_THRESHOLD. |
| 22 stale UI, runtime alive | source/fetch clear + Candidate cycle mismatch tests; no source timestamp renewed by fetch. |
| 23 runtime alive, MT5 dead | console projection down-terminal tests: FEED BLOCKED, independent web liveness. |
| 24 MT5 alive, Candidate stale | console Candidate-behind/different-feed and heartbeat fingerprint tests: SNAPSHOT AGE STALE. |

Actual continuous brokerage reconciliation is not implemented as a second engine.
The read model presents UNKNOWN / QUERY_REQUIRED / CONTRADICTION / STALE from the
existing owner comparison and evidence provenance. No IN_SYNC is claimed merely
from a successful targeted lookup or empty inventory. Real startup/reconnect,
partial-fill, account economics and broker clock evidence remain Step2206/2122
external gates. Future active execution transport is separately unauthorized and
absent; no first-order readiness approval is implied by green repository tests.
