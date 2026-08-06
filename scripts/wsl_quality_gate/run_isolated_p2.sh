#!/usr/bin/env bash
set -Eeuo pipefail

repository_path="${1:?repository path is required}"
run_id="${2:-RUN-P2-IC-001-WSL}"
host_execution_id="${WSL_HOST_WRAPPER_EXECUTION_ID:?host wrapper execution id is required}"
distro="${WSL_DISTRO_NAME:-unknown}"
evidence_root="$repository_path/test/evidence/phase2/$run_id"
manifest="$evidence_root/run-manifest.json"
python_bin="$repository_path/.venv/bin/python"

blocked() {
  local reason="$1"
  mkdir -p "$evidence_root"
  printf '{"state":"BLOCKED","reason":"%s","generated_at":"%s"}\n' "$reason" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$evidence_root/verification.json"
  exit 20
}

[[ "$run_id" == "RUN-P2-IC-001-WSL" ]] || blocked "Run ID is not the fixed WSL scope"
[[ -d "$repository_path" && -f "$manifest" ]] || blocked "repository or manifest is missing"
[[ -x "$python_bin" ]] || blocked "Linux .venv/bin/python is missing"
[[ -f "$repository_path/scripts/quality_gate/trusted_scopes.json" ]] || blocked "trusted scope registry is missing"
[[ -f "$repository_path/tests/fixtures/market_data/catalog_resolver_fixture.json" ]] || blocked "fixture is missing"
if grep -RInE '^[[:space:]]*(import|from)[[:space:]]+(databento|broker|requests|urllib|httpx|socket)([[:space:]]|$)' \
  "$repository_path/src/autotrade/market_data" "$repository_path/tests/market_data" "$repository_path/tests/fixtures/market_data"; then
  blocked "prohibited external dependency found in target scope"
fi

addr_summary="$(ip addr show up 2>/dev/null || true)"
addr_records="$(ip -o addr show up 2>/dev/null || true)"
route_summary="$(ip route show 2>/dev/null || true)"
[[ -z "$(printf '%s\n' "$route_summary" | awk '$1 == "default" {print}')" ]] || blocked "default route remains"
if printf '%s\n' "$addr_records" | awk '$2 != "lo" && ($3 == "inet" || $3 == "inet6") {found=1} END {exit found ? 0 : 1}'; then
  blocked "outward-facing NIC remains"
fi

expected_python="3.12.13"; expected_ruff="0.16.1"; expected_mypy="2.3.0"; expected_pytest="9.1.1"; expected_cov="7.1.0"
python_version="$($python_bin --version 2>&1)"; ruff_version="$($python_bin -m ruff --version 2>&1)"; mypy_version="$($python_bin -m mypy --version 2>&1)"; pytest_version="$($python_bin -m pytest --version 2>&1)"; cov_version="$($python_bin -m pip show pytest-cov 2>/dev/null | awk -F': ' '/^Version:/ {print $2}')"
[[ "$python_version" == *"$expected_python"* ]] || blocked "Python version mismatch"
[[ "$ruff_version" == *"$expected_ruff"* ]] || blocked "ruff version mismatch"
[[ "$mypy_version" == *"$expected_mypy"* ]] || blocked "mypy version mismatch"
[[ "$pytest_version" == *"$expected_pytest"* ]] || blocked "pytest version mismatch"
[[ "$cov_version" == "$expected_cov" ]] || blocked "pytest-cov version mismatch"

fixture_hash="sha256:$(sha256sum "$repository_path/tests/fixtures/market_data/catalog_resolver_fixture.json" | awk '{print $1}')"
expected_fixture="sha256:94022229698e972353b8ec9537f455af5cb29d47253f5f2a1ed5d33b08b50169"
[[ "$fixture_hash" == "$expected_fixture" ]] || blocked "fixture checksum mismatch"

cat > "$evidence_root/host-isolation.json" <<EOF
{
  "state": "CONFIRMED", "wsl_version": "${WSL_VERSION:-unknown}", "distro": "${distro}", "networking_mode": "none",
  "host_wrapper_execution_id": "${host_execution_id}", "ip_addr_summary": $(printf '%s' "$addr_summary" | "$python_bin" -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
  "ip_route_summary": $(printf '%s' "$route_summary" | "$python_bin" -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
  "confirmed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "scope": ["src/autotrade/market_data", "tests/market_data", "tests/fixtures/market_data"], "fixture_sha256": "${fixture_hash}"
}
EOF

export QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED=1
export QUALITY_GATE_HOST_ISOLATION_EVIDENCE="$evidence_root/host-isolation.json"
set +e
"$python_bin" -m scripts.quality_gate.run_quality_gate --manifest "$manifest" --project-root "$repository_path"
gate_exit=$?
set -e
"$python_bin" - "$evidence_root/verification.json" "$gate_exit" "$python_version" "$ruff_version" "$mypy_version" "$pytest_version" "$cov_version" "$fixture_hash" <<'PY'
import json, sys
from pathlib import Path
path, exit_code, python, ruff, mypy, pytest, coverage, fixture = sys.argv[1:]
result = json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else {"state": "FAILED"}
manifest = json.loads((Path(path).parent / "run-manifest.json").read_text(encoding="utf-8"))
result.update({"exit_code": int(exit_code), "tool_versions": {"python": python, "ruff": ruff, "mypy": mypy, "pytest": pytest, "pytest_cov": coverage}, "scope": "target_only", "fixture_sha256": fixture, "target_only_change_sha256": manifest["change_hash"], "restore_pending": True})
Path(path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
exit "$gate_exit"
