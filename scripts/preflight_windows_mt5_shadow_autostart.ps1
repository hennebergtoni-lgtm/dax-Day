param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BrokerTimezone,

    [string]$Mt5Executable = '',
    [string]$Symbol = 'DE40',
    [int]$Bars = 20,
    [double]$MaxAgeSeconds = 600.0,
    [string]$StateDir = '.runtime\mt5_shadow_preflight',
    [string]$PythonExecutable = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$repoSrc = Join-Path $repoRoot 'src'

if ($PythonExecutable) {
    $python = $PythonExecutable
} else {
    $python = Join-Path $repoRoot '.venv-mt5\Scripts\python.exe'
}
$supervisor = Join-Path $repoRoot 'scripts\mt5_shadow_supervisor.py'

if (-not (Test-Path -LiteralPath $repoSrc -PathType Container)) {
    throw "DAXLAB source directory not found: $repoSrc"
}
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "MT5 Python environment not found: $python"
}
if (-not (Test-Path -LiteralPath $supervisor -PathType Leaf)) {
    throw "MT5 SHADOW supervisor not found: $supervisor"
}
foreach ($command in @('Register-ScheduledTask', 'Get-ScheduledTask', 'New-ScheduledTask')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required ScheduledTasks command is unavailable: $command"
    }
}

if ($Mt5Executable) {
    $mt5Path = (Resolve-Path -LiteralPath $Mt5Executable -ErrorAction Stop).Path
} else {
    $running = Get-Process -Name 'terminal64' -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -and (Test-Path -LiteralPath $_.Path -PathType Leaf) } |
        Select-Object -First 1
    if (-not $running) {
        throw 'Running terminal64.exe was not found. Start MT5 or pass -Mt5Executable.'
    }
    $mt5Path = $running.Path
}

if (-not (Test-Path -LiteralPath $mt5Path -PathType Leaf)) {
    throw "MT5 executable is not a file: $mt5Path"
}

if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$repoSrc;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $repoSrc
}

& $python -c "from zoneinfo import ZoneInfo; ZoneInfo(r'''$BrokerTimezone''')"
if ($LASTEXITCODE -ne 0) {
    throw "Broker timezone is not valid for Python zoneinfo: $BrokerTimezone"
}

Write-Host 'PRECHECK | ScheduledTasks commands: OK'
Write-Host "PRECHECK | MT5 executable: $mt5Path"
Write-Host "PRECHECK | RepoSrc: $repoSrc"
Write-Host "PRECHECK | Python: $python"
Write-Host "PRECHECK | Broker timezone: $BrokerTimezone"
Write-Host 'PRECHECK | Running one read-only SHADOW cycle...'

& $python $supervisor `
    --symbol $Symbol `
    --bars $Bars `
    --max-age-seconds $MaxAgeSeconds `
    --broker-timezone $BrokerTimezone `
    --interval-seconds 60 `
    --state-dir $StateDir `
    --once

if ($LASTEXITCODE -ne 0) {
    throw "One-shot SHADOW preflight failed with exit code $LASTEXITCODE"
}

$heartbeatPath = Join-Path (Join-Path $repoRoot $StateDir) 'heartbeat.json'
if (-not (Test-Path -LiteralPath $heartbeatPath -PathType Leaf)) {
    throw "Preflight heartbeat was not written: $heartbeatPath"
}
$heartbeat = Get-Content -LiteralPath $heartbeatPath -Raw | ConvertFrom-Json
if ($heartbeat.execution_capability -ne 'NONE') {
    throw 'Preflight execution_capability is not NONE.'
}
if ($heartbeat.order_execution_enabled -ne $false) {
    throw 'Preflight order_execution_enabled is not false.'
}
if ($heartbeat.status -ne 'GREEN') {
    throw "Preflight heartbeat is not GREEN: $($heartbeat.status) [$($heartbeat.blockers -join ', ')]"
}

Write-Host 'PREFLIGHT GREEN | MT5 read-only SHADOW is ready for task installation.'
Write-Host 'SAFETY | execution_capability=NONE | order_execution_enabled=false'
