# MT5 Broker / Session Normalization Contract V1

Status: READ-ONLY PREPARATION

- Broker timezone must be an explicit valid IANA timezone; timestamps are timezone-aware.
- Conversion to `Europe/Berlin` uses timezone rules/DST, never fixed offsets.
- Broker session hours are observations only. `BROKER_OBSERVED`, `BROKER_DOCUMENTED`, or `UNKNOWN` records do not alter the frozen historical 09:00–17:30 Europe/Berlin V11.2 assumption.
- Unknown session source cannot assert hours. Open/close must be supplied together.
- DAX symbol resolution remains fail-closed. A configured symbol must match exactly. Multiple tradeable aliases remain `AMBIGUOUS`; disabled/close-only aliases cannot auto-resolve.
- Symbol audit evidence records metadata only: symbol name, digits, point, trade mode. No credentials/account identifiers.
- This contract grants no execution capability and does not start a bot, shadow, paper or live run.
