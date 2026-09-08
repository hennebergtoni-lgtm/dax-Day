# Runtime / Replay / Live Parity Architecture

Status: FOUNDATION IMPLEMENTED + CI TESTED; V11.2 end-to-end replay parity still required before paper/live.

## One decision core
The target system does not maintain a separate live strategy. The same deterministic decision core is intended to run in five modes:

`HISTORICAL -> REPLAY -> SHADOW -> PAPER -> LIVE`

Only the market-data adapter and execution boundary may change between modes.

## Canonical market event
`src/daxlab/runtime/contracts.py` defines the canonical Candle contract with symbol, timeframe, event/close/receive timestamps, OHLC, volume, source, closed state and quality state. Runtime timestamps are timezone-aware and OHLC invariants are enforced.

## Data-quality states
`OK`, `STALE`, `GAP`, `DUPLICATE`, `OUT_OF_ORDER`, `CLOCK_SKEW`, `SOURCE_DISAGREEMENT`, `UNSAFE`.

Every state other than `OK` is non-tradeable at the hard runtime safety boundary. There is no UI or confidence override.

## Closed-candle causality
Only closed, safe candles are admitted to the replay decision history. Existing research prefix-stability tests remain the feature-level no-lookahead gate. V11.2 entry semantics remain frozen: confirmation on a completed candle, entry on the next bar; entry-time features may use only information strictly before entry time.

## Europe/Berlin / DST
`src/daxlab/runtime/time.py` converts aware timestamps through the IANA `Europe/Berlin` zone. Tests cover the spring DST jump and autumn repeated-hour fold while preserving strict absolute-time ordering.

## Decision audit
Every future decision record can retain data fingerprint, regime, structure, setup, filter results, blocker reasons, risk result, final action, config fingerprint and deterministic decision ID. `NO_TRADE` is a first-class auditable outcome.

## Runtime hard gates
`src/daxlab/runtime/gates.py` blocks trade requests for unsafe data, feed interruption, excessive spread and contradictory runtime state. Multiple simultaneous blockers remain visible for audit.

## Drift
Drift may classify observations as `OK`, `WARN` or `BLOCK`. It cannot change parameters, self-optimize or promote research variants.

## Failure injection
Automated tests inject missing bars, duplicates, out-of-order bars, late bars, feed interruption, extreme spread and contradictory state. Each unsafe path must end in `NO_TRADE`.

## Remaining mandatory parity gate
The generic runtime/replay contracts are not equivalent to proving the frozen V11.2 strategy end-to-end across modes. Before SHADOW/PAPER promotion, the repository still needs a deterministic fixture that runs the actual frozen V11.2 decision/feature path through HISTORICAL and REPLAY and asserts feature equality, decision equality, config fingerprint equality and stable decision IDs on the same audited input surface.
