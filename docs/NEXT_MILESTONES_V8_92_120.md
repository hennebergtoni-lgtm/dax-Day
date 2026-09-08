# V8 — Prospective Readiness Milestones (92–120)

Status: ACTIVE
Date: 2026-09-09
Starting project counter: 91/150

## Authorization boundary
Step 91 was explicitly released by the user in chat on 2026-09-09 to continue beyond the prospective-run stop gate.
This release authorizes continued SHADOW/PAPER preparation and, once the external MT5 host exists and all hard gates are green, prospective non-live operation.
It does **not** authorize real-money LIVE execution. LIVE remains a separate explicit authorization boundary.

## 92–101 — Prospective gate and dry-run readiness
- [x] 92. Record Step-91 authorization scope without credentials or account identifiers.
- [x] 93. Define SHADOW/PAPER/LIVE prospective modes.
- [x] 94. Require Step-91 authorization as a necessary gate.
- [x] 95. Keep LIVE separately unauthorized.
- [x] 96. Require healthy read-only MT5 host evidence.
- [x] 97. Require exact broker-symbol resolution.
- [x] 98. Require fresh closed-M5 feed.
- [x] 99. Require safe clock and single-instance lock.
- [x] 100. Prevent execution-enabled state from passing SHADOW/PAPER preparation.
- [x] 101. Add unit tests for prospective authorization behavior.

## 102–110 — External MT5 handshake
- [ ] 102. Establish supported Windows MT5 host environment.
- [ ] 103. Log in to a demo trading account without exposing credentials.
- [ ] 104. Capture terminal/account connected state.
- [ ] 105. Enumerate DAX aliases and resolve exactly one broker symbol.
- [ ] 106. Capture symbol digits/point/trade-mode/contract-size/volume metadata.
- [ ] 107. Capture broker timezone and observed session metadata.
- [ ] 108. Pull closed M5 bars with bar 0 excluded.
- [ ] 109. Verify freshness, chronology, OHLC and discontinuity diagnostics.
- [ ] 110. Persist credential-free host evidence and health snapshot.

## 111–118 — Shadow/paper observation layer
- [ ] 111. Define observation-only decision loop input contract.
- [ ] 112. Bind V11.2 frozen decision engine without mutation.
- [ ] 113. Emit NO_ORDER shadow decisions with reason codes.
- [ ] 114. Add deterministic decision IDs and duplicate suppression.
- [ ] 115. Add checkpoint/resume for observation loop.
- [ ] 116. Add watchdog stop conditions and stale-feed fail-closed behavior.
- [ ] 117. Add read-only dashboard counters for prospective observations.
- [ ] 118. Add recovery round-trip for synthetic prospective observations.

## 119–120 — Prospective start gate
- [ ] 119. Run full CI + main Neon/recovery gates after implementation.
- [ ] 120. Start first SHADOW observation only if external MT5 host/feed gates are all green; otherwise remain blocked with explicit reasons.

## Non-negotiable constraints
- V11.2 remains frozen.
- Research findings are not silently promoted into trading rules.
- No fake VWAP.
- No credentials or account identifiers in repository evidence.
- No real-money LIVE execution without a separate explicit user authorization.
- A failed or ambiguous MT5 state must produce NO_ORDER / blocked readiness, never fallback execution.
