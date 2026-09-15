Set-StrictMode -Version Latest

function Throw-Step2238Code {
    param([Parameter(Mandatory = $true)][string]$Code)
    throw $Code
}

function Get-Step2238Property {
    param(
        [object]$Value,
        [string]$Name,
        [string]$ErrorCode,
        [ValidateSet('Any', 'String', 'Integer', 'Enumerable')]
        [string]$ExpectedType = 'Any'
    )
    try {
        if ($null -eq $Value) { Throw-Step2238Code $ErrorCode }
        $property = $Value.PSObject.Properties[$Name]
        if ($null -eq $property -or $null -eq $property.Value) {
            Throw-Step2238Code $ErrorCode
        }
        if ($ExpectedType -eq 'String' -and $property.Value -isnot [string]) {
            Throw-Step2238Code $ErrorCode
        }
        if ($ExpectedType -eq 'Integer' -and $property.Value -isnot [int] -and
            $property.Value -isnot [long]) {
            Throw-Step2238Code $ErrorCode
        }
        if ($ExpectedType -eq 'Enumerable' -and
            ($property.Value -is [string] -or
             $property.Value -isnot [System.Collections.IEnumerable])) {
            Throw-Step2238Code $ErrorCode
        }
        if ($ExpectedType -eq 'Enumerable') {
            Write-Output -NoEnumerate $property.Value
            return
        }
        return $property.Value
    } catch {
        if ($_.Exception.Message -eq $ErrorCode) { throw }
        Throw-Step2238Code $ErrorCode
    }
}

function Get-Step2238FullPath {
    param([object]$Value, [string]$ErrorCode, [hashtable]$Hooks = @{})
    try {
        if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value)) {
            Throw-Step2238Code $ErrorCode
        }
        $path = if ($Hooks.ContainsKey('FullPath')) {
            $hook = $Hooks['FullPath']
            & $hook $Value
        } else {
            [System.IO.Path]::GetFullPath($Value)
        }
        if ($path -isnot [string] -or [string]::IsNullOrWhiteSpace($path)) {
            Throw-Step2238Code $ErrorCode
        }
        return $path
    } catch {
        if ($_.Exception.Message -eq $ErrorCode) { throw }
        Throw-Step2238Code $ErrorCode
    }
}

function Test-Step2238Leaf {
    param([string]$Path, [string]$ErrorCode, [hashtable]$Hooks = @{})
    try {
        $result = if ($Hooks.ContainsKey('TestPath')) {
            $hook = $Hooks['TestPath']
            & $hook $Path
        } else {
            Test-Path -LiteralPath $Path -PathType Leaf -ErrorAction Stop
        }
        if ($result -isnot [bool]) { Throw-Step2238Code $ErrorCode }
        return $result
    } catch {
        if ($_.Exception.Message -eq $ErrorCode) { throw }
        Throw-Step2238Code $ErrorCode
    }
}

function Resolve-Step2238PythonRuntime {
    param([string]$PythonExecutable, [hashtable]$Hooks = @{})
    try {
        try {
            $commands = @(
                if ($Hooks.ContainsKey('GetCommand')) {
                    $hook = $Hooks['GetCommand']
                    & $hook $PythonExecutable
                } else {
                    Get-Command -Name $PythonExecutable -CommandType Application -ErrorAction Stop
                }
            )
        } catch { Throw-Step2238Code 'PYTHON_COMMAND_DISCOVERY_FAILED' }
        if ($commands.Count -eq 0 -or $null -eq $commands[0]) {
            Throw-Step2238Code 'PYTHON_COMMAND_RESULT_NULL'
        }
        if ($commands.Count -ne 1) { Throw-Step2238Code 'PYTHON_COMMAND_RESULT_MULTIPLE' }
        $source = Get-Step2238Property $commands[0] 'Source' `
            'PYTHON_COMMAND_IDENTITY_INVALID' String
        if ([string]::IsNullOrWhiteSpace($source)) {
            Throw-Step2238Code 'PYTHON_COMMAND_IDENTITY_INVALID'
        }
        $path = Get-Step2238FullPath $source 'PYTHON_EXECUTABLE_PATH_FAILED' $Hooks
        if (!(Test-Step2238Leaf $path 'PYTHON_EXECUTABLE_CHECK_FAILED' $Hooks)) {
            Throw-Step2238Code 'PYTHON_EXECUTABLE_NOT_FOUND'
        }
        return $path
    } catch {
        $known = @(
            'PYTHON_COMMAND_DISCOVERY_FAILED', 'PYTHON_COMMAND_RESULT_NULL',
            'PYTHON_COMMAND_RESULT_MULTIPLE', 'PYTHON_COMMAND_IDENTITY_INVALID',
            'PYTHON_EXECUTABLE_PATH_FAILED', 'PYTHON_EXECUTABLE_CHECK_FAILED',
            'PYTHON_EXECUTABLE_NOT_FOUND'
        )
        if ($known -contains $_.Exception.Message) { throw }
        Throw-Step2238Code 'PYTHON_DISCOVERY_INTERNAL_FAILURE'
    }
}

function Invoke-Step2238Probe {
    param([string]$Kind, [string]$PythonPath, [string]$Program,
          [string[]]$Arguments = @(), [hashtable]$Hooks = @{})
    $errorCode = if ($Kind -eq 'Version') {
        'PYTHON_VERSION_PROBE_LAUNCH_FAILED'
    } else { 'PYTHON_IMPORT_PROBE_LAUNCH_FAILED' }
    try {
        if ($Hooks.ContainsKey($Kind + 'Probe')) {
            $hook = $Hooks[$Kind + 'Probe']
            return & $hook $PythonPath $Program $Arguments
        }
        $lines = @(& $PythonPath -I -S -c $Program @Arguments 2>$null)
        return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Lines = $lines }
    } catch { Throw-Step2238Code $errorCode }
}

function Convert-Step2238ProbeJson {
    param([object]$Response, [string]$Prefix)
    $responseCode = $Prefix + '_RESPONSE_INVALID'
    $outputCode = $Prefix + '_OUTPUT_INVALID'
    $exitCode = Get-Step2238Property $Response 'ExitCode' $responseCode Integer
    $lines = Get-Step2238Property $Response 'Lines' $responseCode Enumerable
    if ($exitCode -ne 0) { Throw-Step2238Code ($Prefix + '_EXIT_FAILED') }
    if ($lines -is [string] -or $lines -isnot [System.Collections.IEnumerable]) {
        Throw-Step2238Code $outputCode
    }
    $array = @($lines)
    if ($array.Count -ne 1 -or $array[0] -isnot [string] -or
        [string]::IsNullOrWhiteSpace($array[0])) {
        Throw-Step2238Code $outputCode
    }
    try { return $array[0] | ConvertFrom-Json -ErrorAction Stop }
    catch { Throw-Step2238Code ($Prefix + '_JSON_INVALID') }
}

function Test-Step2238PythonRuntimeParity {
    param([string]$PythonPath, [string]$DeploymentRoot, [hashtable]$Hooks = @{})
    try {
        try {
            $sourceRoot = Join-Path $DeploymentRoot 'src' -ErrorAction Stop
            $scriptsRoot = Join-Path $DeploymentRoot 'scripts' -ErrorAction Stop
            $collectorPath = Join-Path $scriptsRoot 'run_ig_predemo_readiness_2238.py' -ErrorAction Stop
        } catch { Throw-Step2238Code 'PYTHON_DEPLOYMENT_PATH_BUILD_FAILED' }
        if (!(Test-Step2238Leaf $collectorPath 'PYTHON_SCRIPT_CHECK_FAILED' $Hooks)) {
            Throw-Step2238Code 'PYTHON_SCRIPT_MISSING'
        }
        $versionProgram = 'import json,pathlib,sys;print(json.dumps({' +
            '"major":sys.version_info.major,"minor":sys.version_info.minor,' +
            '"executable":str(pathlib.Path(sys.executable).resolve())},' +
            'separators=(",",":")))'
        $response = Invoke-Step2238Probe -Kind Version -PythonPath $PythonPath `
            -Program $versionProgram -Hooks $Hooks
        $version = Convert-Step2238ProbeJson -Response $response -Prefix 'PYTHON_VERSION_PROBE'
        $major = Get-Step2238Property $version 'major' 'PYTHON_VERSION_IDENTITY_INVALID' Integer
        $minor = Get-Step2238Property $version 'minor' 'PYTHON_VERSION_IDENTITY_INVALID' Integer
        $executable = Get-Step2238Property $version 'executable' 'PYTHON_VERSION_IDENTITY_INVALID' String
        if ($major -ne 3 -or $minor -lt 11) { Throw-Step2238Code 'PYTHON_VERSION_UNSUPPORTED' }
        $expectedExecutable = Get-Step2238FullPath $PythonPath 'PYTHON_IDENTITY_PATH_FAILED' $Hooks
        $observedExecutable = Get-Step2238FullPath $executable 'PYTHON_IDENTITY_PATH_FAILED' $Hooks
        if ($expectedExecutable -ne $observedExecutable) {
            Throw-Step2238Code 'PYTHON_EXECUTABLE_IDENTITY_MISMATCH'
        }
        $importProgram = @'
import importlib, json, pathlib, sys
src = pathlib.Path(sys.argv[1]).resolve()
scripts = pathlib.Path(sys.argv[2]).resolve()
sys.path[:0] = [str(src), str(scripts)]
daxlab = importlib.import_module("daxlab")
runner = importlib.import_module("run_ig_predemo_readiness_2238")
print(json.dumps({"daxlab_origin": str(pathlib.Path(daxlab.__file__).resolve()),
"runner_origin": str(pathlib.Path(runner.__file__).resolve())}, separators=(",", ":")))
'@
        $response = Invoke-Step2238Probe -Kind Import -PythonPath $PythonPath `
            -Program $importProgram -Arguments @($sourceRoot, $scriptsRoot) -Hooks $Hooks
        $identity = Convert-Step2238ProbeJson -Response $response -Prefix 'PYTHON_IMPORT_PROBE'
        $daxlabOrigin = Get-Step2238Property $identity 'daxlab_origin' 'PYTHON_IMPORT_IDENTITY_INVALID' String
        $runnerOrigin = Get-Step2238Property $identity 'runner_origin' 'PYTHON_IMPORT_IDENTITY_INVALID' String
        try {
            $separator = [System.IO.Path]::DirectorySeparatorChar
            $expectedDaxlab = Get-Step2238FullPath (Join-Path $sourceRoot 'daxlab') 'PYTHON_IMPORT_ORIGIN_PATH_FAILED' $Hooks
            $expectedDaxlab = $expectedDaxlab.TrimEnd($separator) + $separator
            $observedDaxlab = Get-Step2238FullPath $daxlabOrigin 'PYTHON_IMPORT_ORIGIN_PATH_FAILED' $Hooks
            $expectedRunner = Get-Step2238FullPath $collectorPath 'PYTHON_IMPORT_ORIGIN_PATH_FAILED' $Hooks
            $observedRunner = Get-Step2238FullPath $runnerOrigin 'PYTHON_IMPORT_ORIGIN_PATH_FAILED' $Hooks
            $daxlabMatches = $observedDaxlab.StartsWith($expectedDaxlab, [StringComparison]::OrdinalIgnoreCase)
        } catch {
            if ($_.Exception.Message -eq 'PYTHON_IMPORT_ORIGIN_PATH_FAILED') { throw }
            Throw-Step2238Code 'PYTHON_IMPORT_ORIGIN_COMPARE_FAILED'
        }
        if (!$daxlabMatches -or $observedRunner -ne $expectedRunner) {
            Throw-Step2238Code 'PYTHON_IMPORT_ORIGIN_MISMATCH'
        }
        return [pscustomobject]@{ SourceRoot = $sourceRoot; ScriptsRoot = $scriptsRoot; CollectorPath = $collectorPath }
    } catch {
        if ($_.Exception.Message -like 'PYTHON_*') { throw }
        Throw-Step2238Code 'PYTHON_PARITY_INTERNAL_FAILURE'
    }
}

function Invoke-Step2238Collector {
    param([string]$PythonPath, [object]$Parity, [string]$ExpectedHead,
          [string]$Namespace, [string]$CredentialsFile, [string]$RuntimeRoot,
          [string[]]$SafeErrorCodes, [hashtable]$Hooks = @{})
    try {
        $sourceRoot = Get-Step2238Property $Parity 'SourceRoot' 'PYTHON_COLLECTOR_PATHS_INVALID' String
        $scriptsRoot = Get-Step2238Property $Parity 'ScriptsRoot' 'PYTHON_COLLECTOR_PATHS_INVALID' String
        $collectorPath = Get-Step2238Property $Parity 'CollectorPath' 'PYTHON_COLLECTOR_PATHS_INVALID' String
        $bootstrap = @'
import pathlib, runpy, sys
src = pathlib.Path(sys.argv.pop(1)).resolve()
scripts = pathlib.Path(sys.argv.pop(1)).resolve()
collector = pathlib.Path(sys.argv.pop(1)).resolve()
sys.path[:0] = [str(src), str(scripts)]
sys.argv[0] = str(collector)
runpy.run_path(str(collector), run_name="__main__")
'@
        try {
            if ($Hooks.ContainsKey('Collector')) {
                $hook = $Hooks['Collector']
                $response = & $hook
            }
            else {
                $lines = @(& $PythonPath -I -S -c $bootstrap $sourceRoot $scriptsRoot $collectorPath --expected-head $ExpectedHead --namespace $Namespace --credentials-file $CredentialsFile --runtime-root $RuntimeRoot 2>$null)
                $response = [pscustomobject]@{ ExitCode = $LASTEXITCODE; Lines = $lines }
            }
        } catch { Throw-Step2238Code 'PYTHON_COLLECTOR_START_FAILED' }
        if ($null -eq $response) { Throw-Step2238Code 'PYTHON_COLLECTOR_RESPONSE_NULL' }
        $exitCode = Get-Step2238Property $response 'ExitCode' 'PYTHON_COLLECTOR_RESPONSE_INVALID' Integer
        $lines = Get-Step2238Property $response 'Lines' 'PYTHON_COLLECTOR_RESPONSE_INVALID' Enumerable
        $array = @($lines)
        if ($array.Count -eq 0) { Throw-Step2238Code 'PYTHON_COLLECTOR_NO_OUTPUT' }
        if ($array.Count -ne 1) { Throw-Step2238Code 'PYTHON_COLLECTOR_MULTILINE_OUTPUT' }
        if ($array[0] -isnot [string] -or [string]::IsNullOrWhiteSpace($array[0])) {
            Throw-Step2238Code 'PYTHON_COLLECTOR_OUTPUT_TYPE_INVALID'
        }
        try { $result = $array[0] | ConvertFrom-Json -ErrorAction Stop }
        catch { Throw-Step2238Code 'PYTHON_COLLECTOR_JSON_INVALID' }
        $status = Get-Step2238Property $result 'status' 'PYTHON_COLLECTOR_RESULT_INVALID' String
        $innerCode = Get-Step2238Property $result 'error_code' 'PYTHON_COLLECTOR_RESULT_INVALID' String
        if ($exitCode -eq 0 -and $status -eq 'SUCCESS') {
            $null = Get-Step2238Property $result 'namespace' 'PYTHON_COLLECTOR_RESULT_INVALID' String
            return $result
        }
        if ($exitCode -eq 0 -or $SafeErrorCodes -notcontains $innerCode) {
            Throw-Step2238Code 'PYTHON_COLLECTOR_EXIT_MISMATCH'
        }
        Throw-Step2238Code $innerCode
    } catch {
        if ($_.Exception.Message -like 'PYTHON_*' -or $SafeErrorCodes -contains $_.Exception.Message) { throw }
        Throw-Step2238Code 'PYTHON_COLLECTOR_INTERNAL_FAILURE'
    }
}

Export-ModuleMember -Function Resolve-Step2238PythonRuntime
Export-ModuleMember -Function Test-Step2238PythonRuntimeParity
Export-ModuleMember -Function Invoke-Step2238Collector
