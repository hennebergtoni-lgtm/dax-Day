param(
    [string]$ModulePath = ''
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (!$ModulePath) {
    $ModulePath = Join-Path $repoRoot 'scripts/dax_windows_host_lane.psm1'
}
$runnerPath = Join-Path $repoRoot 'scripts/run_ig_predemo_readiness_2238.ps1'
$expected = @(
    'Invoke-DaxHostJsonProcess',
    'Resolve-DaxHostPython',
    'Write-DaxHostPreflight',
    'Write-DaxPythonSelection'
)

function Assert-Code {
    param(
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][scriptblock]$Operation
    )
    try {
        & $Operation | Out-Null
        throw ('ASSERT_NO_ERROR:' + $Expected)
    } catch {
        if ($_.Exception.Message -ne $Expected) {
            throw ('ASSERT_WRONG_ERROR:{0}:OBSERVED_{1}' -f $Expected, $_.Exception.GetType().Name)
        }
    }
}

# Load only the production pre-import function from the runner AST. This does not
# execute deployment, Python, credentials, networking, or broker code.
$runnerTokens = $null
$runnerErrors = $null
$runnerAst = [System.Management.Automation.Language.Parser]::ParseFile(
    $runnerPath, [ref]$runnerTokens, [ref]$runnerErrors)
if ($null -eq $runnerAst -or $runnerErrors.Count -ne 0) {
    throw 'ASSERT_RUNNER_PARSE_FAILED'
}
$importFunction = $runnerAst.Find({
    param($node)
    return ($node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
        $node.Name -eq 'Import-DaxHostRuntimeOwner')
}, $true)
if ($null -eq $importFunction) { throw 'ASSERT_IMPORT_FUNCTION_MISSING' }
. ([scriptblock]::Create($importFunction.Extent.Text))

function Assert-ModuleImport {
    param([Parameter(Mandatory = $true)][string]$Path)
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $tokens = $null
    $parseErrors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile(
        $fullPath, [ref]$tokens, [ref]$parseErrors)
    if ($null -eq $ast -or $parseErrors.Count -ne 0) {
        throw 'ASSERT_MODULE_PARSE_FAILED'
    }
    $modules = @(Import-Module -Name $fullPath -Force -PassThru -ErrorAction Stop)
    if ($modules.Count -ne 1) { throw 'ASSERT_MODULE_IMPORT_COUNT_FAILED' }
    $exports = @($modules[0].ExportedFunctions.Keys)
    if ($exports.Count -ne $expected.Count) { throw 'ASSERT_MODULE_EXPORT_COUNT_FAILED' }
    foreach ($name in $expected) {
        if ($exports -notcontains $name) { throw 'ASSERT_MODULE_EXPORT_MISSING' }
        $command = Get-Command -Name $name -CommandType Function -ErrorAction Stop
        if ($command.Module.Path -ne $fullPath) { throw 'ASSERT_MODULE_EXPORT_ORIGIN_FAILED' }
    }
    Remove-Module -ModuleInfo $modules[0] -Force -ErrorAction Stop
}

Assert-ModuleImport -Path $ModulePath

$temporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
    'dax module unicode-' + [char]0x00FC + '-' + [Guid]::NewGuid().ToString('N'))
try {
    [System.IO.Directory]::CreateDirectory($temporaryRoot) | Out-Null
    $source = [System.IO.File]::ReadAllText(
        [System.IO.Path]::GetFullPath($ModulePath), [System.Text.Encoding]::ASCII)
    $lfPath = Join-Path $temporaryRoot 'host lane lf.psm1'
    $crlfPath = Join-Path $temporaryRoot 'host lane crlf.psm1'
    [System.IO.File]::WriteAllText(
        $lfPath, $source.Replace("`r`n", "`n"), [System.Text.Encoding]::ASCII)
    $normalized = $source.Replace("`r`n", "`n").Replace("`n", "`r`n")
    [System.IO.File]::WriteAllText($crlfPath, $normalized, [System.Text.Encoding]::ASCII)
    Assert-ModuleImport -Path $lfPath
    Assert-ModuleImport -Path $crlfPath

    $nested = $temporaryRoot
    while ($nested.Length -lt 190) {
        $nested = Join-Path $nested 'bounded-long-path-segment'
    }
    [System.IO.Directory]::CreateDirectory($nested) | Out-Null
    $boundedPath = Join-Path $nested 'host-lane.psm1'
    [System.IO.File]::WriteAllText($boundedPath, $source, [System.Text.Encoding]::ASCII)
    Assert-ModuleImport -Path $boundedPath

    $productionRoot = Join-Path $temporaryRoot 'production-preimport'
    $productionScripts = Join-Path $productionRoot 'scripts'
    [System.IO.Directory]::CreateDirectory($productionScripts) | Out-Null
    Assert-Code -Expected 'MODULE_FILE_MISSING' -Operation {
        Import-DaxHostRuntimeOwner -DeploymentRoot $productionRoot `
            -ModuleRelativePath 'scripts/missing.psm1'
    }

    $malformedPath = Join-Path $productionScripts 'malformed.psm1'
    [System.IO.File]::WriteAllText(
        $malformedPath, 'function Broken {', [System.Text.Encoding]::ASCII)
    Assert-Code -Expected 'MODULE_PARSE_FAILED' -Operation {
        Import-DaxHostRuntimeOwner -DeploymentRoot $productionRoot `
            -ModuleRelativePath 'scripts/malformed.psm1'
    }

    $bomPath = Join-Path $productionScripts 'bom.psm1'
    [byte[]]$bomBytes = [byte[]](0xEF, 0xBB, 0xBF) + [System.Text.Encoding]::ASCII.GetBytes(
        "function Safe-Bom { return 'SAFE' }")
    [System.IO.File]::WriteAllBytes($bomPath, $bomBytes)
    Assert-Code -Expected 'MODULE_PARSE_FAILED' -Operation {
        Import-DaxHostRuntimeOwner -DeploymentRoot $productionRoot `
            -ModuleRelativePath 'scripts/bom.psm1'
    }

    if ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) {
        $markedPath = Join-Path $productionScripts 'marked.psm1'
        [System.IO.File]::WriteAllText($markedPath, $source, [System.Text.Encoding]::ASCII)
        try {
            Set-Content -LiteralPath $markedPath -Stream Zone.Identifier `
                -Value "[ZoneTransfer]`r`nZoneId=3" -Encoding ASCII -ErrorAction Stop
            Assert-Code -Expected 'MODULE_IMPORT_EXCEPTION' -Operation {
                Import-DaxHostRuntimeOwner -DeploymentRoot $productionRoot `
                    -ModuleRelativePath 'scripts/marked.psm1'
            }
        } catch {
            if ($_.Exception.Message -match '^ASSERT_') { throw }
            # Filesystems without alternate data streams report this capability as unavailable.
        }
    }

    $throwsPath = Join-Path $productionScripts 'throws.psm1'
    [System.IO.File]::WriteAllText(
        $throwsPath, "throw 'SAFE_TEST_IMPORT_FAILURE'", [System.Text.Encoding]::ASCII)
    Assert-Code -Expected 'MODULE_IMPORT_EXCEPTION' -Operation {
        Import-DaxHostRuntimeOwner -DeploymentRoot $productionRoot `
            -ModuleRelativePath 'scripts/throws.psm1'
    }

    $wrongExportsPath = Join-Path $productionScripts 'wrong-exports.psm1'
    [System.IO.File]::WriteAllText(
        $wrongExportsPath,
        "function Wrong-Export { return 'SAFE' }`r`nExport-ModuleMember -Function Wrong-Export`r`n",
        [System.Text.Encoding]::ASCII)
    Assert-Code -Expected 'MODULE_EXPORT_CONTRACT_FAILED' -Operation {
        Import-DaxHostRuntimeOwner -DeploymentRoot $productionRoot `
            -ModuleRelativePath 'scripts/wrong-exports.psm1'
    }

    $productionModulePath = Join-Path $productionScripts 'dax_windows_host_lane.psm1'
    [System.IO.File]::WriteAllText(
        $productionModulePath, $source, [System.Text.Encoding]::ASCII)
    $context = Import-DaxHostRuntimeOwner -DeploymentRoot $productionRoot `
        -ModuleRelativePath 'scripts/dax_windows_host_lane.psm1'
    try {
        if ($context.ModuleFileSha256 -notmatch '^[0-9a-f]{64}$' -or
            $context.SourcePathFingerprint -notmatch '^[0-9a-f]{64}$') {
            throw 'ASSERT_PRODUCTION_IMPORT_FINGERPRINT_FAILED'
        }
        $writeCommand = $context.WritePythonSelection
        & $writeCommand -Candidates @() | Out-Null
    } finally {
        Remove-Module -ModuleInfo $context.Module -Force -ErrorAction SilentlyContinue
    }

    # A stale module with the canonical basename must not collide with the
    # unique runner-owned module identity or its prefixed command names.
    $staleRoot = Join-Path $temporaryRoot 'stale-module'
    [System.IO.Directory]::CreateDirectory($staleRoot) | Out-Null
    $stalePath = Join-Path $staleRoot 'dax_windows_host_lane.psm1'
    [System.IO.File]::WriteAllText($stalePath, $source, [System.Text.Encoding]::ASCII)
    $stale = Import-Module -Name $stalePath -Global -PassThru -Force -ErrorAction Stop
    try {
        $context = Import-DaxHostRuntimeOwner -DeploymentRoot $productionRoot `
            -ModuleRelativePath 'scripts/dax_windows_host_lane.psm1'
        try {
            if ($context.Module.Path -eq $stale.Path) {
                throw 'ASSERT_STALE_MODULE_COLLISION'
            }
        } finally {
            Remove-Module -ModuleInfo $context.Module -Force -ErrorAction SilentlyContinue
        }
    } finally {
        Remove-Module -ModuleInfo $stale -Force -ErrorAction SilentlyContinue
    }
} finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        [System.IO.Directory]::Delete($temporaryRoot, $true)
    }
}

Write-Output ('DAX Windows module import contract: OK | edition={0} | version={1}' -f
    [string]$PSVersionTable.PSEdition, $PSVersionTable.PSVersion.ToString())
