# Remote Operator Runbook — read-only SHADOW

This console observes existing runtime artifacts. It never submits orders, repairs
state, releases reservations or authorizes DEMO/PAPER/LIVE. Step 2206 and host lane
2122 remain WAITING_EXTERNAL / USER_AUTH. A responding web process is not a healthy
MT5 terminal, a fresh Candidate, reviewed risk or broker reconciliation.

## Windows startup

Use the existing Windows environment and scheduled-task/single-instance owner.
Do not start another supervisor when the scheduled task already owns the lane.
Inside the actual runtime checkout:

```powershell
git status --short
git rev-parse HEAD
$env:PYTHONPATH = 'src'
python scripts/mt5_shadow_supervisor.py --help
```

Compare checkout HEAD with the independently verified PR #109 head, then compare
**supervisor startup build observation** in the console with that same head. The
webserver checkout does not prove the running bot's revision. Uncommitted,
unsupported or mismatched build evidence blocks pre-DEMO trust.

Open the already configured MT5 terminal. Verify connection, the expected DEMO
account, server and symbol directly on the host; never enter credentials in the
browser. Broker timezone must come from the real host review, not the iPhone or
Windows timezone. Only after replacing the placeholders with reviewed values,
start the existing SHADOW owner if it is not already running:

```powershell
python scripts/mt5_shadow_supervisor.py --symbol <REVIEWED_SYMBOL> --broker-timezone <REVIEWED_IANA_ZONE> --state-dir .runtime/mt5_shadow
```

Do not override freshness/cost/risk policies as part of this runbook. Supervisor
polling interval is not a policy freshness limit. Existing Task Scheduler restart
must preserve `.runtime/mt5_shadow`, original Candidate checkpoint and any original
reserved-attempt store. Never delete a consumed slot to obtain a clean restart.

## Console startup and local verification

In a second shell, with the same Python environment and `PYTHONPATH=src`:

```powershell
python scripts/serve_operator_console.py --state-dir .runtime/mt5_shadow --port 8765
Invoke-WebRequest http://127.0.0.1:8765/healthz
Invoke-WebRequest http://127.0.0.1:8765/api/operator
```

Open `http://127.0.0.1:8765/`. The socket is fixed to loopback. There is no bind-all
option. Only fixed GET observation/static routes exist; control methods return
405. HTTP 200 means the canonical required source files were read and validated;
`healthz.process_responding=true` is web liveness only. It grants no readiness.
503 or an invalid response clears old browser evidence.

If an **original pinned reservation and operational read-only lookup export**
already exist, attach them using the existing file-store load owner:

```powershell
python scripts/serve_operator_console.py --state-dir .runtime/mt5_shadow --attempt-state-dir <ORIGINAL_STORE_DIRECTORY> --attempt-key <ORIGINAL_KEY> --reservation-fingerprint <ORIGINAL_RESERVATION_SHA256> --broker-evidence <EXISTING_LOOKUP_ENVELOPE_FILE> --broker-evidence-fingerprint <ORIGINAL_ENVELOPE_SHA256>
```

The existing query/export owner optionally includes full-account orders/positions
with `--include-account-open-inventory`; its existing request/QUERY preflight
remains mandatory. This runbook does not create a reservation, fake a QUERY grant
or provide an order step. Without supplied real inventory, INVENTORY=UNKNOWN.
The export is immutable observed evidence, not an automatically renewed live query.

## Secure remote access and iPhone

Prefer your existing protected Remote Desktop session; open the Windows-local URL
inside that session from the iPhone. Alternatively use a private VPN plus an
already administered SSH tunnel. A VPN alone does not make a loopback listener
reachable. The tunnel must terminate at Windows loopback; e.g. on an SSH client:

```text
ssh -N -L 8765:127.0.0.1:8765 <ADMINISTERED_WINDOWS_SSH_HOST>
```

Open `http://127.0.0.1:8765/` in the browser **on the tunnel's client**. On iPhone
this requires a managed iOS client that exposes a local forwarded port to Safari;
otherwise use Remote Desktop. This has not been proven on your actual iPhone.
Host/Origin must remain the supported local URL/port. A different forwarded port
or proxy Host is deliberately rejected. Do not relax the same-origin contract to
make an unreviewed proxy work. No public API, cloud deployment, port-forwarding on
the router or credentials in frontend files is required.

## Interpret the screen

- GREEN: only the specific source-backed observation named by that field.
- WARN/BLOCKED: inspect every blocker; a live process may remain LIVENESS=GREEN.
- UNKNOWN / UNVERIFIED_THRESHOLD: evidence or a reviewed freshness policy is missing.
- STALE: reviewed source limit exceeded or exact observation-cycle binding differs.
- WAITING_EXTERNAL / USER_AUTH: real host/policy evidence or separate approval required.
- QUERY_REQUIRED: reservation or an unapplied venue report requires canonical query/reconcile.
- EXECUTION=BLOCKED/DISABLED: mandatory current safety, never GREEN.

Browser fetch time, snapshot generated-at, CLOSED-M5 close, MT5 host observation,
local inventory collection, broker clock and reconciliation timestamps are distinct.
Reloading the page renews none of them. A successful empty inventory query proves
only those completed non-atomic open-object queries; history and ownership remain
unverified. A matching shortened transport tag does not claim a manual position.

## Incident response without orders

On stale Candidate/feed or MT5 disconnect, keep execution disabled, record the
exact source/build timestamps and blocker identities, and inspect the existing
supervisor/Task Scheduler/MT5 connection on Windows. Preserve checkpoints. A
reconnect does not erase the ambiguous outcome of a hypothetical future submission.
For any existing reservation, unexpected broker object, partial fill, local/venue
mismatch or incomplete history: stop promotion, preserve original evidence and use
only the canonical authorized QUERY/reconciliation review. Never assume flat,
retry/resubmit, cancel/modify or release a slot from this console.

## Monday pre-DEMO checklist

1. Independently verify exact PR head, both required CI checks and unchanged main.
2. Verify actual runtime checkout/startup build and persistent scheduled-task owner.
3. Check real Windows host and MT5 terminal/account connections.
4. Check fresh feed and latest genuinely CLOSED-M5 at the canonical reviewed limit.
5. Check broker clock, timezone mapping, local drift and session review.
6. Check actual expected DEMO account fingerprint, server and symbol; exclude REAL.
7. Observe full-account open orders/positions through the existing query owner;
   review foreign/manual inventory, source time and non-atomic collection.
8. Review real broker economics and exact account/source binding.
9. Review FixedCashRiskPolicy and LossExposurePolicy numeric limits explicitly;
   verify current loss/exposure observation and checkpoint provenance.
10. Review current protection, session guard, reservation and lifecycle checkpoints.
11. Resolve every ambiguous/local-venue/history/quantity/precision contradiction via
    canonical QUERY/reconcile; missing or short history never proves no exposure.
12. Verify telemetry/checkpoint/heartbeat cross-bindings and freshness-policy gaps.
13. Verify NONE/false and SHADOW-only authorization remain visible.
14. Complete external Step 2206 and lane 2122 review. Any first DEMO evidence order
    still requires a separate explicit bounded user authorization and reviewed
    active submission capability; this read-only tranche does not provide either.

Any UNKNOWN, STALE, BLOCKED, unresolved QUERY_REQUIRED, unexpected inventory,
unreviewed economics/risk/loss/protection or missing authorization blocks promotion.
No order procedure is included.
