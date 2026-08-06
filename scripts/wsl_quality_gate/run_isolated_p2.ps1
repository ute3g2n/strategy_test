[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Distro,
    [Parameter(Mandatory = $true)][string]$RepositoryPath,
    [string]$RunId = "RUN-P2-IC-001-WSL",
    [switch]$DryRun
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$evidence = Join-Path $root "test/evidence/phase2/$RunId"
$config = Join-Path $env:UserProfile ".wslconfig"
$backup = Join-Path ([IO.Path]::GetTempPath()) ("autotrade-wslconfig-" + [guid]::NewGuid().ToString("N") + ".bak")
$hadConfig = Test-Path -LiteralPath $config -PathType Leaf
$originalHash = $null
$executionId = [guid]::NewGuid().ToString("N")

function Invoke-WslText([string[]]$Arguments) {
    $output = & wsl.exe @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "wsl.exe failed ($LASTEXITCODE): $($output -join ' ')" }
    return ($output -join "`n")
}
function Invoke-WslCapture([string[]]$Arguments) {
    $output = & wsl.exe @Arguments 2>&1
    return @{ Output = ($output -join "`n"); ExitCode = $LASTEXITCODE }
}
function Get-Hash([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Write-Evidence([hashtable]$Value, [string]$Name) {
    New-Item -ItemType Directory -Force -Path $evidence | Out-Null
    $Value | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $evidence $Name) -Encoding utf8
}
function Write-WslEvidence([hashtable]$Value, [string]$Name) {
    $json = $Value | ConvertTo-Json -Depth 8 -Compress
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json))
    $wslPath = "$RepositoryPath/test/evidence/phase2/$RunId/$Name"
    $command = "mkdir -p '$RepositoryPath/test/evidence/phase2/$RunId'; printf '%s' '$encoded' | base64 -d > '$wslPath'"
    Invoke-WslText @("-d", $Distro, "--", "bash", "-lc", $command) | Out-Null
}

try {
    if ($RunId -ne "RUN-P2-IC-001-WSL") { throw "RunId is not the fixed WSL scope" }
    $wslVersion = Invoke-WslText @("--version")
    $list = Invoke-WslText @("-l", "-v")
    if ($list -notmatch [regex]::Escape($Distro) -or $list -notmatch "(?m)$([regex]::Escape($Distro)).*\s2\s*$") { throw "対象ディストリビューションがVERSION 2ではありません" }
    if ($RepositoryPath -match '[\r\n''"]') { throw "RepositoryPath contains unsafe quoting characters" }
    Invoke-WslText @("-d", $Distro, "--", "bash", "-lc", "test -d '$RepositoryPath' && test -f '$RepositoryPath/scripts/quality_gate/trusted_scopes.json' && test -f '$RepositoryPath/test/evidence/phase2/$RunId/run-manifest.json' && test -x '$RepositoryPath/.venv/bin/python'") | Out-Null
}
catch {
    Write-Evidence @{ state = "BLOCKED"; reason = $_.Exception.Message; execution_id = $executionId } "preflight.json"
    exit 20
}

if ($DryRun) {
    [ordered]@{ state = "DRY_RUN"; isolation = "networkingMode=none; firewall=true"; shutdown = "wsl --shutdown"; wsl_command = "bash scripts/wsl_quality_gate/run_isolated_p2.sh '$RepositoryPath' '$RunId'"; restore = "restore original .wslconfig bytes and wsl --shutdown" } | ConvertTo-Json
    exit 0
}

try {
    if ($hadConfig) { [IO.File]::Copy($config, $backup, $true); $originalHash = Get-Hash $config }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    $lines = if ($hadConfig) { [IO.File]::ReadAllLines($config) } else { @() }
    $section = -1
    for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim() -eq "[wsl2]") { $section = $i; break } }
    if ($section -lt 0) { $lines += "[wsl2]"; $section = $lines.Count - 1 }
    $end = $lines.Count
    for ($i = $section + 1; $i -lt $lines.Count; $i++) { if ($lines[$i].Trim().StartsWith("[")) { $end = $i; break } }
    $body = [Collections.Generic.List[string]]::new()
    for ($i = $section + 1; $i -lt $end; $i++) { if ($lines[$i] -notmatch '^\s*(networkingMode|firewall)\s*=') { $body.Add($lines[$i]) } }
    $body.Add("networkingMode=none"); $body.Add("firewall=true")
    $newLines = [Collections.Generic.List[string]]::new(); $newLines.AddRange($lines[0..$section]); $newLines.AddRange($body)
    if ($end -lt $lines.Count) { $newLines.AddRange($lines[$end..($lines.Count - 1)]) }
    [IO.File]::WriteAllText($config, (($newLines -join "`r`n") + "`r`n"), $utf8)
    & wsl.exe --shutdown
    if ($LASTEXITCODE -ne 0) { throw "wsl --shutdown failed" }
    $env:WSL_HOST_WRAPPER_EXECUTION_ID = $executionId; $env:WSL_VERSION = $wslVersion; $env:WSL_DISTRO_NAME = $Distro
    $runner = Invoke-WslCapture @("-d", $Distro, "--", "bash", "-lc", "cd '$RepositoryPath' && exec bash scripts/wsl_quality_gate/run_isolated_p2.sh '$RepositoryPath' '$RunId'")
    Write-Evidence @{ state = if ($runner.ExitCode -eq 0) { "RUNNER_COMPLETED" } else { "RUNNER_NONZERO" }; output = $runner.Output; exit_code = $runner.ExitCode; execution_id = $executionId } "host-runner.json"
    if ($runner.ExitCode -ne 0) { throw "WSL runner returned non-zero; inspect verification.json" }
}
catch {
    Write-Evidence @{ state = "FAILED"; reason = $_.Exception.Message; execution_id = $executionId } "host-runner.json"
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
    if (-not $restored) { throw "wslconfig restoration verification failed" }
}
