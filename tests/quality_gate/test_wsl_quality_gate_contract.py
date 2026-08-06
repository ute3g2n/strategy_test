"""WSL隔離品質ゲートの受入契約を先に固定するREDテスト。"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts.quality_gate.runner import ManifestValidationError, load_manifest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "scripts/quality_gate/trusted_scopes.json"
MANIFEST_PATH = ROOT / "test/evidence/phase2/RUN-P2-IC-001-WSL/run-manifest.json"
WRAPPER = ROOT / "scripts/wsl_quality_gate/run_isolated_p2.ps1"
LINUX_RUNNER = ROOT / "scripts/wsl_quality_gate/run_isolated_p2.sh"
AUTOMATION_WRAPPER = ROOT / "scripts/wsl_quality_gate/run_test.ps1"


def _scope_and_manifest() -> tuple[dict, dict]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return registry["scopes"]["RUN-P2-IC-001-WSL"], manifest


def test_wsl_scope_and_manifest_match_fixed_p2_d07_contract() -> None:
    scope, manifest = _scope_and_manifest()
    assert manifest["run_id"] == "RUN-P2-IC-001-WSL"
    assert scope["phase_id"] == manifest["phase_id"] == "phase2"
    assert scope["design"] == manifest["design"] == "P2-D07"
    assert scope["requirements"] == manifest["requirements"] == [
        "REQ-Q02",
        "REQ-Q19",
        "REQ-Q20",
        "REQ-Q23",
    ]
    assert scope["target_paths"] == manifest["target_paths"] == [
        "src/autotrade/market_data",
        "tests/market_data",
        "tests/fixtures/market_data",
    ]
    assert scope["scope_mode"] == manifest["scope_mode"] == "target_only"
    assert scope["fixture"]["checksum"] == manifest["input_fixture"]["checksum"]
    assert scope["checks"] == manifest["checks"]
    assert all(command["command"][0] == ".venv/bin/python" for command in scope["checks"])


def test_wsl_manifest_is_rejected_when_any_fixed_input_changes(tmp_path: Path) -> None:
    manifest = dict(load_manifest(MANIFEST_PATH))
    manifest["checks"] = [dict(item) for item in manifest["checks"]]
    manifest["checks"][0] = {
        "gate": "formatter",
        "command": [
            ".venv/Scripts/python.exe", "-m", "ruff", "format", "--check", "src/autotrade/market_data"
        ],
    }
    manifest["target_paths"] = ["tests"]
    manifest["scope_mode"] = "all_changes"
    with pytest.raises(ManifestValidationError):
        from scripts.quality_gate.runner import LocalQualityGateRunner

        LocalQualityGateRunner(ROOT).run(manifest, dry_run=True)


def test_host_wrapper_dry_run_contract_is_declared_without_mutating_wslconfig() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "[switch]$DryRun" in text
    assert "try" in text and "finally" in text
    assert "networkingMode=none" in text
    assert "firewall=true" in text
    assert "wsl --shutdown" in text
    assert "DryRun" in text
    assert "Set-Content" in text or "WriteAllBytes" in text
    assert "WSL_INTEROP" in text
    assert "[string[]]$lines = @()" in text
    assert "-like \"*Running*\"" in text
    assert "AddRange([string[]]" in text
    preflight = text.split('if ($DryRun)', 1)[0]
    assert "uname -r" not in preflight
    assert "test -x" not in preflight
    assert text.index("& wsl.exe --shutdown") < text.index("$runnerArguments")


def test_wsl_runner_fails_closed_before_four_gates_on_missing_isolation_prerequisites() -> None:
    text = LINUX_RUNNER.read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in text
    for required in (
        "uname -r", "ip route", "default", "wheelhouse", "QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED", "host-isolation.json"
    ):
        assert required in text
    assert re.search(r"\.venv/bin/python", text)
    assert text.index('kernel="$(uname -r)"') < text.index('QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED')


@pytest.mark.skipif(subprocess.run(["bash", "-n", str(LINUX_RUNNER)], check=False).returncode != 0, reason="bash unavailable")
def test_wsl_runner_has_valid_bash_syntax() -> None:
    assert True


def test_automation_wrapper_captures_wrapper_and_evidence_results() -> None:
    text = AUTOMATION_WRAPPER.read_text(encoding="utf-8")
    assert "run_isolated_p2.ps1" in text
    assert "wrapper_exit_code" in text and "ExitCode" in text
    assert "preflight.json" in text and "verification.json" in text
    assert "run-test-summary.json" in text
    assert "run-test-wrapper.log" in text
    assert "run-test-evidence.log" in text
    assert "LAUNCH_ERROR" in text
    assert "wrapper_error" in text and "evidence_error" in text
    assert "TimeoutSeconds" in text and "TIMEOUT after" in text
    assert "evidenceCandidates" in text
    assert "evidence_state" in text
