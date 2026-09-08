# V7 — Next 50 Milestones (42–91)

Status: ACTIVE
Date: 2026-09-08
Starting project counter: 41/150

## Binding constraints
- V11.2 remains frozen and immutable.
- Research families remain research-only unless separately promoted by evidence.
- No fake VWAP; TWAP001 remains the declared OHLC anchored-price/TWAP reference.
- No credentials, passwords, OTPs or account identifiers in repository evidence.
- MT5 integration remains read-only and fail-closed.
- `order_execution_enabled` must remain false.
- No shadow/paper/live/bot run may start in this block. Explicit user authorization is required at the prospective-run stop gate.

## 42–51 — MT5 host boundary
- [x] 42. Verify post-merge main CI for MT5 host contract.
- [x] 43. Freeze main SHA for this block.
- [x] 44. Create isolated V7 work branch.
- [x] 45. Define strict serialized MT5 host-probe payload boundary.
- [x] 46. Reject unknown payload fields to prevent accidental credential ingress.
- [x] 47. Require timezone-aware observation timestamps.
- [x] 48. Require explicit boolean execution guard.
- [x] 49. Validate broker-symbol core metadata.
- [x] 50. Validate optional contract/volume metadata when supplied.
- [x] 51. Add unit tests for payload fail-closed behavior.

## 52–61 — Feed safety preparation
- [ ] 52. Add closed-M5 payload schema.
- [ ] 53. Reject MT5 bar 0 at the serialized request boundary.
- [ ] 54. Enforce timezone-aware bar timestamps.
- [ ] 55. Enforce OHLC invariants on incoming bars.
- [ ] 56. Enforce chronological uniqueness.
- [ ] 57. Define latest-closed-bar identity fingerprint.
- [ ] 58. Define feed freshness threshold contract.
- [ ] 59. Define stale-feed reason codes.
- [ ] 60. Add feed discontinuity diagnostics without synthetic filling.
- [ ] 61. Add tests for all feed-safety failures.

## 62–71 — Broker/session normalization
- [ ] 62. Capture broker timezone as observation metadata.
- [ ] 63. Define broker-to-Europe/Berlin conversion boundary.
- [ ] 64. Preserve DST-aware conversion tests.
- [ ] 65. Define session-open/session-close metadata observation.
- [ ] 66. Prevent inferred broker sessions from silently becoming historical assumptions.
- [ ] 67. Extend symbol resolution evidence with candidate metadata.
- [ ] 68. Add configured-symbol exact-match audit record.
- [ ] 69. Add ambiguous-symbol audit record.
- [ ] 70. Add disabled/close-only symbol tests.
- [ ] 71. Produce broker/session normalization contract doc.

## 72–81 — Health, watchdog, observability
- [ ] 72. Define deterministic health snapshot payload.
- [ ] 73. Add terminal connectivity reason codes.
- [ ] 74. Add account connectivity reason codes without account identifiers.
- [ ] 75. Add clock-skew observation contract.
- [ ] 76. Add engine-loop heartbeat age contract.
- [ ] 77. Add feed-age watchdog state.
- [ ] 78. Add single-instance-lock status field.
- [ ] 79. Extend read-only web status for host handshake.
- [ ] 80. Add `why_no_trade` mapping for host/feed blockers.
- [ ] 81. Add integrity tests ensuring web status cannot imply execution readiness.

## 82–88 — Recovery and evidence
- [ ] 82. Define immutable host-observation evidence ID.
- [ ] 83. Define payload hash canonicalization.
- [ ] 84. Exclude credentials/account identifiers from recoverable evidence.
- [ ] 85. Add host-probe evidence to recovery manifest contract.
- [ ] 86. Add duplicate/conflict detection rules.
- [ ] 87. Add recovery round-trip test for synthetic read-only evidence.
- [ ] 88. Re-audit recovery dependency direction; no deletion-first refactor.

## 89–91 — Closure / hard stop
- [ ] 89. Run full CI/recovery/research/web integrity gates.
- [ ] 90. Consolidate V7 readiness and remaining external MT5 requirements.
- [ ] 91. HARD STOP: do not start shadow/paper/live/bot operation; present evidence and obtain explicit user authorization before any prospective run.

## External dependency
The real terminal handshake cannot be completed from the iPhone app alone. The eventual Python MT5 host requires a supported running MT5 desktop environment. A MetaQuotes demo can be used first to validate terminal connectivity; broker-specific feed validation remains separate.
