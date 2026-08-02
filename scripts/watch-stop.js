const { execFileSync } = require("node:child_process");

const command = [
  "$processes = Get-CimInstance Win32_Process |",
  "Where-Object {",
  "  ($_.Name -eq 'node.exe' -or $_.Name -eq 'cmd.exe')",
  "  -and ($_.CommandLine -like '*chokidar*' -or $_.CommandLine -like '*watch-commit*')",
  "  -and $_.CommandLine -like '*strategy_test*'",
  "};",
  "if (-not $processes) { Write-Output 'watch-commit is not running.'; exit 0 }",
  "$ids = $processes | Select-Object -ExpandProperty ProcessId;",
  "$ids | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue };",
  'Write-Output ("stopped: " + (($ids | Sort-Object -Unique) -join ", "))',
].join(" ");

try {
  const output = execFileSync("powershell.exe", ["-NoProfile", "-Command", command], {
    encoding: "utf8",
  });
  process.stdout.write(output);
} catch (error) {
  process.stderr.write(error.stdout || "");
  process.stderr.write(error.stderr || error.message);
  process.exit(error.status || 1);
}
