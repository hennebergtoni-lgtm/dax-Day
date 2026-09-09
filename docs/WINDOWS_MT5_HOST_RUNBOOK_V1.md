# Windows MT5 Host Runbook V1

Status: PREPARED / NOT YET EXECUTED ON REAL HOST
Date: 2026-09-09

## Goal
Connect the already existing MetaQuotes demo terminal to DAXLAB in read-only mode and capture credential-free evidence. This does not enable paper-order placement or live-money execution.

## Before starting
1. Windows PC is available.
2. MetaTrader 5 Desktop is installed from an official source.
3. MT5 Desktop is open and already logged into the demo account.
4. Do not paste login, password, OTP, email, phone number, tax data or account identifiers into chat, GitHub or scripts.
5. Keep `order_execution_enabled=false`.

## Fast path
From the repository root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows_mt5_bootstrap.ps1
```

The helper creates an isolated venv, installs the project and the MetaTrader5 Python package, and runs the read-only probe. It does not take credentials.

## Expected output
`mt5_probe.json` with:
- terminal connected state;
- demo-account connected boolean only, without account ID;
- exact/ambiguous DAX symbol resolution state;
- safe symbol metadata;
- closed M5 bars pulled from position 1 or later;
- UTC observation timestamp;
- explicit `order_execution_enabled=false`;
- no credentials or personal identifiers.

## Fail-closed interpretation
- `TERMINAL_NOT_CONNECTED`: MT5 Desktop is not reachable.
- no symbol / ambiguous symbol: do not guess; rerun with an exact `--symbol` only after checking the terminal symbol list.
- no M5 bars: do not continue to prospective observation.
- any evidence of bar 0: block.
- any credential/personal identifier in output: do not upload; delete the file and investigate.

## Mobile evidence already observed
The iPhone MetaQuotes demo showed a `DE40 / Germany 40 Index` M5 chart and symbol/session information. This is useful preliminary evidence only. It is not a substitute for the Windows-host handshake and is not treated as broker-specific production evidence.

## Hard boundary
Successful completion of this runbook may satisfy the technical host/read-only parts of steps 102–110. It does not authorize real-money LIVE execution and does not add an order adapter.
