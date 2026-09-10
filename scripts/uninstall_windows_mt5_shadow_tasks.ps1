param(
    [string]$Mt5TaskName = 'DAXLAB MT5 Terminal',
    [string]$ShadowTaskName = 'DAXLAB MT5 SHADOW'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

foreach ($name in @($ShadowTaskName, $Mt5TaskName)) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "Task not present: $name"
        continue
    }
    try {
        Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    }
    finally {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
    }
    Write-Host "Removed task: $name"
}

Write-Host 'Runtime state and resume evidence were intentionally kept.'
Write-Host 'No MT5 credentials or trading settings were changed.'
