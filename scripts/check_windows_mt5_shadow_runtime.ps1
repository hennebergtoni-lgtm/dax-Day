param(
    [string]$Mt5TaskName = 'DAXLAB MT5 Terminal',
    [string]$ShadowTaskName = 'DAXLAB MT5 SHADOW',
    [string]$StateDir = '.runtime\mt5_shadow'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Convert-TaskDurationToTimeSpan {
    param(
        [Parameter(Mandatory = $true)]
        $Value,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if ($Value -is [TimeSpan]) {
        return $Value
    }

    try {
        return [System.Xml.XmlConvert]::ToTimeSpan([string]$Value)
    }
    catch {
        throw "Could not parse $Label as a task duration: $Value"
    }
}

function Assert-TaskRuntimePolicy {
    param(
        [Parameter(Mandatory = $true)]
        $Task,
        [Parameter(Mandatory = $true)]
        [string]$TaskName,
        [Parameter(Mandatory = $true)]
        [int]$ExpectedRestartCount,
        [Parameter(Mandatory = $true)]
        [int]$ExpectedRestartMinutes
    )

    $settings = $Task.Settings
    if (-not $settings) {
        throw "Scheduled task has no settings: $TaskName"
    }

    if ([int]$settings.RestartCount -ne $ExpectedRestartCount) {
        throw "Task restart count drift: $TaskName | expected=$ExpectedRestartCount | actual=$($settings.RestartCount)"
    }

    $restartInterval = Convert-TaskDurationToTimeSpan `
        -Value $settings.RestartInterval `
        -Label "$TaskName RestartInterval"
    if ([double]$restartInterval.TotalMinutes -ne [double]$ExpectedRestartMinutes) {
        throw "Task restart interval drift: $TaskName | expected=${ExpectedRestartMinutes}m | actual=$($settings.RestartInterval)"
    }

    if ([string]$settings.MultipleInstances -ne 'IgnoreNew') {
        throw "Task multiple-instance policy drift: $TaskName | expected=IgnoreNew | actual=$($settings.MultipleInstances)"
    }

    $executionLimit = Convert-TaskDurationToTimeSpan `
        -Value $settings.ExecutionTimeLimit `
        -Label "$TaskName ExecutionTimeLimit"
    if ($executionLimit -ne [TimeSpan]::Zero) {
        throw "Task execution-time-limit drift: $TaskName | expected=0 | actual=$($settings.ExecutionTimeLimit)"
    }

    Write-Host "TASK POLICY $TaskName | Restart=$ExpectedRestartCount x ${ExpectedRestartMinutes}m | MultipleInstances=IgnoreNew | ExecutionTimeLimit=0"
}

$mt5Task = Get-ScheduledTask -TaskName $Mt5TaskName -ErrorAction SilentlyContinue
if (-not $mt5Task) {
    throw "Scheduled task missing: $Mt5TaskName"
}
$mt5Info = Get-ScheduledTaskInfo -TaskName $Mt5TaskName
Write-Host "TASK $Mt5TaskName | State=$($mt5Task.State) | LastResult=$($mt5Info.LastTaskResult) | LastRun=$($mt5Info.LastRunTime)"
Assert-TaskRuntimePolicy `
    -Task $mt5Task `
    -TaskName $Mt5TaskName `
    -ExpectedRestartCount 5 `
    -ExpectedRestartMinutes 2

$shadowTask = Get-ScheduledTask -TaskName $ShadowTaskName -ErrorAction SilentlyContinue
if (-not $shadowTask) {
    throw "Scheduled task missing: $ShadowTaskName"
}
$shadowInfo = Get-ScheduledTaskInfo -TaskName $ShadowTaskName
Write-Host "TASK $ShadowTaskName | State=$($shadowTask.State) | LastResult=$($shadowInfo.LastTaskResult) | LastRun=$($shadowInfo.LastRunTime)"
Assert-TaskRuntimePolicy `
    -Task $shadowTask `
    -TaskName $ShadowTaskName `
    -ExpectedRestartCount 3 `
    -ExpectedRestartMinutes 5

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
