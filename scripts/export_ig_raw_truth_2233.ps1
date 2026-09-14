param(
    [Parameter(Mandatory = $true)][string]$ExpectedHead,
    [string]$RepoRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
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
    'RAW_EXPORT_FAILED_CLOSED', 'RAW_EXPORT_DUPLICATE_JSON_KEY',
    'RAW_EXPORT_RESOURCE_LIMIT', 'RAW_EXPORT_INVALID_UTF8', 'RAW_EXPORT_INVALID_JSON',
    'RAW_EXPORT_REQUIRED_FILES', 'RAW_EXPORT_RUNTIME_HEAD',
    'RAW_EXPORT_CAPTURE_CONTRACT_INVALID', 'RAW_EXPORT_EVIDENCE_HEAD',
    'RAW_EXPORT_COMPARE_MISMATCH', 'RAW_EXPORT_CLOCK', 'RAW_EXPORT_REQUEST_WINDOW',
    'RAW_EXPORT_SCHEDULE', 'RAW_EXPORT_SUMMARY_CONTRACT_OR_HASH',
    'RAW_EXPORT_SYMLINK', 'RAW_EXPORT_OUTPUT_EXISTS',
    'RAW_EXPORT_MISSING_OR_SYMLINK', 'RAW_EXPORT_SOURCE_CHANGED',
    'RAW_EXPORT_CODE_GATE_BLOCKED', 'RAW_EXPORT_CODE_CHANGED',
    'RAW_EXPORT_LOCK_UNAVAILABLE', 'RAW_EXPORT_PERMISSION_DENIED',
    'RAW_EXPORT_OUTPUT_RACE', 'RAW_EXPORT_PUBLICATION_FAILED',
    'RAW_EXPORT_FILESYSTEM_FAILED', 'RAW_EXPORT_UNEXPECTED_FAILURE',
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

function Invoke-OfflineExporter {
    try {
        Get-Command -Name $PythonExecutable -ErrorAction Stop | Out-Null
    } catch {
        throw 'PYTHON_NOT_AVAILABLE'
    }
    try {
        $resultLines = @(
            & $PythonExecutable (Join-Path $RepoRoot 'scripts/export_ig_raw_truth_2233.py') --expected-head $ExpectedHead 2>$null
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
    if ($exitCode -eq 0 -and $result.status -eq 'SUCCESS') { return }
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

    Write-Host 'START: exact-head deployment and offline original-evidence export'
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
        'merge-base', '--is-ancestor', '2a99f96e06f7ce1f311c767dec43d236bb63eedd', $head
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
    Write-Host 'WAIT: validate six originals; no login or broker call'
    Invoke-OfflineExporter
    Write-Host 'SUMMARY: SUCCESS; error_code=NONE; upload .runtime/ig_raw_truth_2233_attempt_03_originals.zip'
    exit 0
} catch {
    $candidate = [string]$_.Exception.Message
    $errorCode = if ($SafeErrorCodes -contains $candidate) {
        $candidate
    } else {
        'RUNNER_UNEXPECTED_FAILURE'
    }
    Write-Host ("SUMMARY: BLOCKED / FAIL_CLOSED; error_code={0}; original evidence retained; execution disabled" -f $errorCode)
    exit 2
}
