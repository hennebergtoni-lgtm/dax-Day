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
            throw "ASSERT_WRONG_ERROR:$Expected`:OBSERVED_$observed"
        }
    }
}

$command = { [pscustomobject]@{ Source = $PSHOME + [IO.Path]::DirectorySeparatorChar + 'pwsh' } }
$identity = { param($Path) return [string]$Path }
$exists = { param($Path) return $true }

Assert-Code 'PYTHON_COMMAND_DISCOVERY_FAILED' {
    Resolve-DaxHostPython python @{ GetCommand = { throw [InvalidOperationException]::new('secret') } }
}
Assert-Code 'PYTHON_COMMAND_RESULT_NULL' {
    Resolve-DaxHostPython python @{ GetCommand = { return $null } }
}
Assert-Code 'PYTHON_COMMAND_RESULT_MULTIPLE' {
    Resolve-DaxHostPython python @{
        GetCommand = { @([pscustomobject]@{ Source = '/a' }, [pscustomobject]@{ Source = '/b' }) }
        FullPath = $identity
    }
}
Assert-Code 'PYTHON_COMMAND_IDENTITY_INVALID' {
    Resolve-DaxHostPython python @{ GetCommand = { [pscustomobject]@{ Source = @(1) } } }
}
Assert-Code 'PYTHON_EXECUTABLE_PATH_FAILED' {
    Resolve-DaxHostPython python @{
        GetCommand = $command
        FullPath = { throw [ArgumentException]::new('secret') }
    }
}
Assert-Code 'PYTHON_EXECUTABLE_CHECK_FAILED' {
    Resolve-DaxHostPython python @{
        GetCommand = $command
        FullPath = $identity
        TestPath = { throw [IO.IOException]::new('secret') }
    }
}
Assert-Code 'PYTHON_EXECUTABLE_NOT_FOUND' {
    Resolve-DaxHostPython python @{ GetCommand = $command; FullPath = $identity; TestPath = { $false } }
}
$selected = Resolve-DaxHostPython python @{
    GetCommand = { @([pscustomobject]@{ Source = '/same' }, [pscustomobject]@{ Source = '/same' }) }
    FullPath = $identity
    TestPath = $exists
}
if ($selected -ne '/same') { throw 'ASSERT_DEDUPLICATION_FAILED' }

$base = @{
    PythonPath = '/python'
    ScriptPath = $modulePath
    Arguments = @()
    SafePayloadCodes = @('PREFLIGHT_REQUIRED_CHECK_FAILED')
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
Assert-Code 'HOST_LANE_PROCESS_EXIT_MISMATCH' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{ ExitCode = 2; Lines = @('{"status":"BLOCKED","error_code":"UNKNOWN"}') } } }
}
Assert-Code 'PREFLIGHT_REQUIRED_CHECK_FAILED' {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
        ExitCode = 2
        Lines = @('{"status":"BLOCKED","error_code":"PREFLIGHT_REQUIRED_CHECK_FAILED","checks":[]}')
    } } }
}
try {
    Invoke-DaxHostJsonProcess @base -Hooks @{ Process = { [pscustomobject]@{
        ExitCode = 2
        Lines = @('{"status":"BLOCKED","error_code":"PREFLIGHT_REQUIRED_CHECK_FAILED","checks":[]}')
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
    Lines = @('{"status":"PASS","error_code":"NONE","checks":[]}')
} } }
if ($success.status -ne 'PASS') { throw 'ASSERT_SUCCESS_SHAPE_FAILED' }

Write-Output 'DAX Windows host lane failure injection: OK'
