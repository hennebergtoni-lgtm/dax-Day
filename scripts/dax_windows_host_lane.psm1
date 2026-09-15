Set-StrictMode -Version Latest

$script:HostLaneCodes = @(
    'PYTHON_COMMAND_DISCOVERY_FAILED', 'PYTHON_COMMAND_RESULT_NULL',
    'PYTHON_COMMAND_RESULT_MULTIPLE', 'PYTHON_COMMAND_IDENTITY_INVALID',
    'PYTHON_EXECUTABLE_PATH_FAILED', 'PYTHON_EXECUTABLE_CHECK_FAILED',
    'PYTHON_EXECUTABLE_NOT_FOUND', 'PYTHON_DISCOVERY_INTERNAL_FAILURE',
    'PYTHON_RUNTIME_NO_VALID_CANDIDATE', 'PYTHON_RUNTIME_AMBIGUOUS',
    'PYTHON_RUNTIME_PROBE_MISSING', 'PYTHON_RUNTIME_SELECTION_INVALID',
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
    $exception = [System.Exception]::new($Code)
    $exception.Data['HostLaneCode'] = $Code
    throw $exception
}

function Throw-HostLaneSelectionCode {
    param(
        [Parameter(Mandatory = $true)][string]$Code,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Candidates
    )
    $exception = [System.Exception]::new($Code)
    $exception.Data['HostLaneCode'] = $Code
    $exception.Data['PythonSelectionCandidates'] = $Candidates
    throw $exception
}

function Test-HostLaneCode {
    param([Parameter(Mandatory = $true)][object]$Exception)
    try {
        if ($Exception.Data.Contains('HostLaneCode')) {
            return $script:HostLaneCodes -contains [string]$Exception.Data['HostLaneCode']
        }
        return $script:HostLaneCodes -contains [string]$Exception.Message
    } catch {
        return $false
    }
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
        [Parameter(Mandatory = $true)][string]$DeploymentRoot,
        [Parameter(Mandatory = $true)][ValidateSet('32_BIT', '64_BIT')]
        [string]$PowerShellArchitecture,
        [hashtable]$Hooks = @{}
    )
    try {
        $configuredLeaf = try { [System.IO.Path]::GetFileName($PythonExecutable) }
        catch { Throw-HostLaneCode 'PYTHON_COMMAND_IDENTITY_INVALID' }
        $configuredStem = [System.IO.Path]::GetFileNameWithoutExtension($configuredLeaf).ToLowerInvariant()
        $specifications = @()
        $configuredIsPath = try { [System.IO.Path]::IsPathRooted($PythonExecutable) }
        catch { Throw-HostLaneCode 'PYTHON_COMMAND_IDENTITY_INVALID' }
        if ($configuredIsPath) {
            $specifications += [pscustomobject]@{ Name = $PythonExecutable; Rank = 0; Arguments = @() }
        } elseif ($configuredStem -eq 'python') {
            $specifications += [pscustomobject]@{ Name = 'python'; Rank = 0; Arguments = @() }
            $specifications += [pscustomobject]@{ Name = 'python.exe'; Rank = 0; Arguments = @() }
            $specifications += [pscustomobject]@{ Name = 'py'; Rank = 1; Arguments = @('-3') }
            $specifications += [pscustomobject]@{ Name = 'py.exe'; Rank = 1; Arguments = @('-3') }
        } elseif ($configuredStem -eq 'py') {
            $specifications += [pscustomobject]@{ Name = 'py'; Rank = 0; Arguments = @('-3') }
            $specifications += [pscustomobject]@{ Name = 'py.exe'; Rank = 0; Arguments = @('-3') }
            $specifications += [pscustomobject]@{ Name = 'python'; Rank = 1; Arguments = @() }
            $specifications += [pscustomobject]@{ Name = 'python.exe'; Rank = 1; Arguments = @() }
        } else {
            $specifications += [pscustomobject]@{ Name = $PythonExecutable; Rank = 0; Arguments = @() }
        }
        $probePath = try {
            [System.IO.Path]::GetFullPath((Join-Path $DeploymentRoot 'scripts/dax_windows_python_runtime_probe.py'))
        } catch { Throw-HostLaneCode 'PYTHON_EXECUTABLE_PATH_FAILED' }
        try { $probePresent = Test-Path -LiteralPath $probePath -PathType Leaf -ErrorAction Stop }
        catch { Throw-HostLaneCode 'PYTHON_RUNTIME_PROBE_MISSING' }
        if (!$probePresent) { Throw-HostLaneCode 'PYTHON_RUNTIME_PROBE_MISSING' }

        $discoverySucceeded = $false
        $discovered = @()
        $discoveryMatrix = @()
        $rawCommandCount = 0
        foreach ($specification in $specifications) {
            try {
                $commands = @(
                    if ($Hooks.ContainsKey('GetCommand')) {
                        $hook = $Hooks['GetCommand']
                        & $hook $specification.Name
                    } else {
                        Get-Command -Name $specification.Name -CommandType Application -All -ErrorAction Stop
                    }
                )
                $discoverySucceeded = $true
            } catch {
                continue
            }
            foreach ($command in @($commands | Where-Object { $null -ne $_ })) {
                $rawCommandCount += 1
                try {
                    $source = Get-HostLaneProperty $command 'Source' 'PYTHON_COMMAND_IDENTITY_INVALID' String
                    $full = if ($Hooks.ContainsKey('FullPath')) {
                        $hook = $Hooks['FullPath']
                        & $hook $source
                    } else { [System.IO.Path]::GetFullPath($source) }
                    if ($full -isnot [string] -or [string]::IsNullOrWhiteSpace($full)) {
                        Throw-HostLaneCode 'PYTHON_EXECUTABLE_PATH_FAILED'
                    }
                    $discovered += [pscustomobject]@{
                        Resolver = $specification.Name
                        Rank = [int]$specification.Rank
                        Source = $full
                        Arguments = @($specification.Arguments)
                    }
                } catch {
                    $reason = if ($_.Exception.Message -eq 'PYTHON_COMMAND_IDENTITY_INVALID') {
                        'PYTHON_CANDIDATE_COMMAND_IDENTITY_INVALID'
                    } else { 'PYTHON_CANDIDATE_PATH_RESOLUTION_FAILED' }
                    $discoveryMatrix += [pscustomobject]@{
                        resolver = $specification.Name; resolver_rank = [int]$specification.Rank
                        status = 'REJECTED'; reason_code = $reason
                        identity_fingerprint = 'NONE'; executable_basename = 'REDACTED'
                        version = 'UNKNOWN'; architecture = 'UNKNOWN'
                    }
                }
            }
        }
        if (!$discoverySucceeded) { Throw-HostLaneCode 'PYTHON_COMMAND_DISCOVERY_FAILED' }
        if ($rawCommandCount -eq 0) { Throw-HostLaneCode 'PYTHON_COMMAND_RESULT_NULL' }

        $launchers = @{}
        foreach ($item in $discovered) {
            $key = $item.Source.ToLowerInvariant() + '|' + (@($item.Arguments) -join ' ')
            if (!$launchers.ContainsKey($key) -or $item.Rank -lt $launchers[$key].Rank) {
                $launchers[$key] = $item
            }
        }
        $matrix = @($discoveryMatrix)
        $valid = @()
        foreach ($item in @($launchers.Values)) {
            $candidateKey = $item.Source.ToLowerInvariant() + '|' + (@($item.Arguments) -join ' ')
            $reason = 'NONE'
            $probe = $null
            if ($item.Source -match '(?i)[\\/]Microsoft[\\/]WindowsApps[\\/]') {
                $reason = 'PYTHON_CANDIDATE_STORE_ALIAS_REJECTED'
            } else {
                try {
                    $exists = if ($Hooks.ContainsKey('TestPath')) {
                        $hook = $Hooks['TestPath']
                        & $hook $item.Source
                    } else { Test-Path -LiteralPath $item.Source -PathType Leaf -ErrorAction Stop }
                    if ($exists -isnot [bool]) { $reason = 'PYTHON_CANDIDATE_PATH_CHECK_FAILED' }
                    elseif (!$exists) { $reason = 'PYTHON_CANDIDATE_NOT_FOUND' }
                } catch { $reason = 'PYTHON_CANDIDATE_PATH_CHECK_FAILED' }
            }
            if ($reason -eq 'NONE') {
                try {
                    if ($Hooks.ContainsKey('Probe')) {
                        $hook = $Hooks['Probe']
                        $response = & $hook $item $probePath $DeploymentRoot $PowerShellArchitecture
                    } else {
                        $probeArguments = @($item.Arguments) + @(
                            '-B', $probePath, '--deployment-root', $DeploymentRoot,
                            '--powershell-architecture', $PowerShellArchitecture
                        )
                        $lines = @(& $item.Source @probeArguments 2>$null)
                        $response = [pscustomobject]@{ ExitCode = $LASTEXITCODE; Lines = $lines }
                    }
                    $exitCode = Get-HostLaneProperty $response 'ExitCode' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' Integer
                    $rawLines = Get-HostLaneProperty $response 'Lines' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' Enumerable
                    $lines = @($rawLines)
                    if ($lines.Count -eq 0) { $reason = 'PYTHON_CANDIDATE_PROBE_NO_OUTPUT' }
                    elseif ($lines.Count -ne 1 -or $lines[0] -isnot [string]) {
                        $reason = 'PYTHON_CANDIDATE_PROBE_OUTPUT_INVALID'
                    } else {
                        try { $probe = $lines[0] | ConvertFrom-Json -ErrorAction Stop }
                        catch { $reason = 'PYTHON_CANDIDATE_PROBE_JSON_INVALID' }
                    }
                    if ($reason -eq 'NONE') {
                        $status = Get-HostLaneProperty $probe 'status' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                        $innerCode = Get-HostLaneProperty $probe 'error_code' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                        if ($status -eq 'PASS' -and $innerCode -eq 'NONE' -and $exitCode -eq 0) {
                            $path = Get-HostLaneProperty $probe 'executable_path' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $identity = Get-HostLaneProperty $probe 'identity_fingerprint' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $basename = Get-HostLaneProperty $probe 'executable_basename' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $version = Get-HostLaneProperty $probe 'version' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $architecture = Get-HostLaneProperty $probe 'architecture' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $pathFingerprint = Get-HostLaneProperty $probe 'executable_path_fingerprint' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $projectOrigin = Get-HostLaneProperty $probe 'project_origin' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $collectorOrigin = Get-HostLaneProperty $probe 'collector_origin' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $capability = Get-HostLaneProperty $probe 'execution_capability' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' String
                            $enabled = Get-HostLaneProperty $probe 'order_execution_enabled' 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID' Object
                            try {
                                $normalizedPath = [System.IO.Path]::GetFullPath($path)
                                $selectedPathExists = if ($Hooks.ContainsKey('TestPath')) {
                                    $hook = $Hooks['TestPath']; & $hook $normalizedPath
                                } else { Test-Path -LiteralPath $normalizedPath -PathType Leaf -ErrorAction Stop }
                            } catch { $selectedPathExists = $false }
                            if (![System.IO.Path]::IsPathRooted($path) -or
                                $selectedPathExists -isnot [bool] -or !$selectedPathExists -or
                                $identity -notmatch '^[0-9a-f]{64}$' -or
                                $pathFingerprint -notmatch '^[0-9a-f]{64}$' -or
                                $version -notmatch '^3\.(1[1-9]|[2-9][0-9])\.[0-9]+' -or
                                $architecture -ne $PowerShellArchitecture -or
                                $projectOrigin -ne 'EXACT_DEPLOYMENT_SRC' -or
                                $collectorOrigin -ne 'EXACT_DEPLOYMENT_SCRIPT' -or
                                $capability -ne 'NONE' -or $enabled -isnot [bool] -or $enabled) {
                                $reason = 'PYTHON_CANDIDATE_PROBE_SHAPE_INVALID'
                            } else {
                                $valid += [pscustomobject]@{
                                    Resolver = $item.Resolver; Rank = $item.Rank; PythonPath = $normalizedPath
                                    Identity = $identity; Basename = $basename; Version = $version
                                    Architecture = $architecture; CandidateKey = $candidateKey
                                }
                            }
                        } elseif ($status -eq 'BLOCKED' -and $exitCode -ne 0 -and
                                  $innerCode -match '^PYTHON_CANDIDATE_[A-Z0-9_]+$') {
                            $reason = $innerCode
                        } else { $reason = 'PYTHON_CANDIDATE_PROBE_EXIT_MISMATCH' }
                    }
                } catch {
                    if ($_.Exception.Message -match '^PYTHON_CANDIDATE_[A-Z0-9_]+$') {
                        $reason = [string]$_.Exception.Message
                    } else { $reason = 'PYTHON_CANDIDATE_PROBE_START_FAILED' }
                }
            }
            $matching = @($valid | Where-Object {
                $_.CandidateKey -eq $candidateKey
            } | Select-Object -Last 1)
            $matrix += [pscustomobject]@{
                resolver = $item.Resolver
                resolver_rank = $item.Rank
                status = if ($matching.Count -eq 1 -and $reason -eq 'NONE') { 'VALID' } else { 'REJECTED' }
                reason_code = $reason
                identity_fingerprint = if ($matching.Count -eq 1) { $matching[0].Identity } else { 'NONE' }
                executable_basename = if ($matching.Count -eq 1) { $matching[0].Basename } else { 'REDACTED' }
                version = if ($matching.Count -eq 1) { $matching[0].Version } else { 'UNKNOWN' }
                architecture = if ($matching.Count -eq 1) { $matching[0].Architecture } else { 'UNKNOWN' }
            }
        }
        if ($valid.Count -eq 0) {
            Throw-HostLaneSelectionCode 'PYTHON_RUNTIME_NO_VALID_CANDIDATE' $matrix
        }
        $bestRank = ($valid | Measure-Object -Property Rank -Minimum).Minimum
        $best = @($valid | Where-Object { $_.Rank -eq $bestRank })
        $identities = @($best | Group-Object -Property Identity)
        if ($identities.Count -ne 1) {
            Throw-HostLaneSelectionCode 'PYTHON_RUNTIME_AMBIGUOUS' $matrix
        }
        $selected = $identities[0].Group | Select-Object -First 1
        return [pscustomobject]@{
            PythonPath = $selected.PythonPath
            ResolverRank = $selected.Rank
            IdentityFingerprint = $selected.Identity
            ExecutableBasename = $selected.Basename
            Version = $selected.Version
            Architecture = $selected.Architecture
            Candidates = $matrix
        }
    } catch {
        if (Test-HostLaneCode $_.Exception) { throw }
        Throw-HostLaneCode 'PYTHON_DISCOVERY_INTERNAL_FAILURE'
    }
}

function Write-DaxPythonSelection {
    param([Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$Candidates)
    foreach ($candidate in @($Candidates)) {
        Write-Host ('PYTHON_CANDIDATE: ' + ($candidate | ConvertTo-Json -Compress))
    }
}

function Invoke-DaxHostJsonProcess {
    param(
        [Parameter(Mandatory = $true)][string]$PythonPath,
        [Parameter(Mandatory = $true)][string]$ScriptPath,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][string[]]$Arguments,
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
        $exception.Data['HostLaneCode'] = $innerCode
        $exception.Data['HostLaneResult'] = $result
        throw $exception
    } catch {
        if ((Test-HostLaneCode $_.Exception) -or
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
Export-ModuleMember -Function Write-DaxPythonSelection
Export-ModuleMember -Function Invoke-DaxHostJsonProcess
Export-ModuleMember -Function Write-DaxHostPreflight
