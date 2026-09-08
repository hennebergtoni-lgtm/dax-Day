# DATA FINGERPRINT PROVENANCE V1

Status: IMPLEMENTED PROVENANCE CLARIFICATION — 2026-09-08

## Why this exists
V3 correctly refused to call the recovered `GER30_5m.csv` HASH_VERIFIED because the frozen session fingerprint had not been reproduced from that recovered source. During V4 provenance archaeology, repository history recovered the exact committed fingerprint algorithm. Therefore the blocker is narrowed: the fingerprint **method is known**, but the recovered source has not yet reproduced the frozen hash through the exact historical source-normalization path.

## Frozen target
- dataset: `DAX_M5_2014_2019_AUDITED`
- session: Europe/Berlin 09:00–17:30 inclusive
- expected session rows: 172,319
- expected session days: 1,673
- expected session OHLC SHA-256: `e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`
- expected audited ZIP SHA-256: `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870`

## Recovered committed fingerprint algorithm
Repository commit `77971ecd1ddb12efd003bf1b6f9c1cf6220614a6` introduced `src/daxlab/data/fingerprint.py` with deterministic `fingerprint_ohlc(df)` semantics:
1. validate OHLC;
2. select `REQUIRED_OHLC` columns only;
3. convert the DataFrame index to signed int64 timestamp values;
4. serialize with pandas `to_csv(index=True, header=True, float_format="%.10f")`;
5. UTF-8 encode;
6. SHA-256 the resulting bytes.

Repository commit `b31f1b6d3be7e13a52f8d4781abc0ae3a415d775` introduced the recovered daily-M5 source normalization:
- exactly 1,673 CSV files;
- exactly 288 M5 rows per daily file;
- required source columns `timestamp_utc, open, high, low, close`;
- UTC-aware timestamp parse;
- reject duplicate UTC timestamps;
- convert timestamps to Europe/Berlin for the session mask;
- keep local 09:00 through 17:30 inclusive;
- restore UTC timestamp as the session DataFrame index;
- validate 1,673 session days and 172,319 session rows;
- apply `fingerprint_ohlc(session)`.

Commit `14ec9e3116ceeef36d3eb6c40e07e3a85cc15a2b` then froze the target session hash and ZIP hash in the audited manifest.

## Evidence classification
### VERIFIED
- The historical fingerprint algorithm is recoverable from Git history.
- The historical daily-file normalization contract is recoverable from Git history.
- The frozen target hashes remain unchanged.

### NOT YET VERIFIED
- That the currently recovered single `GER30_5m.csv` can be transformed through an evidence-equivalent source-normalization path and reproduce the frozen session hash.
- That the original audited ZIP can be re-observed and reproduce the frozen ZIP SHA.

## Blocker correction
Do **not** use `HASH_METHOD_UNRESOLVED` as the primary blocker anymore.

Use:
`HASH_REPRODUCTION_PENDING_SOURCE_NORMALIZATION`

Meaning: the hashing method is known, but the recovered source representation/path has not yet reproduced the frozen target hash.

## Promotion rule
`STRUCTURAL_MATCH` remains the current recovered-data identity until the frozen target hash is actually reproduced. Knowing the method does not by itself upgrade the data to `HASH_VERIFIED`.
