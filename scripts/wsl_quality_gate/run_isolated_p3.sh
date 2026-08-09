#!/usr/bin/env bash
set -Eeuo pipefail

repository_path="${1:?repository path is required}"
run_id="${2:?run id is required}"
host_execution_id="${WSL_HOST_WRAPPER_EXECUTION_ID:-${3:?host wrapper execution id is required}}"
distro="${WSL_DISTRO_NAME:-unknown}"
evidence_root="$repository_path/tests/evidence/phase3/$run_id"
manifest="$evidence_root/run-manifest.json"
python_bin="$repository_path/.venv/bin/python"

blocked() {
  local reason="$1"
  mkdir -p "$evidence_root"
  printf '{"state":"BLOCKED","reason":"%s","generated_at":"%s","host_wrapper_execution_id":"%s"}\n' \
    "$reason" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$host_execution_id" > "$evidence_root/verification.json"
  exit 20
}

[[ -d "$repository_path" && -f "$manifest" ]] || blocked "repository or manifest is missing"
[[ -x "$python_bin" ]] || blocked "Linux .venv/bin/python is missing"
[[ -f "$repository_path/scripts/quality_gate/trusted_scopes.json" ]] || blocked "trusted scope registry is missing"

readarray -t input_metadata < <("$python_bin" - "$repository_path/scripts/quality_gate/trusted_scopes.json" "$run_id" <<'PY'
import json
import sys

registry_path, run_id = sys.argv[1:]
registry = json.loads(open(registry_path, encoding="utf-8").read())
scope = registry.get("scopes", {}).get(run_id)
if not isinstance(scope, dict) or scope.get("phase_id") != "phase3":
    raise SystemExit(2)
fixture = scope.get("fixture", {})
print(fixture.get("path", ""))
print(fixture.get("checksum", ""))
PY
); [[ "${#input_metadata[@]}" -eq 2 ]] || blocked "trusted phase3 fixture metadata is missing"
input_location="${input_metadata[0]}"
expected_input_hash="${input_metadata[1]}"
[[ -n "$input_location" && -n "$expected_input_hash" ]] || blocked "trusted phase3 fixture metadata is incomplete"
input_location="$repository_path/$input_location"
[[ -f "$input_location" ]] || blocked "fixture is missing"

kernel="$(uname -r)"
[[ "$kernel" == *WSL2* || "$kernel" == *microsoft-standard-WSL2* ]] || blocked "kernel is not WSL2: $kernel"
addr_summary="$(ip addr show up 2>/dev/null || true)"
addr_records="$(ip -o addr show up 2>/dev/null || true)"
route_summary="$(ip route show 2>/dev/null || true)"
[[ -z "$(printf '%s\n' "$route_summary" | awk '$1 == "default" {print}')" ]] || blocked "default route remains"
if printf '%s\n' "$addr_records" | awk '$2 != "lo" && ($3 == "inet" || $3 == "inet6") {found=1} END {exit found ? 0 : 1}'; then
  blocked "outward-facing NIC remains"
fi

input_hash="sha256:$(sha256sum "$input_location" | awk '{print $1}')"
[[ "$input_hash" == "$expected_input_hash" ]] || blocked "input checksum mismatch"

target_scope_json="$("$python_bin" - "$repository_path/scripts/quality_gate/trusted_scopes.json" "$run_id" <<'PY'
import json
import sys
from pathlib import Path

scope = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["scopes"][sys.argv[2]]
print(json.dumps(scope["target_paths"], ensure_ascii=False))
PY
)" || blocked "trusted target scope cannot be read"

cat > "$evidence_root/host-isolation.json" <<EOF
{
  "state": "CONFIRMED", "wsl_version": "${WSL_VERSION:-unknown}", "kernel": "${kernel}", "distro": "${distro}", "networking_mode": "none",
  "host_wrapper_execution_id": "${host_execution_id}",
  "ip_addr_summary": $(printf '%s' "$addr_summary" | "$python_bin" -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
  "ip_route_summary": $(printf '%s' "$route_summary" | "$python_bin" -c 'import json,sys; print(json.dumps(sys.stdin.read()))'),
  "confirmed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "scope": ${target_scope_json}, "input_sha256": "${input_hash}", "input_kind": "fixture"
}
EOF

export PYTHONPATH="$repository_path/src"
export QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED=1
export QUALITY_GATE_HOST_ISOLATION_EVIDENCE="$evidence_root/host-isolation.json"
export MYPY_CACHE_DIR="/tmp/codex-strategy-test-mypy-cache"
set +e
"$python_bin" -m scripts.quality_gate.run_quality_gate --manifest "$manifest" --project-root "$repository_path"
gate_exit=$?
set -e

post_input_hash="sha256:$(sha256sum "$input_location" | awk '{print $1}')"
if [[ "$post_input_hash" != "$input_hash" || "$post_input_hash" != "$expected_input_hash" ]]; then
  printf '{"state":"BLOCKED","reason":"input checksum changed during isolated execution","pre_input_sha256":"%s","post_input_sha256":"%s","host_wrapper_execution_id":"%s"}\n' \
    "$input_hash" "$post_input_hash" "$host_execution_id" > "$evidence_root/verification.json"
  exit 20
fi

"$python_bin" - "$evidence_root/verification.json" "$gate_exit" "$input_hash" "$post_input_hash" "$host_execution_id" <<'PY'
import json
import sys
from pathlib import Path

path, exit_code, input_hash, post_input_hash, host_execution_id = sys.argv[1:]
verification_path = Path(path)
result = json.loads(verification_path.read_text(encoding="utf-8")) if verification_path.exists() else {"state": "FAILED"}
manifest = json.loads((verification_path.parent / "run-manifest.json").read_text(encoding="utf-8"))
result.update(
    {
        "exit_code": int(exit_code),
        "scope": "target_only",
        "input_sha256": input_hash,
        "post_input_sha256": post_input_hash,
        "target_only_change_sha256": manifest["change_hash"],
        "host_wrapper_execution_id": host_execution_id,
        "restore_pending": True,
        "execution_user": __import__("getpass").getuser(),
        "execution_uid": __import__("os").getuid(),
    }
)
verification_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
exit "$gate_exit"
