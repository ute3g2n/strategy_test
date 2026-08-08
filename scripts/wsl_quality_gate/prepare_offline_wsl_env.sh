#!/usr/bin/env bash
set -Eeuo pipefail

repository_path="${1:?repository path is required}"
wheelhouse="${2:?approved Linux wheelhouse is required}"
run_id="${3:-RUN-P2-IC-001-WSL}"
requirements_relative_path="${4:-requirements-dev.txt}"
evidence_root="${repository_path}/tests/evidence/phase2/${run_id}"
requirements="${repository_path}/${requirements_relative_path}"
python_bin="${repository_path}/.venv/bin/python"
[[ -d "$wheelhouse" ]] || { echo "BLOCKED: approved wheelhouse is missing" >&2; exit 20; }
[[ -f "$requirements" ]] || { echo "BLOCKED: hash-pinned requirements are missing" >&2; exit 20; }
command -v python3 >/dev/null || { echo "BLOCKED: python3 is missing" >&2; exit 20; }
mkdir -p "$evidence_root"
python3 -m venv "$repository_path/.venv"
"$python_bin" -m pip install --no-index --require-hashes --find-links "$wheelhouse" -r "$requirements"
"$python_bin" - "$requirements" "$wheelhouse" "$evidence_root/offline-preparation.json" <<'PY'
import hashlib, json, sys
from importlib import metadata
from pathlib import Path
requirements, wheelhouse, output = map(Path, sys.argv[1:])
packages = {}
for line in requirements.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if line and not line.startswith("#"):
        requirement = line.split(" --hash=", 1)[0]
        name, version = requirement.split("==", 1)
        installed = metadata.version(name)
        if version != installed:
            raise SystemExit(f"BLOCKED: version mismatch: {name}")
        packages[name] = {"required": version, "installed": installed}
wheels = [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(wheelhouse.glob("*.whl"))]
Path(output).write_text(json.dumps({"source": "approved-local-wheelhouse", "requirements_sha256": hashlib.sha256(requirements.read_bytes()).hexdigest(), "packages": packages, "wheelhouse": wheels}, indent=2) + "\n", encoding="utf-8")
PY
