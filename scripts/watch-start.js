const { execFileSync } = require("node:child_process");
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

function psQuote(value) {
  return `'${value.replace(/'/g, "''")}'`;
}

const startCommand = [
  "Start-Process",
  "-FilePath npm.cmd",
  "-ArgumentList @('run','watch-commit')",
  `-WorkingDirectory ${psQuote(root)}`,
  `-RedirectStandardOutput ${psQuote(logPath)}`,
  `-RedirectStandardError ${psQuote(errPath)}`,
  "-WindowStyle Hidden",
  "-PassThru | Select-Object -ExpandProperty Id",
].join(" ");

const pid = execFileSync("powershell.exe", ["-NoProfile", "-Command", startCommand], {
  encoding: "utf8",
}).trim();

console.log(`watch-commit started. pid=${pid}`);
