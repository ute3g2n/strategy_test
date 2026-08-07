[CmdletBinding()]
param(
    [string]$Distro = "Ubuntu-24.04",
    [string]$RepositoryPath = "/home/oue/strategy_test",
    [string]$RunId = "RUN-P2-IC-001-WSL",
    [switch]$AllowRunningDistro
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$evidenceRoot = Join-Path $repositoryRoot "test/evidence/phase2/$RunId"
$automationRoot = Join-Path $evidenceRoot "automation"
$wrapperPath = Join-Path $PSScriptRoot "run_isolated_p2.ps1"
$startedAt = (Get-Date).ToUniversalTime()

New-Item -ItemType Directory -Force -Path $automationRoot | Out-Null

function Convert-OutputText([object[]]$Output) {
    if ($null -eq $Output) { return "" }
    return (($Output | ForEach-Object { if ($null -eq $_) { "" } else { [string]$_ } }) -join "`n")
}

function Write-TextFile([string]$Path, [string]$Text) {
    Set-Content -LiteralPath $Path -Value $Text -Encoding utf8
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

$wrapperArguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $wrapperPath,
    "-Distro", $Distro,
    "-RepositoryPath", $RepositoryPath,
    "-RunId", $RunId
)
if ($AllowRunningDistro) { $wrapperArguments += "-AllowRunningDistro" }
$wrapperCommand = "powershell.exe " + (($wrapperArguments | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' }) -join " ")
$wrapperResult = Invoke-Captured "powershell.exe" $wrapperArguments 180
$wrapperOutputPath = Join-Path $automationRoot "run-test-wrapper.log"
$wrapperLog = "COMMAND: $wrapperCommand`n`n$($wrapperResult.output)"
if ($wrapperResult.error) { $wrapperLog += "`n`nLAUNCH_ERROR:`n$($wrapperResult.error)" }
Write-TextFile $wrapperOutputPath $wrapperLog

$evidenceRootInWsl = "$RepositoryPath/test/evidence/phase2/$RunId"
$preflightPath = Join-Path $evidenceRoot "preflight.json"
$verificationPath = Join-Path $evidenceRoot "verification.json"
$evidenceCommand = "cat '$evidenceRootInWsl/preflight.json' 2>/dev/null || cat '$evidenceRootInWsl/verification.json' 2>/dev/null"
$preflightIsRecent = Test-Path -LiteralPath $preflightPath -and ((Get-Item -LiteralPath $preflightPath).LastWriteTimeUtc -ge $startedAt.AddSeconds(-2))
$verificationIsRecent = Test-Path -LiteralPath $verificationPath -and ((Get-Item -LiteralPath $verificationPath).LastWriteTimeUtc -ge $startedAt.AddSeconds(-2))
$preferPreflight = ($wrapperResult.exit_code -eq 20) -or (($null -eq $wrapperResult.exit_code) -and $preflightIsRecent)
$evidenceCandidates = if ($preferPreflight) {
    @(@{ Path = $preflightPath; Command = "Get-Content $preflightPath" }, @{ Path = $verificationPath; Command = "Get-Content $verificationPath" })
} else {
    @(@{ Path = $verificationPath; Command = "Get-Content $verificationPath" }, @{ Path = $preflightPath; Command = "Get-Content $preflightPath" })
}
$localEvidence = $evidenceCandidates | Where-Object { Test-Path -LiteralPath $_.Path } | Select-Object -First 1
if ($null -ne $localEvidence) {
    $evidenceResult = [ordered]@{ exit_code = 0; output = Get-Content -LiteralPath $localEvidence.Path -Raw; error = "" }
    $evidenceCommand = $localEvidence.Command
} else {
    $evidenceResult = Invoke-Captured "wsl.exe" @("-d", $Distro, "--", "bash", "-lc", $evidenceCommand) 45
}
$evidenceOutputPath = Join-Path $automationRoot "run-test-evidence.log"
$evidenceLog = "COMMAND: $evidenceCommand`n`n$($evidenceResult.output)"
if ($evidenceResult.error) { $evidenceLog += "`n`nLAUNCH_ERROR:`n$($evidenceResult.error)" }
Write-TextFile $evidenceOutputPath $evidenceLog

$evidenceState = ""
try { $evidenceState = ([string]$evidenceResult.output | ConvertFrom-Json).state } catch { $evidenceState = "" }
$effectiveWrapperExitCode = $wrapperResult.exit_code
if ($null -eq $effectiveWrapperExitCode) {
    $effectiveWrapperExitCode = if ($evidenceState -eq "BLOCKED") { 20 } else { 1 }
}

$exitCodePath = Join-Path $automationRoot "run-test-exit-code.txt"
Write-TextFile $exitCodePath ([string]$effectiveWrapperExitCode)

$finishedAt = (Get-Date).ToUniversalTime()
$state = if ($effectiveWrapperExitCode -eq 0) { "COMPLETED" } elseif ($effectiveWrapperExitCode -eq 20) { "BLOCKED" } else { "FAILED" }
$summary = [ordered]@{
    state = $state
    run_id = $RunId
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
    preflight_is_recent = $preflightIsRecent
    verification_is_recent = $verificationIsRecent
    files = [ordered]@{
        wrapper_log = $wrapperOutputPath
        evidence_log = $evidenceOutputPath
        exit_code = $exitCodePath
    }
}
$summaryPath = Join-Path $automationRoot "run-test-summary.json"
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $summaryPath -Encoding utf8

$runnerWasInvoked = $wrapperResult.output -match 'kind=capture'
if ($AllowRunningDistro -and $runnerWasInvoked) { & wsl.exe --shutdown | Out-Null }

Write-Host "run_test.ps1 completed: state=$state wrapper_exit_code=$effectiveWrapperExitCode"
Write-Host "summary=$summaryPath"
exit $effectiveWrapperExitCode
