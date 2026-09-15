param(
    [Parameter(Mandatory = $true)][string]$ExpectedHead,
    [string]$RepoRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
    [string]$RuntimeRoot = 'C:\Users\Mandy\Documents\dax-Day-ig-hostcheck',
    [string]$Namespace = '.runtime/ig_predemo_readiness_2238_v3_attempt_01',
    [string]$CredentialsFile = 'C:\Users\Mandy\ig_demo.env',
    [string]$PythonExecutable = 'python'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SafeErrorCodes = @(
    'HEAD_INVALID', 'HOST_UNAVAILABLE', 'RUNTIME_ROOT_UNAVAILABLE',
    'GIT_NOT_AVAILABLE', 'REMOTE_QUERY_FAILED', 'REMOTE_MISMATCH',
    'FETCH_FAILED', 'PUBLISHED_HEAD_QUERY_FAILED', 'BRANCH_DRIFT',
    'START_HEAD_NOT_ANCESTOR', 'TARGET_COMMIT_UNAVAILABLE',
    'DEPLOYMENT_PATH_COLLISION', 'DEPLOYMENT_PARENT_CREATE_FAILED',
    'DEPLOYMENT_OWNER_MARKER_FAILED', 'LOCAL_CLONE_FAILED',
    'DEPLOYMENT_HOOKS_CREATE_FAILED',
    'ISOLATED_CHECKOUT_FAILED', 'DEPLOYMENT_HEAD_QUERY_FAILED',
    'DEPLOYMENT_HEAD_MISMATCH', 'DEPLOYMENT_STATUS_FAILED',
    'DEPLOYMENT_NOT_CLEAN', 'DEPLOYMENT_CLEANUP_FAILED_RETAINED',
    'MODULE_FILE_MISSING', 'MODULE_PARSE_FAILED',
    'MODULE_VERSION_INCOMPATIBLE', 'MODULE_IMPORT_EXCEPTION',
    'MODULE_EXPORT_CONTRACT_FAILED', 'PYTHON_COMMAND_DISCOVERY_FAILED',
    'PYTHON_COMMAND_RESULT_NULL', 'PYTHON_COMMAND_RESULT_MULTIPLE',
    'PYTHON_COMMAND_IDENTITY_INVALID', 'PYTHON_EXECUTABLE_PATH_FAILED',
    'PYTHON_EXECUTABLE_CHECK_FAILED', 'PYTHON_EXECUTABLE_NOT_FOUND',
    'PYTHON_DISCOVERY_INTERNAL_FAILURE', 'HOST_LANE_SCRIPT_PATH_FAILED',
    'PYTHON_RUNTIME_NO_VALID_CANDIDATE', 'PYTHON_RUNTIME_AMBIGUOUS',
    'PYTHON_RUNTIME_PROBE_MISSING', 'PYTHON_RUNTIME_SELECTION_INVALID',
    'HOST_LANE_SCRIPT_MISSING', 'HOST_LANE_PROCESS_START_FAILED',
    'HOST_LANE_PROCESS_NO_OUTPUT', 'HOST_LANE_PROCESS_MULTILINE_OUTPUT',
    'HOST_LANE_PROCESS_OUTPUT_TYPE_INVALID', 'HOST_LANE_PROCESS_JSON_INVALID',
    'HOST_LANE_PROCESS_RESULT_INVALID', 'HOST_LANE_PROCESS_EXIT_MISMATCH',
    'HOST_LANE_INTERNAL_FAILURE', 'PREFLIGHT_REQUIRED_CHECK_FAILED',
    'PREFLIGHT_INTERNAL_FAILURE', 'EVIDENCE_PREFLIGHT_PUBLICATION_FAILED',
    'HOST_UNCLASSIFIED_FAILURE', 'POWERSHELL_UNCLASSIFIED_FAILURE',
    'GIT_UNCLASSIFIED_FAILURE', 'FILESYSTEM_UNCLASSIFIED_FAILURE',
    'PYTHON_UNCLASSIFIED_FAILURE', 'IMPORT_UNCLASSIFIED_FAILURE',
    'PREFLIGHT_UNCLASSIFIED_FAILURE', 'NETWORK_UNCLASSIFIED_FAILURE',
    'CREDENTIAL_UNCLASSIFIED_FAILURE', 'SAFETY_UNCLASSIFIED_FAILURE',
    'COLLECTOR_PRECHECK_UNCLASSIFIED_FAILURE',
    'IG_SESSION_UNCLASSIFIED_FAILURE',
    'EVIDENCE_UNCLASSIFIED_FAILURE', 'CLEANUP_UNCLASSIFIED_FAILURE',
    'GOVERNANCE_WINDOWS_HOST_REQUIRED', 'GOVERNANCE_INVALID_HEAD',
    'GOVERNANCE_HEAD_MISMATCH', 'GOVERNANCE_TRACKED_DRIFT',
    'GOVERNANCE_UNTRACKED_CODE', 'GOVERNANCE_IMPORT_PARITY',
    'STATE_INVALID_NAMESPACE', 'STATE_NAMESPACE_SYMLINK',
    'STATE_NAMESPACE_EXISTS', 'STATE_RUNTIME_ROOT_INVALID',
    'STATE_RUNTIME_ROOT_UNAVAILABLE', 'STATE_PUBLICATION_FAILED',
    'STATE_READBACK_FAILED', 'STATE_CHANGED_OVERLAP',
    'STATE_ANCHOR_NOT_FOUND', 'STATE_NO_NEW_FINALIZED_M5',
    'HEAD_MISMATCH', 'HEAD_QUERY_FAILED', 'NAMESPACE_EXISTS',
    'PYTHON_COLLECTOR_UNCLASSIFIED_FAILURE',
    'DATA_IG_M5_PROVIDER_CONTRACT_UNVERIFIED',
    'DATA_STALE_AT_PROCESSING', 'DATA_TEST_FAILED',
    'FRESH_START_FAILED', 'RESUME_FAILED', 'OPERATOR_FAILED',
    'SESSION_SETUP_FAILED', 'CREDENTIALS_FILE_UNAVAILABLE_OR_INVALID',
    'IG_AUTHENTICATION_FAILED_NO_RETRY',
    'IG_SESSION_READ_FAILED_NO_RETRY', 'IG_READINESS_MATRIX_INCOMPLETE',
    'IG_READINESS_DERIVATION_INCOMPLETE',
    'IG_SESSION_CLEANUP_FAILED',
    'CLOCK_INVALID_UTC', 'CLOCK_MOVED_BACKWARDS',
    'CLOCK_DISCONTINUITY', 'SAFETY_EXECUTION_CAPABILITY',
    'EVIDENCE_INVALID', 'EVIDENCE_PUBLICATION_FAILED', 'RAW_PERSISTENCE_FAILED', 'UNEXPECTED_FAILURE',
    'RUNNER_UNEXPECTED_FAILURE'
)

function Invoke-GitGate {
    param(
        [Parameter(Mandatory = $true)][string]$ErrorCode,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$WorkingDirectory = $RepoRoot
    )
    try {
        $result = @(& git -C $WorkingDirectory @Arguments 2>$null)
        $exitCode = $LASTEXITCODE
    } catch {
        throw $ErrorCode
    }
    if ($exitCode -ne 0) { throw $ErrorCode }
    return (($result -join [Environment]::NewLine).Trim())
}

function Get-LegacyPartialState {
    param([Parameter(Mandatory = $true)][string]$TemporaryRoot)
    $registered = 0
    $directories = 0
    $queryFailed = $false
    try {
        $lines = @(& git -C $RepoRoot worktree list --porcelain 2>$null)
        if ($LASTEXITCODE -ne 0) {
            $queryFailed = $true
        } else {
            foreach ($line in $lines) {
                if ($line -notmatch '^worktree (.+)$') { continue }
                try {
                    $path = [System.IO.Path]::GetFullPath($Matches[1])
                    $parent = Split-Path -Parent $path
                    $leaf = Split-Path -Leaf $path
                    $parentLeaf = Split-Path -Leaf $parent
                    if ($leaf -eq 'exact-head' -and
                        $parentLeaf -match '^dax-day-step2238-[0-9a-f]{32}$' -and
                        $parent.StartsWith($TemporaryRoot, [StringComparison]::OrdinalIgnoreCase)) {
                        $registered += 1
                    }
                } catch {
                    $queryFailed = $true
                }
            }
        }
    } catch {
        $queryFailed = $true
    }
    try {
        $legacy = @([System.IO.Directory]::EnumerateDirectories($TemporaryRoot) |
            Where-Object {
                [System.IO.Path]::GetFileName($_) -match '^dax-day-step2238-[0-9a-f]{32}$'
            })
        $directories = $legacy.Count
    } catch {
        $queryFailed = $true
    }
    if ($queryFailed) { return 'QUERY_INCOMPLETE_RETAINED' }
    if ($registered -gt 0 -or $directories -gt 0) { return 'DETECTED_RETAINED' }
    return 'NONE_DETECTED'
}

function Test-RunnerOwnedDeployment {
    param(
        [Parameter(Mandatory = $true)][string]$TemporaryRoot,
        [Parameter(Mandatory = $true)][string]$DeploymentParent,
        [Parameter(Mandatory = $true)][string]$DeploymentRoot,
        [Parameter(Mandatory = $true)][string]$MarkerPath,
        [Parameter(Mandatory = $true)][string]$OwnerToken
    )
    try {
        $trimChars = [char[]]@(
            [System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar
        )
        $temporaryFull = [System.IO.Path]::GetFullPath($TemporaryRoot).TrimEnd($trimChars) +
            [System.IO.Path]::DirectorySeparatorChar
        $parentFull = [System.IO.Path]::GetFullPath($DeploymentParent)
        $rootFull = [System.IO.Path]::GetFullPath($DeploymentRoot)
        if (!$parentFull.StartsWith($temporaryFull, [StringComparison]::OrdinalIgnoreCase)) {
            return $false
        }
        if ((Split-Path -Leaf $parentFull) -notmatch '^d2238-[0-9a-f]{32}$') {
            return $false
        }
        if ($rootFull -ne [System.IO.Path]::GetFullPath((Join-Path $parentFull 'repo'))) {
            return $false
        }
        if (!(Test-Path -LiteralPath $MarkerPath -PathType Leaf)) { return $false }
        $parentAttributes = [System.IO.File]::GetAttributes($parentFull)
        if (($parentAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            return $false
        }
        $markerAttributes = [System.IO.File]::GetAttributes($MarkerPath)
        if (($markerAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            return $false
        }
        $marker = Get-Content -LiteralPath $MarkerPath -Raw -ErrorAction Stop |
            ConvertFrom-Json -ErrorAction Stop
        if ($marker.schema -ne 'DAX_STEP2238_DEPLOYMENT_OWNER_V1' -or
            $marker.owner_token -ne $OwnerToken -or
            $marker.expected_head -ne $ExpectedHead -or
            $marker.deployment_child -ne 'repo') {
            return $false
        }
        $allowed = @('.dax-step2238-owner.json', '.hooks', 'repo')
        foreach ($child in [System.IO.Directory]::EnumerateFileSystemEntries($parentFull)) {
            if ($allowed -notcontains [System.IO.Path]::GetFileName($child)) { return $false }
        }
        if (Test-Path -LiteralPath $rootFull) {
            $rootAttributes = [System.IO.File]::GetAttributes($rootFull)
            if (($rootAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                return $false
            }
        }
        $hooksFull = Join-Path $parentFull '.hooks'
        if (Test-Path -LiteralPath $hooksFull) {
            $hooksAttributes = [System.IO.File]::GetAttributes($hooksFull)
            if (($hooksAttributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                return $false
            }
        }
        return $true
    } catch {
        return $false
    }
}

function Write-IgReadinessMatrix {
    param([Parameter(Mandatory = $true)]$Result)
    try {
        $property = $Result.PSObject.Properties['readiness_matrix']
        if ($null -eq $property -or $null -eq $property.Value) { return }
        $rows = @($property.Value)
        $loginSucceeded = $Result.PSObject.Properties['login_success']
        if ($null -ne $loginSucceeded -and $loginSucceeded.Value -eq $true -and
            $rows.Count -ne 8) { throw 'INVALID_AUTHENTICATED_COUNT' }
        if ($rows.Count -gt 8) { throw 'INVALID_COUNT' }
        Write-Host ('IG READINESS MATRIX: rows={0}' -f $rows.Count)
        foreach ($row in $rows) {
            $resource = [string]$row.resource
            $endpoint = [string]$row.endpoint_family
            $status = [string]$row.status
            $reason = [string]$row.reason_code
            $httpClass = if ($null -eq $row.http_status_class) { 'NONE' } else { [string]$row.http_status_class }
            $providerCode = if ($null -eq $row.provider_error_code) { 'NONE' } else { [string]$row.provider_error_code }
            $shape = [string]$row.response_shape_status
            $requestId = if ($null -eq $row.request_id_fingerprint) { 'NONE' } else { [string]$row.request_id_fingerprint }
            $started = if ($null -eq $row.request_started_at_utc) { 'NONE' } else { [string]$row.request_started_at_utc }
            $observed = if ($null -eq $row.response_observed_at_utc) { 'NONE' } else { [string]$row.response_observed_at_utc }
            if ($resource -notmatch '^[A-Z][A-Z0-9_]*$' -or
                $endpoint -notmatch '^[A-Z][A-Z0-9_]*$' -or
                $status -notin @('PASS', 'FAIL', 'BLOCKED', 'UNKNOWN') -or
                $reason -notmatch '^[A-Z][A-Z0-9_]*$' -or
                $httpClass -notmatch '^(?:NONE|HTTP_[1-5]XX|HTTP_OTHER)$' -or
                $providerCode -notmatch '^(?:NONE|[a-z0-9.-]+)$' -or
                $shape -notmatch '^[A-Z][A-Z0-9_]*$' -or
                $requestId -notmatch '^(?:NONE|[0-9a-f]{64})$' -or
                $started -notmatch '^(?:NONE|[0-9T:+.-]+)$' -or
                $observed -notmatch '^(?:NONE|[0-9T:+.-]+)$') {
                throw 'INVALID_ROW'
            }
            Write-Host ('IG_READ: resource={0}; endpoint_family={1}; status={2}; reason_code={3}; http_status_class={4}; provider_error_code={5}; response_shape_status={6}; request_started_at_utc={7}; response_observed_at_utc={8}; request_id_fingerprint={9}' -f
                $resource, $endpoint, $status, $reason, $httpClass, $providerCode,
                $shape, $started, $observed, $requestId)
        }
    } catch {
        Write-Host 'IG READINESS MATRIX: SANITIZED_SHAPE_INVALID'
    }
}

function Import-DaxHostRuntimeOwner {
    param(
        [Parameter(Mandatory = $true)][string]$DeploymentRoot,
        [Parameter(Mandatory = $true)][string]$ModuleRelativePath
    )
    $diagnostic = [ordered]@{
        status = 'FAIL'
        error_code = 'MODULE_IMPORT_EXCEPTION'
        import_phase = 'VERSION'
        exception_class = 'NONE'
        fully_qualified_error_id = 'NONE'
        error_category = 'NONE'
        path_category = 'EXACT_DEPLOYMENT_MODULE'
        path_fingerprint = 'UNKNOWN'
        powershell_version = $PSVersionTable.PSVersion.ToString()
        powershell_edition = [string]$PSVersionTable.PSEdition
        language_mode = [string]$ExecutionContext.SessionState.LanguageMode
        execution_policy = 'UNKNOWN'
        module_file_sha256 = 'UNKNOWN'
        security_marker = 'UNKNOWN'
        module_identity = 'UNASSIGNED'
    }
    try {
        $policy = [string](Get-ExecutionPolicy -ErrorAction Stop)
        if ($policy -match '^[A-Za-z]+$') { $diagnostic.execution_policy = $policy }
    } catch { }
    if ($PSVersionTable.PSVersion -lt [Version]'5.1') {
        $diagnostic.error_code = 'MODULE_VERSION_INCOMPATIBLE'
        Write-Host ('MODULE_DIAGNOSTIC: ' + ($diagnostic | ConvertTo-Json -Compress))
        throw 'MODULE_VERSION_INCOMPATIBLE'
    }
    if ($diagnostic.language_mode -ne 'FullLanguage') {
        $diagnostic.import_phase = 'LANGUAGE_MODE'
        $diagnostic.exception_class = 'RuntimeException'
        Write-Host ('MODULE_DIAGNOSTIC: ' + ($diagnostic | ConvertTo-Json -Compress))
        throw 'MODULE_IMPORT_EXCEPTION'
    }
    try {
        $rootPath = [System.IO.Path]::GetFullPath($DeploymentRoot)
        $modulePath = [System.IO.Path]::GetFullPath((Join-Path $rootPath $ModuleRelativePath))
        $rootPrefix = $rootPath.TrimEnd([System.IO.Path]::DirectorySeparatorChar,
            [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
        if (!$modulePath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'MODULE_FILE_MISSING'
        }
        $present = Test-Path -LiteralPath $modulePath -PathType Leaf -ErrorAction Stop
        if (!$present) { throw 'MODULE_FILE_MISSING' }
        $attributes = [System.IO.File]::GetAttributes($modulePath)
        if (($attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'MODULE_FILE_MISSING'
        }
    } catch {
        $diagnostic.error_code = 'MODULE_FILE_MISSING'
        $diagnostic.import_phase = 'FILE'
        Write-Host ('MODULE_DIAGNOSTIC: ' + ($diagnostic | ConvertTo-Json -Compress))
        if ($_.Exception.Message -eq 'MODULE_FILE_MISSING') { throw }
        throw 'MODULE_FILE_MISSING'
    }
    try {
        $bytes = [System.IO.File]::ReadAllBytes($modulePath)
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        try {
            $diagnostic.module_file_sha256 = ([BitConverter]::ToString(
                $sha256.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
            $pathBytes = [System.Text.Encoding]::UTF8.GetBytes($modulePath.ToLowerInvariant())
            $diagnostic.path_fingerprint = ([BitConverter]::ToString(
                $sha256.ComputeHash($pathBytes))).Replace('-', '').ToLowerInvariant()
        } finally { $sha256.Dispose() }
        if ($bytes.Length -eq 0) { throw 'MODULE_PARSE_FAILED' }
        foreach ($value in $bytes) {
            if ($value -eq 0 -or $value -gt 127) { throw 'MODULE_PARSE_FAILED' }
        }
        $tokens = $null
        $parseErrors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile(
            $modulePath, [ref]$tokens, [ref]$parseErrors)
        if ($null -eq $ast -or $null -eq $parseErrors -or $parseErrors.Count -ne 0) {
            throw 'MODULE_PARSE_FAILED'
        }
    } catch {
        $diagnostic.error_code = 'MODULE_PARSE_FAILED'
        $diagnostic.import_phase = 'PARSE'
        $diagnostic.exception_class = $_.Exception.GetType().Name
        Write-Host ('MODULE_DIAGNOSTIC: ' + ($diagnostic | ConvertTo-Json -Compress))
        if ($_.Exception.Message -eq 'MODULE_PARSE_FAILED') { throw }
        throw 'MODULE_PARSE_FAILED'
    }

    try {
        $zone = @(Get-Item -LiteralPath $modulePath -Stream Zone.Identifier `
            -ErrorAction SilentlyContinue)
        $diagnostic.security_marker = if ($zone.Count -eq 0) { 'ABSENT' } else { 'PRESENT' }
    } catch { $diagnostic.security_marker = 'UNKNOWN' }
    if ($diagnostic.security_marker -eq 'PRESENT') {
        $diagnostic.import_phase = 'SECURITY_POLICY'
        $diagnostic.exception_class = 'PSSecurityException'
        Write-Host ('MODULE_DIAGNOSTIC: ' + ($diagnostic | ConvertTo-Json -Compress))
        throw 'MODULE_IMPORT_EXCEPTION'
    }

    $module = $null
    $materializedPath = $null
    $prefix = 'D2238' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
    try {
        $diagnostic.import_phase = 'MODULE_MATERIALIZATION'
        $materializedPath = Join-Path (Split-Path -Parent $rootPath) `
            ('dax-windows-host-lane-' + [Guid]::NewGuid().ToString('N') + '.psm1')
        [System.IO.File]::WriteAllBytes($materializedPath, $bytes)
        $readback = [System.IO.File]::ReadAllBytes($materializedPath)
        if ($readback.Length -ne $bytes.Length) { throw 'MODULE_IMPORT_EXCEPTION' }
        for ($index = 0; $index -lt $bytes.Length; $index += 1) {
            if ($readback[$index] -ne $bytes[$index]) { throw 'MODULE_IMPORT_EXCEPTION' }
        }
        $diagnostic.path_category = 'RUNNER_OWNED_HASH_VERIFIED_MODULE_COPY'
        $diagnostic.module_identity = 'UNIQUE_PER_RUN'
        $diagnostic.import_phase = 'MODULE_INITIALIZATION_OR_COMMAND_REGISTRATION'
        $loaded = @(Import-Module -Name $materializedPath -Global -Prefix $prefix `
            -Force -PassThru -ErrorAction Stop)
        if ($loaded.Count -ne 1) { throw 'MODULE_IMPORT_EXCEPTION' }
        $module = $loaded[0]
    } catch {
        $record = $_
        $exceptionType = $record.Exception.GetType().Name
        if ($exceptionType -match '^[A-Za-z][A-Za-z0-9.]{0,127}$') {
            $diagnostic.exception_class = $exceptionType
        } else { $diagnostic.exception_class = 'OTHER' }
        $fqid = [string]$record.FullyQualifiedErrorId
        if ($fqid -match '^[A-Za-z0-9_.:,-]{1,160}$') {
            $diagnostic.fully_qualified_error_id = $fqid
        }
        $category = [string]$record.CategoryInfo.Category
        if ($category -match '^[A-Za-z]+$') { $diagnostic.error_category = $category }
        if ($exceptionType -match 'Security|Unauthorized' -or
            $fqid -match 'Authorization|ExecutionPolicy|Unauthorized') {
            $diagnostic.import_phase = 'SECURITY_POLICY'
        } elseif ($exceptionType -match 'SessionState|Command' -or
                  $fqid -match 'SessionState|Command|Function.*Capacity') {
            $diagnostic.import_phase = 'COMMAND_REGISTRATION'
        }
        Write-Host ('MODULE_DIAGNOSTIC: ' + ($diagnostic | ConvertTo-Json -Compress))
        if ($_.Exception.Message -eq 'MODULE_IMPORT_EXCEPTION') { throw }
        throw 'MODULE_IMPORT_EXCEPTION'
    }
    try {
        $commandMap = @{}
        foreach ($name in @(
                'Invoke-DaxHostJsonProcess', 'Resolve-DaxHostPython',
                'Write-DaxHostPreflight', 'Write-DaxPythonSelection')) {
            $parts = $name -split '-', 2
            $registeredName = $parts[0] + '-' + $prefix + $parts[1]
            $commands = @(Get-Command -Name $registeredName -CommandType Function `
                -ErrorAction Stop)
            if ($commands.Count -ne 1 -or
                $commands[0].Module.Path -ne $materializedPath) {
                throw 'MODULE_EXPORT_CONTRACT_FAILED'
            }
            $commandMap[$name] = $commands[0]
        }
    } catch {
        $diagnostic.error_code = 'MODULE_EXPORT_CONTRACT_FAILED'
        $diagnostic.import_phase = 'EXPORT_DISCOVERY_OR_COMMAND_REGISTRATION'
        $diagnostic.exception_class = $_.Exception.GetType().Name
        Write-Host ('MODULE_DIAGNOSTIC: ' + ($diagnostic | ConvertTo-Json -Compress))
        if ($null -ne $module) {
            Remove-Module -ModuleInfo $module -Force -ErrorAction SilentlyContinue
        }
        if ($_.Exception.Message -eq 'MODULE_EXPORT_CONTRACT_FAILED') { throw }
        throw 'MODULE_EXPORT_CONTRACT_FAILED'
    }
    $lineEndings = if ([System.Text.Encoding]::ASCII.GetString($bytes).Contains("`r`n")) {
        'CRLF_OR_MIXED'
    } else { 'LF' }
    Write-Host ('MODULE_PREFLIGHT: status=PASS; edition={0}; version={1}; encoding=ASCII; line_endings={2}; path=HASH_VERIFIED_RUNNER_OWNED_COPY; exports=4; dependencies=NONE; source_sha256={3}; language_mode={4}; execution_policy={5}; module_identity=UNIQUE_PER_RUN' -f
        [string]$PSVersionTable.PSEdition, $PSVersionTable.PSVersion.ToString(),
        $lineEndings, $diagnostic.module_file_sha256, $diagnostic.language_mode,
        $diagnostic.execution_policy)
    return [pscustomobject]@{
        Module = $module
        ResolvePython = $commandMap['Resolve-DaxHostPython']
        WritePythonSelection = $commandMap['Write-DaxPythonSelection']
        InvokeJsonProcess = $commandMap['Invoke-DaxHostJsonProcess']
        WritePreflight = $commandMap['Write-DaxHostPreflight']
        SourcePathFingerprint = $diagnostic.path_fingerprint
        ModuleFileSha256 = $diagnostic.module_file_sha256
        MaterializedPath = $materializedPath
    }
}

function Invoke-Closeout {
    param([Parameter(Mandatory = $true)][string]$DeploymentRoot)
    $ownerContext = $null
    try {
        $ownerContext = Import-DaxHostRuntimeOwner -DeploymentRoot $DeploymentRoot `
            -ModuleRelativePath 'scripts/dax_windows_host_lane.psm1'
        $resolvePythonCommand = $ownerContext.ResolvePython
        $writePythonSelectionCommand = $ownerContext.WritePythonSelection
        $invokeJsonProcessCommand = $ownerContext.InvokeJsonProcess
        $writePreflightCommand = $ownerContext.WritePreflight
        $script:runnerPhase = 'PYTHON'
        try { $powerShellExecutable = [System.IO.Path]::GetFileName(
                [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName) }
        catch { $powerShellExecutable = 'UNKNOWN' }
        $powerShellArchitecture = if ([Environment]::Is64BitProcess) { '64_BIT' } else { '32_BIT' }
        try {
            $pythonSelection = & $resolvePythonCommand -PythonExecutable $PythonExecutable `
                -DeploymentRoot $DeploymentRoot -PowerShellArchitecture $powerShellArchitecture
            & $writePythonSelectionCommand -Candidates $pythonSelection.Candidates
            Write-Host ("PYTHON_SELECTION: status=SELECTED; resolver_rank={0}; basename={1}; version={2}; architecture={3}; identity_fingerprint={4}" -f
                $pythonSelection.ResolverRank, $pythonSelection.ExecutableBasename,
                $pythonSelection.Version, $pythonSelection.Architecture,
                $pythonSelection.IdentityFingerprint)
            $pythonPath = $pythonSelection.PythonPath
        } catch {
            if ($_.Exception.Data.Contains('PythonSelectionCandidates')) {
                & $writePythonSelectionCommand `
                    -Candidates $_.Exception.Data['PythonSelectionCandidates']
            }
            throw
        }
        $preflightPath = Join-Path $DeploymentRoot 'scripts/dax_windows_host_preflight.py'
        $preflightArguments = @(
            '--expected-head', $ExpectedHead,
            '--deployment-root', $DeploymentRoot,
            '--deployment-source-root', $RepoRoot,
            '--runtime-root', $RuntimeRoot,
            '--namespace', $Namespace,
            '--credentials-file', $CredentialsFile,
            '--powershell-version', $PSVersionTable.PSVersion.ToString(),
            '--powershell-edition', [string]$PSVersionTable.PSEdition,
            '--powershell-executable', $powerShellExecutable,
            '--powershell-language-mode', [string]$ExecutionContext.SessionState.LanguageMode,
            '--powershell-architecture', $powerShellArchitecture,
            '--git-clone', 'PASS', '--git-checkout', 'PASS',
            '--git-long-path', 'PASS', '--git-hooks-isolation', 'PASS'
        )
        $script:runnerPhase = 'PREFLIGHT'
        try {
            $preflight = & $invokeJsonProcessCommand -PythonPath $pythonPath `
                -ScriptPath $preflightPath -Arguments $preflightArguments `
                -SafePayloadCodes $SafeErrorCodes
            & $writePreflightCommand -Result $preflight
        } catch {
            if ($_.Exception.Data.Contains('HostLaneResult')) {
                $preflightResult = $_.Exception.Data['HostLaneResult']
                & $writePreflightCommand -Result $preflightResult
                try {
                    $preflightPhase = [string]$preflightResult.failure_phase
                    if ($preflightPhase -in @(
                            'HOST', 'POWERSHELL', 'GIT', 'FILESYSTEM', 'PYTHON',
                            'IMPORT', 'NETWORK', 'CREDENTIAL', 'EVIDENCE', 'SAFETY',
                            'PREFLIGHT')) {
                        $script:runnerPhase = $preflightPhase
                    }
                } catch {
                    $script:runnerPhase = 'PREFLIGHT'
                }
            }
            throw
        }
        $collectorPath = Join-Path $DeploymentRoot 'scripts/run_ig_predemo_readiness_2238.py'
        $collectorArguments = @(
            '--expected-head', $ExpectedHead, '--namespace', $Namespace,
            '--credentials-file', $CredentialsFile, '--runtime-root', $RuntimeRoot
        )
        $script:runnerPhase = 'COLLECTOR_PRECHECK'
        Write-Host 'COLLECTOR PRECHECK: exact deployment head; runtime namespace; credential shape; no IG login'
        try {
            $precheck = & $invokeJsonProcessCommand -PythonPath $pythonPath `
                -ScriptPath $collectorPath `
                -Arguments @($collectorArguments + '--pre-auth-precheck') `
                -SafePayloadCodes $SafeErrorCodes
            if ([string]$precheck.pre_auth_precheck -ne 'PASS') {
                throw 'COLLECTOR_PRECHECK_UNCLASSIFIED_FAILURE'
            }
        } catch {
            try { $_.Exception.Data['FailurePhase'] = 'COLLECTOR_PRECHECK' } catch { }
            throw
        }
        $script:runnerPhase = 'IG_SESSION'
        Write-Host 'AUTH READ-ONLY START: one login; eight-resource readiness matrix; no retry; one cleanup'
        try {
            $collectorResult = & $invokeJsonProcessCommand -PythonPath $pythonPath `
                -ScriptPath $collectorPath -Arguments $collectorArguments `
                -SafePayloadCodes $SafeErrorCodes
            Write-IgReadinessMatrix -Result $collectorResult
            return $collectorResult
        } catch {
            if ($_.Exception.Data.Contains('HostLaneResult')) {
                Write-IgReadinessMatrix -Result $_.Exception.Data['HostLaneResult']
            }
            try { $_.Exception.Data['FailurePhase'] = 'IG_SESSION' } catch { }
            throw
        }
    } catch {
        try {
            if (!$_.Exception.Data.Contains('FailurePhase')) {
                $_.Exception.Data['FailurePhase'] = $script:runnerPhase
            }
        } catch { }
        if ($SafeErrorCodes -contains $_.Exception.Message) { throw }
        throw 'HOST_LANE_INTERNAL_FAILURE'
    } finally {
        if ($null -ne $ownerContext -and $null -ne $ownerContext.Module) {
            Remove-Module -ModuleInfo $ownerContext.Module -Force -ErrorAction SilentlyContinue
        }
        if ($null -ne $ownerContext -and $null -ne $ownerContext.MaterializedPath -and
            (Test-Path -LiteralPath $ownerContext.MaterializedPath -PathType Leaf)) {
            try {
                [System.IO.File]::Delete([string]$ownerContext.MaterializedPath)
            } catch { }
        }
    }
}

$deploymentParent = $null
$deploymentRoot = $null
$markerPath = $null
$hooksRoot = $null
$ownerToken = $null
$deploymentParentCreated = $false
$primaryErrorCode = $null
$cleanupErrorCode = $null
$payloadFailurePhase = 'NONE'
$processExitContract = 'NONE'
$result = $null
$legacyPartialState = 'NOT_QUERIED'
$runnerPhase = 'HOST'
$failureClass = 'NONE'
$previousNoByteCode = $env:PYTHONDONTWRITEBYTECODE

try {
    if ($ExpectedHead -notmatch '^[0-9a-f]{40}$') { throw 'HEAD_INVALID' }
    if (!(Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw 'HOST_UNAVAILABLE' }
    if (!(Test-Path -LiteralPath $RuntimeRoot -PathType Container)) {
        throw 'RUNTIME_ROOT_UNAVAILABLE'
    }
    try {
        Get-Command -Name 'git' -CommandType Application -ErrorAction Stop | Out-Null
    } catch {
        throw 'GIT_NOT_AVAILABLE'
    }

    Write-Host 'START: isolated exact-head Step2238 deployment; existing checkout remains untouched'
    $runnerPhase = 'GIT'
    $remote = Invoke-GitGate -ErrorCode 'REMOTE_QUERY_FAILED' -Arguments @(
        'remote', 'get-url', 'origin'
    )
    if ($remote -notin @('https://github.com/hennebergtoni-lgtm/dax-Day.git',
                         'https://github.com/hennebergtoni-lgtm/dax-Day',
                         'git@github.com:hennebergtoni-lgtm/dax-Day.git')) {
        throw 'REMOTE_MISMATCH'
    }
    Invoke-GitGate -ErrorCode 'FETCH_FAILED' -Arguments @(
        'fetch', '--quiet', 'origin', 'nextgen-bot-line-v1'
    ) | Out-Null
    $published = Invoke-GitGate -ErrorCode 'PUBLISHED_HEAD_QUERY_FAILED' -Arguments @(
        'rev-parse', 'origin/nextgen-bot-line-v1'
    )
    if ($published -ne $ExpectedHead) { throw 'BRANCH_DRIFT' }
    Invoke-GitGate -ErrorCode 'START_HEAD_NOT_ANCESTOR' -Arguments @(
        'merge-base', '--is-ancestor',
        '4461e7cab62e195eb56676fb7e402a13eec64437', $ExpectedHead
    ) | Out-Null
    Invoke-GitGate -ErrorCode 'TARGET_COMMIT_UNAVAILABLE' -Arguments @(
        'cat-file', '-e', ("{0}^{{commit}}" -f $ExpectedHead)
    ) | Out-Null

    $runnerPhase = 'FILESYSTEM'
    $temporaryRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    $legacyPartialState = Get-LegacyPartialState -TemporaryRoot $temporaryRoot
    $ownerToken = [Guid]::NewGuid().ToString('N')
    $deploymentParent = Join-Path $temporaryRoot ('d2238-' + $ownerToken)
    if (Test-Path -LiteralPath $deploymentParent) { throw 'DEPLOYMENT_PATH_COLLISION' }
    try {
        New-Item -ItemType Directory -Path $deploymentParent -ErrorAction Stop | Out-Null
        $deploymentParentCreated = $true
    } catch {
        throw 'DEPLOYMENT_PARENT_CREATE_FAILED'
    }
    $deploymentRoot = Join-Path $deploymentParent 'repo'
    $markerPath = Join-Path $deploymentParent '.dax-step2238-owner.json'
    $hooksRoot = Join-Path $deploymentParent '.hooks'
    try {
        $markerPayload = [ordered]@{
            schema = 'DAX_STEP2238_DEPLOYMENT_OWNER_V1'
            owner_token = $ownerToken
            expected_head = $ExpectedHead
            deployment_child = 'repo'
        } | ConvertTo-Json -Compress
        [System.IO.File]::WriteAllText(
            $markerPath,
            $markerPayload,
            [System.Text.UTF8Encoding]::new($false)
        )
    } catch {
        throw 'DEPLOYMENT_OWNER_MARKER_FAILED'
    }
    if (!(Test-RunnerOwnedDeployment -TemporaryRoot $temporaryRoot `
            -DeploymentParent $deploymentParent -DeploymentRoot $deploymentRoot `
            -MarkerPath $markerPath -OwnerToken $ownerToken)) {
        throw 'DEPLOYMENT_OWNER_MARKER_FAILED'
    }
    try {
        New-Item -ItemType Directory -Path $hooksRoot -ErrorAction Stop | Out-Null
    } catch {
        throw 'DEPLOYMENT_HOOKS_CREATE_FAILED'
    }

    try {
        & git -c ("core.hooksPath={0}" -f $hooksRoot) -c core.longpaths=true `
            clone --quiet --no-checkout --no-hardlinks `
            $RepoRoot $deploymentRoot 2>$null | Out-Null
        $cloneExit = $LASTEXITCODE
    } catch {
        throw 'LOCAL_CLONE_FAILED'
    }
    if ($cloneExit -ne 0) { throw 'LOCAL_CLONE_FAILED' }
    try {
        & git -C $deploymentRoot -c ("core.hooksPath={0}" -f $hooksRoot) `
            -c core.longpaths=true checkout --quiet --detach `
            $ExpectedHead 2>$null | Out-Null
        $checkoutExit = $LASTEXITCODE
    } catch {
        throw 'ISOLATED_CHECKOUT_FAILED'
    }
    if ($checkoutExit -ne 0) { throw 'ISOLATED_CHECKOUT_FAILED' }

    $deployedHead = Invoke-GitGate -WorkingDirectory $deploymentRoot `
        -ErrorCode 'DEPLOYMENT_HEAD_QUERY_FAILED' -Arguments @('rev-parse', 'HEAD')
    if ($deployedHead -ne $ExpectedHead) { throw 'DEPLOYMENT_HEAD_MISMATCH' }
    $deploymentStatus = Invoke-GitGate -WorkingDirectory $deploymentRoot `
        -ErrorCode 'DEPLOYMENT_STATUS_FAILED' -Arguments @(
            'status', '--porcelain', '--untracked-files=all'
        )
    if ($deploymentStatus) { throw 'DEPLOYMENT_NOT_CLEAN' }

    $env:PYTHONDONTWRITEBYTECODE = '1'
    $runnerPhase = 'POWERSHELL'
    Write-Host 'WAIT: aggregate local/network/credential-shape preflight before any IG session'
    $result = Invoke-Closeout -DeploymentRoot $deploymentRoot
} catch {
    try {
        if ($_.Exception.Data.Contains('FailurePhase')) {
            $reportedPhase = [string]$_.Exception.Data['FailurePhase']
            if ($reportedPhase -in @(
                    'HOST', 'POWERSHELL', 'GIT', 'FILESYSTEM', 'PYTHON',
                    'IMPORT', 'PREFLIGHT', 'NETWORK', 'CREDENTIAL', 'SAFETY',
                    'COLLECTOR_PRECHECK', 'IG_SESSION', 'EVIDENCE', 'CLEANUP')) {
                $runnerPhase = $reportedPhase
            }
        }
        if ($_.Exception.Data.Contains('HostLaneProcessExitContract')) {
            $reportedExitContract = [string]$_.Exception.Data['HostLaneProcessExitContract']
            if ($reportedExitContract -in @(
                    'FAILURE_EXIT_MATCH', 'FAILURE_PAYLOAD_EXIT_ZERO',
                    'FAILURE_PAYLOAD_NONSTANDARD_NONZERO')) {
                $processExitContract = $reportedExitContract
            }
        }
        if ($_.Exception.Data.Contains('HostLaneResult')) {
            $phaseProperty = $_.Exception.Data['HostLaneResult'].PSObject.Properties['failure_phase']
            if ($null -ne $phaseProperty -and $phaseProperty.Value -is [string] -and
                $phaseProperty.Value -match '^[A-Z][A-Z0-9_]*$') {
                $payloadFailurePhase = [string]$phaseProperty.Value
            }
        }
    } catch { }
    $candidate = [string]$_.Exception.Message
    $exceptionName = $_.Exception.GetType().Name
    $failureClass = if ($exceptionName -in @(
            'UnauthorizedAccessException', 'IOException', 'ArgumentException',
            'InvalidOperationException', 'CommandNotFoundException',
            'RuntimeException', 'MethodInvocationException')) {
        $exceptionName
    } else { 'OTHER' }
    $primaryErrorCode = if ($SafeErrorCodes -contains $candidate) {
        $candidate
    } else {
        switch ($runnerPhase) {
            'HOST' { 'HOST_UNCLASSIFIED_FAILURE' }
            'POWERSHELL' { 'POWERSHELL_UNCLASSIFIED_FAILURE' }
            'GIT' { 'GIT_UNCLASSIFIED_FAILURE' }
            'FILESYSTEM' { 'FILESYSTEM_UNCLASSIFIED_FAILURE' }
            'PYTHON' { 'PYTHON_UNCLASSIFIED_FAILURE' }
            'IMPORT' { 'IMPORT_UNCLASSIFIED_FAILURE' }
            'PREFLIGHT' { 'PREFLIGHT_UNCLASSIFIED_FAILURE' }
            'NETWORK' { 'NETWORK_UNCLASSIFIED_FAILURE' }
            'CREDENTIAL' { 'CREDENTIAL_UNCLASSIFIED_FAILURE' }
            'SAFETY' { 'SAFETY_UNCLASSIFIED_FAILURE' }
            'COLLECTOR_PRECHECK' { 'COLLECTOR_PRECHECK_UNCLASSIFIED_FAILURE' }
            'IG_SESSION' { 'IG_SESSION_UNCLASSIFIED_FAILURE' }
            'EVIDENCE' { 'EVIDENCE_UNCLASSIFIED_FAILURE' }
            'CLEANUP' { 'CLEANUP_UNCLASSIFIED_FAILURE' }
            default { 'RUNNER_UNEXPECTED_FAILURE' }
        }
    }
} finally {
    if ($null -eq $previousNoByteCode) {
        Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue
    } else {
        $env:PYTHONDONTWRITEBYTECODE = $previousNoByteCode
    }

    if ($deploymentParentCreated -and $deploymentParent -and
        (Test-Path -LiteralPath $deploymentParent)) {
        if (Test-RunnerOwnedDeployment -TemporaryRoot $temporaryRoot `
                -DeploymentParent $deploymentParent -DeploymentRoot $deploymentRoot `
                -MarkerPath $markerPath -OwnerToken $ownerToken) {
            try {
                [System.IO.Directory]::Delete($deploymentParent, $true)
                if (Test-Path -LiteralPath $deploymentParent) {
                    $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
                }
            } catch {
                $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
            }
        } else {
            $cleanupErrorCode = 'DEPLOYMENT_CLEANUP_FAILED_RETAINED'
        }
    }
}

$errorCode = if ($primaryErrorCode) { $primaryErrorCode } else { $cleanupErrorCode }
$secondaryCleanupError = if ($primaryErrorCode -and $cleanupErrorCode) {
    $cleanupErrorCode
} else { 'NONE' }
if (!$primaryErrorCode -and $cleanupErrorCode) { $runnerPhase = 'CLEANUP' }
if ($errorCode) {
    Write-Host (
        'SUMMARY: BLOCKED / FAIL_CLOSED; error_code={0}; failure_phase={1}; payload_failure_phase={2}; process_exit_contract={3}; exception_class={4}; cleanup_error_code={5}; legacy_partial_state={6}; existing checkout/evidence retained; execution disabled' `
        -f $errorCode, $runnerPhase, $payloadFailurePhase, $processExitContract, `
            $failureClass, $secondaryCleanupError, $legacyPartialState
    )
    exit 2
}
Write-Host (
    'SUMMARY: SUCCESS; error_code=NONE; namespace={0}; legacy_partial_state={1}; deployment cleaned; NONE/false' `
    -f $result.namespace, $legacyPartialState
)
exit 0
