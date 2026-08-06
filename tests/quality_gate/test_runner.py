"""Local quality-gate runner behavior tests."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.quality_gate import run_quality_gate
from scripts.quality_gate.runner import (
    ChangeRecord,
    CommandResult,
    LocalQualityGateRunner,
    ManifestValidationError,
)


@dataclass
class FakeExecutor:
    """Deterministic local-command substitute used by the unit tests."""

    results: dict[tuple[str, ...], CommandResult]
    calls: list[tuple[str, ...]]

    def run(self, command: tuple[str, ...], cwd: Path) -> CommandResult:
        del cwd
        self.calls.append(command)
        return self.results[command]


@dataclass
class FakeChangeInspector:
    """Deterministic repository-change substitute used by unit tests."""

    changes: tuple[ChangeRecord, ...] = ()
    has_test_skip: bool = False

    def list_changes(self, project_root: Path, baseline_ref: str) -> tuple[ChangeRecord, ...]:
        del project_root, baseline_ref
        return self.changes

    def has_new_test_skip(self, project_root: Path, baseline_ref: str) -> bool:
        del project_root, baseline_ref
        return self.has_test_skip

    def change_hash(self, project_root: Path, baseline_ref: str) -> str:
        del project_root, baseline_ref
        return "test-change-hash"


def manifest(tmp_path: Path, **overrides: object) -> dict[str, object]:
    """Return a minimal, local-only run manifest."""
    value: dict[str, object] = {
        "run_id": "RUN-P2-S2-001",
        "phase_id": "phase2",
        "step_id": "S2",
        "requirements": ["REQ-P2-001"],
        "design": "AF-D18",
        "orchestrator": "AutoTradeProject_ImplementationQuality_Orchestrator_v0_1",
        "agents": ["AutoTrade_A110_PythonTestEngineer_v0_1", "AutoTrade_A130_VerificationEngineer_v0_1"],
        "skills": ["autotrade_skill_python_test_quality_v0_1"],
        "input_fixture": {"name": "quality_gate", "version": "v1", "checksum": "sha256:test"},
        "data_version": "v1",
        "change_hash": "test-change-hash",
        "baseline_ref": "HEAD",
        "target_paths": ["scripts/quality_gate", "tests/quality_gate"],
        "excluded_paths": [".env"],
        "evidence_root": str(tmp_path / "test" / "evidence" / "phase2" / "RUN-P2-S2-001"),
        "checks": [
            {"gate": "formatter", "command": ["ruff", "format", "--check", "scripts/quality_gate", "tests/quality_gate"]},
            {"gate": "lint", "command": ["ruff", "check", "scripts/quality_gate", "tests/quality_gate"]},
            {"gate": "type", "command": ["mypy", "scripts/quality_gate"]},
            {"gate": "test", "command": ["python", "-m", "scripts.quality_gate.local_pytest"]},
        ],
        "review": {"critical": 0, "high": 0},
        "human_gate_policy": "S2-HG-01",
        "unknowns": [],
    }
    value.update(overrides)
    return value


def successful_executor() -> FakeExecutor:
    commands = {
        ("ruff", "format", "--check", "scripts/quality_gate", "tests/quality_gate"),
        ("ruff", "check", "scripts/quality_gate", "tests/quality_gate"),
        ("mypy", "scripts/quality_gate"),
        ("python", "-m", "scripts.quality_gate.local_pytest"),
    }
    return FakeExecutor(
        results={command: CommandResult(exit_code=0, duration_ms=1) for command in commands},
        calls=[],
    )


def runner(tmp_path: Path, executor: FakeExecutor, inspector: FakeChangeInspector | None = None) -> LocalQualityGateRunner:
    return LocalQualityGateRunner(tmp_path, executor=executor, change_inspector=inspector or FakeChangeInspector())


def test_dry_run_records_planned_local_gates_without_executing(tmp_path: Path) -> None:
    executor = successful_executor()

    result = runner(tmp_path, executor).run(manifest(tmp_path), dry_run=True)

    assert result.state == "DRY_RUN"
    assert [gate.status for gate in result.gates] == ["PLANNED"] * 4
    assert executor.calls == []


def test_success_requires_external_human_gate_and_writes_sanitized_evidence(tmp_path: Path) -> None:
    executor = successful_executor()
    run_manifest = manifest(tmp_path)
    result = runner(tmp_path, executor).run(run_manifest, write_evidence=True)

    evidence_path = Path(str(run_manifest["evidence_root"])) / "verification.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert result.state == "HUMAN_GATE_REQUIRED"
    assert evidence["state"] == "HUMAN_GATE_REQUIRED"
    assert "stdout" not in json.dumps(evidence)
    assert len(executor.calls) == 4


def test_failed_gate_stops_before_later_gates(tmp_path: Path) -> None:
    executor = successful_executor()
    lint_command = ("ruff", "check", "scripts/quality_gate", "tests/quality_gate")
    executor.results[lint_command] = CommandResult(exit_code=1, duration_ms=2)

    result = runner(tmp_path, executor).run(manifest(tmp_path))

    assert result.state == "FAILED"
    assert [gate.status for gate in result.gates] == ["PASS", "FAIL"]
    assert executor.calls == [
        ("ruff", "format", "--check", "scripts/quality_gate", "tests/quality_gate"),
        lint_command,
    ]


@pytest.mark.parametrize(
    ("override", "expected_state"),
    [
        ({"review": {"critical": 0, "high": 1}}, "REVIEW_RETURNED"),
        ({}, "HUMAN_GATE_REQUIRED"),
        ({"unknowns": ["UNK-AIF-01"]}, "BLOCKED"),
    ],
)
def test_non_passing_governance_states_are_not_accepted(
    tmp_path: Path, override: dict[str, object], expected_state: str
) -> None:
    executor = successful_executor()

    result = runner(tmp_path, executor).run(manifest(tmp_path, **override))

    assert result.state == expected_state


def test_rejects_non_allowlisted_command_without_running_it(tmp_path: Path) -> None:
    executor = successful_executor()
    unsafe_checks = list(manifest(tmp_path)["checks"])
    unsafe_checks[-1] = {"gate": "test", "command": ["powershell", "Invoke-WebRequest", "https://example.invalid"]}

    with pytest.raises(ManifestValidationError, match="allowlist"):
        runner(tmp_path, executor).run(manifest(tmp_path, checks=unsafe_checks))

    assert executor.calls == []


def test_rejects_evidence_path_outside_project_test_evidence(tmp_path: Path) -> None:
    executor = successful_executor()

    with pytest.raises(ManifestValidationError, match="test/evidence"):
        runner(tmp_path, executor).run(
            manifest(tmp_path, evidence_root=str(tmp_path / "outside"))
        )

    assert executor.calls == []


def test_rejects_wrong_command_type_for_gate_without_running(tmp_path: Path) -> None:
    executor = successful_executor()
    wrong_checks = list(manifest(tmp_path)["checks"])
    wrong_checks[0] = {"gate": "formatter", "command": ["ruff", "check", "scripts/quality_gate"]}

    with pytest.raises(ManifestValidationError, match="formatter"):
        runner(tmp_path, executor).run(manifest(tmp_path, checks=wrong_checks))

    assert executor.calls == []


def test_rejects_test_target_outside_approved_boundary_without_running(tmp_path: Path) -> None:
    executor = successful_executor()
    unsafe_checks = list(manifest(tmp_path)["checks"])
    unsafe_checks[-1] = {"gate": "test", "command": ["python", "-m", "pytest", "research", "-q"]}

    with pytest.raises(ManifestValidationError, match="target_paths"):
        runner(tmp_path, executor).run(manifest(tmp_path, checks=unsafe_checks))

    assert executor.calls == []


def test_blocks_changes_outside_target_paths_before_running_gates(tmp_path: Path) -> None:
    executor = successful_executor()
    inspector = FakeChangeInspector(changes=(ChangeRecord(status="M", path="settings/ai_component_rules.md"),))

    result = runner(tmp_path, executor, inspector).run(manifest(tmp_path))

    assert result.state == "BLOCKED"
    assert executor.calls == []


def test_blocks_added_test_skip_before_running_gates(tmp_path: Path) -> None:
    executor = successful_executor()

    result = runner(tmp_path, executor, FakeChangeInspector(has_test_skip=True)).run(manifest(tmp_path))

    assert result.state == "BLOCKED"
    assert executor.calls == []


def test_cli_runs_from_its_script_path_in_dry_run_mode(tmp_path: Path) -> None:
    run_manifest = manifest(
        tmp_path,
        evidence_root="test/evidence/phase2/RUN-P2-S2-cli",
    )
    manifest_path = tmp_path / "run-manifest.json"
    manifest_path.write_text(json.dumps(run_manifest), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/quality_gate/run_quality_gate.py",
            "--manifest",
            str(manifest_path),
            "--project-root",
            ".",
            "--dry-run",
            "--no-write-evidence",
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert json.loads(completed.stdout)["state"] == "DRY_RUN"


def test_cli_main_returns_dry_run_summary_without_writing_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run_manifest = manifest(
        tmp_path,
        evidence_root=str(tmp_path / "test" / "evidence" / "phase2" / "RUN-P2-S2-cli-main"),
    )
    manifest_path = tmp_path / "run-manifest.json"
    manifest_path.write_text(json.dumps(run_manifest), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_quality_gate.py",
            "--manifest",
            str(manifest_path),
            "--project-root",
            str(tmp_path),
            "--dry-run",
            "--no-write-evidence",
        ],
    )

    exit_code = run_quality_gate.main()

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["state"] == "DRY_RUN"


def test_cli_main_reports_invalid_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest_path = tmp_path / "invalid.json"
    manifest_path.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["run_quality_gate.py", "--manifest", str(manifest_path)])

    exit_code = run_quality_gate.main()

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["state"] == "INVALID_MANIFEST"
