# TWAP001 — Causality Preflight

Status: CAUSALITY TESTED / RESEARCH ONLY. No V11.2 mutation. No promotion implied.

## Implemented invariant
`session_twap_before_entry` uses only Europe/Berlin session M5 bars whose completion time (`open_time + 5m`) is strictly earlier than `entry_time`.

## Tested failure modes
- entry candle / bar completing exactly at entry is excluded;
- prior-session bars are excluded;
- future suffix bars cannot alter a prior TWAP state;
- no available completed session bar returns no state;
- timezone-naive entry/bar timestamps fail closed;
- session reset is Europe/Berlin aware.

## Evidence boundary
These tests establish causal plumbing only. They do not establish predictive value, selector value, robustness or promotion evidence. TWAP001 remains research-only until descriptive and later independent validation gates are completed.
