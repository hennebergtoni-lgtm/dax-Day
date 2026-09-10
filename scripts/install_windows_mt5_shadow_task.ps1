param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BrokerTimezone,

    [string]$Mt5Executable = '',
    [string]$Mt5TaskName = 'DAXLAB MT5 Terminal',
    [string]$ShadowTaskName = 'DAXLAB MT5 SHADOW',
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
if ($Bars -lt 2) {
    throw 'Bars must be >= 2.'
}
if ($MaxAgeSeconds -lt 0) {
    throw 'MaxAgeSeconds must be >= 0.'
}
if ($IntervalSeconds -lt 1) {
    throw 'IntervalSeconds must be >= 1.'
}

function Resolve-Mt5Executable {
    param([string]$ConfiguredPath)

    if ($ConfiguredPath) {
        $resolved = (Resolve-Path -LiteralPath $ConfiguredPath -ErrorAction Stop).Path
        if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
            throw "MT5 executable is not a file: $resolved"
        }
        return $resolved
    }

    $running = Get-Process -Name 'terminal64' -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -and (Test-Path -LiteralPath $_.Path -PathType Leaf) } |
        Select-Object -First 1
    if ($running) {
        return $running.Path
    }

    throw 'MT5 executable path could not be resolved. Start MT5 first or pass -Mt5Executable.'
}

$mt5Path = Resolve-Mt5Executable -ConfiguredPath $Mt5Executable
$mt5Directory = Split-Path -Parent $mt5Path
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$mt5Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
$mt5Action = New-ScheduledTaskAction -Execute $mt5Path -WorkingDirectory $mt5Directory
$mt5Task = New-ScheduledTask `
    -Action $mt5Action `
    -Trigger $logonTrigger `
    -Settings $mt5Settings `
    -Principal $principal `
    -Description 'MetaTrader 5 terminal host for DAXLAB read-only SHADOW. No credentials are stored by DAXLAB.'
Register-ScheduledTask -TaskName $Mt5TaskName -InputObject $mt5Task -Force | Out-Null

$shadowArguments = "-NoProfile -File `"$startScript`" -BrokerTimezone `"$BrokerTimezone`" -Symbol `"$Symbol`" -Bars $Bars -MaxAgeSeconds $MaxAgeSeconds -IntervalSeconds $IntervalSeconds"
$shadowAction = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument $shadowArguments `
    -WorkingDirectory $repoRoot
$shadowSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
$shadowTask = New-ScheduledTask `
    -Action $shadowAction `
    -Trigger $logonTrigger `
    -Settings $shadowSettings `
    -Principal $principal `
    -Description 'DAXLAB credential-free MT5 read-only SHADOW supervisor. execution_capability=NONE; order_execution_enabled=false.'
Register-ScheduledTask -TaskName $ShadowTaskName -InputObject $shadowTask -Force | Out-Null

foreach ($name in @($Mt5TaskName, $ShadowTaskName)) {
    $registered = Get-ScheduledTask -TaskName $name
    if ($registered.State -eq 'Disabled') {
        throw "Scheduled task was registered but is disabled: $name"
    }
}

Write-Host "Installed task: $Mt5TaskName"
Write-Host "MT5 executable: $mt5Path"
Write-Host "Installed task: $ShadowTaskName"
Write-Host "Repo: $repoRoot"
Write-Host "Symbol: $Symbol"
Write-Host "Broker timezone: $BrokerTimezone"
Write-Host 'Mode: SHADOW / execution_capability=NONE / order_execution_enabled=false'
Write-Host 'Restart policy: MT5 terminal 5 attempts / 2 min; SHADOW supervisor 3 attempts / 5 min.'
Write-Host 'Both tasks start at user logon. The SHADOW supervisor fails closed until MT5 is reachable.'
