# Recovered data hash verification — 2026-09-08

Status: **SESSION HASH VERIFIED**

## Source
- Drive folder: `DAX_V11_2_DATA_2014_2019`
- source file: `GER30_5m.csv`
- Drive file id: `1ctn8x_Mcd0-cnZ_2X4nGoBbw-tVtX7LF`
- raw file bytes: `29,997,351`
- raw rows: `481,824`
- raw file SHA-256: `a1379e13d70005363e60eb0015e2a648af392becbe7c4d5825bb00a8193f5103`

## Evidence-equivalent normalization
The recovered aggregate CSV uses source column `datetime`. For the historical daily-M5 contract this is mapped to `timestamp_utc`, parsed UTC-aware, converted to Europe/Berlin only for the inclusive 09:00–17:30 session mask, then restored as the UTC-aware `timestamp_utc` session index.

The resulting session surface has:
- 1,673 session days
- 172,319 M5 session rows
- exactly 103 bars per session day
- OHLC columns ordered `open, high, low, close`

The frozen V1 fingerprint method is then applied:
1. validate OHLC;
2. select OHLC only;
3. encode the UTC-aware DatetimeIndex as pandas int64 nanoseconds;
4. `to_csv(index=True, header=True, float_format="%.10f")`;
5. UTF-8;
6. SHA-256.

## Result
Observed session SHA-256:
`e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`

Frozen active-reference session SHA-256:
`e51bba6cb2befe5e7eb0376318e43b096a3e2ecaae3f556019862975c60286a2`

**Exact match: TRUE.**

## Important forensic note
A Berlin-local-naive index produces a different digest (`f705bdd01e426003cb535879dcac9c3fd13d27c3c46d50ba2899a5d70d5d5063`). That representation belongs to older engine normalization observations but is not the committed audited-dataset fingerprint contract. The committed dataset contract restores UTC as the session index before fingerprinting. This distinction explains the earlier apparent mismatch without changing any frozen reference value.

## Evidence classification change
For the recovered session OHLC surface, `RecoveryIdentity` may now be classified as `HASH_VERIFIED` because both structural invariants and the frozen session fingerprint match exactly.

This does **not** verify the missing audited ZIP archive hash `c46c09a391ee83a19a117fb43628cb75ab0a75703701ed7a84731d2963b24870`; ZIP identity remains separately unobserved.

This also does **not** by itself prove the full 81-window V11.2 replay result. The next gate is guarded full-reference replay against the frozen active-reference metrics.
