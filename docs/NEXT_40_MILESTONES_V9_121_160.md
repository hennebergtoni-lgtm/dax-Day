# V9 — Next 40 Milestones (121–160)

Status: OFFLINE PREPARATION COMPLETE EXCEPT REAL-HOST EVIDENCE
Date: 2026-09-09

User authorization covers the next 40 project steps for continued non-live development and preparation. It does not authorize real-money LIVE execution. External-host steps remain evidence-gated.

## 121–130 — Windows host bootstrap
- [x] 121. Merge CI-green V8 offline shadow hardening.
- [x] 122. Create dedicated V9 Windows-host preparation branch.
- [x] 123. Add credential-free Windows MT5 read-only probe.
- [x] 124. Add isolated Windows Python bootstrap helper.
- [x] 125. Ensure probe contains no order API.
- [x] 126. Force `order_execution_enabled=false` in host evidence.
- [x] 127. Force closed-M5 request to start at position 1.
- [x] 128. Add static tests for no credentials/order API/bar-0 exclusion.
- [x] 129. Add iPhone-friendly Windows host runbook.
- [x] 130. Mark mobile DE40 observations as preliminary, not host evidence.

## 131–140 — Probe validation and evidence hygiene
- [x] 131. Add probe JSON schema validation.
- [x] 132. Add OHLC invariant validation for returned M5 bars.
- [x] 133. Add chronological ordering validation.
- [x] 134. Add duplicate-bar rejection.
- [x] 135. Add latest-closed-bar freshness calculation.
- [ ] 136. Add broker/server-time observation fields without hard-coded offset. Code-side tick/UTC clock observation exists; exact broker/session timezone remains real-host evidence-gated.
- [x] 137. Add Berlin DST normalization test matrix.
- [x] 138. Add exact-symbol override path for ambiguous aliases.
- [x] 139. Add disabled/close-only symbol handling for data-only mode.
- [x] 140. Add credential-key recursive redaction/deny-list tests.

## 141–150 — One-click diagnostics
- [x] 141. Add single health summary with GREEN/BLOCKED status.
- [x] 142. Add deterministic blocker reason ordering.
- [x] 143. Add compact iPhone-readable console summary.
- [x] 144. Add JSON evidence fingerprint.
- [x] 145. Add evidence bundle/manifest identity with schema/version/hash.
- [x] 146. Add safe overwrite protection for probe files.
- [x] 147. Add timestamped evidence output option.
- [x] 148. Add offline fixture replay through the same validator.
- [x] 149. Add restart/re-run idempotency test.
- [x] 150. Add negative tests for terminal disconnected / no bars / ambiguity.

## 151–160 — Integration readiness
- [x] 151. Map validated host evidence into `Mt5HostObservation`.
- [x] 152. Map closed bars into the existing feed payload contract.
- [x] 153. Bind watchdog freshness to validated latest closed bar.
- [x] 154. Bind single-instance lock to host health output.
- [x] 155. Bind prospective SHADOW gate to validated host evidence.
- [x] 156. Add synthetic end-to-end host→feed→shadow NO_ORDER test.
- [x] 157. Add recovery round-trip for host evidence + shadow checkpoint.
- [x] 158. Extend web status with credential-free host readiness summary.
- [x] 159. Run full PR CI/recovery/research/web gates (PR #6 run #435 GREEN on code head).
- [ ] 160. HARD REVIEW: real Windows host evidence still required before declaring steps 102–110 complete.

## Current boundary
- Offline host→feed→SHADOW path is implemented and tested with synthetic closed-M5 evidence.
- A real MT5-connected bot run is not claimed. Steps 102–110 and exact broker/session observations remain blocked until a real Windows MT5 Desktop host is available.
- SHADOW output remains `NO_ORDER`; execution capability is `NONE` and `order_execution_enabled=false`.

## Constraints
- V11.2 remains frozen.
- No research candidate is silently promoted.
- No order adapter is added in V9.
- No real-money LIVE execution without a separate explicit authorization.
- Credentials and account identifiers must never enter repository evidence.
