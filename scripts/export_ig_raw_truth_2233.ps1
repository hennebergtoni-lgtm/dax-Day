param(
    [Parameter(Mandatory = $true)][string]$ExpectedHead,
    [string]$RepoRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
    [string]$PythonExecutable = 'python'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Git-Checked {
    param([string[]]$Arguments)
    $result = & git -C $RepoRoot @Arguments 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'GIT_GATE_FAILED' }
    return ($result | Out-String).Trim()
}
try {
    if ($ExpectedHead -notmatch '^[0-9a-f]{40}$') { throw 'HEAD_INVALID' }
    if (!(Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw 'HOST_UNAVAILABLE' }
    Write-Host 'START: exact-head deployment and offline original-evidence export'
    $remote = Git-Checked @('remote', 'get-url', 'origin')
    if ($remote -notin @('https://github.com/hennebergtoni-lgtm/dax-Day.git',
                        'https://github.com/hennebergtoni-lgtm/dax-Day',
                        'git@github.com:hennebergtoni-lgtm/dax-Day.git')) { throw 'REMOTE_MISMATCH' }
    if ((Git-Checked @('status', '--porcelain', '--untracked-files=no'))) { throw 'TRACKED_DRIFT' }
    if ((Git-Checked @('ls-files', '--others', '--exclude-standard', 'scripts/*.py', 'src/*.py'))) {
        throw 'UNTRACKED_CODE'
    }
    $head = Git-Checked @('rev-parse', 'HEAD')
    Git-Checked @('merge-base', '--is-ancestor', '2a99f96e06f7ce1f311c767dec43d236bb63eedd', $head) | Out-Null
    Git-Checked @('fetch', '--quiet', 'origin', 'nextgen-bot-line-v1') | Out-Null
    $published = Git-Checked @('rev-parse', 'origin/nextgen-bot-line-v1')
    if ($published -ne $ExpectedHead) { throw 'BRANCH_DRIFT' }
    Git-Checked @('merge-base', '--is-ancestor', $head, $ExpectedHead) | Out-Null
    if ($head -ne $ExpectedHead) {
        Git-Checked @('checkout', '--detach', $ExpectedHead) | Out-Null
    }
    if ((Git-Checked @('rev-parse', 'HEAD')) -ne $ExpectedHead) { throw 'HEAD_MISMATCH' }
    Set-Location -LiteralPath $RepoRoot
    Write-Host 'WAIT: validate six originals; no login or broker call'
    & $PythonExecutable (Join-Path $RepoRoot 'scripts/export_ig_raw_truth_2233.py') --expected-head $ExpectedHead
    if ($LASTEXITCODE -ne 0) { throw 'EXPORT_FAILED' }
    Write-Host 'SUMMARY: SUCCESS; upload .runtime/ig_raw_truth_2233_attempt_03_originals.zip'
    exit 0
} catch {
    Write-Host 'SUMMARY: BLOCKED / FAIL_CLOSED; original evidence retained; execution disabled'
    exit 2
}
