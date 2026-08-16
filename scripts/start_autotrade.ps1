[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [ValidateRange(10, 300)]
    [int]$WaitSeconds = 60
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$uiRoot = Join-Path $projectRoot 'ui\mock'
$apiScript = Join-Path $projectRoot 'scripts\phase5r\backtest_api_server.py'
$storageRoot = 'E:\strategy_test_data\autotrade'
$runtimeRoot = Join-Path $storageRoot 'logs'
$startupLog = Join-Path $runtimeRoot 'startup.log'
$buildLog = Join-Path $runtimeRoot 'build.log'
$apiLog = Join-Path $runtimeRoot 'api.log'
$apiErrorLog = Join-Path $runtimeRoot 'api.error.log'
$uiLog = Join-Path $runtimeRoot 'ui.log'
$uiErrorLog = Join-Path $runtimeRoot 'ui.error.log'
$apiUrl = 'http://127.0.0.1:8765'
$uiUrl = 'http://127.0.0.1:4173'

function Write-StartupMessage {
    param([string]$Message)

    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Write-Host $line
    if (Test-Path -LiteralPath (Split-Path -Parent $startupLog) -PathType Container) {
        Add-Content -LiteralPath $startupLog -Value $line -Encoding UTF8
    }
}

function Test-HttpEndpoint {
    param([Parameter(Mandatory)][string]$Uri)

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 2
        return ([int]$response.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Wait-HttpEndpoint {
    param([Parameter(Mandatory)][string]$Uri)

    $deadline = (Get-Date).AddSeconds($WaitSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpEndpoint -Uri $Uri) {
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Get-ListeningPortConnection {
    param([Parameter(Mandatory)][int]$Port)

    try {
        return @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop)
    }
    catch {
        return @()
    }
}

function Invoke-NpmCommand {
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$OutputPath
    )

    Push-Location $uiRoot
    try {
        $output = & $npmCommand @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        $output | Set-Content -LiteralPath $OutputPath -Encoding UTF8
        $output | ForEach-Object { Write-Host $_ }
    }
    finally {
        Pop-Location
    }

    if ($exitCode -ne 0) {
        throw "npmコマンドが失敗しました。exit=$exitCode。ログ: $OutputPath"
    }
}

function Stop-StartedProcess {
    param([int]$ProcessId)

    try {
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    }
    catch {
        Write-StartupMessage "起動途中のプロセスを停止できませんでした。PID=$ProcessId"
    }
}

$startedProcessIds = New-Object System.Collections.Generic.List[int]

try {
    if (-not (Test-Path -LiteralPath 'E:\' -PathType Container)) {
        throw 'Eドライブが見つかりません。CドライブやWindows一時フォルダーへはフォールバックしません。'
    }
    New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null

    if (-not (Test-Path -LiteralPath $uiRoot -PathType Container)) {
        throw "UIフォルダーが見つかりません: $uiRoot"
    }
    if (-not (Test-Path -LiteralPath $apiScript -PathType Leaf)) {
        throw "API起動スクリプトが見つかりません: $apiScript"
    }

    $npmCommand = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
    if ([string]::IsNullOrWhiteSpace($npmCommand)) {
        throw 'npmが見つかりません。Node.jsをインストールしてから、もう一度実行してください。'
    }

    $venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPython -PathType Leaf) {
        $pythonCommand = $venvPython
        $pythonArguments = @($apiScript, '--host', '127.0.0.1', '--port', '8765')
    }
    else {
        $pythonLauncher = (Get-Command py.exe -ErrorAction SilentlyContinue).Source
        if ([string]::IsNullOrWhiteSpace($pythonLauncher)) {
            throw 'Pythonが見つかりません。.venvまたはPython Launcher (py -3)を準備してから、もう一度実行してください。'
        }
        $pythonCommand = $pythonLauncher
        $pythonArguments = @('-3', $apiScript, '--host', '127.0.0.1', '--port', '8765')
    }

    if (-not (Test-Path -LiteralPath (Join-Path $uiRoot 'package-lock.json') -PathType Leaf)) {
        throw "package-lock.jsonが見つかりません: $uiRoot"
    }

    Write-StartupMessage 'AutoTradeアプリの一括起動を開始します。外部接続は行いません。'

    if (-not (Test-Path -LiteralPath (Join-Path $uiRoot 'node_modules') -PathType Container)) {
        Write-StartupMessage 'UI依存パッケージがないため、npm ciを実行します。'
        Invoke-NpmCommand -Arguments @('ci') -OutputPath (Join-Path $runtimeRoot 'npm-ci.log')
    }

    Write-StartupMessage 'UIをbuildします。'
    Invoke-NpmCommand -Arguments @('run', 'build') -OutputPath $buildLog

    $apiReady = Test-HttpEndpoint -Uri "$apiUrl/health"
    $uiReady = Test-HttpEndpoint -Uri $uiUrl

    if (-not $apiReady) {
        $apiListeners = Get-ListeningPortConnection -Port 8765
        if ($apiListeners.Count -gt 0) {
            $pids = ($apiListeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ', '
            throw "8765番ポートは既に使われていますが、AutoTrade APIのhealth checkに失敗しました。PID=$pids。既存アプリを確認してから再実行してください。"
        }

        Write-StartupMessage 'AutoTrade Application APIを起動します。'
        $apiProcess = Start-Process -FilePath $pythonCommand -ArgumentList $pythonArguments -WorkingDirectory $projectRoot -RedirectStandardOutput $apiLog -RedirectStandardError $apiErrorLog -WindowStyle Hidden -PassThru
        $startedProcessIds.Add($apiProcess.Id)
        Write-StartupMessage "API process started. PID=$($apiProcess.Id)"
        if (-not (Wait-HttpEndpoint -Uri "$apiUrl/health")) {
            throw "APIのhealth checkが$WaitSeconds秒以内に成功しませんでした。ログ: $apiLog / $apiErrorLog"
        }
    }
    else {
        Write-StartupMessage 'AutoTrade Application APIは既に起動済みです。二重起動しません。'
    }

    if (-not $uiReady) {
        $uiListeners = Get-ListeningPortConnection -Port 4173
        if ($uiListeners.Count -gt 0) {
            $pids = ($uiListeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ', '
            throw "4173番ポートは既に使われていますが、AutoTrade UIのhealth checkに失敗しました。PID=$pids。既存アプリを確認してから再実行してください。"
        }

        Write-StartupMessage 'AutoTrade UI previewを起動します。'
        $uiProcess = Start-Process -FilePath $npmCommand -ArgumentList @('run', 'preview', '--', '--host', '127.0.0.1', '--port', '4173') -WorkingDirectory $uiRoot -RedirectStandardOutput $uiLog -RedirectStandardError $uiErrorLog -WindowStyle Hidden -PassThru
        $startedProcessIds.Add($uiProcess.Id)
        Write-StartupMessage "UI process started. PID=$($uiProcess.Id)"
        if (-not (Wait-HttpEndpoint -Uri $uiUrl)) {
            throw "UIのhealth checkが$WaitSeconds秒以内に成功しませんでした。ログ: $uiLog / $uiErrorLog"
        }
    }
    else {
        Write-StartupMessage 'AutoTrade UIは既に起動済みです。二重起動しません。'
    }

    if (-not (Test-HttpEndpoint -Uri "$apiUrl/health")) {
        throw "最終確認でAPIが応答しません。ログ: $apiLog / $apiErrorLog"
    }
    if (-not (Test-HttpEndpoint -Uri $uiUrl)) {
        throw "最終確認でUIが応答しません。ログ: $uiLog / $uiErrorLog"
    }

    Write-StartupMessage "起動完了。ブラウザURL: $uiUrl"
    Write-StartupMessage "ログ: $runtimeRoot（Eドライブ）"
    if (-not $NoBrowser) {
        Start-Process $uiUrl | Out-Null
    }
    exit 0
}
catch {
    $message = $_.Exception.Message
    Write-StartupMessage "起動失敗: $message"
    Write-Host "APIログ（保存できる場合）: $apiLog"
    Write-Host "UIログ（保存できる場合）: $uiLog"
    foreach ($processId in $startedProcessIds) {
        Stop-StartedProcess -ProcessId $processId
    }
    exit 1
}
