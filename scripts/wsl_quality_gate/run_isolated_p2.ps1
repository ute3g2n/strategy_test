[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Distro,
    [Parameter(Mandatory = $true)][string]$RepositoryPath,
    [string]$RunId = "RUN-P2-IC-001-WSL",
    [string]$EvidencePhase = "phase2",
    [switch]$DryRun,
    [switch]$AllowRunningDistro,
    [switch]$RunAsRoot
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$EvidencePhase = $EvidencePhase.ToLowerInvariant()
if ($EvidencePhase -notmatch '^phase[0-9]+$') { throw "EvidencePhase must be phaseN" }
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$evidence = Join-Path $root "tests/evidence/$EvidencePhase/$RunId"
$config = Join-Path $env:UserProfile ".wslconfig"
$backup = Join-Path ([IO.Path]::GetTempPath()) ("autotrade-wslconfig-" + [guid]::NewGuid().ToString("N") + ".bak")
$hadConfig = Test-Path -LiteralPath $config -PathType Leaf
$originalHash = $null
$executionId = [guid]::NewGuid().ToString("N")
$debugRecords = [Collections.Generic.List[object]]::new()
$originalWslHostWrapperExecutionId = $env:WSL_HOST_WRAPPER_EXECUTION_ID
$originalWslVersion = $env:WSL_VERSION
$originalWslDistroName = $env:WSL_DISTRO_NAME
$originalWslEnv = $env:WSLENV
$originalHumanApproved = $env:QUALITY_GATE_HUMAN_APPROVED

function Convert-OutputText([object[]]$Output) {
    if ($null -eq $Output) { return "" }
    return (($Output | ForEach-Object { if ($null -eq $_) { "" } else { [string]$_ } }) -join "`n")
}
function Add-DebugRecord([string[]]$Arguments, [object[]]$Output, [int]$ExitCode, [string]$Kind) {
    $text = Convert-OutputText $Output
    $record = [ordered]@{
        kind = $Kind
        command = @("wsl.exe") + $Arguments
        powershell_location = (Get-Location).Path
        exit_code = $ExitCode
        output = $text
        recorded_at = (Get-Date).ToUniversalTime().ToString("o")
    }
    $debugRecords.Add($record)
    Write-Host ("[WSL-DEBUG] kind={0} exit={1} command={2}" -f $Kind, $ExitCode, ($record.command -join " "))
    if ($text) { Write-Host ("[WSL-DEBUG] output={0}" -f $text) }
}

function Invoke-WslText([string[]]$Arguments) {
    $output = & wsl.exe @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    Add-DebugRecord $Arguments $output $exitCode "strict"
    if ($exitCode -ne 0) {
        $detail = Convert-OutputText $output
        $command = (@("wsl.exe") + $Arguments) -join " "
        throw "wsl.exe failed ($exitCode) command=$command detail=$detail"
    }
    return ($output -join "`n")
}
function Invoke-WslCapture([string[]]$Arguments) {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & wsl.exe @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    Add-DebugRecord $Arguments $output $exitCode "capture"
    return @{ Output = ($output -join "`n"); ExitCode = $exitCode }
}
function Decode-Utf8Base64([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    try { return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($Value -replace '\s', ''))) }
    catch { return "" }
}
function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Write-Evidence([hashtable]$Value, [string]$Name) {
    New-Item -ItemType Directory -Force -Path $evidence | Out-Null
    $json = (($Value | ConvertTo-Json -Depth 8) -replace "`r`n", "`n") + "`n"
    [IO.File]::WriteAllText((Join-Path $evidence $Name), $json, (New-Object System.Text.UTF8Encoding($true)))
}
function Write-WslEvidence([hashtable]$Value, [string]$Name) {
    $json = $Value | ConvertTo-Json -Depth 8 -Compress
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
    $wslPath = "$RepositoryPath/tests/evidence/$EvidencePhase/$RunId/$Name"
    $command = "mkdir -p '$RepositoryPath/tests/evidence/$EvidencePhase/$RunId'; printf '%s' '$encoded' | base64 -d > '$wslPath'"
    $arguments = [string[]]("-d", $Distro, "--", "bash", "-lc", "cd / && $command")
    Invoke-WslText $arguments | Out-Null
}

try {
    Write-Host "WSL_HOST_WRAPPER_EXECUTION_ID=$executionId"
    $registryPath = Join-Path $root "scripts/quality_gate/trusted_scopes.json"
    if (-not (Test-Path -LiteralPath $registryPath -PathType Leaf)) { throw "trusted scope registry is missing" }
    $registry = Get-Content -LiteralPath $registryPath -Raw -Encoding utf8 | ConvertFrom-Json
    if ($null -eq $registry.scopes.PSObject.Properties[$RunId]) { throw "RunId is not registered in trusted scopes: $RunId" }
    if (-not [string]::IsNullOrWhiteSpace($env:WSL_INTEROP) -or -not [string]::IsNullOrWhiteSpace($env:WSL_DISTRO_NAME)) {
        throw "Run this wrapper from native Windows PowerShell, not from WSL. wsl --shutdown would terminate the execution environment (current distro: $($env:WSL_DISTRO_NAME))"
    }
    $versionArguments = [string[]]("--version")
    $wslVersion = Invoke-WslText $versionArguments
    $listArguments = [string[]]("-l", "-v")
    $list = (Invoke-WslText $listArguments) -replace "`r", ""
    $list = $list.Replace(([char]0).ToString(), "")
    $runningLines = @($list -split "`n" | Where-Object { $_ -match '\bRunning\b' })
    $otherRunningLines = @($runningLines | Where-Object { $_ -notlike "*$Distro*" })
    if ($otherRunningLines.Count -gt 0) { throw "Stop all WSL distributions other than the target before running this wrapper." }
    if ($runningLines.Count -gt 0 -and -not $AllowRunningDistro) { throw "Target WSL distribution is already Running. Stop Codex and WSL, then rerun with -AllowRunningDistro when launching from a \\wsl.localhost path." }
    $distroLine = ($list -split "`n" | Where-Object { $_ -like "*$Distro*" } | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($distroLine) -or $distroLine -notlike "* 2") { throw "Target distro is not registered as WSL version 2: $Distro" }
    if ($RepositoryPath -match '[\r\n''"]') { throw "RepositoryPath contains unsafe quoting characters" }
    $scope = $registry.scopes.PSObject.Properties[$RunId].Value
    $dbnScope = if ($null -ne $scope.PSObject.Properties["dbn_input"]) { $scope.dbn_input } else { $null }
    if ($null -ne $dbnScope) {
        $protectedPath = [string]$dbnScope.protected_path
        if ([string]::IsNullOrWhiteSpace($protectedPath) -or $protectedPath -notmatch '^/' -or $protectedPath -match '[\r\n''"]') {
            throw "trusted DBN protected path is invalid"
        }
        $inputCheckArguments = [string[]]("-d", $Distro, "--", "bash", "-lc", "test -f '$protectedPath' && ! test -L '$protectedPath'")
        $inputCheck = Invoke-WslCapture $inputCheckArguments
        if ($inputCheck.ExitCode -ne 0) {
            throw "protected DBN input is missing or is a symbolic link: $protectedPath"
        }
    }
}
catch {
    Write-Evidence @{ state = "BLOCKED"; reason = $_.Exception.Message; execution_id = $executionId } "preflight.json"
    Write-Evidence @{ state = "BLOCKED"; execution_id = $executionId; error = $_.Exception.ToString(); debug = @($debugRecords) } "preflight-debug.json"
    exit 20
}

if ($DryRun) {
    $shellScript = if ($EvidencePhase -eq "phase3") { "run_isolated_p3.sh" } else { "run_isolated_p2.sh" }
    [ordered]@{ state = "DRY_RUN"; isolation = "networkingMode=none; firewall=true"; shutdown = "wsl --shutdown"; wsl_command = "bash scripts/wsl_quality_gate/$shellScript '$RepositoryPath' '$RunId'"; restore = "restore original .wslconfig bytes and wsl --shutdown" } | ConvertTo-Json
    exit 0
}

try {
    if ($hadConfig) { [IO.File]::Copy($config, $backup, $true); $originalHash = Get-Hash $config }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [string[]]$lines = @()
    if ($hadConfig) { $lines = [string[]][IO.File]::ReadAllLines($config) }
    $section = -1
    for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim() -eq "[wsl2]") { $section = $i; break } }
    if ($section -lt 0) { $lines += "[wsl2]"; $section = $lines.Count - 1 }
    $end = $lines.Count
    for ($i = $section + 1; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim().StartsWith("[")) { $end = $i; break } }
    $body = [Collections.Generic.List[string]]::new()
    for ($i = $section + 1; $i -lt $end; $i++) { if ($lines[$i] -notmatch '^\s*(networkingMode|firewall)\s*=') { $body.Add($lines[$i]) } }
    $body.Add("networkingMode=none"); $body.Add("firewall=true")
    $newLines = [Collections.Generic.List[string]]::new()
    $newLines.AddRange([string[]]($lines[0..$section])); $newLines.AddRange($body)
    if ($end -lt $lines.Count) { $newLines.AddRange([string[]]($lines[$end..($lines.Count - 1)])) }
    [IO.File]::WriteAllText($config, (($newLines -join "`r`n") + "`r`n"), $utf8)
    & wsl.exe --shutdown
    if ($LASTEXITCODE -ne 0) { throw "wsl --shutdown failed" }
    $approvalPath = Join-Path $evidence "human-gate-user-declaration.md"
    $userApproved = (Test-Path -LiteralPath $approvalPath -PathType Leaf) -and [bool](Select-String -LiteralPath $approvalPath -Pattern "USER_APPROVAL_DECLARED=1" -Quiet)
    if ($userApproved) { $env:QUALITY_GATE_HUMAN_APPROVED = "1" } else { Remove-Item Env:QUALITY_GATE_HUMAN_APPROVED -ErrorAction SilentlyContinue }
    $wslVersionValue = (($wslVersion -replace "`0", "" -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1).Trim())
    $env:WSL_HOST_WRAPPER_EXECUTION_ID = $executionId; $env:WSL_VERSION = $wslVersionValue; $env:WSL_DISTRO_NAME = $Distro
    $wslEnvNames = [Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($env:WSLENV)) { $wslEnvNames.AddRange([string[]]($env:WSLENV -split ':')) }
    if (-not $wslEnvNames.Contains('WSL_HOST_WRAPPER_EXECUTION_ID')) { $wslEnvNames.Add('WSL_HOST_WRAPPER_EXECUTION_ID') }
    if (-not $wslEnvNames.Contains('WSL_VERSION')) { $wslEnvNames.Add('WSL_VERSION') }
    if ($userApproved -and -not $wslEnvNames.Contains('QUALITY_GATE_HUMAN_APPROVED')) { $wslEnvNames.Add('QUALITY_GATE_HUMAN_APPROVED') }
    $env:WSLENV = $wslEnvNames -join ':'
    $runnerArguments = [Collections.Generic.List[string]]::new()
    # root実行は本番運用で許可するが、通常ユーザー実行も選択できる。
    # 入力hash、対象範囲、ネットワーク隔離、固定Gateの検証は従来どおり先に行う。
    $runnerArguments.AddRange([string[]]("-d", $Distro))
    if ($RunAsRoot) { $runnerArguments.AddRange([string[]]("-u", "root")) }
    $shellScript = if ($EvidencePhase -eq "phase3") { "run_isolated_p3.sh" } else { "run_isolated_p2.sh" }
    $runnerArguments.AddRange([string[]]("--", "bash", "-lc", "cd / && cd '$RepositoryPath' && exec bash scripts/wsl_quality_gate/$shellScript '$RepositoryPath' '$RunId' '$executionId'"))
    $runner = Invoke-WslCapture $runnerArguments
    $verificationPathInWsl = "$RepositoryPath/tests/evidence/$EvidencePhase/$RunId/verification.json"
    $verificationArguments = [string[]]("-d", $Distro, "--", "bash", "-lc", "cd / && base64 -w0 '$verificationPathInWsl'")
    $verificationCapture = Invoke-WslCapture $verificationArguments
    $verification = $null
    $verificationRaw = Decode-Utf8Base64 ([string]$verificationCapture.Output)
    if ($verificationCapture.ExitCode -eq 0) {
        try { $verification = $verificationRaw | ConvertFrom-Json } catch { $verification = $null }
    }
    $hostIsolationPathInWsl = "$RepositoryPath/tests/evidence/$EvidencePhase/$RunId/host-isolation.json"
    $hostIsolationArguments = [string[]]("-d", $Distro, "--", "bash", "-lc", "cd / && cat '$hostIsolationPathInWsl'")
    $hostIsolationCapture = Invoke-WslCapture $hostIsolationArguments
    $hostIsolation = $null
    if ($hostIsolationCapture.ExitCode -eq 0) {
        try { $hostIsolation = $hostIsolationCapture.Output | ConvertFrom-Json } catch { $hostIsolation = $null }
    }
    $verificationId = if (($null -ne $verification) -and ($null -ne $verification.PSObject.Properties["host_wrapper_execution_id"])) { [string]$verification.host_wrapper_execution_id } else { "" }
    if ([string]::IsNullOrWhiteSpace($verificationId)) {
        $verificationIdMatch = [regex]::Match($verificationRaw, '"host_wrapper_execution_id"\s*:\s*"(?<id>[0-9a-fA-F]{32})"')
        if ($verificationIdMatch.Success) { $verificationId = $verificationIdMatch.Groups["id"].Value }
    }
    $hostIsolationId = if (($null -ne $hostIsolation) -and ($null -ne $hostIsolation.PSObject.Properties["host_wrapper_execution_id"])) { [string]$hostIsolation.host_wrapper_execution_id } else { "" }
    if (($null -ne $verification) -and [string]::IsNullOrWhiteSpace($verificationId) -and ($hostIsolationId -eq $executionId)) {
        $verification | Add-Member -NotePropertyName host_wrapper_execution_id -NotePropertyValue $executionId -Force
        $verificationId = $executionId
    }
    $captureState = if (($verificationId -eq $executionId) -and ($verificationCapture.ExitCode -eq 0)) { "CAPTURED" } else { "UNAVAILABLE" }
    Write-Evidence @{
        state = $captureState
        source_kind = "wsl_verification"
        execution_id = $executionId
        captured_at = (Get-Date).ToUniversalTime().ToString("o")
        source_repository_path = $RepositoryPath
        source_path = $verificationPathInWsl
        retrieval_exit_code = $verificationCapture.ExitCode
        verification = $verification
        verification_raw = $verificationRaw
        host_isolation = $hostIsolation
    } "wsl-verification-capture.json"
    if ($captureState -ne "CAPTURED") { throw "current WSL verification evidence was not captured for this wrapper execution" }
    Write-Evidence @{ state = if ($runner.ExitCode -eq 0) { "RUNNER_COMPLETED" } else { "RUNNER_NONZERO" }; output = $runner.Output; exit_code = $runner.ExitCode; execution_id = $executionId } "host-runner.json"
    if ($runner.ExitCode -ne 0) { throw "WSL runner returned non-zero; inspect verification.json" }
}
catch {
    Write-Evidence @{ state = "FAILED"; reason = $_.Exception.Message; execution_id = $executionId } "host-runner.json"
    Write-Evidence @{ state = "FAILED"; execution_id = $executionId; error = $_.Exception.ToString(); debug = @($debugRecords) } "host-runner-debug.json"
    throw
}
finally {
    if ($hadConfig) { [IO.File]::Copy($backup, $config, $true) } else { if (Test-Path -LiteralPath $config) { Remove-Item -LiteralPath $config -Force } }
    $restored = if ($hadConfig) { (Get-Hash $config) -eq $originalHash } else { -not (Test-Path -LiteralPath $config) }
    $restoreRecord = @{ state = if ($restored) { "RESTORED" } else { "FAILED" }; existed_before = $hadConfig; original_sha256 = $originalHash; restored = $restored; execution_id = $executionId }
    Write-Evidence $restoreRecord "restore.json"
    try { Write-WslEvidence $restoreRecord "restore.json" } catch { Write-Evidence @{ state = "FAILED"; reason = "WSL restore evidence write failed: $($_.Exception.Message)" } "restore-evidence-error.json" }
    & wsl.exe --shutdown
    Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue
    if ($null -eq $originalWslHostWrapperExecutionId) { Remove-Item Env:WSL_HOST_WRAPPER_EXECUTION_ID -ErrorAction SilentlyContinue } else { $env:WSL_HOST_WRAPPER_EXECUTION_ID = $originalWslHostWrapperExecutionId }
    if ($null -eq $originalWslVersion) { Remove-Item Env:WSL_VERSION -ErrorAction SilentlyContinue } else { $env:WSL_VERSION = $originalWslVersion }
    if ($null -eq $originalWslDistroName) { Remove-Item Env:WSL_DISTRO_NAME -ErrorAction SilentlyContinue } else { $env:WSL_DISTRO_NAME = $originalWslDistroName }
    if ($null -eq $originalWslEnv) { Remove-Item Env:WSLENV -ErrorAction SilentlyContinue } else { $env:WSLENV = $originalWslEnv }
    if ($null -eq $originalHumanApproved) { Remove-Item Env:QUALITY_GATE_HUMAN_APPROVED -ErrorAction SilentlyContinue } else { $env:QUALITY_GATE_HUMAN_APPROVED = $originalHumanApproved }
    if (-not $restored) { throw "wslconfig restoration verification failed" }
}
