# V11.2 clean reference — replay parity status

Status: PARTIALLY VERIFIED / FULL CLEAN-REFERENCE GATE BLOCKED

## VERIFIED
- The exact recovered V11.2 candidate engine is loaded only after strict SHA-256 verification.
- The engine surface used by the bridge is the existing V11.2 implementation; no second strategy implementation was created.
- Canonical safe closed candles are converted to the V11.2 dataframe contract.
- Historical and replay execution through the recovered V11.2 engine match on deterministic complete-session fixtures.
- Unsafe/open candles are rejected before V11.2 evaluation.
- Current-day range mutation does not change the current day's `daily_context`, confirming the prior-day causal context contract on the tested surface.
- Europe/Berlin winter/summer session conversion preserves 09:00 local session semantics with the correct UTC offsets.
- Repeated replay runs produce identical results and deterministic result fingerprints.
- Guarded replay smoke CI run: `FIXTURE_ONLY`, 17 days, 1,751 bars, fingerprint `ada7a911eccbefc508f7fdc895426a857c617c477d8c2dc3d87b5ddced0cad0e`.

## VERIFIED CI SURFACE
The guarded smoke path is part of `research-lab-ci` together with Ruff, the unit/integration test suite, the V11.2 engine probe, Neon connectivity, migrations and database integrity.

## NOT YET VERIFIED
The following must **not** be claimed as proven yet:
- 1,673-day Historical-vs-Replay equality on the audited 2014–2019 raw/session dataset;
- replay reproduction of the frozen clean-reference 856 OOS trades;
- replay reproduction of normal return `-31.309210619787684 R`;
- replay reproduction of 37 positive / 44 negative WF windows;
- replay reproduction of the 1.5x and 2x cost-stress reference aggregates;
- per-trade or per-WF clean-reference replay equality.

## Blocking evidence
The public repository intentionally contains only the audited dataset manifest, not the large market-data payload. Repository and connected Drive searches have not yet established an independently verifiable clean-reference detailed artifact matching the committed WF/selection hashes or the audited dataset ZIP hash.

Expected audited dataset identifiers remain:
- session OHLC SHA-256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`
- audited ZIP SHA-256: `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870`

## Gate decision
**DO NOT promote full replay parity.**

The next full-reference replay run becomes eligible only when the audited payload is located and its bytes/session normalization pass the committed dataset fingerprints before execution. Legacy FAST caches or older V11.2 result folders may be used for provenance investigation only and must not substitute for the clean audited source.
