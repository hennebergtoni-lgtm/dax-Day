param(
    [Parameter(Mandatory = $true)][string]$ExpectedHead,
    [string]$RepoRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
    [string]$Namespace = '.runtime/ig_m5_contract_2237_interval_start_v2_attempt_01',
    [string]$CredentialsFile = 'C:\Users\Mandy\ig_demo.env',
    [string]$PythonExecutable = 'python'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SafeErrorCodes = @(
    'HEAD_INVALID', 'HOST_UNAVAILABLE', 'GIT_NOT_AVAILABLE',
    'REMOTE_QUERY_FAILED', 'REMOTE_MISMATCH', 'WORKTREE_STATUS_FAILED',
    'TRACKED_DRIFT', 'UNTRACKED_CODE_QUERY_FAILED', 'UNTRACKED_CODE',
    'LOCAL_HEAD_QUERY_FAILED', 'START_HEAD_NOT_ANCESTOR', 'FETCH_FAILED',
    'PUBLISHED_HEAD_QUERY_FAILED', 'BRANCH_DRIFT',
    'LOCAL_HEAD_NOT_ANCESTOR_FINAL', 'DETACHED_CHECKOUT_FAILED',
    'HEAD_VERIFY_QUERY_FAILED', 'HEAD_MISMATCH', 'PYTHON_NOT_AVAILABLE',
    'PYTHON_START_FAILED', 'PYTHON_RESULT_INVALID',
    'GOVERNANCE_WINDOWS_HOST_REQUIRED', 'GOVERNANCE_INVALID_HEAD',
    'GOVERNANCE_HEAD_MISMATCH', 'GOVERNANCE_TRACKED_DRIFT',
    'GOVERNANCE_UNTRACKED_CODE', 'GOVERNANCE_IMPORT_PARITY',
    'STATE_INVALID_NAMESPACE', 'STATE_NAMESPACE_SYMLINK',
    'STATE_NAMESPACE_EXISTS', 'STATE_PUBLICATION_FAILED',
    'STATE_CHANGED_OVERLAP', 'STATE_ANCHOR_NOT_FOUND',
    'STATE_NO_NEW_FINALIZED_M5',
    'DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED',
    'DATA_STALE_AT_PROCESSING', 'DATA_TEST_FAILED',
    'IG_AUTHENTICATION_FAILED_NO_RETRY',
    'IG_SESSION_READ_FAILED_NO_RETRY', 'IG_SESSION_CLEANUP_FAILED',
    'CLOCK_INVALID_UTC', 'CLOCK_MOVED_BACKWARDS',
    'CLOCK_DISCONTINUITY', 'SAFETY_EXECUTION_CAPABILITY',
    'RUNNER_UNEXPECTED_FAILURE'
)

function Invoke-GitGate {
    param(
        [Parameter(Mandatory = $true)][string]$ErrorCode,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    try {
        $result = @(& git -C $RepoRoot @Arguments 2>$null)
        $exitCode = $LASTEXITCODE
    } catch {
        throw $ErrorCode
    }
    if ($exitCode -ne 0) { throw $ErrorCode }
    return (($result -join [Environment]::NewLine).Trim())
}

function Invoke-Closeout {
    try {
        Get-Command -Name $PythonExecutable -ErrorAction Stop | Out-Null
    } catch {
        throw 'PYTHON_NOT_AVAILABLE'
    }
    try {
        $resultLines = @(
            & $PythonExecutable (Join-Path $RepoRoot 'scripts/run_ig_m5_contract_2237.py') `
                --expected-head $ExpectedHead --namespace $Namespace `
                --credentials-file $CredentialsFile 2>$null
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

try {
    if ($ExpectedHead -notmatch '^[0-9a-f]{40}$') { throw 'HEAD_INVALID' }
    if (!(Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw 'HOST_UNAVAILABLE' }
    try {
        Get-Command -Name 'git' -CommandType Application -ErrorAction Stop | Out-Null
    } catch {
        throw 'GIT_NOT_AVAILABLE'
    }

    Write-Host 'START: deploy exact head; one IG read-only session; fresh start; resume; Operator'
    $remote = Invoke-GitGate -ErrorCode 'REMOTE_QUERY_FAILED' -Arguments @('remote', 'get-url', 'origin')
    if ($remote -notin @('https://github.com/hennebergtoni-lgtm/dax-Day.git',
                         'https://github.com/hennebergtoni-lgtm/dax-Day',
                         'git@github.com:hennebergtoni-lgtm/dax-Day.git')) { throw 'REMOTE_MISMATCH' }
    $tracked = Invoke-GitGate -ErrorCode 'WORKTREE_STATUS_FAILED' -Arguments @(
        'status', '--porcelain', '--untracked-files=no'
    )
    if ($tracked) { throw 'TRACKED_DRIFT' }
    $untrackedCode = Invoke-GitGate -ErrorCode 'UNTRACKED_CODE_QUERY_FAILED' -Arguments @(
        'ls-files', '--others', '--exclude-standard', 'scripts/*.py', 'src/*.py'
    )
    if ($untrackedCode) { throw 'UNTRACKED_CODE' }

    $head = Invoke-GitGate -ErrorCode 'LOCAL_HEAD_QUERY_FAILED' -Arguments @('rev-parse', 'HEAD')
    Invoke-GitGate -ErrorCode 'START_HEAD_NOT_ANCESTOR' -Arguments @(
        'merge-base', '--is-ancestor', '7728453c3c4f8fcd2cf6f8189b0f94562ccfa04f', $head
    ) | Out-Null
    Invoke-GitGate -ErrorCode 'FETCH_FAILED' -Arguments @(
        'fetch', '--quiet', 'origin', 'nextgen-bot-line-v1'
    ) | Out-Null
    $published = Invoke-GitGate -ErrorCode 'PUBLISHED_HEAD_QUERY_FAILED' -Arguments @(
        'rev-parse', 'origin/nextgen-bot-line-v1'
    )
    if ($published -ne $ExpectedHead) { throw 'BRANCH_DRIFT' }
    Invoke-GitGate -ErrorCode 'LOCAL_HEAD_NOT_ANCESTOR_FINAL' -Arguments @(
        'merge-base', '--is-ancestor', $head, $ExpectedHead
    ) | Out-Null
    if ($head -ne $ExpectedHead) {
        Invoke-GitGate -ErrorCode 'DETACHED_CHECKOUT_FAILED' -Arguments @(
            'checkout', '--detach', $ExpectedHead
        ) | Out-Null
    }
    $verifiedHead = Invoke-GitGate -ErrorCode 'HEAD_VERIFY_QUERY_FAILED' -Arguments @('rev-parse', 'HEAD')
    if ($verifiedHead -ne $ExpectedHead) { throw 'HEAD_MISMATCH' }

    Set-Location -LiteralPath $RepoRoot
    Write-Host 'WAIT: bounded fresh-start and next-true-close resume; no order endpoint'
    $result = Invoke-Closeout
    Write-Host ("SUMMARY: SUCCESS; error_code=NONE; namespace={0}; NONE/false" -f $result.namespace)
    exit 0
} catch {
    $candidate = [string]$_.Exception.Message
    $errorCode = if ($SafeErrorCodes -contains $candidate) {
        $candidate
    } else {
        'RUNNER_UNEXPECTED_FAILURE'
    }
    Write-Host ("SUMMARY: BLOCKED / FAIL_CLOSED; error_code={0}; evidence retained; execution disabled" -f $errorCode)
    exit 2
}
