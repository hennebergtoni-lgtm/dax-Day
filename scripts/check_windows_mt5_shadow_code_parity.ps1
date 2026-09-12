param(
    [string]$ExpectedCommit = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Invoke-GitLine {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $output = & git @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed: $($output -join [Environment]::NewLine)"
    }
    return (($output | Out-String).Trim())
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'git is required for code parity verification.'
}

$localHead = (Invoke-GitLine -Arguments @('rev-parse', 'HEAD')).Trim().ToLowerInvariant()
if ([string]::IsNullOrWhiteSpace($ExpectedCommit)) {
    $ExpectedCommit = (Invoke-GitLine -Arguments @('rev-parse', '--verify', '@{upstream}')).Trim()
}
$ExpectedCommit = $ExpectedCommit.Trim().ToLowerInvariant()

if ($ExpectedCommit -notmatch '^[0-9a-f]{40}$') {
    throw "ExpectedCommit must resolve to a full 40-character lowercase git SHA: $ExpectedCommit"
}
if ($localHead -notmatch '^[0-9a-f]{40}$') {
    throw "Local HEAD did not resolve to a full git SHA: $localHead"
}

Write-Host "DAXLAB MT5 SHADOW CODE PARITY | expected_commit=$ExpectedCommit | local_head=$localHead"
Write-Host 'Execution: READ_ONLY / NO_ORDER / NO_SCHEDULER_CHANGES'

if ($localHead -ne $ExpectedCommit) {
    Write-Host 'HEAD PARITY | MISMATCH — local checkout is not at the expected/upstream commit.'
    Write-Host 'SAFETY | execution_capability=NONE | order_execution_enabled=false'
    exit 1
}
Write-Host 'HEAD PARITY | MATCH'

$fixedRuntimeFiles = @(
    'scripts/check_windows_mt5_shadow_code_parity.ps1',
    'scripts/check_windows_mt5_shadow_runtime.ps1',
    'scripts/install_windows_mt5_shadow_task.ps1',
    'scripts/mt5_shadow_supervisor.py',
    'scripts/mt5_windows_probe.py',
    'scripts/preflight_windows_mt5_shadow_autostart.ps1',
    'scripts/windows_mt5_shadow_start.ps1',
    'src/daxlab/runtime/atomic_json.py',
    'src/daxlab/runtime/operator_runtime_bridge.py',
    'src/daxlab/runtime/operator_snapshot.py',
    'src/daxlab/runtime/product_identity.py',
    'src/daxlab/runtime/prospective_gate.py',
    'src/daxlab/runtime/shadow_observation.py',
    'src/daxlab/runtime/shadow_resume_anchor.py',
    'src/daxlab/runtime/shadow_soak.py',
    'src/daxlab/runtime/single_instance.py'
)

$runtimeTreeText = Invoke-GitLine -Arguments @('ls-tree', '-r', '--name-only', $ExpectedCommit, '--', 'src/daxlab/runtime')
$dynamicRuntimeFiles = @(
    $runtimeTreeText -split "`r?`n" |
        Where-Object { $_ -match '^src/daxlab/runtime/(candidate_|mt5_).+\.py$' }
)
$runtimeFiles = @($fixedRuntimeFiles + $dynamicRuntimeFiles) | Sort-Object -Unique

if ($dynamicRuntimeFiles.Count -eq 0) {
    throw 'No candidate_/mt5_ runtime files were discovered at the expected commit.'
}

Write-Host "PARITY SURFACE | files=$($runtimeFiles.Count) | dynamic_candidate_mt5=$($dynamicRuntimeFiles.Count)"
Write-Host 'PARITY MODE | GIT_CANONICAL_BLOB / CRLF_SAFE'

$results = @()
foreach ($relativePath in $runtimeFiles) {
    $localPath = Join-Path $repoRoot ($relativePath -replace '/', [IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $localPath -PathType Leaf)) {
        $results += [PSCustomObject]@{
            Path = $relativePath
            Status = 'MISSING_LOCAL'
            LocalObjectId = $null
            ExpectedObjectId = $null
        }
        continue
    }

    try {
        $expectedObjectId = (Invoke-GitLine -Arguments @('rev-parse', "${ExpectedCommit}:$relativePath")).Trim().ToLowerInvariant()
    }
    catch {
        $results += [PSCustomObject]@{
            Path = $relativePath
            Status = 'EXPECTED_BLOB_UNAVAILABLE'
            LocalObjectId = $null
            ExpectedObjectId = $null
        }
        continue
    }

    try {
        # Use the path-aware Git clean-filter pipeline so normal Windows CRLF
        # worktree conversion does not create a false parity mismatch.
        $localObjectId = (Invoke-GitLine -Arguments @('hash-object', "--path=$relativePath", $localPath)).Trim().ToLowerInvariant()
    }
    catch {
        $results += [PSCustomObject]@{
            Path = $relativePath
            Status = 'LOCAL_HASH_UNAVAILABLE'
            LocalObjectId = $null
            ExpectedObjectId = $expectedObjectId
        }
        continue
    }

    $status = if ($localObjectId -eq $expectedObjectId) { 'MATCH' } else { 'MISMATCH' }
    $results += [PSCustomObject]@{
        Path = $relativePath
        Status = $status
        LocalObjectId = $localObjectId
        ExpectedObjectId = $expectedObjectId
    }
}

$results | Format-Table Path, Status, LocalObjectId, ExpectedObjectId -AutoSize

$failed = @($results | Where-Object { $_.Status -ne 'MATCH' })
Write-Host "PARITY SUMMARY | commit=$ExpectedCommit | total=$($results.Count) | match=$($results.Count - $failed.Count) | failed=$($failed.Count)"
Write-Host 'SAFETY | execution_capability=NONE | order_execution_enabled=false'

if ($failed.Count -gt 0) {
    exit 1
}

exit 0
