# strategy_test

## 自動コミット監視

このリポジトリには、ファイル変更を検知して自動的に `git commit` と
`git push` を行う監視コマンドがあります。

### 開始方法

PowerShell または Git Bash で通常起動する場合:

```bash
npm run watch-commit
```

PowerShell でバックグラウンド起動する場合:

```powershell
Start-Process -FilePath npm.cmd -ArgumentList 'run watch-commit' -WorkingDirectory C:\project\strategy_test -WindowStyle Hidden
```

Git Bash でバックグラウンド起動する場合:

```bash
nohup npm run watch-commit > watch-commit.log 2> watch-commit.err.log &
```

### 停止方法

通常起動している場合は、起動中のターミナルで次を押します。

```text
Ctrl+C
```

PowerShell でバックグラウンド起動している場合は、まず関連する `node` と `cmd` の
プロセス ID を確認します。

```powershell
Get-Process node,cmd -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime
```

確認したプロセス ID を指定して停止します。

```powershell
Stop-Process -Id <PID1>,<PID2>,<PID3>,<PID4>
```

例:

```powershell
Stop-Process -Id 19652,37176,27272,35932
```

Git Bash でバックグラウンド起動している場合は、プロセス ID を確認します。

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
- 実際の処理は `auto-commit.cmd` 経由で `auto-commit.sh` を実行します。
