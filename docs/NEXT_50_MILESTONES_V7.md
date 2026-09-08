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
- [x] 52. Add closed-M5 payload schema.
- [x] 53. Reject MT5 bar 0 at the serialized request boundary.
- [x] 54. Enforce timezone-aware bar timestamps.
- [x] 55. Enforce OHLC invariants on incoming bars.
- [x] 56. Enforce chronological uniqueness.
- [x] 57. Define latest-closed-bar identity fingerprint.
- [x] 58. Define feed freshness threshold contract.
- [x] 59. Define stale-feed reason codes.
- [x] 60. Add feed discontinuity diagnostics without synthetic filling.
- [x] 61. Add tests for all feed-safety failures.

## 62–71 — Broker/session normalization
- [x] 62. Capture broker timezone as observation metadata.
- [x] 63. Define broker-to-Europe/Berlin conversion boundary.
- [x] 64. Preserve DST-aware conversion tests.
- [x] 65. Define session-open/session-close metadata observation.
- [x] 66. Prevent inferred broker sessions from silently becoming historical assumptions.
- [x] 67. Extend symbol resolution evidence with candidate metadata.
- [x] 68. Add configured-symbol exact-match audit record.
- [x] 69. Add ambiguous-symbol audit record.
- [x] 70. Add disabled/close-only symbol tests.
- [x] 71. Produce broker/session normalization contract doc.

## 72–81 — Health, watchdog, observability
- [x] 72. Define deterministic health snapshot payload.
- [x] 73. Add terminal connectivity reason codes.
- [x] 74. Add account connectivity reason codes without account identifiers.
- [x] 75. Add clock-skew observation contract.
- [x] 76. Add engine-loop heartbeat age contract.
- [x] 77. Add feed-age watchdog state.
- [x] 78. Add single-instance-lock status field.
- [x] 79. Extend read-only web status for host handshake.
- [x] 80. Add `why_no_trade` mapping for host/feed blockers.
- [x] 81. Add integrity tests ensuring web status cannot imply execution readiness.

## 82–88 — Recovery and evidence
- [x] 82. Define immutable host-observation evidence ID.
- [x] 83. Define payload hash canonicalization.
- [x] 84. Exclude credentials/account identifiers from recoverable evidence.
- [x] 85. Add host-probe evidence to recovery manifest contract.
- [x] 86. Add duplicate/conflict detection rules.
- [x] 87. Add recovery round-trip test for synthetic read-only evidence.
- [x] 88. Re-audit recovery dependency direction; no deletion-first refactor.

## 89–91 — Closure / hard stop
- [x] 89. Run full PR CI/recovery/research/web integrity gates. PR workflow #422 GREEN; main-only Neon gates remain to be verified after merge.
- [x] 90. Consolidate V7 readiness and remaining external MT5 requirements in `docs/V7_READINESS_42_90_RESULT.md`.
- [ ] 91. HARD STOP: do not start shadow/paper/live/bot operation; present evidence and obtain explicit user authorization before any prospective run.

## External dependency
The real terminal handshake cannot be completed from the iPhone app alone. The eventual Python MT5 host requires a supported running MT5 desktop environment. A MetaQuotes demo can be used first to validate terminal connectivity; broker-specific feed validation remains separate.
