param(
    [string]$ExpectedCommit = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$repository = 'hennebergtoni-lgtm/dax-Day'

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

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("daxlab-parity-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

$results = @()
try {
    foreach ($relativePath in $runtimeFiles) {
        $localPath = Join-Path $repoRoot ($relativePath -replace '/', [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path -LiteralPath $localPath -PathType Leaf)) {
            $results += [PSCustomObject]@{
                Path = $relativePath
                Status = 'MISSING_LOCAL'
                LocalSHA256 = $null
                PublicSHA256 = $null
            }
            continue
        }

        $fileName = [IO.Path]::GetFileName($relativePath)
        $tempPath = Join-Path $tempRoot (([Guid]::NewGuid().ToString('N')) + '-' + $fileName)
        $rawUrl = "https://raw.githubusercontent.com/$repository/$ExpectedCommit/$relativePath"

        try {
            Invoke-WebRequest -Uri $rawUrl -OutFile $tempPath -UseBasicParsing
        }
        catch {
            $results += [PSCustomObject]@{
                Path = $relativePath
                Status = 'REMOTE_UNAVAILABLE'
                LocalSHA256 = $null
                PublicSHA256 = $null
            }
            continue
        }

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
Write-Host "PARITY SUMMARY | commit=$ExpectedCommit | total=$($results.Count) | match=$($results.Count - $failed.Count) | failed=$($failed.Count)"
Write-Host 'SAFETY | execution_capability=NONE | order_execution_enabled=false'

if ($failed.Count -gt 0) {
    exit 1
}

exit 0