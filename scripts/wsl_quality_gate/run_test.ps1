[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu-24.04",
    [string]$RepositoryPath = "/home/oue/strategy_test",
    [string]$RunId = "RUN-P2-IC-001-WSL",
    [switch]$AllowRunningDistro,
    [switch]$RunAsRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$registryPath = Join-Path $repositoryRoot "scripts/quality_gate/trusted_scopes.json"
$registry = Get-Content -LiteralPath $registryPath -Raw -Encoding utf8 | ConvertFrom-Json
$scopeProperty = $registry.scopes.PSObject.Properties[$RunId]
if ($null -eq $scopeProperty) { throw "RunId is not registered in trusted scopes: $RunId" }
$evidencePhase = [string]$scopeProperty.Value.phase_id
if ($evidencePhase -notmatch '^phase[0-9]+$') { throw "trusted scope phase_id is invalid: $evidencePhase" }
$evidenceRoot = Join-Path $repositoryRoot "tests/evidence/$evidencePhase/$RunId"
$automationRoot = Join-Path $evidenceRoot "automation"
$wrapperPath = Join-Path $PSScriptRoot "run_isolated_p2.ps1"
$evidenceSelectorPath = Join-Path $PSScriptRoot "select_automation_evidence.ps1"
$startedAt = (Get-Date).ToUniversalTime()

New-Item -ItemType Directory -Force -Path $automationRoot | Out-Null

function Convert-OutputText([object[]]$Output) {
    if ($null -eq $Output) { return "" }
    return (($Output | ForEach-Object { if ($null -eq $_) { "" } else { [string]$_ } }) -join "`n")
}

function Write-TextFile([string]$Path, [string]$Text) {
    $normalized = ($Text -replace "`r`n", "`n")
    [IO.File]::WriteAllText($Path, $normalized, (New-Object System.Text.UTF8Encoding($true)))
}

function Invoke-Captured([string]$FilePath, [string[]]$Arguments, [int]$TimeoutSeconds = 120) {
    $token = [guid]::NewGuid().ToString("N")
    $stdoutPath = Join-Path ([IO.Path]::GetTempPath()) ("run-test-$token.stdout")
    $stderrPath = Join-Path ([IO.Path]::GetTempPath()) ("run-test-$token.stderr")
    try {
        $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru -WindowStyle Hidden
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $process.Kill()
            $process.WaitForExit()
            return [ordered]@{
                exit_code = 124
                output = ""
                error = "TIMEOUT after $TimeoutSeconds seconds: $FilePath"
            }
        }
        $process.Refresh()
        $output = if (Test-Path -LiteralPath $stdoutPath) { Get-Content -LiteralPath $stdoutPath -Raw } else { "" }
        $error = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw } else { "" }
        return [ordered]@{
            exit_code = $process.ExitCode
            output = [string]$output
            error = [string]$error
        }
    }
    catch {
        return [ordered]@{
            exit_code = 1
            output = ""
            error = $_.Exception.ToString()
        }
    }
    finally {
        Remove-Item -LiteralPath $stdoutPath, $stderrPath -Force -ErrorAction SilentlyContinue
    }
}

. $evidenceSelectorPath

$wrapperArguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $wrapperPath,
    "-Distro", $Distro,
    "-RepositoryPath", $RepositoryPath,
    "-RunId", $RunId,
    "-EvidencePhase", $evidencePhase
)
if ($AllowRunningDistro) { $wrapperArguments += "-AllowRunningDistro" }
if ($RunAsRoot) { $wrapperArguments += "-RunAsRoot" }
$wrapperCommand = "powershell.exe " + (($wrapperArguments | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }) -join " ")
$wrapperResult = Invoke-Captured "powershell.exe" $wrapperArguments 180
$wrapperOutputPath = Join-Path $automationRoot "run-test-wrapper.log"
$wrapperLog = "COMMAND: $wrapperCommand`n`n$($wrapperResult.output)"
if ($wrapperResult.error) { $wrapperLog += "`n`nLAUNCH_ERROR:`n$($wrapperResult.error)" }
Write-TextFile $wrapperOutputPath $wrapperLog

$preflightPath = Join-Path $evidenceRoot "preflight.json"
$wslVerificationCapturePath = Join-Path $evidenceRoot "wsl-verification-capture.json"
$preflightIsRecent = (Test-Path -LiteralPath $preflightPath) -and ((Get-Item -LiteralPath $preflightPath).LastWriteTimeUtc -ge $startedAt.AddSeconds(-2))
$preferPreflight = $wrapperResult.exit_code -eq 20
$executionIdMatch = [regex]::Match([string]$wrapperResult.output, '(?m)^WSL_HOST_WRAPPER_EXECUTION_ID=([0-9a-f]{32})\s*$')
$expectedExecutionId = if ($executionIdMatch.Success) { $executionIdMatch.Groups[1].Value } else { "" }
$selection = if ($expectedExecutionId) {
    Select-AutomationEvidence -WrapperExitCode $wrapperResult.exit_code -StartedAt $startedAt -ExpectedExecutionId $expectedExecutionId -PreflightPath $preflightPath -WslVerificationCapturePath $wslVerificationCapturePath
} else {
    [ordered]@{ selected = $false; source = ""; state = ""; json = ""; command = ""; reason = "wrapper execution ID was not emitted" }
}
$evidenceCommand = [string]$selection.command
if ($selection.selected) {
    $evidenceResult = [ordered]@{ exit_code = 0; output = [string]$selection.json; error = "" }
} else {
    $evidenceResult = [ordered]@{ exit_code = 1; output = ""; error = [string]$selection.reason }
}
$evidenceOutputPath = Join-Path $automationRoot "run-test-evidence.log"
$evidenceLog = "COMMAND: $evidenceCommand`n`n$($evidenceResult.output)"
if ($evidenceResult.error) { $evidenceLog += "`n`nLAUNCH_ERROR:`n$($evidenceResult.error)" }
Write-TextFile $evidenceOutputPath $evidenceLog

$evidenceState = ""
try { $evidenceState = ([string]$evidenceResult.output | ConvertFrom-Json).state } catch { $evidenceState = "" }
$effectiveWrapperExitCode = $wrapperResult.exit_code
if ($evidenceResult.exit_code -ne 0) {
    $effectiveWrapperExitCode = if ($wrapperResult.exit_code -eq 20) { 20 } else { 1 }
} elseif ($evidenceState -in @("BLOCKED", "HUMAN_GATE_REQUIRED")) {
    $effectiveWrapperExitCode = 20
} elseif ($null -eq $effectiveWrapperExitCode) {
    $effectiveWrapperExitCode = if ($evidenceState -eq "PASS") { 0 } elseif ($evidenceState -in @("BLOCKED", "HUMAN_GATE_REQUIRED")) { 20 } else { 1 }
}

$exitCodePath = Join-Path $automationRoot "run-test-exit-code.txt"
Write-TextFile $exitCodePath ([string]$effectiveWrapperExitCode)

$finishedAt = (Get-Date).ToUniversalTime()
$state = if ($effectiveWrapperExitCode -eq 0) { if ($evidenceState -eq "PASS") { "PASS" } else { "COMPLETED" } } elseif ($effectiveWrapperExitCode -eq 20) { "BLOCKED" } else { "FAILED" }
$summary = [ordered]@{
    state = $state
    run_id = $RunId
    evidence_phase = $evidencePhase
    distro = $Distro
    repository_path = $RepositoryPath
    started_at = $startedAt.ToString("o")
    finished_at = $finishedAt.ToString("o")
    wrapper_command = $wrapperCommand
    wrapper_exit_code = $effectiveWrapperExitCode
    raw_wrapper_exit_code = $wrapperResult.exit_code
    wrapper_error = $wrapperResult.error
    evidence_command = $evidenceCommand
    evidence_exit_code = $evidenceResult.exit_code
    evidence_error = $evidenceResult.error
    evidence_state = $evidenceState
    evidence_source = $selection.source
    expected_execution_id = $expectedExecutionId
    preflight_is_recent = $preflightIsRecent
    wsl_verification_capture_path = $wslVerificationCapturePath
    files = [ordered]@{
        wrapper_log = $wrapperOutputPath
        evidence_log = $evidenceOutputPath
        exit_code = $exitCodePath
    }
}
$summaryPath = Join-Path $automationRoot "run-test-summary.json"
$summaryJson = (($summary | ConvertTo-Json -Depth 8) -replace "`r`n", "`n") + "`n"
Write-TextFile $summaryPath $summaryJson

$runnerWasInvoked = $wrapperResult.output -match 'kind=capture'

Write-Host "run_test.ps1 completed: state=$state wrapper_exit_code=$effectiveWrapperExitCode"
Write-Host "summary=$summaryPath"
exit $effectiveWrapperExitCode
