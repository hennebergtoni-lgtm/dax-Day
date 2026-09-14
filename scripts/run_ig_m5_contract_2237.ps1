param(
    [Parameter(Mandatory = $true)][string]$ExpectedHead,
    [string]$RepoRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
    [string]$RuntimeRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
    [string]$Namespace = '.runtime/ig_m5_contract_2237_interval_start_v2_attempt_02',
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
    'WORKTREE_ADD_FAILED', 'WORKTREE_ADD_FAILED_DEPLOYMENT_RETAINED',
    'DEPLOYMENT_HEAD_QUERY_FAILED', 'DEPLOYMENT_HEAD_MISMATCH',
    'DEPLOYMENT_STATUS_FAILED', 'DEPLOYMENT_NOT_CLEAN',
    'DEPLOYMENT_CLEANUP_FAILED_RETAINED',
    'DEPLOYMENT_PARENT_CLEANUP_FAILED_RETAINED',
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
$deploymentParentCreated = $false
$worktreeAdded = $false
$primaryErrorCode = $null
$cleanupErrorCode = $null
$result = $null
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

    Write-Host 'START: isolated exact-head deployment; existing checkout remains untouched'
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
        '236ea841d3d9e9d30532b08270995cc4925abaa5', $ExpectedHead
    ) | Out-Null
    Invoke-GitGate -ErrorCode 'TARGET_COMMIT_UNAVAILABLE' -Arguments @(
        'cat-file', '-e', ("{0}^{{commit}}" -f $ExpectedHead)
    ) | Out-Null

    $deploymentParent = Join-Path ([System.IO.Path]::GetTempPath()) (
        'dax-day-step2237-' + [Guid]::NewGuid().ToString('N')
    )
    if (Test-Path -LiteralPath $deploymentParent) { throw 'DEPLOYMENT_PATH_COLLISION' }
    try {
        New-Item -ItemType Directory -Path $deploymentParent -ErrorAction Stop | Out-Null
        $deploymentParentCreated = $true
    } catch {
        throw 'DEPLOYMENT_PARENT_CREATE_FAILED'
    }
    $deploymentRoot = Join-Path $deploymentParent 'exact-head'
    try {
        & git -C $RepoRoot worktree add --detach $deploymentRoot $ExpectedHead 2>$null | Out-Null
        $worktreeExit = $LASTEXITCODE
    } catch {
        throw 'WORKTREE_ADD_FAILED'
    }
    if ($worktreeExit -ne 0) { throw 'WORKTREE_ADD_FAILED' }
    $worktreeAdded = $true

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

    if ($worktreeAdded -and $deploymentRoot) {
        try {
            $finalStatus = Invoke-GitGate -WorkingDirectory $deploymentRoot `
                -ErrorCode 'DEPLOYMENT_STATUS_FAILED' -Arguments @(
                    'status', '--porcelain', '--untracked-files=all'
                )
            if ($finalStatus) {
                $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
            } else {
                & git -C $RepoRoot worktree remove $deploymentRoot 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0 -or (Test-Path -LiteralPath $deploymentRoot)) {
                    $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
                }
            }
        } catch {
            $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
        }
    } elseif ($deploymentParentCreated -and $deploymentRoot -and
              (Test-Path -LiteralPath $deploymentRoot)) {
        try {
            $children = @(Get-ChildItem -LiteralPath $deploymentRoot -Force -ErrorAction Stop)
            if ($children.Count -eq 0) {
                [System.IO.Directory]::Delete($deploymentRoot, $false)
            } else {
                $cleanupErrorCode = 'WORKTREE_ADD_FAILED_DEPLOYMENT_RETAINED'
            }
        } catch {
            $cleanupErrorCode = 'WORKTREE_ADD_FAILED_DEPLOYMENT_RETAINED'
        }
    }

    if ($deploymentParentCreated -and $deploymentParent -and
        (Test-Path -LiteralPath $deploymentParent)) {
        try {
            $remaining = @(Get-ChildItem -LiteralPath $deploymentParent -Force -ErrorAction Stop)
            if ($remaining.Count -eq 0) {
                [System.IO.Directory]::Delete($deploymentParent, $false)
            } elseif (!$cleanupErrorCode) {
                $cleanupErrorCode = 'DEPLOYMENT_PARENT_CLEANUP_FAILED_RETAINED'
            }
        } catch {
            if (!$cleanupErrorCode) {
                $cleanupErrorCode = 'DEPLOYMENT_PARENT_CLEANUP_FAILED_RETAINED'
            }
        }
    }
}

$errorCode = if ($cleanupErrorCode) { $cleanupErrorCode } else { $primaryErrorCode }
if ($errorCode) {
    Write-Host (
        'SUMMARY: BLOCKED / FAIL_CLOSED; error_code={0}; existing checkout/evidence retained; execution disabled' `
        -f $errorCode
    )
    exit 2
}
Write-Host (
    'SUMMARY: SUCCESS; error_code=NONE; namespace={0}; deployment cleaned; NONE/false' `
    -f $result.namespace
)
exit 0
