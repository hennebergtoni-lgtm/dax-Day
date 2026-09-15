param(
    [Parameter(Mandatory = $true)]
    [string]$ExpectedHead,
    [string]$Namespace = '.runtime/ig_raw_m5_truth_2233_v2_attempt_03',
    [string]$CredentialsFile = 'C:\Users\Mandy\ig_demo.env',
    [string]$PythonExecutable = 'python'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
try {
    $repoRoot = Split-Path -Parent $PSScriptRoot
    Set-Location -LiteralPath $repoRoot
    $runner = Join-Path $PSScriptRoot 'run_ig_raw_truth_2233.py'
    & $PythonExecutable $runner --expected-head $ExpectedHead --namespace $Namespace --credentials-file $CredentialsFile
    exit $LASTEXITCODE
} catch {
    Write-Host 'FINAL STATUS: ABORTED_FAIL_CLOSED'
    Write-Host 'error_code: RAW_WINDOWS_LAUNCH_FAILED'
    exit 2
}
