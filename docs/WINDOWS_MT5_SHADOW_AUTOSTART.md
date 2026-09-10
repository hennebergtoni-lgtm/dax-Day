# Windows MT5 SHADOW Autostart

Status: IMPLEMENTED IN REPOSITORY; REAL WINDOWS HOST VERIFICATION REQUIRED.

This runbook configures MetaTrader 5 Desktop and the DAXLAB read-only SHADOW supervisor to start at Windows user logon. It does not authorize PAPER or LIVE trading and does not add any order API.

## Safety contract

- `execution_capability=NONE`
- `order_execution_enabled=false`
- SHADOW only
- no login, password, token, or account identifier is written by DAXLAB
- MT5 credentials remain inside the already configured terminal profile
- bar 0 remains excluded by the existing probe path
- invalid or stale runtime state fails closed

## Prerequisites

1. Repository is checked out on the Windows host.
2. `.venv-mt5` was created with `scripts/windows_mt5_bootstrap.ps1`.
3. MetaTrader 5 Desktop can already be opened and is logged into the intended DEMO profile.
4. Exact DAX symbol is known.
5. Broker/server timezone has been verified separately. Do not guess it.

## Mandatory read-only preflight

Open PowerShell in the repository root while MT5 is running, then execute:

```powershell
.\scripts\preflight_windows_mt5_shadow_autostart.ps1 -BrokerTimezone '<VERIFIED_TIMEZONE>'
```

Do not install the scheduled tasks unless the preflight ends with `PREFLIGHT GREEN`. The preflight creates no scheduled task and performs exactly one read-only SHADOW cycle with `execution_capability=NONE` and `order_execution_enabled=false`.

## Install

Only after a green preflight, execute:

```powershell
.\scripts\install_windows_mt5_shadow_task.ps1 -BrokerTimezone '<VERIFIED_TIMEZONE>'
```

The installer resolves the running `terminal64.exe` path. If discovery is unavailable, pass the exact executable explicitly:

```powershell
.\scripts\install_windows_mt5_shadow_task.ps1 -BrokerTimezone '<VERIFIED_TIMEZONE>' -Mt5Executable 'C:\Path\To\terminal64.exe'
```

Two current-user tasks are created:

- `DAXLAB MT5 Terminal`
- `DAXLAB MT5 SHADOW`

Both use `AtLogOn`, `StartWhenAvailable`, `MultipleInstances=IgnoreNew`, no execution time limit, and restart-on-failure settings.

## Check

```powershell
.\scripts\check_windows_mt5_shadow_runtime.ps1
```

A valid SHADOW runtime must report:

- task presence for MT5 and SHADOW
- heartbeat `Status=GREEN`
- `execution_capability=NONE`
- `order_execution_enabled=false`

A missing heartbeat or non-green heartbeat is not a trading permission. It is a fail-closed condition to diagnose.

## Reboot verification gate

Do not mark Windows autostart VERIFIED until all of the following have been observed on the real host after an actual reboot/logon:

1. MT5 starts without manual launch.
2. SHADOW supervisor starts without manual launch.
3. exactly one supervisor instance owns the lock.
4. heartbeat returns to GREEN after MT5 becomes reachable.
5. resume payload validates and previously seen bars are suppressed.
6. a newly closed M5 bar advances the checkpoint exactly once.
7. `execution_capability=NONE` remains present.
8. `order_execution_enabled=false` remains present.
9. no credential material appears in heartbeat, resume, or latest bundle evidence.

## Uninstall

```powershell
.\scripts\uninstall_windows_mt5_shadow_tasks.ps1
```

This removes the scheduled tasks but intentionally keeps `.runtime\mt5_shadow` evidence and resume state.
