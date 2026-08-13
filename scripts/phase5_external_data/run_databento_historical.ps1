[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Request = 'tests/evidence/phase5/RUN-P5-08-DATABENTO-001/request.json',
    [Parameter(Mandatory = $false)]
    [string]$RunId = 'RUN-P5-08-DATABENTO-001',
    [Parameter(Mandatory = $false)]
    [string]$EvidenceRoot = 'tests/evidence/phase5/RUN-P5-08-DATABENTO-001',
    [Parameter(Mandatory = $false)]
    [decimal]$MaxCostUsd = 25,
    [Parameter(Mandatory = $true)]
    [switch]$NoLive,
    [Parameter(Mandatory = $false)]
    [switch]$Execute
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location -LiteralPath $repoRoot

if (-not $NoLive) {
    throw 'NO_LIVE_REQUIRED'
}
if ($MaxCostUsd -ne 25) {
    throw 'COST_CAP_MUST_MATCH_APPROVED_VALUE'
}

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'PYTHON_3_12_VENV_NOT_FOUND'
}

$arguments = @(
    (Join-Path $repoRoot 'scripts\phase5_external_data\run_databento_historical.py'),
    '--request', $Request,
    '--run-id', $RunId,
    '--evidence-root', $EvidenceRoot,
    '--max-cost-usd', $MaxCostUsd.ToString([Globalization.CultureInfo]::InvariantCulture),
    '--no-live'
)
if ($Execute) {
    $arguments += '--execute'
}

& $python @arguments
exit $LASTEXITCODE
