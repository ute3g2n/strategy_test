[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$storageRoot = 'E:\strategy_test_data\autotrade'
$runtimeRoot = Join-Path $storageRoot 'logs'
$uiRoot = Join-Path $projectRoot 'ui\app'
$stopLog = Join-Path $runtimeRoot 'stop.log'

function Write-StopMessage {
    param([string]$Message)

    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    if (Test-Path -LiteralPath (Split-Path -Parent $stopLog) -PathType Container) {
        Add-Content -LiteralPath $stopLog -Value $line -Encoding UTF8
    }
}

function Get-ProcessSnapshot {
    try {
        return @(Get-CimInstance Win32_Process -ErrorAction Stop)
    }
    catch {
        return @()
    }
}

try {
    if (Test-Path -LiteralPath 'E:\' -PathType Container) {
        New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
    }

    $processes = Get-ProcessSnapshot
    $processById = @{}
    foreach ($process in $processes) {
        $processById[[int]$process.ProcessId] = $process
    }

    $directTargets = foreach ($process in $processes) {
        $commandLine = [string]$process.CommandLine
        $apiProcess = $commandLine -like "*$projectRoot*" -and $commandLine -match '(?i)backtest_api_server\.py' -and $commandLine -match '(?i)(--port\s+8765|8765)'
        $uiProcess = $commandLine -like "*$uiRoot*" -and $commandLine -match '(?i)(npm.*preview|vite.*preview)' -and $commandLine -match '(?i)(--port\s+4173|4173)'
        if ($apiProcess -or $uiProcess) {
            $process
        }
    }

    $targetById = @{}
    foreach ($directTarget in $directTargets) {
        $targetById[[int]$directTarget.ProcessId] = $directTarget
        $parentId = [int]$directTarget.ParentProcessId
        while ($parentId -gt 0 -and $processById.ContainsKey($parentId)) {
            $parent = $processById[$parentId]
            $parentCommandLine = [string]$parent.CommandLine
            if ($parentCommandLine -notmatch '(?i)(npm.*preview|vite.*preview|cmd.*preview)') {
                break
            }
            $targetById[$parentId] = $parent
            $parentId = [int]$parent.ParentProcessId
        }
    }

    $uniqueTargets = @($targetById.Values | Sort-Object ProcessId -Descending)
    if ($uniqueTargets.Count -eq 0) {
        Write-StopMessage 'AutoTrade API/UIの対象プロセスは見つかりませんでした。'
        exit 0
    }

    foreach ($target in $uniqueTargets) {
        $commandLine = [string]$target.CommandLine
        Write-StopMessage "対象プロセスを停止します。PID=$($target.ProcessId) CommandLine=$commandLine"
        Stop-Process -Id ([int]$target.ProcessId) -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep -Milliseconds 500
    $remaining = @(Get-ProcessSnapshot | Where-Object {
        $commandLine = [string]$_.CommandLine
        ($commandLine -like "*$projectRoot*" -and $commandLine -match '(?i)backtest_api_server\.py' -and $commandLine -match '(?i)(--port\s+8765|8765)') -or
        ($commandLine -like "*$uiRoot*" -and $commandLine -match '(?i)(npm.*preview|vite.*preview)' -and $commandLine -match '(?i)(--port\s+4173|4173)')
    })
    if ($remaining.Count -gt 0) {
        throw "一部のAutoTrade対象プロセスが残っています。タスクマネージャーと$runtimeRootのログを確認してください。"
    }

    Write-StopMessage 'AutoTrade API/UIを停止しました。'
    exit 0
}
catch {
    Write-StopMessage "停止失敗: $($_.Exception.Message)"
    exit 1
}
