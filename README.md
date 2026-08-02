# strategy_test

## 自動コミット監視

このリポジトリには、ファイル変更を検知して自動的に `git commit` と
`git push` を行う監視コマンドがあります。

### ワンコマンドで開始

バックグラウンドで監視を開始します。

```bash
npm run watch-start
```

すでに監視が動いている場合は、新しい監視プロセスを増やさずに終了します。

### ワンコマンドで終了

バックグラウンドで動いている監視を終了します。

```bash
npm run watch-stop
```

### 手動で通常起動する場合

PowerShell または Git Bash で通常起動する場合:

```bash
npm run watch-commit
```

停止する場合は、起動中のターミナルで次を押します。

```text
Ctrl+C
```

### 従来のバックグラウンド起動

PowerShell でバックグラウンド起動する場合:

```powershell
Start-Process -FilePath npm.cmd -ArgumentList 'run watch-commit' -WorkingDirectory C:\project\strategy_test -WindowStyle Hidden
```

Git Bash でバックグラウンド起動する場合:

```bash
nohup npm run watch-commit > watch-commit.log 2> watch-commit.err.log &
```

### 従来のバックグラウンド停止

PowerShell でプロセス ID を確認する場合:

```powershell
Get-Process node,cmd -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime
```

確認したプロセス ID を指定して停止します。

```powershell
Stop-Process -Id <PID1>,<PID2>,<PID3>,<PID4>
```

Git Bash でプロセス ID を確認する場合:

```bash
ps -ef | grep chokidar
```

該当するプロセス ID を指定して停止します。

```bash
kill <PID>
```

### 監視の仕様

- `.git`、`node_modules`、`.env`、`.env.*`、`*.log` は監視対象外です。
- 連続変更による過剰なコミットを防ぐため、3秒待ってから実行します。
- コミットメッセージは `auto: update by Codex [YYYY-MM-DD HH:MM:SS]` 形式です。
- 実際のコミット処理は `auto-commit.cmd` 経由で `auto-commit.sh` を実行します。
