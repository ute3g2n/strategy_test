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
MANIFEST_PATH = ROOT / "tests/evidence/phase2/RUN-P2-IC-001-WSL/run-manifest.json"
WRAPPER = ROOT / "scripts/wsl_quality_gate/run_isolated_p2.ps1"
LINUX_RUNNER = ROOT / "scripts/wsl_quality_gate/run_isolated_p2.sh"
AUTOMATION_WRAPPER = ROOT / "scripts/wsl_quality_gate/run_test.ps1"
EVIDENCE_SELECTOR = ROOT / "scripts/wsl_quality_gate/select_automation_evidence.ps1"


def _scope_and_manifest() -> tuple[dict, dict]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return registry["scopes"]["RUN-P2-IC-001-WSL"], manifest


def test_wsl_scope_and_manifest_match_fixed_p2_d07_contract() -> None:
    scope, manifest = _scope_and_manifest()
    assert manifest["run_id"] == "RUN-P2-IC-001-WSL"
    assert scope["phase_id"] == manifest["phase_id"] == "phase2"
    assert scope["design"] == manifest["design"] == "P2-D07"
    assert (
        scope["requirements"]
        == manifest["requirements"]
        == [
            "REQ-Q02",
            "REQ-Q19",
            "REQ-Q20",
            "REQ-Q23",
        ]
    )
    assert (
        scope["target_paths"]
        == manifest["target_paths"]
        == [
            "src/autotrade/market_data",
            "tests/market_data",
            "tests/fixtures/market_data",
        ]
    )
    assert scope["scope_mode"] == manifest["scope_mode"] == "target_only"
    assert scope["fixture"]["checksum"] == manifest["input_fixture"]["checksum"]
    assert scope["checks"] == manifest["checks"]
    assert all(command["command"][0] == ".venv/bin/python" for command in scope["checks"])


def test_wsl_manifest_is_rejected_when_any_fixed_input_changes(tmp_path: Path) -> None:
    manifest = dict(load_manifest(MANIFEST_PATH))
    manifest["checks"] = [dict(item) for item in manifest["checks"]]
    manifest["checks"][0] = {
        "gate": "formatter",
        "command": [".venv/Scripts/python.exe", "-m", "ruff", "format", "--check", "src/autotrade/market_data"],
    }
    manifest["target_paths"] = ["tests"]
    manifest["scope_mode"] = "all_changes"
    with pytest.raises(ManifestValidationError):
        from scripts.quality_gate.runner import LocalQualityGateRunner

        LocalQualityGateRunner(ROOT).run(manifest, dry_run=True)


def test_host_wrapper_dry_run_contract_is_declared_without_mutating_wslconfig() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "[switch]$DryRun" in text
    assert "[switch]$AllowRunningDistro" in text
    assert "try" in text and "finally" in text
    assert "networkingMode=none" in text
    assert "firewall=true" in text
    assert "wsl --shutdown" in text
    assert "DryRun" in text
    assert "WriteAllText" in text
    assert "WSL_INTEROP" in text
    assert "[string[]]$lines = @()" in text
    assert "runningLines" in text
    assert "otherRunningLines" in text
    assert "AddRange([string[]]" in text
    assert "dbn_input" in text
    assert "protected DBN input is missing or is a symbolic link" in text
    assert "test -f '$protectedPath' && ! test -L '$protectedPath'" in text
    assert '"-u", "root"' in text
    preflight = text.split("if ($DryRun)", 1)[0]
    assert "uname -r" not in preflight
    assert "test -x" not in preflight
    assert text.index("& wsl.exe --shutdown") < text.index("$runnerArguments")


def test_wsl_runner_fails_closed_before_four_gates_on_missing_isolation_prerequisites() -> None:
    text = LINUX_RUNNER.read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in text
    for required in (
        "uname -r",
        "ip route",
        "default",
        "wheelhouse",
        "QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED",
        "host-isolation.json",
    ):
        assert required in text
    assert re.search(r"\.venv/bin/python", text)
    assert text.index('kernel="$(uname -r)"') < text.index("QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED")
    assert 'host_execution_id="${WSL_HOST_WRAPPER_EXECUTION_ID:-${3:?host wrapper execution id is required}}"' in text
    assert "DBN input integrity check must run as root" in text
    assert "runuser -u \"$repository_owner\"" in text


def test_wsl_runner_has_valid_bash_syntax() -> None:
    result = subprocess.run(
        ["bash", "-n", "scripts/wsl_quality_gate/run_isolated_p2.sh"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_automation_wrapper_captures_wrapper_and_evidence_results() -> None:
    text = AUTOMATION_WRAPPER.read_text(encoding="utf-8")
    assert "run_isolated_p2.ps1" in text
    assert "wrapper_exit_code" in text and "ExitCode" in text
    assert "preflight.json" in text and "wsl-verification-capture.json" in text
    assert "run-test-summary.json" in text
    assert "run-test-wrapper.log" in text
    assert "run-test-evidence.log" in text
    assert "LAUNCH_ERROR" in text
    assert "wrapper_error" in text and "evidence_error" in text
    assert "TimeoutSeconds" in text and "TIMEOUT after" in text
    assert "Select-AutomationEvidence" in text
    assert "evidence_state" in text
    assert 'evidenceState -in @("BLOCKED", "HUMAN_GATE_REQUIRED")' in text
    assert 'evidenceState -eq "PASS"' in text
    assert "LastWriteTimeUtc" in text
    assert "(Test-Path -LiteralPath $preflightPath) -and" in text
    assert "preflightIsRecent" in text and "preferPreflight" in text
    assert "AllowRunningDistro" in text
    assert "runnerWasInvoked" in text


def test_automation_evidence_prefers_current_wsl_capture_over_stale_windows_verification(
    tmp_path: Path,
) -> None:
    """古いWindows側の同名証跡を、今回のWSL採取証跡として扱わない。"""
    stale_windows_verification = tmp_path / "windows" / "verification.json"
    stale_windows_verification.parent.mkdir()
    stale_windows_verification.write_text(
        json.dumps({"state": "DRY_RUN", "generated_at": "2026-08-01T00:00:00Z"}),
        encoding="utf-8",
    )

    execution_id = "a" * 32
    capture_path = tmp_path / "automation" / "wsl-verification-capture.json"
    capture_path.parent.mkdir()
    capture_path.write_text(
        json.dumps(
            {
                "state": "CAPTURED",
                "source_kind": "wsl_verification",
                "execution_id": execution_id,
                "captured_at": "2026-08-07T00:00:02Z",
                "source_repository_path": "/home/oue/strategy_test",
                "source_path": "/home/oue/strategy_test/tests/evidence/phase2/RUN-P2-IC-001-WSL/verification.json",
                "verification": {
                    "state": "BLOCKED",
                    "host_wrapper_execution_id": execution_id,
                    "generated_at": "2026-08-07T00:00:01Z",
                },
            }
        ),
        encoding="utf-8",
    )

    command = (
        f". '{EVIDENCE_SELECTOR}'; "
        "$selected = Select-AutomationEvidence "
        f"-WrapperExitCode 1 -StartedAt ([DateTimeOffset]'2026-08-07T00:00:00Z') "
        f"-ExpectedExecutionId '{execution_id}' "
        f"-WslVerificationCapturePath '{capture_path}'; "
        "$selected | ConvertTo-Json -Depth 8 -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    selected = json.loads(result.stdout)
    assert stale_windows_verification.exists()
    assert selected["source"] == "wsl_verification_capture"
    assert selected["state"] == "BLOCKED"
    assert selected["json"] != stale_windows_verification.read_text(encoding="utf-8")


def test_automation_wrapper_uses_only_execution_matched_wsl_verification_capture() -> None:
    text = AUTOMATION_WRAPPER.read_text(encoding="utf-8")
    assert "Select-AutomationEvidence" in text
    assert "wsl-verification-capture.json" in text
    assert "$verificationPath =" not in text
    assert 'Invoke-Captured "wsl.exe"' not in text


def test_selector_accepts_raw_wsl_verification_when_nested_json_parse_was_unavailable(tmp_path: Path) -> None:
    execution_id = "b" * 32
    capture_path = tmp_path / "wsl-verification-capture.json"
    capture_path.write_text(
        json.dumps(
            {
                "state": "CAPTURED",
                "source_kind": "wsl_verification",
                "execution_id": execution_id,
                "captured_at": "2026-08-07T00:00:02Z",
                "verification": None,
                "verification_raw": json.dumps(
                    {"state": "HUMAN_GATE_REQUIRED", "host_wrapper_execution_id": execution_id}
                ),
            }
        ),
        encoding="utf-8",
    )
    command = (
        f". '{EVIDENCE_SELECTOR}'; "
        "$selected = Select-AutomationEvidence "
        f"-WrapperExitCode 1 -StartedAt ([DateTimeOffset]'2026-08-07T00:00:00Z') "
        f"-ExpectedExecutionId '{execution_id}' "
        f"-WslVerificationCapturePath '{capture_path}'; "
        "$selected | ConvertTo-Json -Depth 8 -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    selected = json.loads(result.stdout)
    assert selected["source"] == "wsl_verification_capture"
    assert selected["state"] == "HUMAN_GATE_REQUIRED"


def test_host_wrapper_captures_wsl_verification_before_restoring_isolation() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "WSL_HOST_WRAPPER_EXECUTION_ID=$executionId" in text
    assert "$env:WSLENV" in text
    assert "wslEnvNames.Contains('WSL_VERSION')" in text
    assert "QUALITY_GATE_HUMAN_APPROVED" in text
    assert '$ErrorActionPreference = "Continue"' in text
    assert "wsl-verification-capture.json" in text
    assert "host-isolation.json" in text
    assert "base64 -w0" in text
    assert "verification_raw" in text
    assert 'source_kind = "wsl_verification"' in text
    assert "$verificationId -eq $executionId" in text
    assert "hostIsolation.host_wrapper_execution_id" in text
    assert "'$executionId'" in text
    assert text.index("$verificationCapture = Invoke-WslCapture") < text.rindex("finally")
