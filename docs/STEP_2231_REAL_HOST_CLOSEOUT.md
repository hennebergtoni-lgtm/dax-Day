# Step 2231 — corrected IG real-host closeout

Date: 2026-09-14. Status: COMPLETED / VERIFIED AS SUPPLIED.
Scope: corrected IG M5/Freshness/pagination feed lane only; M01 overall remains incomplete.

## Evidence and provenance

Source: the user's explicit STEP2231 CLOSEOUT / STEP2232 Work mandate in this turn.
Work did not remotely operate Windows or authenticate to IG.
Expected and actual start head: `8523c6cd98944c6ed95f6f7af585e2c4d9eb41de`; no drift.
main: `e0784ebfc11bee28475fd9c3385be661af58a738`; PR109 OPEN/UNMERGED.
Start-head CI: DAX #670/run34831356532 and Research #1454/run34831356485 SUCCESS.

| Acceptance item | Supplied actual Windows result |
|---|---|
| Worktree | `C:\Users\Mandy\Documents\dax-Day-ig-hostcheck` |
| Checkout | clean at the current PR head, as reported |
| Credentials location | `C:\Users\Mandy\ig_demo.env`, external to Git; contents never accessed |
| Probe | existing `ig_demo_readonly_probe.py`, exact EPIC `IX.D.DAX.IFMM.IP`, bars40 |
| Process/output | exit0; evidence file newly written |
| Raw/closed/excluded | raw40; excluded0; derived closed40 |
| Freshness | FRESH; latest closed age approximately231 seconds; unchanged600-second limit |
| Timestamp contract | IG_MINUTE_5_SNAPSHOT_UTC_INTERVAL_END_V1 |
| Market | TRADEABLE |
| Inventory | open positions0, working orders0 |
| Safety | NONE/false; no order, cancel or modify reported |
| Fingerprint | present, actual digest not supplied |
| Protection/reconciliation | UNKNOWN / UNKNOWN |

The actual JSON bytes, exact timestamps, OHLC values and fingerprint digest were not
provided in this turn. They are not reconstructed from approximate age or invented.
The successful corrected probe closes the earlier actual host freshness blocker,
but does not isolate pagination as its sole historical cause or formally prove all
IG instruments' label semantics. It verifies this observed corrected Demo lane.
Zero counts are non-atomic observations, not full-history flatness/protection proof.

## Remaining scope

Step2232 must prove IG input reaches the existing generic CAND-001 SHADOW pipeline,
state/virtual lifecycle and validated operator telemetry on the actual host.
M01 overall, Step2206 policy review and MT5 host2122 remain independent/external.
Execution NONE/false, SHADOW only; no DEMO/PAPER/LIVE orders, cancel/modify, slot
release, merge, force push, Acceptance refresh, strategy or frozen V11.2 change.
