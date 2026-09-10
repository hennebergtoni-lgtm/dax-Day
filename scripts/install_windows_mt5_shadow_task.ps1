param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BrokerTimezone,

    [string]$TaskName = 'DAXLAB MT5 SHADOW',
    [string]$Symbol = 'DE40',
    [int]$Bars = 20,
    [double]$MaxAgeSeconds = 600.0,
    [double]$IntervalSeconds = 60.0
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$startScript = Join-Path $repoRoot 'scripts\windows_mt5_shadow_start.ps1'

if (-not (Test-Path -LiteralPath $startScript -PathType Leaf)) {
    throw "Start wrapper not found: $startScript"
}
if (-not (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)) {
    throw 'Windows ScheduledTasks module is not available.'
}

$escapedScript = $startScript.Replace("'", "''")
$escapedTimezone = $BrokerTimezone.Replace("'", "''")
$escapedSymbol = $Symbol.Replace("'", "''")
$arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`" -BrokerTimezone `"$BrokerTimezone`" -Symbol `"$Symbol`" -Bars $Bars -MaxAgeSeconds $MaxAgeSeconds -IntervalSeconds $IntervalSeconds"

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument $arguments `
    -WorkingDirectory $repoRoot

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

$task = New-ScheduledTask `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description 'DAXLAB credential-free MT5 read-only SHADOW supervisor. execution_capability=NONE; order_execution_enabled=false.'

Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null

$registered = Get-ScheduledTask -TaskName $TaskName
if ($registered.State -eq 'Disabled') {
    throw "Scheduled task was registered but is disabled: $TaskName"
}

Write-Host "Installed scheduled task: $TaskName"
Write-Host "User: $env:USERNAME"
Write-Host "Repo: $repoRoot"
Write-Host "Symbol: $Symbol"
Write-Host "Broker timezone: $BrokerTimezone"
Write-Host 'Mode: SHADOW / execution_capability=NONE / order_execution_enabled=false'
Write-Host 'The task starts at user logon and Windows retries it after process failure.'
