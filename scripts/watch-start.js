const { execFileSync } = require("node:child_process");
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
        "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'node.exe' -or $_.Name -eq 'cmd.exe' -or $_.Name -eq 'python.exe') -and ($_.CommandLine -like '*chokidar*' -or $_.CommandLine -like '*watch-commit*' -or $_.CommandLine -like '*context_watch*') -and $_.CommandLine -like '*strategy_test*' } | Select-Object -First 1 -ExpandProperty ProcessId",
      ],
      { encoding: "utf8" },
    );
    return output.trim().length > 0;
  } catch {
    return false;
  }
}

function pythonExecutable() {
  const candidate = path.join(root, ".venv", "Scripts", "python.exe");
  return fs.existsSync(candidate) ? candidate : "python";
}

try {
  execFileSync(
    pythonExecutable(),
    ["-m", "scripts.context_index.context_watch", "--root", root, "--check-start"],
    { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
  );
} catch (error) {
  process.stderr.write(error.stdout || "");
  process.stderr.write(error.stderr || error.message);
  process.exit(error.status || 1);
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
