# Operator UI verification — 2026-09-13

Runtime page remains vanilla HTML/CSS/JS. Fourteen source-backed status tiles,
mandatory SHADOW safety banner and prominent blockers precede details. Decision
shows existing Regime -> Structure -> Setup/Entry, admission, signal reason and
proposed Entry/Stop/Target/RR. Browser does not compute decisions or risk values.
Broker inventory and local lifecycle/checkpoint remain separate panels.
Health/freshness/Monday gate lists use native collapsed details to avoid placing
large evidence lists before the decision. Source hashes are textual and wrap;
there are no Start/Stop/Trade/Cancel/Modify buttons (one refresh button only).

Executed evidence:

- Real loopback GET and forbidden-method / same-origin / source-error socket tests.
- Actual Node execution of frontend validator rejects EXECUTION=GREEN.
- Actual Node DOM-branch execution renders fourteen tiles, STALE/UNKNOWN/BLOCKED,
  external POSITION inventory, long blocker text and USER_AUTH gate.
- Failed fetch clears prior inventory/GREEN and retains EXECUTION=BLOCKED.
- Structural mobile tests verify viewport/safe-area, 650px responsive breakpoint,
  three-column mobile status grid, wrapped evidence and 44px touch refresh.

**UNVERIFIED rendered browser evidence:** Chromium/Chrome is not installed; the
Playwright cache contains no browser executable. The previous installation
attempt timed out at the CDN. No desktop/iPhone screenshot is claimed, and Node
DOM tests are not pixel/layout/WebKit or real-device tests. Actual protected
remote transport and iPhone access also remain WAITING_EXTERNAL, with concrete
instructions in REMOTE_OPERATOR_RUNBOOK_V1.md. Source fields never become current
by a browser reload. Backend failure, backgrounded tab and invalid payload clear
old observations.
