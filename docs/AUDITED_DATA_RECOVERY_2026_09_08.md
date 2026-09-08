# Audited data recovery — 2026-09-08

Status: **RECOVERED_SOURCE_CANDIDATE / STRUCTURAL_MATCH_VERIFIED / HISTORICAL_HASH_METHOD_UNRESOLVED**

This record preserves the recovery evidence without changing the frozen V11.2 active reference.

## Recovered Drive source

- Drive folder: `DAX_V11_2_DATA_2014_2019`
- File: `GER30_5m.csv`
- Drive file id: `1ctn8x_Mcd0-cnZ_2X4nGoBbw-tVtX7LF`
- File size: `29,997,351` bytes
- Recovered raw rows: `481,824`

## Structural audit match

The recovered source reproduces the frozen manifest's structural invariants:

- research period: 2014-01-01 through 2019-12-31
- Europe/Berlin session: 09:00–17:30
- session days: 1,673
- session M5 rows: 172,319
- bars per valid session day: 103
- invalid OHLC rows: 0

These match `data/manifests/dax_m5_2014_2019_audited.json` exactly.

## Hash caveat

The frozen manifest records:

- session OHLC SHA-256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`
- audited ZIP SHA-256: `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870`

The historical Colab V2.6 recovery log independently reports the same 1,673 / 172,319 / 103 data gate but a different data SHA (`0a26954639260aec3d0e8d3ae0668f2c67a78e9a965f961f1a0a50ec12940f6d`). This demonstrates that multiple historical serialization/fingerprint conventions existed. Therefore a hash mismatch alone must not be silently reinterpreted as either a data mismatch or a successful fingerprint reproduction.

Until the exact original `e51b...` serialization procedure or the audited ZIP is recovered, status remains `HISTORICAL_HASH_METHOD_UNRESOLVED`.

## Additional recovered provenance

Drive contains methodology audit v3.5.4 artifacts with a green parity gate for the exact candidate engine:

- engine source SHA-256: `b3d62e0cad72420d36ade523857d024d4a334298be51a8313069e36614bda888`
- variants: 144
- WFs tested: 3
- costs tested: 3
- comparisons: 1,296
- matches: 1,296
- mismatches: 0
- strategy_changed: false
- data_repaired: false

Drive also contains the V2.8.16 FAST parity audit on the full 1,673-day cache. Its exact-vs-FAST control trade case matched all reported metrics and confirmed cache inventory of 1,673 days and 3,346 OR structures.

These artifacts are provenance/supporting evidence. They do **not** replace the frozen clean V11.2 active reference or prove full 2014–2019 historical↔replay parity.

## Binding decision

1. Do not replace or alter V11.2 active-reference hashes/results.
2. Do not import synthetic detailed rows.
3. Treat the recovered CSV as the strongest recovered source candidate because all structural invariants match.
4. Full historical replay/reference promotion remains gated on exact reproducible evidence.
5. Research may use the recovered source only with provenance/status carried explicitly; any result that depends on unresolved identity must not be promoted as a clean active-reference result.
