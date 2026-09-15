param(
    [Parameter(Mandatory = $true)][string]$ExpectedHead,
    [string]$RepoRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
    [string]$RuntimeRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
    [string]$Namespace = '.runtime/ig_m5_contract_2237_interval_start_v2_attempt_03',
    [string]$CredentialsFile = 'C:\Users\Mandy\ig_demo.env',
    [string]$PythonExecutable = 'python'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SafeErrorCodes = @(
    'HEAD_INVALID', 'HOST_UNAVAILABLE', 'RUNTIME_ROOT_UNAVAILABLE',
    'GIT_NOT_AVAILABLE', 'REMOTE_QUERY_FAILED', 'REMOTE_MISMATCH',
    'FETCH_FAILED', 'PUBLISHED_HEAD_QUERY_FAILED', 'BRANCH_DRIFT',
    'START_HEAD_NOT_ANCESTOR', 'TARGET_COMMIT_UNAVAILABLE',
    'DEPLOYMENT_PATH_COLLISION', 'DEPLOYMENT_PARENT_CREATE_FAILED',
    'DEPLOYMENT_OWNER_MARKER_FAILED', 'LOCAL_CLONE_FAILED',
    'DEPLOYMENT_HOOKS_CREATE_FAILED',
    'ISOLATED_CHECKOUT_FAILED', 'DEPLOYMENT_HEAD_QUERY_FAILED',
    'DEPLOYMENT_HEAD_MISMATCH', 'DEPLOYMENT_STATUS_FAILED',
    'DEPLOYMENT_NOT_CLEAN', 'DEPLOYMENT_CLEANUP_FAILED_RETAINED',
    'PYTHON_NOT_AVAILABLE', 'PYTHON_START_FAILED', 'PYTHON_RESULT_INVALID',
    'GOVERNANCE_WINDOWS_HOST_REQUIRED', 'GOVERNANCE_INVALID_HEAD',
    'GOVERNANCE_HEAD_MISMATCH', 'GOVERNANCE_TRACKED_DRIFT',
    'GOVERNANCE_UNTRACKED_CODE', 'GOVERNANCE_IMPORT_PARITY',
    'STATE_INVALID_NAMESPACE', 'STATE_NAMESPACE_SYMLINK',
    'STATE_NAMESPACE_EXISTS', 'STATE_RUNTIME_ROOT_INVALID',
    'STATE_RUNTIME_ROOT_UNAVAILABLE', 'STATE_PUBLICATION_FAILED',
    'STATE_READBACK_FAILED', 'STATE_CHANGED_OVERLAP',
    'STATE_ANCHOR_NOT_FOUND', 'STATE_NO_NEW_FINALIZED_M5',
    'DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED',
    'DATA_STALE_AT_PROCESSING', 'DATA_TEST_FAILED',
    'FRESH_START_FAILED', 'RESUME_FAILED', 'OPERATOR_FAILED',
    'SESSION_SETUP_FAILED', 'CREDENTIALS_FILE_UNAVAILABLE_OR_INVALID',
    'IG_AUTHENTICATION_FAILED_NO_RETRY',
    'IG_SESSION_READ_FAILED_NO_RETRY', 'IG_SESSION_CLEANUP_FAILED',
    'CLOCK_INVALID_UTC', 'CLOCK_MOVED_BACKWARDS',
    'CLOCK_DISCONTINUITY', 'SAFETY_EXECUTION_CAPABILITY',
    'RUNNER_UNEXPECTED_FAILURE'
)

function Invoke-GitGate {
    param(
        [Parameter(Mandatory = $true)][string]$ErrorCode,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$WorkingDirectory = $RepoRoot
    )
    try {
        $result = @(& git -C $WorkingDirectory @Arguments 2>$null)
        $exitCode = $LASTEXITCODE
    } catch {
        throw $ErrorCode
    }
    if ($exitCode -ne 0) { throw $ErrorCode }
    return (($result -join [Environment]::NewLine).Trim())
}

function Get-LegacyPartialState {
    param([Parameter(Mandatory = $true)][string]$TemporaryRoot)
    $registered = 0
    $directories = 0
    $queryFailed = $false
    try {
        $lines = @(& git -C $RepoRoot worktree list --porcelain 2>$null)
        if ($LASTEXITCODE -ne 0) {
            $queryFailed = $true
        } else {
            foreach ($line in $lines) {
                if ($line -notmatch '^worktree (.+)$') { continue }
                try {
                    $path = [System.IO.Path]::GetFullPath($Matches[1])
                    $parent = Split-Path -Parent $path
                    $leaf = Split-Path -Leaf $path
                    $parentLeaf = Split-Path -Leaf $parent
                    if ($leaf -eq 'exact-head' -and
                        $parentLeaf -match '^dax-day-step2237-[0-9a-f]{32}$' -and
                        $parent.StartsWith($TemporaryRoot, [StringComparison]::OrdinalIgnoreCase)) {
                        $registered += 1
                    }
                } catch {
                    $queryFailed = $true
                }
            }
        }
    } catch {
        $queryFailed = $true
    }
    try {
        $legacy = @([System.IO.Directory]::EnumerateDirectories($TemporaryRoot) |
            Where-Object {
                [System.IO.Path]::GetFileName($_) -match '^dax-day-step2237-[0-9a-f]{32}$'
            })
        $directories = $legacy.Count
    } catch {
        $queryFailed = $true
    }
    if ($queryFailed) { return 'QUERY_INCOMPLETE_RETAINED' }
    if ($registered -gt 0 -or $directories -gt 0) { return 'DETECTED_RETAINED' }
    return 'NONE_DETECTED'
}

function Test-RunnerOwnedDeployment {
    param(
        [Parameter(Mandatory = $true)][string]$TemporaryRoot,
        [Parameter(Mandatory = $true)][string]$DeploymentParent,
        [Parameter(Mandatory = $true)][string]$DeploymentRoot,
        [Parameter(Mandatory = $true)][string]$MarkerPath,
        [Parameter(Mandatory = $true)][string]$OwnerToken
    )
    try {
        $trimChars = [char[]]@(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar
        )
        $temporaryFull = [System.IO.Path]::GetFullPath($TemporaryRoot).TrimEnd($trimChars) +
            [System.IO.Path]::DirectorySeparatorChar
        $parentFull = [System.IO.Path]::GetFullPath($DeploymentParent)
        $rootFull = [System.IO.Path]::GetFullPath($DeploymentRoot)
        if (!$parentFull.StartsWith($temporaryFull, [StringComparison]::OrdinalIgnoreCase)) {
            return $false
        }
        if ((Split-Path -Leaf $parentFull) -notmatch '^d2237-[0-9a-f]{32}$') {
            return $false
        }
        if ($rootFull -ne [System.IO.Path]::GetFullPath((Join-Path $parentFull 'repo'))) {
            return $false
        }
        if (!(Test-Path -LiteralPath $MarkerPath -PathType Leaf)) { return $false }
        $parentAttributes = [System.IO.File]::GetAttributes($parentFull)
        if (($parentAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            return $false
        }
        $markerAttributes = [System.IO.File]::GetAttributes($MarkerPath)
        if (($markerAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            return $false
        }
        $marker = Get-Content -LiteralPath $MarkerPath -Raw -ErrorAction Stop |
            ConvertFrom-Json -ErrorAction Stop
        if ($marker.schema -ne 'DAX_STEP2237_DEPLOYMENT_OWNER_V1' -or
            $marker.owner_token -ne $OwnerToken -or
            $marker.expected_head -ne $ExpectedHead -or
            $marker.deployment_child -ne 'repo') {
            return $false
        }
        $allowed = @('.dax-step2237-owner.json', '.hooks', 'repo')
        foreach ($child in [System.IO.Directory]::EnumerateFileSystemEntries($parentFull)) {
            if ($allowed -notcontains [System.IO.Path]::GetFileName($child)) { return $false }
        }
        if (Test-Path -LiteralPath $rootFull) {
            $rootAttributes = [System.IO.File]::GetAttributes($rootFull)
            if (($rootAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                return $false
            }
        }
        $hooksFull = Join-Path $parentFull '.hooks'
        if (Test-Path -LiteralPath $hooksFull) {
            $hooksAttributes = [System.IO.File]::GetAttributes($hooksFull)
            if (($hooksAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                return $false
            }
        }
        return $true
    } catch {
        return $false
    }
}

function Invoke-Closeout {
    param([Parameter(Mandatory = $true)][string]$DeploymentRoot)
    try {
        Get-Command -Name $PythonExecutable -ErrorAction Stop | Out-Null
    } catch {
        throw 'PYTHON_NOT_AVAILABLE'
    }
    try {
        $resultLines = @(
            & $PythonExecutable (Join-Path $DeploymentRoot 'scripts/run_ig_m5_contract_2237.py') `
                --expected-head $ExpectedHead --namespace $Namespace `
                --credentials-file $CredentialsFile --runtime-root $RuntimeRoot 2>$null
        )
        $exitCode = $LASTEXITCODE
    } catch {
        throw 'PYTHON_START_FAILED'
    }
    if (!$resultLines -or $resultLines.Count -ne 1) { throw 'PYTHON_RESULT_INVALID' }
    try {
        $result = $resultLines[0] | ConvertFrom-Json -ErrorAction Stop
    } catch {
        throw 'PYTHON_RESULT_INVALID'
    }
    if ($exitCode -eq 0 -and $result.status -eq 'SUCCESS') { return $result }
    $innerCode = [string]$result.error_code
    if ($SafeErrorCodes -notcontains $innerCode) { throw 'PYTHON_RESULT_INVALID' }
    throw $innerCode
}

$deploymentParent = $null
$deploymentRoot = $null
$markerPath = $null
$hooksRoot = $null
$ownerToken = $null
$deploymentParentCreated = $false
$primaryErrorCode = $null
$cleanupErrorCode = $null
$result = $null
$legacyPartialState = 'NOT_QUERIED'
$previousNoByteCode = $env:PYTHONDONTWRITEBYTECODE

try {
    if ($ExpectedHead -notmatch '^[0-9a-f]{40}$') { throw 'HEAD_INVALID' }
    if (!(Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw 'HOST_UNAVAILABLE' }
    if (!(Test-Path -LiteralPath $RuntimeRoot -PathType Container)) {
        throw 'RUNTIME_ROOT_UNAVAILABLE'
    }
    try {
        Get-Command -Name 'git' -CommandType Application -ErrorAction Stop | Out-Null
    } catch {
        throw 'GIT_NOT_AVAILABLE'
    }

    Write-Host 'START: isolated exact-head local clone; existing checkout remains untouched'
    $remote = Invoke-GitGate -ErrorCode 'REMOTE_QUERY_FAILED' -Arguments @(
        'remote', 'get-url', 'origin'
    )
    if ($remote -notin @('https://github.com/hennebergtoni-lgtm/dax-Day.git',
                         'https://github.com/hennebergtoni-lgtm/dax-Day',
                         'git@github.com:hennebergtoni-lgtm/dax-Day.git')) {
        throw 'REMOTE_MISMATCH'
    }
    Invoke-GitGate -ErrorCode 'FETCH_FAILED' -Arguments @(
        'fetch', '--quiet', 'origin', 'nextgen-bot-line-v1'
    ) | Out-Null
    $published = Invoke-GitGate -ErrorCode 'PUBLISHED_HEAD_QUERY_FAILED' -Arguments @(
        'rev-parse', 'origin/nextgen-bot-line-v1'
    )
    if ($published -ne $ExpectedHead) { throw 'BRANCH_DRIFT' }
    Invoke-GitGate -ErrorCode 'START_HEAD_NOT_ANCESTOR' -Arguments @(
        'merge-base', '--is-ancestor',
        '78fb8cf8648e51de964f09e205f7f278193c5439', $ExpectedHead
    ) | Out-Null
    Invoke-GitGate -ErrorCode 'TARGET_COMMIT_UNAVAILABLE' -Arguments @(
        'cat-file', '-e', ("{0}^{{commit}}" -f $ExpectedHead)
    ) | Out-Null

    $temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    $legacyPartialState = Get-LegacyPartialState -TemporaryRoot $temporaryRoot
    $ownerToken = [Guid]::NewGuid().ToString('N')
    $deploymentParent = Join-Path $temporaryRoot ('d2237-' + $ownerToken)
    if (Test-Path -LiteralPath $deploymentParent) { throw 'DEPLOYMENT_PATH_COLLISION' }
    try {
        New-Item -ItemType Directory -Path $deploymentParent -ErrorAction Stop | Out-Null
        $deploymentParentCreated = $true
    } catch {
        throw 'DEPLOYMENT_PARENT_CREATE_FAILED'
    }
    $deploymentRoot = Join-Path $deploymentParent 'repo'
    $markerPath = Join-Path $deploymentParent '.dax-step2237-owner.json'
    $hooksRoot = Join-Path $deploymentParent '.hooks'
    try {
        $markerPayload = [ordered]@{
            schema = 'DAX_STEP2237_DEPLOYMENT_OWNER_V1'
            owner_token = $ownerToken
            expected_head = $ExpectedHead
            deployment_child = 'repo'
        } | ConvertTo-Json -Compress
        [System.IO.File]::WriteAllText(
            $markerPath,
            $markerPayload,
            [System.Text.UTF8Encoding]::new($false)
        )
    } catch {
        throw 'DEPLOYMENT_OWNER_MARKER_FAILED'
    }
    if (!(Test-RunnerOwnedDeployment -TemporaryRoot $temporaryRoot `
            -DeploymentParent $deploymentParent -DeploymentRoot $deploymentRoot `
            -MarkerPath $markerPath -OwnerToken $ownerToken)) {
        throw 'DEPLOYMENT_OWNER_MARKER_FAILED'
    }
    try {
        New-Item -ItemType Directory -Path $hooksRoot -ErrorAction Stop | Out-Null
    } catch {
        throw 'DEPLOYMENT_HOOKS_CREATE_FAILED'
    }

    try {
        & git -c ("core.hooksPath={0}" -f $hooksRoot) -c core.longpaths=true `
            clone --quiet --no-checkout --no-hardlinks `
            $RepoRoot $deploymentRoot 2>$null | Out-Null
        $cloneExit = $LASTEXITCODE
    } catch {
        throw 'LOCAL_CLONE_FAILED'
    }
    if ($cloneExit -ne 0) { throw 'LOCAL_CLONE_FAILED' }
    try {
        & git -C $deploymentRoot -c ("core.hooksPath={0}" -f $hooksRoot) `
            -c core.longpaths=true checkout --quiet --detach `
            $ExpectedHead 2>$null | Out-Null
        $checkoutExit = $LASTEXITCODE
    } catch {
        throw 'ISOLATED_CHECKOUT_FAILED'
    }
    if ($checkoutExit -ne 0) { throw 'ISOLATED_CHECKOUT_FAILED' }

    $deployedHead = Invoke-GitGate -WorkingDirectory $deploymentRoot `
        -ErrorCode 'DEPLOYMENT_HEAD_QUERY_FAILED' -Arguments @('rev-parse', 'HEAD')
    if ($deployedHead -ne $ExpectedHead) { throw 'DEPLOYMENT_HEAD_MISMATCH' }
    $deploymentStatus = Invoke-GitGate -WorkingDirectory $deploymentRoot `
        -ErrorCode 'DEPLOYMENT_STATUS_FAILED' -Arguments @(
            'status', '--porcelain', '--untracked-files=all'
        )
    if ($deploymentStatus) { throw 'DEPLOYMENT_NOT_CLEAN' }

    $env:PYTHONDONTWRITEBYTECODE = '1'
    Write-Host 'WAIT: one IG read-only session; fresh start; next true close; resume; Operator'
    $result = Invoke-Closeout -DeploymentRoot $deploymentRoot
} catch {
    $candidate = [string]$_.Exception.Message
    $primaryErrorCode = if ($SafeErrorCodes -contains $candidate) {
        $candidate
    } else {
        'RUNNER_UNEXPECTED_FAILURE'
    }
} finally {
    if ($null -eq $previousNoByteCode) {
        Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue
    } else {
        $env:PYTHONDONTWRITEBYTECODE = $previousNoByteCode
    }

    if ($deploymentParentCreated -and $deploymentParent -and
        (Test-Path -LiteralPath $deploymentParent)) {
        if (Test-RunnerOwnedDeployment -TemporaryRoot $temporaryRoot `
                -DeploymentParent $deploymentParent -DeploymentRoot $deploymentRoot `
                -MarkerPath $markerPath -OwnerToken $ownerToken) {
            try {
                [System.IO.Directory]::Delete($deploymentParent, $true)
                if (Test-Path -LiteralPath $deploymentParent) {
                    $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
                }
            } catch {
                $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
            }
        } else {
            $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
        }
    }
}

$errorCode = if ($cleanupErrorCode) { $cleanupErrorCode } else { $primaryErrorCode }
if ($errorCode) {
    Write-Host (
        'SUMMARY: BLOCKED / FAIL_CLOSED; error_code={0}; legacy_partial_state={1}; existing checkout/evidence retained; execution disabled' `
        -f $errorCode, $legacyPartialState
    )
    exit 2
}
Write-Host (
    'SUMMARY: SUCCESS; error_code=NONE; namespace={0}; legacy_partial_state={1}; deployment cleaned; NONE/false' `
    -f $result.namespace, $legacyPartialState
)
exit 0
