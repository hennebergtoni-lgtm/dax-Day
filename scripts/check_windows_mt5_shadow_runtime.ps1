param(
    [string]$Mt5TaskName = 'DAXLAB MT5 Terminal',
    [string]$ShadowTaskName = 'DAXLAB MT5 SHADOW',
    [string]$StateDir = '.runtime\mt5_shadow'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

foreach ($name in @($Mt5TaskName, $ShadowTaskName)) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "TASK MISSING: $name"
        continue
    }
    $info = Get-ScheduledTaskInfo -TaskName $name
    Write-Host "TASK $name | State=$($task.State) | LastResult=$($info.LastTaskResult) | LastRun=$($info.LastRunTime)"
}

$heartbeatPath = Join-Path (Join-Path $repoRoot $StateDir) 'heartbeat.json'
if (-not (Test-Path -LiteralPath $heartbeatPath -PathType Leaf)) {
    Write-Host "HEARTBEAT MISSING: $heartbeatPath"
    exit 2
}

$heartbeat = Get-Content -LiteralPath $heartbeatPath -Raw | ConvertFrom-Json
if ($heartbeat.execution_capability -ne 'NONE') {
    throw 'Heartbeat execution_capability is not NONE.'
}
if ($heartbeat.order_execution_enabled -ne $false) {
    throw 'Heartbeat order_execution_enabled is not false.'
}

Write-Host "HEARTBEAT | Status=$($heartbeat.status) | ObservedUTC=$($heartbeat.observed_at_utc) | Symbol=$($heartbeat.symbol)"
Write-Host "BARS | ClosedM5=$($heartbeat.closed_m5_bars) | AgeSeconds=$($heartbeat.latest_closed_bar_age_seconds) | NewDecisions=$($heartbeat.new_decisions) | Duplicates=$($heartbeat.duplicates_suppressed)"
Write-Host 'SAFETY | execution_capability=NONE | order_execution_enabled=false'

if ($heartbeat.status -ne 'GREEN') {
    Write-Host "BLOCKERS: $($heartbeat.blockers -join ', ')"
    exit 1
}

exit 0
