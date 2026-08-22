[CmdletBinding()]
param()

Set-StrictMode -Version Latest

function ConvertFrom-JsonFile([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json) }
    catch { return $null }
}

function Test-NotBefore([string]$Value, [DateTimeOffset]$StartedAt) {
    try {
        # ConvertFrom-Json may materialize an ISO-8601 ``Z`` value as a local
        # DateTime before this function receives it.  Gate timestamps are UTC;
        # preserve that contract when the timezone marker has been discarded.
        $parsed = [DateTimeOffset]::Parse(
            $Value,
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::AssumeUniversal -bor
                [Globalization.DateTimeStyles]::AdjustToUniversal
        )
        return ($parsed -ge $StartedAt.ToUniversalTime())
    }
    catch { return $false }
}

function Select-AutomationEvidence {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][int]$WrapperExitCode,
        [Parameter(Mandatory = $true)][DateTimeOffset]$StartedAt,
        [Parameter(Mandatory = $true)][string]$ExpectedExecutionId,
        [string]$PreflightPath,
        [Parameter(Mandatory = $true)][string]$WslVerificationCapturePath
    )

    if ($WrapperExitCode -eq 20) {
        $preflight = ConvertFrom-JsonFile $PreflightPath
        $preflightIsCurrent = ($null -ne $preflight) -and
            ($preflight.execution_id -eq $ExpectedExecutionId) -and
            ((Get-Item -LiteralPath $PreflightPath).LastWriteTimeUtc -ge $StartedAt.UtcDateTime)
        if ($preflightIsCurrent) {
            return [ordered]@{
                selected = $true
                source = "current_host_preflight"
                state = [string]$preflight.state
                json = ($preflight | ConvertTo-Json -Depth 8 -Compress)
                command = "Get-Content $PreflightPath"
                reason = ""
            }
        }
        return [ordered]@{ selected = $false; source = ""; state = ""; json = ""; command = ""; reason = "current preflight evidence is missing or does not match the wrapper execution ID" }
    }

    $capture = ConvertFrom-JsonFile $WslVerificationCapturePath
    $verification = if (($null -ne $capture) -and ($null -ne $capture.PSObject.Properties['verification'])) { $capture.verification } else { $null }
    if (($null -eq $verification) -and ($null -ne $capture) -and ($null -ne $capture.PSObject.Properties['verification_raw'])) {
        try { $verification = ([string]$capture.verification_raw | ConvertFrom-Json) } catch { $verification = $null }
    }
    $captureIsCurrent = ($null -ne $capture) -and
        ($capture.state -eq "CAPTURED") -and
        ($capture.source_kind -eq "wsl_verification") -and
        ($capture.execution_id -eq $ExpectedExecutionId) -and
        ($null -ne $verification) -and
        ($verification.host_wrapper_execution_id -eq $ExpectedExecutionId) -and
        (Test-NotBefore ([string]$capture.captured_at) $StartedAt)
    if (-not $captureIsCurrent) {
        return [ordered]@{ selected = $false; source = ""; state = ""; json = ""; command = ""; reason = "current WSL verification capture is missing or does not match the wrapper execution ID" }
    }

    return [ordered]@{
        selected = $true
        source = "wsl_verification_capture"
        state = [string]$verification.state
        json = ($verification | ConvertTo-Json -Depth 8 -Compress)
        command = "Get-Content $WslVerificationCapturePath (captured from WSL during isolation)"
        reason = ""
    }
}
