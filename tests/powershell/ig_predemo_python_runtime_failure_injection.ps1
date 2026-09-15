$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$modulePath = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) `
    'scripts/ig_predemo_python_runtime.psm1'
Import-Module $modulePath -Force -ErrorAction Stop

function Assert-Code {
    param([string]$Expected, [scriptblock]$Operation)
    try {
        & $Operation
        throw "ASSERT_NO_ERROR:$Expected"
    } catch {
        if ($_.Exception.Message -ne $Expected) {
            throw "ASSERT_WRONG_ERROR:$Expected"
        }
    }
}

$exists = { param($Path) return $true }
$identityPath = { param($Path) return [string]$Path }
$oneCommand = { param($Name) [pscustomobject]@{ Source = '/python/python' } }

Assert-Code 'PYTHON_COMMAND_DISCOVERY_FAILED' {
    Resolve-Step2238PythonRuntime python @{ GetCommand = { throw [InvalidOperationException]::new('secret') } }
}
Assert-Code 'PYTHON_COMMAND_RESULT_NULL' {
    Resolve-Step2238PythonRuntime python @{ GetCommand = { return $null } }
}
Assert-Code 'PYTHON_COMMAND_RESULT_MULTIPLE' {
    Resolve-Step2238PythonRuntime python @{ GetCommand = {
        @([pscustomobject]@{ Source = 'a' }, [pscustomobject]@{ Source = 'b' })
    } }
}
Assert-Code 'PYTHON_COMMAND_IDENTITY_INVALID' {
    Resolve-Step2238PythonRuntime python @{ GetCommand = { [pscustomobject]@{} } }
}
Assert-Code 'PYTHON_COMMAND_IDENTITY_INVALID' {
    Resolve-Step2238PythonRuntime python @{ GetCommand = { [pscustomobject]@{ Source = @('a') } } }
}
Assert-Code 'PYTHON_EXECUTABLE_PATH_FAILED' {
    Resolve-Step2238PythonRuntime python @{
        GetCommand = $oneCommand
        FullPath = { throw [ArgumentException]::new('secret') }
    }
}
Assert-Code 'PYTHON_EXECUTABLE_CHECK_FAILED' {
    Resolve-Step2238PythonRuntime python @{
        GetCommand = $oneCommand
        FullPath = $identityPath
        TestPath = { throw [IO.IOException]::new('secret') }
    }
}

function New-ParityHooks {
    param([scriptblock]$VersionProbe, [scriptblock]$ImportProbe, [scriptblock]$FullPath = $identityPath)
    return @{
        TestPath = $exists
        FullPath = $FullPath
        VersionProbe = $VersionProbe
        ImportProbe = $ImportProbe
    }
}
$validVersion = { [pscustomobject]@{ ExitCode = 0; Lines = @('{"major":3,"minor":11,"executable":"/python/python"}') } }
$validImport = { [pscustomobject]@{ ExitCode = 0; Lines = @('{"daxlab_origin":"/deploy/src/daxlab/__init__.py","runner_origin":"/deploy/scripts/run_ig_predemo_readiness_2238.py"}') } }

Assert-Code 'PYTHON_DEPLOYMENT_PATH_BUILD_FAILED' {
    Test-Step2238PythonRuntimeParity '/python/python' $null @{}
}
Assert-Code 'PYTHON_SCRIPT_CHECK_FAILED' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' @{
        TestPath = { throw [IO.IOException]::new('secret') }
    }
}
Assert-Code 'PYTHON_VERSION_PROBE_LAUNCH_FAILED' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks { throw [InvalidOperationException]::new('secret') } $validImport)
}
Assert-Code 'PYTHON_VERSION_PROBE_RESPONSE_INVALID' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks { [pscustomobject]@{ Lines = @('{}') } } $validImport)
}
Assert-Code 'PYTHON_VERSION_PROBE_OUTPUT_INVALID' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks { [pscustomobject]@{ ExitCode = 0; Lines = @('{}', '{}') } } $validImport)
}
Assert-Code 'PYTHON_VERSION_PROBE_JSON_INVALID' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks { [pscustomobject]@{ ExitCode = 0; Lines = @('{') } } $validImport)
}
Assert-Code 'PYTHON_VERSION_IDENTITY_INVALID' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks { [pscustomobject]@{ ExitCode = 0; Lines = @('{"major":"3","minor":11,"executable":"x"}') } } $validImport)
}
Assert-Code 'PYTHON_IDENTITY_PATH_FAILED' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks $validVersion $validImport { throw [ArgumentException]::new('secret') })
}
Assert-Code 'PYTHON_IMPORT_PROBE_LAUNCH_FAILED' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks $validVersion { throw [InvalidOperationException]::new('secret') })
}
Assert-Code 'PYTHON_IMPORT_PROBE_JSON_INVALID' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks $validVersion { [pscustomobject]@{ ExitCode = 0; Lines = @('bad') } })
}
Assert-Code 'PYTHON_IMPORT_IDENTITY_INVALID' {
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks $validVersion { [pscustomobject]@{ ExitCode = 0; Lines = @('{"daxlab_origin":42}') } })
}
$pathCalls = 0
Assert-Code 'PYTHON_IMPORT_ORIGIN_PATH_FAILED' {
    $countingPath = {
        param($Path)
        $script:pathCalls += 1
        if ($script:pathCalls -ge 3) { throw [ArgumentException]::new('secret') }
        return [string]$Path
    }
    Test-Step2238PythonRuntimeParity '/python/python' '/deploy' `
        (New-ParityHooks $validVersion $validImport $countingPath)
}

$parity = [pscustomobject]@{
    SourceRoot = '/deploy/src'
    ScriptsRoot = '/deploy/scripts'
    CollectorPath = '/deploy/scripts/run_ig_predemo_readiness_2238.py'
}
$collectorArgs = @{
    PythonPath = '/python/python'; Parity = $parity
    ExpectedHead = ('a' * 40); Namespace = '.runtime/test'
    CredentialsFile = '/secret.env'; RuntimeRoot = '/runtime'
    SafeErrorCodes = @('EVIDENCE_INVALID')
}
Assert-Code 'PYTHON_COLLECTOR_START_FAILED' {
    Invoke-Step2238Collector @collectorArgs -Hooks @{ Collector = { throw [InvalidOperationException]::new('secret') } }
}
Assert-Code 'PYTHON_COLLECTOR_RESPONSE_NULL' {
    Invoke-Step2238Collector @collectorArgs -Hooks @{ Collector = { return $null } }
}
Assert-Code 'PYTHON_COLLECTOR_RESPONSE_INVALID' {
    Invoke-Step2238Collector @collectorArgs -Hooks @{ Collector = { [pscustomobject]@{ ExitCode = '0'; Lines = @('{}') } } }
}
Assert-Code 'PYTHON_COLLECTOR_OUTPUT_TYPE_INVALID' {
    Invoke-Step2238Collector @collectorArgs -Hooks @{ Collector = { [pscustomobject]@{ ExitCode = 0; Lines = '{}' } } }
}
Assert-Code 'PYTHON_COLLECTOR_JSON_INVALID' {
    Invoke-Step2238Collector @collectorArgs -Hooks @{ Collector = { [pscustomobject]@{ ExitCode = 0; Lines = @('{') } } }
}
Assert-Code 'PYTHON_COLLECTOR_RESULT_INVALID' {
    Invoke-Step2238Collector @collectorArgs -Hooks @{ Collector = { [pscustomobject]@{ ExitCode = 0; Lines = @('{"status":"SUCCESS"}') } } }
}
Assert-Code 'PYTHON_COLLECTOR_EXIT_MISMATCH' {
    Invoke-Step2238Collector @collectorArgs -Hooks @{ Collector = { [pscustomobject]@{ ExitCode = 2; Lines = @('{"status":"BLOCKED","error_code":"UNKNOWN_CODE"}') } } }
}

Write-Output 'Step2238 Python runtime failure injection: OK'
