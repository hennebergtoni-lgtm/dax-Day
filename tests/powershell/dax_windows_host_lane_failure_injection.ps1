$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$modulePath = Join-Path $repoRoot 'scripts/dax_windows_host_lane.psm1'
Import-Module $modulePath -Force -ErrorAction Stop

function Assert-Code {
    param([string]$Expected, [scriptblock]$Operation)
    try {
        & $Operation
        throw "ASSERT_NO_ERROR:$Expected"
    } catch {
        $observed = if ($_.Exception.Data.Contains('HostLaneCode')) {
            [string]$_.Exception.Data['HostLaneCode']
        } elseif ($_.Exception.Message -match '^[A-Z][A-Z0-9_]+$') {
            [string]$_.Exception.Message
        } else {
            'CLASS_' + $_.Exception.GetType().Name
        }
        if ($observed -ne $Expected) {
            $candidateDetail = if ($_.Exception.Data.Contains('PythonSelectionCandidates')) {
                ($_.Exception.Data['PythonSelectionCandidates'] | ConvertTo-Json -Compress -Depth 4)
            } else { 'NONE' }
            throw "ASSERT_WRONG_ERROR:$Expected`:OBSERVED_$observed`:CANDIDATES_$candidateDetail"
        }
    }
}

$deploymentRoot = $repoRoot
$identity = { param($Path) return [string]$Path }
$exists = { param($Path) return $true }
$resolveBase = @{
    PythonExecutable = 'python'
    DeploymentRoot = $deploymentRoot
    PowerShellArchitecture = if ([Environment]::Is64BitProcess) { '64_BIT' } else { '32_BIT' }
}

function New-ProbeResponse {
    param(
        [string]$Identity,
        [string]$Executable = '',
        [string]$Version = '3.11.9',
        [string]$Architecture = '',
        [string]$Status = 'PASS',
        [string]$ErrorCode = 'NONE'
    )
    if (!$Executable) { $Executable = Join-Path $repoRoot 'canonical-python.exe' }
    if (!$Architecture) { $Architecture = $resolveBase.PowerShellArchitecture }
    $payload = [ordered]@{
        status = $Status; error_code = $ErrorCode; executable_path = $Executable
        executable_basename = 'python.exe'; identity_fingerprint = $Identity
        executable_path_fingerprint = ('b' * 64)
        version = $Version; architecture = $Architecture
        project_origin = 'EXACT_DEPLOYMENT_SRC'; collector_origin = 'EXACT_DEPLOYMENT_SCRIPT'
        execution_capability = 'NONE'; order_execution_enabled = $false
    } | ConvertTo-Json -Compress
    return [pscustomobject]@{ ExitCode = if ($Status -eq 'PASS') { 0 } else { 2 }; Lines = @($payload) }
}

Assert-Code 'PYTHON_COMMAND_DISCOVERY_FAILED' {
    Resolve-DaxHostPython @resolveBase -Hooks @{
        GetCommand = { throw [InvalidOperationException]::new('secret') }
    }
}
Assert-Code 'PYTHON_COMMAND_RESULT_NULL' {
    Resolve-DaxHostPython @resolveBase -Hooks @{ GetCommand = { return $null } }
}
Assert-Code 'PYTHON_RUNTIME_AMBIGUOUS' {
    Resolve-DaxHostPython @resolveBase -Hooks @{
        GetCommand = {
            param($Name)
            if ($Name -eq 'python') {
                return @([pscustomobject]@{ Source = '/a/python.exe' },
                         [pscustomobject]@{ Source = '/b/python.exe' })
            }
            throw 'NOT_FOUND'
        }
        FullPath = $identity; TestPath = $exists
        Probe = {
            param($Item)
            $identityValue = if ($Item.Source -match '/a/') { 'a' * 64 } else { 'b' * 64 }
            New-ProbeResponse -Identity $identityValue `
                -Executable (Join-Path $repoRoot ($identityValue.Substring(0, 1) + '-python.exe'))
        }
    }
}
Assert-Code 'PYTHON_RUNTIME_NO_VALID_CANDIDATE' {
    Resolve-DaxHostPython @resolveBase -Hooks @{
        GetCommand = {
            param($Name)
            if ($Name -eq 'python') { return [pscustomobject]@{ Source = @(1) } }
            throw 'NOT_FOUND'
        }
    }
}
Assert-Code 'PYTHON_RUNTIME_NO_VALID_CANDIDATE' {
    Resolve-DaxHostPython @resolveBase -Hooks @{
        GetCommand = {
            param($Name)
            if ($Name -eq 'python') { return [pscustomobject]@{ Source = '/bad-path' } }
            throw 'NOT_FOUND'
        }
        FullPath = { throw [ArgumentException]::new('secret') }
    }
}
Assert-Code 'PYTHON_RUNTIME_NO_VALID_CANDIDATE' {
    Resolve-DaxHostPython @resolveBase -Hooks @{
        GetCommand = {
            param($Name)
            if ($Name -eq 'python') { return [pscustomobject]@{ Source = '/missing' } }
            throw 'NOT_FOUND'
        }
        FullPath = $identity; TestPath = { $false }
    }
}

# python + python.exe resolving to one interpreter is one identity, not ambiguity.
$selected = Resolve-DaxHostPython @resolveBase -Hooks @{
    GetCommand = {
        param($Name)
        if ($Name -in @('python', 'python.exe')) {
            return [pscustomobject]@{ Source = '/same/python.exe' }
        }
        throw 'NOT_FOUND'
    }
    FullPath = $identity; TestPath = $exists
    Probe = { New-ProbeResponse -Identity ('a' * 64) }
}
if ($selected.IdentityFingerprint -ne ('a' * 64)) { throw 'ASSERT_PYTHON_EXE_SAME_FAILED' }

# python and py may be different launchers for the same real sys.executable.
$selected = Resolve-DaxHostPython @resolveBase -Hooks @{
    GetCommand = {
        param($Name)
        if ($Name -eq 'python') { return [pscustomobject]@{ Source = '/bin/python.exe' } }
        if ($Name -eq 'py') { return [pscustomobject]@{ Source = '/bin/py.exe' } }
        throw 'NOT_FOUND'
    }
    FullPath = $identity; TestPath = $exists
    Probe = { New-ProbeResponse -Identity ('a' * 64) -Executable (Join-Path $repoRoot 'real-python.exe') }
}
if ($selected.IdentityFingerprint -ne ('a' * 64)) { throw 'ASSERT_PY_LAUNCHER_SAME_FAILED' }

# Repeated PATH entries for the same application are de-duplicated before probing.
$probeCalls = 0
$selected = Resolve-DaxHostPython @resolveBase -Hooks @{
    GetCommand = {
        param($Name)
        if ($Name -eq 'python') {
            return @([pscustomobject]@{ Source = '/same/python.exe' },
                     [pscustomobject]@{ Source = '/same/python.exe' })
        }
        throw 'NOT_FOUND'
    }
    FullPath = $identity; TestPath = $exists
    Probe = { $script:probeCalls += 1; New-ProbeResponse -Identity ('a' * 64) }
}
if ($probeCalls -ne 1) { throw 'ASSERT_PATH_DEDUPLICATION_FAILED' }

# A Microsoft Store alias is never started when another valid runtime exists.
$storeProbeCalled = $false
$selected = Resolve-DaxHostPython @resolveBase -Hooks @{
    GetCommand = {
        param($Name)
        if ($Name -eq 'python') {
            return @(
                [pscustomobject]@{ Source = 'C:\Users\runner\AppData\Local\Microsoft\WindowsApps\python.exe' },
                [pscustomobject]@{ Source = 'C:\Python311\python.exe' }
            )
        }
        throw 'NOT_FOUND'
    }
    FullPath = $identity; TestPath = $exists
    Probe = {
        param($Item)
        if ($Item.Source -match 'WindowsApps') { $script:storeProbeCalled = $true }
        New-ProbeResponse -Identity ('a' * 64) -Executable (Join-Path $repoRoot 'python311.exe')
    }
}
if ($storeProbeCalled) { throw 'ASSERT_STORE_ALIAS_WAS_STARTED' }

# A wrong version is rejected; the only valid identity is selected.
$selected = Resolve-DaxHostPython @resolveBase -Hooks @{
    GetCommand = {
        param($Name)
        if ($Name -eq 'python') {
            return @([pscustomobject]@{ Source = '/old/python.exe' },
                     [pscustomobject]@{ Source = '/good/python.exe' })
        }
        throw 'NOT_FOUND'
    }
    FullPath = $identity; TestPath = $exists
    Probe = {
        param($Item)
        if ($Item.Source -match '/old/') {
            return New-ProbeResponse -Identity ('b' * 64) -Status 'BLOCKED' `
                -ErrorCode 'PYTHON_CANDIDATE_VERSION_UNSUPPORTED'
        }
        New-ProbeResponse -Identity ('a' * 64) -Executable (Join-Path $repoRoot 'good-python.exe')
    }
}
if ($selected.IdentityFingerprint -ne ('a' * 64)) { throw 'ASSERT_ONLY_VALID_FAILED' }

# A valid configured python family outranks a different valid fallback py runtime.
$selected = Resolve-DaxHostPython @resolveBase -Hooks @{
    GetCommand = {
        param($Name)
        if ($Name -eq 'python') { return [pscustomobject]@{ Source = '/preferred/python.exe' } }
        if ($Name -eq 'py') { return [pscustomobject]@{ Source = '/fallback/py.exe' } }
        throw 'NOT_FOUND'
    }
    FullPath = $identity; TestPath = $exists
    Probe = {
        param($Item)
        $identityValue = if ($Item.Resolver -eq 'python') { 'a' * 64 } else { 'b' * 64 }
        New-ProbeResponse -Identity $identityValue `
            -Executable (Join-Path $repoRoot ($Item.Resolver + '-python.exe'))
    }
}
if ($selected.ResolverRank -ne 0 -or $selected.IdentityFingerprint -ne ('a' * 64)) {
    throw 'ASSERT_CANONICAL_PREFERENCE_FAILED'
}

$base = @{
    PythonPath = '/python'
    ScriptPath = $modulePath
    Arguments = @()
    SafePayloadCodes = @(
        'PREFLIGHT_REQUIRED_CHECK_FAILED',
        'IG_SESSION_READ_FAILED_NO_RETRY',
        'IG_READINESS_MATRIX_INCOMPLETE'
    )
}
Assert-Code 'HOST_LANE_PROCESS_START_FAILED' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { throw [InvalidOperationException]::new('secret') } }
}
$badPathBase = $base.Clone()
$badPathBase.Remove('ScriptPath')
Assert-Code 'HOST_LANE_SCRIPT_PATH_FAILED' {
    Invoke-DaxHostJsonProcess @badPathBase -ScriptPath ([string][char]0) -Hooks @{ Process = { throw 'UNREACHED' } }
}
Assert-Code 'HOST_LANE_PROCESS_NO_OUTPUT' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{ ExitCode = 0; Lines = @() } } }
}
Assert-Code 'HOST_LANE_PROCESS_MULTILINE_OUTPUT' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{ ExitCode = 0; Lines = @('{}', '{}') } } }
}
Assert-Code 'HOST_LANE_PROCESS_RESULT_INVALID' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{ ExitCode = '0'; Lines = @('{}') } } }
}
Assert-Code 'HOST_LANE_PROCESS_OUTPUT_TYPE_INVALID' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{ ExitCode = 0; Lines = @(42) } } }
}
Assert-Code 'HOST_LANE_PROCESS_JSON_INVALID' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{ ExitCode = 0; Lines = @('{') } } }
}
Assert-Code 'HOST_LANE_PROCESS_RESULT_INVALID' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{ ExitCode = 0; Lines = @('{"status":"PASS"}') } } }
}
try {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
        ExitCode = 2
        Lines = @('{"status":"BLOCKED","error_code":"IG_READINESS_MATRIX_INCOMPLETE","failure_phase":"READ","readiness_matrix_counts":{"PASS":6,"FAIL":1,"BLOCKED":0,"UNKNOWN":1},"execution_capability":"NONE","order_execution_enabled":false}')
    } } }
    throw 'ASSERT_NO_ERROR:READINESS_MATRIX_RESULT'
} catch {
    if ($_.Exception.Message -ne 'IG_READINESS_MATRIX_INCOMPLETE' -or
        !$_.Exception.Data.Contains('HostLaneResult') -or
        [int]$_.Exception.Data['HostLaneResult'].readiness_matrix_counts.PASS -ne 6) {
        throw 'ASSERT_READINESS_MATRIX_RESULT_NOT_PRESERVED'
    }
}
Assert-Code 'HOST_LANE_PROCESS_EXIT_MISMATCH' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{ ExitCode = 2; Lines = @('{"status":"BLOCKED","error_code":"UNKNOWN","execution_capability":"NONE","order_execution_enabled":false}') } } }
}
Assert-Code 'PREFLIGHT_REQUIRED_CHECK_FAILED' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
        ExitCode = 2
        Lines = @('{"status":"BLOCKED","error_code":"PREFLIGHT_REQUIRED_CHECK_FAILED","checks":[],"execution_capability":"NONE","order_execution_enabled":false}')
    } } }
}
try {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
        ExitCode = 0
        Lines = @('{"status":"BLOCKED","error_code":"IG_SESSION_READ_FAILED_NO_RETRY","execution_capability":"NONE","order_execution_enabled":false}')
    } } }
    throw 'ASSERT_NO_ERROR:FAIL_JSON_EXIT_ZERO'
} catch {
    if ($_.Exception.Message -ne 'IG_SESSION_READ_FAILED_NO_RETRY' -or
        [string]$_.Exception.Data['HostLaneProcessExitContract'] -ne
            'FAILURE_PAYLOAD_EXIT_ZERO') {
        throw 'ASSERT_FAIL_JSON_EXIT_ZERO_NOT_PRESERVED'
    }
}
try {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
        ExitCode = 2
        Lines = @('{"status":"BLOCKED","error_code":"IG_SESSION_READ_FAILED_NO_RETRY","execution_capability":"NONE","order_execution_enabled":false}')
    } } }
    throw 'ASSERT_NO_ERROR:FAIL_JSON_EXIT_NONZERO'
} catch {
    if ($_.Exception.Message -ne 'IG_SESSION_READ_FAILED_NO_RETRY' -or
        [string]$_.Exception.Data['HostLaneProcessExitContract'] -ne
            'FAILURE_EXIT_MATCH') {
        throw 'ASSERT_FAIL_JSON_EXIT_NONZERO_NOT_PRESERVED'
    }
}
Assert-Code 'HOST_LANE_PROCESS_EXIT_MISMATCH' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
        ExitCode = 2
        Lines = @('{"status":"SUCCESS","error_code":"NONE","execution_capability":"NONE","order_execution_enabled":false}')
    } } }
}
try {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
        ExitCode = 2
        Lines = @('{"status":"BLOCKED","error_code":"PREFLIGHT_REQUIRED_CHECK_FAILED","checks":[],"execution_capability":"NONE","order_execution_enabled":false}')
    } } }
    throw 'ASSERT_NO_ERROR:PREFLIGHT_RESULT_RETAINED'
} catch {
    if ($_.Exception.Message -ne 'PREFLIGHT_REQUIRED_CHECK_FAILED' -or
        !$_.Exception.Data.Contains('HostLaneResult')) {
        throw 'ASSERT_PREFLIGHT_RESULT_NOT_RETAINED'
    }
}
$success = Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
    ExitCode = 0
    Lines = @('{"status":"PASS","error_code":"NONE","checks":[],"execution_capability":"NONE","order_execution_enabled":false}')
} } }
if ($success.status -ne 'PASS') { throw 'ASSERT_SUCCESS_SHAPE_FAILED' }

Write-Output 'DAX Windows host lane failure injection: OK'
