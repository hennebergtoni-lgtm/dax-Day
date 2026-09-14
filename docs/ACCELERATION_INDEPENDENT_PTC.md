# Independent Pre-Trade Controls — existing protection owner

Step2236 extends src/daxlab/runtime/broker_execution_protection.py with an independent closed-schema PTC diagnostic. It requires explicit pinned DEMO account/instrument, native quantity/price/tick/increment, cash point value, limits and observed attempt/inventory/session/reservation/emergency states. Bounds and identities are operator/broker-policy inputs; no defaults manufacture IG economics.

Green strategy risk cannot clear price collar, quantity/increment, native price grid, notional exposure proxy, message/attempt count, duplicate, stale price, inventory, account, instrument, session, unresolved reservation or emergency latch vetoes. NONE/false is mandatory even for ALLOW_EVIDENCE. The canonical existing protection verdict is independently required. No public control endpoint, unlock method, dealing route, reservation release or state mutation is introduced.

The notional definition is explicitly native quantity × price × broker cash-per-point-per-unit; it is an exposure proxy, not margin or a universal provider contract. Price collar uses caller-pinned fresh reference. Bounds are inclusive; attempts_used >= max_attempts is blocked. Reservation ambiguity requires query. Broker/source/component hashes are caller pins and need actual source evidence.

Existing normalized protection booleans now require literal bool; truthy strings/integers/None cannot open evidence gates. Persisted execution state requires literal false, preventing NONE/None and NONE/0 contradictions. Finite numeric age validation rejects overflow and wrong types. Existing valid canonical risk/session/loss binding semantics stay intact.

Tests explicitly inject each independent veto with otherwise green risk/protection, invalid native grids, missing identity, credential nesting, stale/unknown clocks, unknown reservations, emergency latch, malformed normalized safety booleans and persisted capability contradictions. These are local synthetic tests, not real IG broker conformance.

**IMPLEMENTED / LOCAL VALIDATION PENDING FINAL CI.** Bounded transport integration and actual IG policy/economics/reconciliation/kill authority are WAITING_EXTERNAL / NOT VERIFIED. This diagnostic does not enable the first order, autonomous emergency dealing or continuous DEMO.
