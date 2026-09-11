param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$BrokerTimezone,

    [string]$Symbol = 'DE40',
    [int]$Bars = 40,
    [double]$MaxAgeSeconds = 600.0,
    [double]$IntervalSeconds = 60.0,
    [string]$StateDir = '.runtime\mt5_shadow',
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
if ($Bars -lt 2) {
    throw 'Bars must be >= 2.'
}
if ($MaxAgeSeconds -lt 0) {
    throw 'MaxAgeSeconds must be >= 0.'
}
if ($IntervalSeconds -lt 1) {
    throw 'IntervalSeconds must be >= 1.'
}

if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$repoSrc;$env:PYTHONPATH"
} else {
    $env:PYTHONPATH = $repoSrc
}

Write-Host 'DAXLAB MT5 SHADOW start'
Write-Host "Repo: $repoRoot"
Write-Host "RepoSrc: $repoSrc"
Write-Host "StateDir: $StateDir"
Write-Host "Python: $python"
Write-Host "Symbol: $Symbol"
Write-Host "Broker timezone: $BrokerTimezone"
Write-Host 'Execution: NONE / NO_ORDER'

& $python $supervisor `
    --symbol $Symbol `
    --bars $Bars `
    --max-age-seconds $MaxAgeSeconds `
    --broker-timezone $BrokerTimezone `
    --interval-seconds $IntervalSeconds `
    --state-dir $StateDir

exit $LASTEXITCODE
