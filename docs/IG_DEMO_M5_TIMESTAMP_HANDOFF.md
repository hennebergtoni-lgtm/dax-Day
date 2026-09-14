# IG Demo M5 host handoff — Step 2231 / M01

Updated: 2026-09-14. Local implementation is **IMPLEMENTED**; corrected Windows host evidence is **WAITING_EXTERNAL**. This handoff does not complete M01/2231 or authorize execution.

## Repository pin and drift

- Repository: `hennebergtoni-lgtm/dax-Day`; branch `nextgen-bot-line-v1`; PR #109 remains open/unmerged.
- Exact start head: `3f96a2e23b1d55bf7cb69cfa67c6721b6da6b1fc`; actual PR head matched: **NO START DRIFT**.
- Main: `e0784ebfc11bee28475fd9c3385be661af58a738`.
- This change creates a newer head. Before the host rerun, re-pin the actual PR head and both required CI checks; synchronize the Windows checkout to that exact head. Never use the start SHA as the fixed deployment target.
- Publication/CI evidence is recorded below once available. Green CI is local/fixture evidence, not a real IG observation.

## Supplied real host evidence — preserve, do not invent

The user verified IG Demo login/API-key, account/market REST reachability, Deutschland 40, primary 1-EUR EPIC `IX.D.DAX.IFMM.IP`, TRADEABLE market, live Bid/Offer and available M5 history. These are **VERIFIED AS SUPPLIED**, not independently rerun here.

At approximately `2026-09-14T09:02:59Z`, ten raw UTC labels were returned: 08:20, 08:25, 08:30, 08:35, 08:40, 08:45, 08:50, 08:55, 09:00, 09:05. The real 40-bar probe still failed closed with `IG candle source requires fresh M5 data` after the previous fix.

## Reproduced defects and limits of causal attribution

1. The pinned adapter interpreted each raw label as bar-open and added five minutes. The probe duplicated that rule. Replaying the supplied ten timestamps against the original code yields **eight** closed bars: the last canonical close is 09:00, but its OHLC belongs to raw **08:55**, not raw 09:00. OHLC values used for this regression are synthetic fixtures, never broker evidence.
2. That exact ten-row sample **does not reproduce the freshness exception**: the original latest calculated close is still only 179 seconds old, below the existing 600-second limit. Do not claim the timestamp fix alone proves the real host exception's complete cause.
3. IG prices v3 defaults to `pageSize=20` / `pageNumber=1`. The original probe requests `max=40` without disabling paging. A bounded fixture reproduces stale first-page history while the requested complete history is fresh. The client now requests `pageSize=0` and rejects an explicit multi-page response. This is a reproduced request-contract gap; actual pagination metadata from the failing Windows 40-bar response was not supplied. Its role in the real failure remains **UNVERIFIED UNTIL HOST RERUN**.

## Canonical M5 contract — IMPLEMENTED, host rerun pending

Owner: `src/daxlab/adapters/ig_market_data.py`, shared by the existing probe. Contract identity: `IG_MINUTE_5_SNAPSHOT_UTC_INTERVAL_END_V1`.

- This IG lane normalizes `snapshotTimeUTC` as the interval-end boundary.
- `close_time = snapshotTimeUTC`; `event_time / bar-open = close_time - 5 minutes`.
- All canonical times are timezone-aware UTC. The UTC-named wire field may omit its offset and is then assigned UTC. No fallback to local `snapshotTime`, no broker/DST wallclock offset guessing.
- At 09:02:59, raw 09:00 closes [08:55, 09:00); raw 09:05 remains excluded. Nine rows are closed and the latest OHLC comes from raw 09:00. At exactly 09:05:00, raw 09:05 is eligible under this contract.
- Closure uses the price request's **start** observation. Response observation drives freshness. A request crossing a bar boundary cannot promote a row fetched while it was still running.
- Chronology, uniqueness, continuous M5 grid, valid UTC labels, OHLC/bid-ask invariants and implausibly future history fail closed. A valid live tail is omitted; it never becomes a canonical future candle.
- Freshness still uses the existing adapter limit of **10 minutes / 600 seconds**, inclusive at the limit; no threshold was invented or loosened. Stale history remains blocked.

Official [IG prices v3 reference](https://labs.ig.com/reference/prices-epic.html) confirms MINUTE_5, UTC field and paging defaults/disable option. It describes `snapshotTimeUTC` only as **Snapshot time**, without formally specifying open versus end. The supplied host labels support this lane's interval-end normalization; official documentation alone does **not** prove a universal endpoint/market convention. [Streaming CONS_END](https://labs.ig.com/streaming-api-reference.html) belongs to a different API and was not substituted as REST proof. The corrected real-host run is still required.

## Read-only evidence and parity boundaries

The existing client still owns the one IG session. Only session login/logout and account, full-account position/working-order, market and M5 GET queries are used. No dealing call is present.

Success evidence includes IG_DEMO, strictly projected account metadata without raw account/login IDs, position/working-order counts, exact EPIC, market status, finite Bid/Offer, raw/closed/excluded M5 counts, raw latest label, latest canonical closed candle, timestamp contract, local request/response observations, existing M5 freshness limit/age and deterministic fingerprint. Provider free text/nested metadata is not copied. Scalar/enumerated allowlists are primary; recursive credential-marker/key checks are additional defense. CLI failures emit fixed local BLOCKED codes rather than provider exception text or secret-bearing traceback chains.

**Do not infer protection or reconciliation parity from counts.** Existing broker-neutral protection/lifecycle/reservation/query owners remain unchanged. This probe does not create a second reconciliation engine, translate IG counts into MT5 account evidence, prove full history/flatness, release reservations or mutate local state. Inventory is non-atomic, history completeness is false, reconciliation/protection remain UNKNOWN. Unexpected inventory requires human review, not automatic action.

Market observation is a local response timestamp, not broker clock evidence. `updateTimeUTC` may lack a date; local `updateTime` is not relabelled UTC. Quote/inventory freshness stays UNKNOWN / UNVERIFIED_THRESHOLD where no reviewed threshold/source timestamp exists. No GREEN promotion or execution readiness is derived from those gaps.

## Validation

- IG focused regressions: **70 passed** (adapter, REST, inventory and actual probe projection/CLI tests).
- Relevant Candidate/broker/runtime/MT5/operator regressions: **1069 passed**.
- Full pytest: **2689 passed, 6 skipped** because local `pwsh` is unavailable; these skips remain separate from real Windows evidence.
- Full Ruff, Python syntax/imports and JavaScript syntax: **PASSED**.
- Eight existing offline gates: recovery preflight, research registry, hypothesis ledger, web static integrity, runtime safety, frozen engine probe, V11.2 replay and shadow soak: **PASSED**. Replay/soak are fixture/synthetic-only.
- Required `dax-bot-1x-ci` and `research-lab-ci`: **PENDING PUBLICATION**, never claimed green in advance.

## Exact next Windows host probe

Prerequisite: synchronized exact current PR head, passing required CI, existing Windows Python environment and the **already used credentials file outside the repository**. Its actual path was not supplied; replace the single placeholder below with that existing path. Do not create or publish new credentials.

```powershell
python scripts/ig_demo_readonly_probe.py --credentials-file "<BISHER_VERWENDETE_IG_CREDENTIALS_DATEI>" --epic IX.D.DAX.IFMM.IP --bars 40 --output .runtime/ig-demo-readonly-evidence.json
```

This is the only next broker-facing command, and is read-only. Require exit 0, a new observation timestamp/fingerprint, the exact EPIC, NONE/false, plausible raw/closed/excluded counts, latest closed <= price request start and age <= 600 seconds. Inspect current Bid/Offer, counts and UNKNOWN provenance limitations. The fixed 09:00/09:05 expectation applies only to the supplied 09:02:59 diagnostic instant; use the actual new UTC boundary for the rerun.

On exit 2 / STALE_M5_HISTORY / INCOMPLETE_M5_PAGINATION / clock reversal: **BLOCKED**, keep execution disabled, share only the redacted output/exit code and timing/page/count evidence. Do not share API keys, session headers, credentials or raw account IDs. Failed runs do not replace an existing output file: never mistake an old saved success for the failed run's current evidence. No retries of orders, no cancel/modify, no slot release.

## Remaining truth and safety

- **2231 / M01:** local correction IMPLEMENTED; corrected Windows rerun WAITING_EXTERNAL; not fully COMPLETED/VERIFIED.
- **2122:** existing Windows/MT5 market-open clock/Candidate/restart evidence WAITING_EXTERNAL; IG observations do not silently close that lane.
- **2206:** host/policy review WAITING_EXTERNAL / USER_AUTH.
- Actual first DEMO evidence order: BLOCKED by absent authorization and execution capability; outside this task.
- `execution_capability=NONE`; `order_execution_enabled=false`; SHADOW authorized only. DEMO/PAPER/LIVE execution unauthorized.
- No actual IG/MT5 session was opened by this Work; broker orders/side effects/order_send calls = 0. V11.2, CAND-001 trading logic, costs, risk/protection/execution and verified MT5 path unchanged. No fabricated broker evidence, merge, force push or Acceptance refresh.
