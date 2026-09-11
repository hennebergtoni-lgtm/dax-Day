param(
    [string]$TaskName = 'DAXLAB MT5 SHADOW TELEMETRY',
    [int]$IntervalMinutes = 1,
    [string]$StateDir = '.runtime\mt5_shadow'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($IntervalMinutes -lt 1) {
    throw 'IntervalMinutes must be >= 1.'
}
if (-not (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)) {
    throw 'Windows ScheduledTasks module is not available.'
}
if (-not $env:NEON_DATABASE_URL) {
    throw 'NEON_DATABASE_URL is not configured for this Windows user.'
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$wrapper = Join-Path $repoRoot 'scripts\windows_mt5_shadow_telemetry_export.ps1'
if (-not (Test-Path -LiteralPath $wrapper -PathType Leaf)) {
    throw "Telemetry wrapper not found: $wrapper"
}

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$wrapper`" -StateDir `"$StateDir`""
$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument $arguments `
    -WorkingDirectory $repoRoot

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 1)

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description 'Exports credential-free MT5 SHADOW heartbeat and closed-M5 evidence to Neon. Observation only; execution_capability=NONE.'

Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
$registered = Get-ScheduledTask -TaskName $TaskName
if ($registered.State -eq 'Disabled') {
    throw "Scheduled telemetry task was registered but is disabled: $TaskName"
}

Write-Host "Installed task: $TaskName"
Write-Host "Interval: $IntervalMinutes minute(s)"
Write-Host "Repo: $repoRoot"
Write-Host "StateDir: $StateDir"
Write-Host 'Direction: local SHADOW artifacts -> Neon only'
Write-Host 'Mode: SHADOW telemetry / execution_capability=NONE / order_execution_enabled=false'
