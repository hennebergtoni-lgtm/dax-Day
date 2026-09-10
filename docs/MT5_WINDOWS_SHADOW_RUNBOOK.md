# MT5 Windows SHADOW – Verification Runbook

Status: repo-side procedure only. Windows host evidence remains UNVERIFIED until each host step is executed and captured.

## Safety boundary

- SHADOW only.
- `execution_capability=NONE`.
- `order_execution_enabled=false`.
- No credentials are written to repo evidence.
- No paper/live order authorization is implied.
- V11.2 remains frozen.

## Host sequence

Run one host step at a time and inspect its output before continuing.

1. Update the local repo to the reviewed `main` commit.
2. Run `scripts/mt5_windows_host_discovery.py` with the dedicated `.venv-mt5` Python.
3. Confirm Windows, Python path, repo root, supervisor presence, and MetaTrader5 importability.
4. Run the existing credential-free `mt5_windows_probe.py` with the candidate broker timezone and a new timestamped evidence filename.
5. Inspect RAW vs NORMALIZED tick-clock deltas. Do not infer verification from configuration alone.
6. Run `mt5_timezone_diagnostic.py` on that evidence. Its result remains explicitly unverified pending host-clock review.
7. Compare MT5/server wall-clock behavior against UTC and Europe/Berlin on the actual host; record the evidence without credentials.
8. Only after that comparison is reviewed may `broker_timezone_verified` become true in a separate evidence decision.
9. Run the supervisor once with `--once`; inspect `heartbeat.json`, `latest_bundle.json`, `resume.json`, and heartbeat history.
10. Confirm `execution_capability=NONE`, `order_execution_enabled=false`, BAR_0 excluded, closed-M5 feed valid, and no credential fields.
11. Test Windows single-instance lock by attempting a second supervisor instance; the loser must not write shared state.
12. Test graceful stop and resume; previously processed bars must be deduplicated.
13. Only after all above gates are green, install the existing Task Scheduler tasks with the verified broker timezone.
14. Inspect both registered tasks: interactive limited user, IgnoreNew, restart policy, no stored DAXLAB credentials.
15. Reboot once and verify MT5 starts, SHADOW starts, heartbeat resumes, and no duplicate processing occurs.
16. Produce a post-reboot Forward Evidence Summary from heartbeat history.

## Fail-closed rule

Any ambiguous timezone, stale feed, invalid resume, missing supervisor/venv, lock failure, schema mismatch, cross-cycle mutation, or credential-contract failure keeps the host BLOCKED/NO_ORDER. Do not bypass a blocker to make the task start.
