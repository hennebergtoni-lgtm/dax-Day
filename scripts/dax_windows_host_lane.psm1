Set-StrictMode -Version Latest

$script:HostLaneCodes = @(
    'PYTHON_COMMAND_DISCOVERY_FAILED', 'PYTHON_COMMAND_RESULT_NULL',
    'PYTHON_COMMAND_RESULT_MULTIPLE', 'PYTHON_COMMAND_IDENTITY_INVALID',
    'PYTHON_EXECUTABLE_PATH_FAILED', 'PYTHON_EXECUTABLE_CHECK_FAILED',
    'PYTHON_EXECUTABLE_NOT_FOUND', 'PYTHON_DISCOVERY_INTERNAL_FAILURE',
    'HOST_LANE_SCRIPT_PATH_FAILED', 'HOST_LANE_SCRIPT_MISSING',
    'HOST_LANE_PROCESS_START_FAILED', 'HOST_LANE_PROCESS_NO_OUTPUT',
    'HOST_LANE_PROCESS_MULTILINE_OUTPUT', 'HOST_LANE_PROCESS_OUTPUT_TYPE_INVALID',
    'HOST_LANE_PROCESS_JSON_INVALID', 'HOST_LANE_PROCESS_RESULT_INVALID',
    'HOST_LANE_PROCESS_EXIT_MISMATCH', 'HOST_LANE_INTERNAL_FAILURE',
    'PREFLIGHT_REQUIRED_CHECK_FAILED', 'PREFLIGHT_INTERNAL_FAILURE',
    'EVIDENCE_PREFLIGHT_PUBLICATION_FAILED'
)

function Throw-HostLaneCode {
    param([Parameter(Mandatory = $true)][string]$Code)
    throw $Code
}

function Get-HostLaneProperty {
    param(
        [object]$Value,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$ErrorCode,
        [ValidateSet('String', 'Integer', 'Enumerable', 'Object')]
        [string]$ExpectedType = 'Object'
    )
    try {
        if ($null -eq $Value) { Throw-HostLaneCode $ErrorCode }
        $property = $Value.PSObject.Properties[$Name]
        if ($null -eq $property -or $null -eq $property.Value) {
            Throw-HostLaneCode $ErrorCode
        }
        $item = $property.Value
        if ($ExpectedType -eq 'String' -and $item -isnot [string]) {
            Throw-HostLaneCode $ErrorCode
        }
        if ($ExpectedType -eq 'Integer' -and $item -isnot [int] -and $item -isnot [long]) {
            Throw-HostLaneCode $ErrorCode
        }
        if ($ExpectedType -eq 'Enumerable' -and
            ($item -is [string] -or $item -isnot [System.Collections.IEnumerable])) {
            Throw-HostLaneCode $ErrorCode
        }
        if ($ExpectedType -eq 'Enumerable') {
            Write-Output -NoEnumerate $item
            return
        }
        return $item
    } catch {
        if ($_.Exception.Message -eq $ErrorCode) { throw }
        Throw-HostLaneCode $ErrorCode
    }
}

function Resolve-DaxHostPython {
    param(
        [Parameter(Mandatory = $true)][string]$PythonExecutable,
        [hashtable]$Hooks = @{}
    )
    try {
        try {
            $commands = @(
                if ($Hooks.ContainsKey('GetCommand')) {
                    $hook = $Hooks['GetCommand']
                    & $hook $PythonExecutable
                } else {
                    Get-Command -Name $PythonExecutable -CommandType Application -All -ErrorAction Stop
                }
            )
        } catch { Throw-HostLaneCode 'PYTHON_COMMAND_DISCOVERY_FAILED' }
        $commands = @($commands | Where-Object { $null -ne $_ })
        if ($commands.Count -eq 0) { Throw-HostLaneCode 'PYTHON_COMMAND_RESULT_NULL' }
        $paths = @()
        foreach ($command in $commands) {
            $source = Get-HostLaneProperty $command 'Source' 'PYTHON_COMMAND_IDENTITY_INVALID' String
            try {
                $full = if ($Hooks.ContainsKey('FullPath')) {
                    $hook = $Hooks['FullPath']
                    & $hook $source
                } else { [System.IO.Path]::GetFullPath($source) }
            } catch { Throw-HostLaneCode 'PYTHON_EXECUTABLE_PATH_FAILED' }
            if ($full -isnot [string] -or [string]::IsNullOrWhiteSpace($full)) {
                Throw-HostLaneCode 'PYTHON_EXECUTABLE_PATH_FAILED'
            }
            if ($paths -notcontains $full) { $paths += $full }
        }
        if ($paths.Count -ne 1) { Throw-HostLaneCode 'PYTHON_COMMAND_RESULT_MULTIPLE' }
        try {
            $exists = if ($Hooks.ContainsKey('TestPath')) {
                $hook = $Hooks['TestPath']
                & $hook $paths[0]
            } else { Test-Path -LiteralPath $paths[0] -PathType Leaf -ErrorAction Stop }
        } catch { Throw-HostLaneCode 'PYTHON_EXECUTABLE_CHECK_FAILED' }
        if ($exists -isnot [bool]) { Throw-HostLaneCode 'PYTHON_EXECUTABLE_CHECK_FAILED' }
        if (!$exists) { Throw-HostLaneCode 'PYTHON_EXECUTABLE_NOT_FOUND' }
        return $paths[0]
    } catch {
        if ($script:HostLaneCodes -contains $_.Exception.Message) { throw }
        Throw-HostLaneCode 'PYTHON_DISCOVERY_INTERNAL_FAILURE'
    }
}

function Invoke-DaxHostJsonProcess {
    param(
        [Parameter(Mandatory = $true)][string]$PythonPath,
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string[]]$SafePayloadCodes,
        [hashtable]$Hooks = @{}
    )
    try {
        try { $fullScript = [System.IO.Path]::GetFullPath($ScriptPath) }
        catch { Throw-HostLaneCode 'HOST_LANE_SCRIPT_PATH_FAILED' }
        try { $exists = Test-Path -LiteralPath $fullScript -PathType Leaf -ErrorAction Stop }
        catch { Throw-HostLaneCode 'HOST_LANE_SCRIPT_MISSING' }
        if (!$exists) { Throw-HostLaneCode 'HOST_LANE_SCRIPT_MISSING' }
        try {
            if ($Hooks.ContainsKey('Process')) {
                $hook = $Hooks['Process']
                $response = & $hook $PythonPath $fullScript $Arguments
            } else {
                $lines = @(& $PythonPath $fullScript @Arguments 2>$null)
                $response = [pscustomobject]@{ ExitCode = $LASTEXITCODE; Lines = $lines }
            }
        } catch { Throw-HostLaneCode 'HOST_LANE_PROCESS_START_FAILED' }
        $exitCode = Get-HostLaneProperty $response 'ExitCode' 'HOST_LANE_PROCESS_RESULT_INVALID' Integer
        $lines = Get-HostLaneProperty $response 'Lines' 'HOST_LANE_PROCESS_RESULT_INVALID' Enumerable
        $array = @($lines)
        if ($array.Count -eq 0) { Throw-HostLaneCode 'HOST_LANE_PROCESS_NO_OUTPUT' }
        if ($array.Count -ne 1) { Throw-HostLaneCode 'HOST_LANE_PROCESS_MULTILINE_OUTPUT' }
        if ($array[0] -isnot [string] -or [string]::IsNullOrWhiteSpace($array[0])) {
            Throw-HostLaneCode 'HOST_LANE_PROCESS_OUTPUT_TYPE_INVALID'
        }
        try { $result = $array[0] | ConvertFrom-Json -ErrorAction Stop }
        catch { Throw-HostLaneCode 'HOST_LANE_PROCESS_JSON_INVALID' }
        $status = Get-HostLaneProperty $result 'status' 'HOST_LANE_PROCESS_RESULT_INVALID' String
        $innerCode = Get-HostLaneProperty $result 'error_code' 'HOST_LANE_PROCESS_RESULT_INVALID' String
        if ($exitCode -eq 0 -and $status -in @('PASS', 'SUCCESS') -and $innerCode -eq 'NONE') {
            return $result
        }
        if ($exitCode -eq 0 -or $SafePayloadCodes -notcontains $innerCode) {
            Throw-HostLaneCode 'HOST_LANE_PROCESS_EXIT_MISMATCH'
        }
        $exception = [System.Exception]::new($innerCode)
        $exception.Data['HostLaneResult'] = $result
        throw $exception
    } catch {
        if ($script:HostLaneCodes -contains $_.Exception.Message -or
            $SafePayloadCodes -contains $_.Exception.Message) { throw }
        Throw-HostLaneCode 'HOST_LANE_INTERNAL_FAILURE'
    }
}

function Write-DaxHostPreflight {
    param([Parameter(Mandatory = $true)][object]$Result)
    try {
        $checks = Get-HostLaneProperty $Result 'checks' 'HOST_LANE_PROCESS_RESULT_INVALID' Enumerable
        $passed = 0
        $failed = 0
        $unknown = 0
        $notRequired = 0
        foreach ($check in @($checks)) {
            $exceptionClass = 'NONE'
            $exceptionProperty = $check.PSObject.Properties['exception_class']
            if ($null -ne $exceptionProperty -and $null -ne $exceptionProperty.Value) {
                if ($exceptionProperty.Value -isnot [string]) {
                    Throw-HostLaneCode 'HOST_LANE_PROCESS_RESULT_INVALID'
                }
                $exceptionClass = [string]$exceptionProperty.Value
            }
            $line = [ordered]@{
                dimension = Get-HostLaneProperty $check 'dimension' 'HOST_LANE_PROCESS_RESULT_INVALID' String
                check = Get-HostLaneProperty $check 'check' 'HOST_LANE_PROCESS_RESULT_INVALID' String
                status = Get-HostLaneProperty $check 'status' 'HOST_LANE_PROCESS_RESULT_INVALID' String
                reason_code = Get-HostLaneProperty $check 'reason_code' 'HOST_LANE_PROCESS_RESULT_INVALID' String
                observed_contract = Get-HostLaneProperty $check 'observed_contract' 'HOST_LANE_PROCESS_RESULT_INVALID' String
                required_contract = Get-HostLaneProperty $check 'required_contract' 'HOST_LANE_PROCESS_RESULT_INVALID' String
                exception_class = $exceptionClass
            }
            if ($line.status -eq 'PASS') { $passed += 1 }
            elseif ($line.status -in @('FAIL', 'BLOCKED')) { $failed += 1 }
            elseif ($line.status -eq 'UNKNOWN') { $unknown += 1 }
            elseif ($line.status -eq 'NOT_REQUIRED') { $notRequired += 1 }
            Write-Host ('PREFLIGHT_ITEM: ' + ($line | ConvertTo-Json -Compress))
        }
        Write-Host ("PREFLIGHT: {0}/{1} PASS; {2} FAIL_OR_BLOCKED; {3} UNKNOWN; {4} NOT_REQUIRED" -f
            $passed, @($checks).Count, $failed, $unknown, $notRequired)
        $namespaceProperty = $Result.PSObject.Properties['diagnostic_namespace']
        $fingerprintProperty = $Result.PSObject.Properties['diagnostic_fingerprint']
        if ($null -ne $namespaceProperty -and $null -ne $namespaceProperty.Value -and
            $null -ne $fingerprintProperty -and $null -ne $fingerprintProperty.Value) {
            Write-Host ("PREFLIGHT_EVIDENCE: namespace={0}; fingerprint={1}" -f
                [string]$namespaceProperty.Value, [string]$fingerprintProperty.Value)
        }
    } catch { Throw-HostLaneCode 'HOST_LANE_PROCESS_RESULT_INVALID' }
}

Export-ModuleMember -Function Resolve-DaxHostPython
Export-ModuleMember -Function Invoke-DaxHostJsonProcess
Export-ModuleMember -Function Write-DaxHostPreflight
