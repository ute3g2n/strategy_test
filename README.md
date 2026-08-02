# strategy_test

## Auto Commit Watcher

This repository includes a file watcher that automatically commits and pushes
file changes to the current Git branch.

### Start

Run the watcher in the foreground:

```powershell
npm run watch-commit
```

To run it in the background on Windows:

```powershell
Start-Process -FilePath npm.cmd -ArgumentList 'run watch-commit' -WorkingDirectory C:\project\strategy_test -WindowStyle Hidden
```

### Stop

If the watcher is running in the foreground, press:

```text
Ctrl+C
```

If the watcher is running in the background, find the related `node` and `cmd`
processes:

```powershell
Get-Process node,cmd -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime
```

Then stop the watcher processes by ID:

```powershell
Stop-Process -Id <PID1>,<PID2>,<PID3>,<PID4>
```

For example, if the watcher was started with process IDs `19652`, `37176`,
`27272`, and `35932`:

```powershell
Stop-Process -Id 19652,37176,27272,35932
```

### Notes

- The watcher ignores `.git`, `node_modules`, `.env`, `.env.*`, and `*.log`.
- Changes are debounced for 3 seconds before commit.
- Commit messages use the format `auto: update by Codex [YYYY-MM-DD HH:MM:SS]`.
