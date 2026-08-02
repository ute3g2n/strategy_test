const { execFileSync, spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const logPath = path.join(root, "watch-commit.log");
const errPath = path.join(root, "watch-commit.err.log");

function hasWatcher() {
  try {
    const output = execFileSync(
      "powershell.exe",
      [
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'node.exe' -or $_.Name -eq 'cmd.exe') -and $_.CommandLine -like '*chokidar*' -and $_.CommandLine -like '*strategy_test*' } | Select-Object -First 1 -ExpandProperty ProcessId",
      ],
      { encoding: "utf8" },
    );
    return output.trim().length > 0;
  } catch {
    return false;
  }
}

if (hasWatcher()) {
  console.log("watch-commit is already running.");
  process.exit(0);
}

const out = fs.openSync(logPath, "a");
const err = fs.openSync(errPath, "a");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";

const child = spawn(npmCommand, ["run", "watch-commit"], {
  cwd: root,
  detached: true,
  stdio: ["ignore", out, err],
  windowsHide: true,
});

child.unref();
console.log(`watch-commit started. pid=${child.pid}`);
