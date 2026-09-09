$ErrorActionPreference = 'Stop'

Write-Host 'DAXLAB Windows MT5 read-only bootstrap'
Write-Host 'This helper does NOT accept credentials and does NOT enable order execution.'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python was not found in PATH.'
}

$venv = '.venv-mt5'
if (-not (Test-Path $venv)) {
    python -m venv $venv
}

$python = Join-Path $venv 'Scripts\python.exe'
& $python -m pip install --upgrade pip
& $python -m pip install -e .
& $python -m pip install MetaTrader5

Write-Host ''
Write-Host 'Prerequisite: MetaTrader 5 Desktop must already be open and logged into the DEMO account.'
Write-Host 'No password is passed to this script.'
Write-Host ''
& $python scripts\mt5_windows_probe.py --bars 20 --output mt5_probe.json

Write-Host ''
Write-Host 'Finished. Share only mt5_probe.json after checking that it contains no personal identifiers.'
