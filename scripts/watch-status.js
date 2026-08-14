const { execFileSync } = require("node:child_process");

const command = [
  "$processes = Get-CimInstance Win32_Process |",
  "Where-Object {",
  "  ($_.Name -eq 'node.exe' -or $_.Name -eq 'cmd.exe' -or $_.Name -eq 'python.exe')",
  "  -and ($_.CommandLine -like '*chokidar*' -or $_.CommandLine -like '*watch-commit*' -or $_.CommandLine -like '*context_watch*')",
  "  -and $_.CommandLine -like '*strategy_test*'",
  "};",
  "if (-not $processes) { Write-Output 'watch-commit is stopped.'; exit 0 }",
  "$processes | Sort-Object ProcessId | ForEach-Object {",
  "  Write-Output ('watch-commit is running. pid=' + $_.ProcessId + ' name=' + $_.Name)",
  "}",
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
