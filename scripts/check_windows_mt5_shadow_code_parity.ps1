param(
    [string]$ExpectedCommit = '8fe0b61a4da0b5637df372343d67b202bfbe8222'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$repository = 'hennebergtoni-lgtm/dax-Day'
$runtimeFiles = @(
    'scripts/windows_mt5_shadow_start.ps1',
    'scripts/mt5_shadow_supervisor.py',
    'scripts/mt5_windows_probe.py',
    'scripts/check_windows_mt5_shadow_runtime.ps1',
    'scripts/install_windows_mt5_shadow_task.ps1',
    'src/daxlab/runtime/atomic_json.py',
    'src/daxlab/runtime/mt5_broker_session.py',
    'src/daxlab/runtime/mt5_cross_cycle_integrity.py',
    'src/daxlab/runtime/mt5_heartbeat_history.py',
    'src/daxlab/runtime/mt5_readonly.py',
    'src/daxlab/runtime/mt5_shadow_integration.py',
    'src/daxlab/runtime/mt5_shadow_supervisor.py',
    'src/daxlab/runtime/mt5_windows_bundle.py',
    'src/daxlab/runtime/prospective_gate.py',
    'src/daxlab/runtime/shadow_observation.py',
    'src/daxlab/runtime/shadow_resume_anchor.py',
    'src/daxlab/runtime/shadow_soak.py',
    'src/daxlab/runtime/single_instance.py'
)

if ($ExpectedCommit -notmatch '^[0-9a-f]{40}$') {
    throw "ExpectedCommit must be a full 40-character lowercase git SHA: $ExpectedCommit"
}

Write-Host "DAXLAB MT5 SHADOW CODE PARITY | expected_commit=$ExpectedCommit"
Write-Host 'Execution: READ_ONLY / NO_ORDER / NO_SCHEDULER_CHANGES'

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("daxlab-parity-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

$results = @()
try {
    foreach ($relativePath in $runtimeFiles) {
        $localPath = Join-Path $repoRoot ($relativePath -replace '/', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $localPath -PathType Leaf)) {
            $results += [PSCustomObject]@{
                Path = $relativePath
                Status = 'MISSING'
                LocalSHA256 = $null
                PublicSHA256 = $null
            }
            continue
        }

        $fileName = [IO.Path]::GetFileName($relativePath)
        $tempPath = Join-Path $tempRoot (([Guid]::NewGuid().ToString('N')) + '-' + $fileName)
        $rawUrl = "https://raw.githubusercontent.com/$repository/$ExpectedCommit/$relativePath"
        Invoke-WebRequest -Uri $rawUrl -OutFile $tempPath -UseBasicParsing

        $localHash = (Get-FileHash -LiteralPath $localPath -Algorithm SHA256).Hash.ToUpperInvariant()
        $publicHash = (Get-FileHash -LiteralPath $tempPath -Algorithm SHA256).Hash.ToUpperInvariant()
        $status = if ($localHash -eq $publicHash) { 'MATCH' } else { 'MISMATCH' }
        $results += [PSCustomObject]@{
            Path = $relativePath
            Status = $status
            LocalSHA256 = $localHash
            PublicSHA256 = $publicHash
        }
    }
}
finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

$results | Format-Table Path, Status, LocalSHA256, PublicSHA256 -AutoSize

$failed = @($results | Where-Object { $_.Status -ne 'MATCH' })
Write-Host "PARITY SUMMARY | total=$($results.Count) | match=$($results.Count - $failed.Count) | failed=$($failed.Count)"
Write-Host 'SAFETY | execution_capability=NONE | order_execution_enabled=false'

if ($failed.Count -gt 0) {
    exit 1
}

exit 0
