param(
    [string]$StateDir = '.runtime\mt5_shadow',
    [string]$PythonExecutable = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if ($PythonExecutable) {
    $python = $PythonExecutable
} else {
    $python = Join-Path $repoRoot '.venv-mt5\Scripts\python.exe'
}
$exporter = Join-Path $repoRoot 'scripts\export_mt5_shadow_telemetry.py'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "MT5 Python environment not found: $python"
}
if (-not (Test-Path -LiteralPath $exporter -PathType Leaf)) {
    throw "MT5 SHADOW telemetry exporter not found: $exporter"
}
if (-not $env:NEON_DATABASE_URL) {
    $env:NEON_DATABASE_URL = [Environment]::GetEnvironmentVariable('NEON_DATABASE_URL', 'User')
}
if (-not $env:NEON_DATABASE_URL) {
    throw 'NEON_DATABASE_URL is not configured for this Windows user.'
}

Write-Host 'DAXLAB MT5 SHADOW telemetry export'
Write-Host "Repo: $repoRoot"
Write-Host "StateDir: $StateDir"
Write-Host "Python: $python"
Write-Host 'Direction: local SHADOW artifacts -> Neon only'
Write-Host 'Execution: NONE / NO_ORDER'

& $python $exporter --state-dir $StateDir
exit $LASTEXITCODE
