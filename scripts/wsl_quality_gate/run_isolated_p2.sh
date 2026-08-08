#!/usr/bin/env bash
set -Eeuo pipefail

repository_path="${1:?repository path is required}"
run_id="${2:-RUN-P2-IC-001-WSL}"
host_execution_id="${WSL_HOST_WRAPPER_EXECUTION_ID:-${3:?host wrapper execution id is required}}"
distro="${WSL_DISTRO_NAME:-unknown}"
evidence_root="$repository_path/tests/evidence/phase2/$run_id"
manifest="$evidence_root/run-manifest.json"
python_bin="$repository_path/.venv/bin/python"

blocked() {
  local reason="$1"
  mkdir -p "$evidence_root"
  printf '{"state":"BLOCKED","reason":"%s","generated_at":"%s","host_wrapper_execution_id":"%s"}\n' "$reason" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$host_execution_id" > "$evidence_root/verification.json"
  exit 20
}

[[ -d "$repository_path" && -f "$manifest" ]] || blocked "repository or manifest is missing"
[[ -x "$python_bin" ]] || blocked "Linux .venv/bin/python is missing"
[[ -d "$repository_path/wheelhouse" ]] || blocked "approved Linux wheelhouse is missing"
[[ -f "$repository_path/scripts/quality_gate/trusted_scopes.json" ]] || blocked "trusted scope registry is missing"
readarray -t input_metadata < <("$python_bin" - "$repository_path/scripts/quality_gate/trusted_scopes.json" "$run_id" <<'PY'
import json
import sys

registry_path, run_id = sys.argv[1:]
registry = json.loads(open(registry_path, encoding="utf-8").read())
scope = registry.get("scopes", {}).get(run_id)
if not isinstance(scope, dict):
    raise SystemExit(2)
dbn_input = scope.get("dbn_input")
if isinstance(dbn_input, dict):
    print("dbn")
    print(dbn_input.get("protected_path", ""))
    print(dbn_input.get("checksum", ""))
    print(scope.get("dbn_requirements", ""))
else:
    fixture = scope.get("fixture", {})
    print("fixture")
    print(fixture.get("path", ""))
    print(fixture.get("checksum", ""))
    print("")
PY
); [[ "${#input_metadata[@]}" -eq 4 ]] || blocked "trusted scope input metadata is missing"
input_kind="${input_metadata[0]}"
input_location="${input_metadata[1]}"
expected_input_hash="${input_metadata[2]}"
dbn_requirements="${input_metadata[3]}"
repository_owner=""
if [[ "$input_kind" == "dbn" ]]; then
  [[ "$(id -u)" -eq 0 ]] || blocked "DBN input integrity check must run as root"
  repository_owner="$(stat -c '%U' "$repository_path")"
  [[ -n "$repository_owner" && "$repository_owner" != "root" ]] || blocked "repository owner is unsafe for DBN gate"
  command -v runuser >/dev/null || blocked "runuser is required to drop DBN gate privileges"
  chown -R "$repository_owner" "$evidence_root" || blocked "DBN evidence ownership cannot be prepared"
  [[ "$input_location" != /mnt/* && "$input_location" != //* ]] || blocked "DBN input must not be mounted from Windows or UNC"
  if test -L "$input_location" || [[ ! -f "$input_location" ]]; then
    blocked "protected DBN input is missing or is a symbolic link"
  fi
  [[ "$(stat -c '%U:%a' "$input_location")" == "root:400" ]] || blocked "protected DBN input must be root-owned read-only mode 400"
  [[ -n "$dbn_requirements" && -f "$repository_path/$dbn_requirements" ]] || blocked "DBN hash-pinned requirements are missing"
  grep -q -- '--hash=sha256:' "$repository_path/$dbn_requirements" || blocked "DBN requirements hash allowlist is missing"
  grep -q -- '--require-hashes' "$repository_path/scripts/wsl_quality_gate/prepare_offline_wsl_env.sh" || blocked "offline installer must require hashes"
  if (cd "$repository_path" && git diff --cached --name-only) | grep -E '\.(dbn|DBN)$|(^|/)raw/' >/dev/null; then
    blocked "DBN or raw input is present in the staged Git changes"
  fi
  if (cd "$repository_path" && git ls-files) | grep -E '\.(dbn|DBN)$|(^|/)raw/' >/dev/null; then
    blocked "DBN or raw input is tracked by Git"
  fi
  "$python_bin" - "$repository_path/scripts/quality_gate/trusted_scopes.json" "$run_id" "$repository_path/$dbn_requirements" "$evidence_root/offline-preparation.json" <<'PY' || blocked "DBN offline dependency evidence does not match the trusted scope"
import hashlib
import json
import sys
from importlib import metadata
from pathlib import Path

registry_path, run_id, requirements_path, evidence_path = sys.argv[1:]
registry_path = Path(registry_path)
requirements_path = Path(requirements_path)
evidence_path = Path(evidence_path)
scope = json.loads(registry_path.read_text(encoding="utf-8"))["scopes"][run_id]
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
if hashlib.sha256(requirements_path.read_bytes()).hexdigest() != scope["dbn_requirements_sha256"]:
    raise SystemExit(1)
if evidence.get("requirements_sha256") != scope["dbn_requirements_sha256"]:
    raise SystemExit(1)
for name, version in scope["dbn_required_packages"].items():
    if metadata.version(name) != version or evidence.get("packages", {}).get(name, {}).get("installed") != version:
        raise SystemExit(1)
PY
else
  input_location="$repository_path/$input_location"
  [[ -f "$input_location" ]] || blocked "fixture is missing"
fi
kernel="$(uname -r)"
[[ "$kernel" == *WSL2* || "$kernel" == *microsoft-standard-WSL2* ]] || blocked "kernel is not WSL2: $kernel"
if grep -RInE '^[[:space:]]*(import|from)[[:space:]]+(broker|requests|urllib|httpx|socket)([[:space:]]|$)' \
  "$repository_path/src/autotrade/market_data" "$repository_path/tests/market_data" "$repository_path/tests/fixtures/market_data"; then
  blocked "prohibited external dependency found in target scope"
fi
if [[ "$input_kind" == "dbn" ]]; then
  dbn_imports="$(grep -RIlE '^[[:space:]]*(import|from)[[:space:]]+databento([[:space:]]|$)' "$repository_path/src/autotrade/market_data" || true)"
  [[ "$dbn_imports" == "$repository_path/src/autotrade/market_data/databento_dbn_decoder.py" ]] || blocked "databento import is allowed only in the DBN decoder adapter"
elif grep -RInE '^[[:space:]]*(import|from)[[:space:]]+databento([[:space:]]|$)' \
  "$repository_path/src/autotrade/market_data" "$repository_path/tests/market_data" "$repository_path/tests/fixtures/market_data"; then
  blocked "databento import is outside the DBN trusted scope"
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

input_hash="sha256:$(sha256sum "$input_location" | awk '{print $1}')"
[[ "$input_hash" == "$expected_input_hash" ]] || blocked "input checksum mismatch"

if [[ "$input_kind" == "dbn" ]]; then
  "$python_bin" - "$input_location" "$input_hash" "$evidence_root/dbn-decoder-probe.json" <<'PY' || blocked "DBN decoder probe failed"
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from autotrade.market_data.databento_dbn_decoder import DatabentoDbnDecoder
from autotrade.market_data.dbn_contracts import DbnReplayInput

input_path = Path(sys.argv[1])
input_sha256 = sys.argv[2]
output_path = Path(sys.argv[3])
source = DbnReplayInput(
    payload_sha256=input_sha256,
    raw_object_id="p2-08-fixed-dbn-decoder-probe-only",
    raw_received_at_utc=datetime(1970, 1, 1, tzinfo=UTC),
    source_vendor="databento",
    dataset_ref="GLBX.MDP3",
    schema_ref="ohlcv-1m",
    stype="parent",
    source_symbol="MCL.FUT",
    request_start_utc=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
    request_end_utc=datetime(2026, 6, 15, 12, 1, tzinfo=UTC),
    request_context_sha256="sha256:decoder-probe-only",
    decoder_version="databento-0.82.0",
    decoder_artifact_sha256="sha256:decoder-probe-only",
    normalization_rule_version="dbn-ohlcv-1m-v1",
)
records = DatabentoDbnDecoder().decode(input_path.read_bytes(), source)
result = {
    "state": "DECODED_NOT_NORMALIZED",
    "input_sha256": source.payload_sha256,
    "schema": source.schema_ref,
    "record_count": len(records),
    "event_times_utc": [record.event_time_utc.isoformat().replace("+00:00", "Z") for record in records],
    "vendor_instrument_ids": [record.vendor_instrument_id for record in records],
    "record_ordinals": [record.record_ordinal for record in records],
    "normalization_state": "NOT_RUN_FAIL_CLOSED",
    "normalization_blockers": ["RAW_RECEIVED_AT_MISSING", "CATALOG_MAPPING_UNRESOLVED"],
    "notes": "受信UTC時刻はデコーダが参照しない仮値であり、正規化・Manifest・MarketEventへ渡していない。",
}
output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
fi

cat > "$evidence_root/host-isolation.json" <<EOF
{
  "state": "CONFIRMED", "wsl_version": "${WSL_VERSION:-unknown}", "kernel": "${kernel}", "distro": "${distro}", "networking_mode": "none",
  "host_wrapper_execution_id": "${host_execution_id}", "ip_addr_summary": $(printf '%s' "$addr_summary" | "$python_bin" -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
  "ip_route_summary": $(printf '%s' "$route_summary" | "$python_bin" -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
  "confirmed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "scope": ["src/autotrade/market_data", "tests/market_data", "tests/fixtures/market_data"], "input_sha256": "${input_hash}", "input_kind": "${input_kind}"
}
EOF

export QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED=1
export QUALITY_GATE_HOST_ISOLATION_EVIDENCE="$evidence_root/host-isolation.json"
set +e
if [[ "$input_kind" == "dbn" ]]; then
  runuser -u "$repository_owner" -- env \
    QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED=1 \
    QUALITY_GATE_HOST_ISOLATION_EVIDENCE="$evidence_root/host-isolation.json" \
    "$python_bin" -m scripts.quality_gate.run_quality_gate --manifest "$manifest" --project-root "$repository_path"
else
  "$python_bin" -m scripts.quality_gate.run_quality_gate --manifest "$manifest" --project-root "$repository_path"
fi
gate_exit=$?
set -e
post_input_hash="sha256:$(sha256sum "$input_location" | awk '{print $1}')"
if [[ "$post_input_hash" != "$input_hash" || "$post_input_hash" != "$expected_input_hash" ]]; then
  printf '{"state":"BLOCKED","reason":"input checksum changed during isolated execution","pre_input_sha256":"%s","post_input_sha256":"%s","host_wrapper_execution_id":"%s"}\n' \
    "$input_hash" "$post_input_hash" "$host_execution_id" > "$evidence_root/verification.json"
  exit 20
fi
"$python_bin" - "$evidence_root/verification.json" "$gate_exit" "$python_version" "$ruff_version" "$mypy_version" "$pytest_version" "$cov_version" "$input_hash" "$host_execution_id" <<'PY'
import json, sys
from pathlib import Path
path, exit_code, python, ruff, mypy, pytest, coverage, fixture, host_execution_id = sys.argv[1:]
result = json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else {"state": "FAILED"}
manifest = json.loads((Path(path).parent / "run-manifest.json").read_text(encoding="utf-8"))
probe_path = Path(path).parent / "dbn-decoder-probe.json"
probe = json.loads(probe_path.read_text(encoding="utf-8")) if probe_path.exists() else None
result.update({"exit_code": int(exit_code), "tool_versions": {"python": python, "ruff": ruff, "mypy": mypy, "pytest": pytest, "pytest_cov": coverage}, "scope": "target_only", "input_sha256": fixture, "post_input_sha256": fixture, "target_only_change_sha256": manifest["change_hash"], "host_wrapper_execution_id": host_execution_id, "restore_pending": True, "dbn_decoder_probe": probe})
Path(path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
exit "$gate_exit"
