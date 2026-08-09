"""Local quality-gate runner behavior tests."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from scripts.quality_gate import local_p2_pytest, local_p3_pytest, run_quality_gate
from scripts.quality_gate.runner import (
    ChangeRecord,
    CommandResult,
    LocalQualityGateRunner,
    ManifestValidationError,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    change_hash_value: str = "test-change-hash"

    requested_paths: tuple[str, ...] | None = None

    def list_changes(
        self, project_root: Path, baseline_ref: str, paths: tuple[str, ...] | None = None
    ) -> tuple[ChangeRecord, ...]:
        del project_root, baseline_ref
        self.requested_paths = paths
        return self.changes

    def has_new_test_skip(self, project_root: Path, baseline_ref: str, paths: tuple[str, ...] | None = None) -> bool:
        del project_root, baseline_ref
        self.requested_paths = paths
        return self.has_test_skip

    def change_hash(self, project_root: Path, baseline_ref: str, paths: tuple[str, ...] | None = None) -> str:
        del project_root, baseline_ref
        self.requested_paths = paths
        return self.change_hash_value


@dataclass
class FakeNetworkProbe:
    confirmed: bool

    def is_confirmed(self, project_root: Path) -> bool:
        del project_root
        return self.confirmed


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
        "evidence_root": str(tmp_path / "tests" / "evidence" / "phase2" / "RUN-P2-S2-001"),
        "checks": [
            {
                "gate": "formatter",
                "command": ["ruff", "format", "--check", "scripts/quality_gate", "tests/quality_gate"],
            },
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
        (
            ".venv/Scripts/python.exe",
            "-m",
            "ruff",
            "format",
            "--check",
            "src/autotrade/market_data",
            "tests/market_data",
        ),
        (".venv/Scripts/python.exe", "-m", "ruff", "check", "src/autotrade/market_data", "tests/market_data"),
        (".venv/Scripts/python.exe", "-m", "mypy", "src/autotrade/market_data"),
        (".venv/Scripts/python.exe", "-m", "scripts.quality_gate.local_p2_pytest"),
        (
            ".venv/Scripts/python.exe",
            "-m",
            "ruff",
            "format",
            "--check",
            "scripts/quality_gate",
            "tests/quality_gate",
            "tests/strategy",
            "tests/backtest",
        ),
        (
            ".venv/Scripts/python.exe",
            "-m",
            "ruff",
            "check",
            "scripts/quality_gate",
            "tests/quality_gate",
            "tests/strategy",
            "tests/backtest",
        ),
        (".venv/Scripts/python.exe", "-m", "mypy", "scripts/quality_gate"),
        (".venv/Scripts/python.exe", "-m", "scripts.quality_gate.local_p3_pytest"),
    }
    return FakeExecutor(
        results={command: CommandResult(exit_code=0, duration_ms=1) for command in commands},
        calls=[],
    )


def runner(
    tmp_path: Path, executor: FakeExecutor, inspector: FakeChangeInspector | None = None
) -> LocalQualityGateRunner:
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


def test_explicit_user_approval_completes_human_gate(tmp_path: Path) -> None:
    executor = successful_executor()
    run_manifest = manifest(tmp_path)
    evidence_root = Path(str(run_manifest["evidence_root"]))
    evidence_root.mkdir(parents=True)
    (evidence_root / "human-gate-user-declaration.md").write_text(
        "# Human Gate\n\n- Run ID: RUN-P2-S2-001\n- ユーザー意思表示: 承認します\n",
        encoding="utf-8",
    )

    result = runner(tmp_path, executor).run(run_manifest, write_evidence=True)

    evidence = json.loads((evidence_root / "verification.json").read_text(encoding="utf-8"))
    assert result.state == "PASS"
    assert evidence["state"] == "PASS"
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

    with pytest.raises(ManifestValidationError, match="tests/evidence"):
        runner(tmp_path, executor).run(manifest(tmp_path, evidence_root=str(tmp_path / "outside")))

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


def test_p2_target_only_scope_ignores_unrelated_worktree_changes(tmp_path: Path) -> None:
    executor = successful_executor()
    run_manifest = p2_manifest(tmp_path)
    inspector = FakeChangeInspector(
        changes=(
            ChangeRecord(status="M", path="settings/ai_component_rules.md"),
            ChangeRecord(status="A", path="doc/00_全Phase残課題Blocked統合台帳.html"),
        ),
        change_hash_value=run_manifest["change_hash"],
    )

    result = LocalQualityGateRunner(
        tmp_path,
        executor=executor,
        change_inspector=inspector,
        network_probe=FakeNetworkProbe(confirmed=True),
    ).run(run_manifest)

    assert result.state == "HUMAN_GATE_REQUIRED"
    assert inspector.requested_paths == (
        "src/autotrade/market_data",
        "tests/market_data",
        "tests/fixtures/market_data",
    )
    assert len(executor.calls) == 4


def test_blocks_added_test_skip_before_running_gates(tmp_path: Path) -> None:
    executor = successful_executor()

    result = runner(tmp_path, executor, FakeChangeInspector(has_test_skip=True)).run(manifest(tmp_path))

    assert result.state == "BLOCKED"
    assert executor.calls == []


def test_cli_runs_from_its_script_path_in_dry_run_mode(tmp_path: Path) -> None:
    run_manifest = manifest(
        tmp_path,
        evidence_root="tests/evidence/phase2/RUN-P2-S2-cli",
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
        evidence_root=str(tmp_path / "tests" / "evidence" / "phase2" / "RUN-P2-S2-cli-main"),
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


def p2_manifest(tmp_path: Path, **overrides: object) -> dict[str, object]:
    """Return the approved P2-D07 pilot manifest shape."""
    (tmp_path / "scripts" / "quality_gate").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tests" / "fixtures" / "market_data").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        PROJECT_ROOT / "scripts" / "quality_gate" / "trusted_scopes.json",
        tmp_path / "scripts" / "quality_gate" / "trusted_scopes.json",
    )
    shutil.copyfile(
        PROJECT_ROOT / "tests" / "fixtures" / "market_data" / "catalog_resolver_fixture.json",
        tmp_path / "tests" / "fixtures" / "market_data" / "catalog_resolver_fixture.json",
    )
    value = manifest(
        tmp_path,
        run_id="RUN-P2-IC-001",
        step_id="P2-05",
        requirements=["REQ-Q02", "REQ-Q19", "REQ-Q20", "REQ-Q23"],
        design="P2-D07",
        component_lifecycle_orchestrator="AutoTradeComponentLifecycle_Orchestrator_v0_1",
        agents=[
            "AutoTrade_A110_PythonTestEngineer_v0_1",
            "AutoTrade_A120_PythonImplementer_v0_1",
            "AutoTrade_A130_VerificationEngineer_v0_1",
            "AutoTrade_A150_PythonCodeReviewer_v0_1",
            "AutoTrade_A160_TradingSecurityReviewer_v0_1",
        ],
        skills=[
            "autotrade_skill_python_implementation_v0_1",
            "autotrade_skill_python_test_quality_v0_1",
            "autotrade_skill_python_code_review_v0_1",
        ],
        input_fixture={
            "name": "catalog_resolver_fixture.json",
            "version": "fixture-catalog-v1",
            "checksum": "sha256:94022229698e972353b8ec9537f455af5cb29d47253f5f2a1ed5d33b08b50169",
        },
        data_version="fixture-catalog-v1",
        change_hash="sha256:" + ("a" * 64),
        target_paths=[
            "src/autotrade/market_data",
            "tests/market_data",
            "tests/fixtures/market_data",
        ],
        excluded_paths=[".env", "third_party/everything-claude-code", "research"],
        scope_mode="target_only",
        checks=[
            {
                "gate": "formatter",
                "command": [
                    ".venv/Scripts/python.exe",
                    "-m",
                    "ruff",
                    "format",
                    "--check",
                    "src/autotrade/market_data",
                    "tests/market_data",
                ],
            },
            {
                "gate": "lint",
                "command": [
                    ".venv/Scripts/python.exe",
                    "-m",
                    "ruff",
                    "check",
                    "src/autotrade/market_data",
                    "tests/market_data",
                ],
            },
            {"gate": "type", "command": [".venv/Scripts/python.exe", "-m", "mypy", "src/autotrade/market_data"]},
            {"gate": "test", "command": [".venv/Scripts/python.exe", "-m", "scripts.quality_gate.local_p2_pytest"]},
        ],
        human_gate_policy="P2-IC-HG-01",
    )
    value.update(overrides)
    return value


def test_p2_registry_accepts_only_the_fixed_scope_and_four_gates(tmp_path: Path) -> None:
    executor = successful_executor()

    result = runner(tmp_path, executor).run(p2_manifest(tmp_path), dry_run=True)

    assert result.state == "DRY_RUN"
    assert [gate.command for gate in result.gates] == [
        (
            ".venv/Scripts/python.exe",
            "-m",
            "ruff",
            "format",
            "--check",
            "src/autotrade/market_data",
            "tests/market_data",
        ),
        (".venv/Scripts/python.exe", "-m", "ruff", "check", "src/autotrade/market_data", "tests/market_data"),
        (".venv/Scripts/python.exe", "-m", "mypy", "src/autotrade/market_data"),
        (".venv/Scripts/python.exe", "-m", "scripts.quality_gate.local_p2_pytest"),
    ]


@pytest.mark.parametrize(
    "field_override",
    [
        {"target_paths": ["research"]},
        {"checks": [{"gate": "formatter", "command": ["powershell", "Invoke-WebRequest"]}]},
        {"checks": [{"gate": "formatter", "command": [".venv/Scripts/python.exe", "-m", "pytest"]}]},
        {
            "input_fixture": {
                "name": "catalog_resolver_fixture.json",
                "version": "fixture-catalog-v1",
                "checksum": "sha256:tampered",
            }
        },
        {"baseline_ref": "main"},
        {"scope_mode": "all_changes"},
        {"change_hash": "sha256:tampered"},
    ],
)
def test_p2_manifest_mutations_are_rejected_before_execution(tmp_path: Path, field_override: dict[str, object]) -> None:
    executor = successful_executor()

    with pytest.raises(ManifestValidationError):
        runner(tmp_path, executor).run(p2_manifest(tmp_path, **field_override))

    assert executor.calls == []


@pytest.mark.parametrize(
    "inspector",
    [
        FakeChangeInspector(changes=(ChangeRecord("A", "untrusted.py"),)),
        FakeChangeInspector(changes=(ChangeRecord("D", "tests/market_data/test_catalog_resolver.py"),)),
        FakeChangeInspector(changes=(ChangeRecord("M", ".env"),)),
        FakeChangeInspector(has_test_skip=True),
    ],
)
def test_p2_untrusted_changes_and_test_mutations_fail_closed(tmp_path: Path, inspector: FakeChangeInspector) -> None:
    executor = successful_executor()

    inspector.change_hash_value = p2_manifest(tmp_path)["change_hash"]
    result = runner(tmp_path, executor, inspector).run(p2_manifest(tmp_path))

    assert result.state == "BLOCKED"
    assert executor.calls == []


def test_p2_requires_host_outbound_isolation_confirmation(tmp_path: Path) -> None:
    executor = successful_executor()

    inspector = FakeChangeInspector(change_hash_value=p2_manifest(tmp_path)["change_hash"])
    result = runner(tmp_path, executor, inspector).run(p2_manifest(tmp_path))

    assert result.state == "BLOCKED"
    assert "outbound" in result.reason.lower()
    assert executor.calls == []


def test_p2_runs_fixed_gates_only_after_host_isolation_confirmation(tmp_path: Path) -> None:
    executor = successful_executor()
    run_manifest = p2_manifest(tmp_path)
    inspector = FakeChangeInspector(change_hash_value=run_manifest["change_hash"])
    quality_runner = LocalQualityGateRunner(
        tmp_path,
        executor=executor,
        change_inspector=inspector,
        network_probe=FakeNetworkProbe(confirmed=True),
    )

    result = quality_runner.run(run_manifest)

    assert result.state == "HUMAN_GATE_REQUIRED"
    assert len(executor.calls) == 4


def test_p2_python_module_mutation_is_rejected_against_registry(tmp_path: Path) -> None:
    executor = successful_executor()
    checks = list(p2_manifest(tmp_path)["checks"])
    checks[3] = {"gate": "test", "command": [".venv/Scripts/python.exe", "-m", "pytest", "tests/market_data", "-q"]}

    with pytest.raises(ManifestValidationError, match="固定template"):
        runner(tmp_path, executor).run(p2_manifest(tmp_path, checks=checks))

    assert executor.calls == []


def test_p2_pytest_wrapper_has_a_fixed_market_data_target(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePytest:
        @staticmethod
        def main(args: list[str]) -> int:
            assert args == ["tests/market_data", "-q"]
            return 0

    monkeypatch.setitem(sys.modules, "pytest", FakePytest)

    assert local_p2_pytest.main() == 0


def test_p3_pytest_wrapper_has_only_fixed_strategy_and_backtest_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePytest:
        @staticmethod
        def main(args: list[str], plugins: list[object]) -> int:
            assert args == ["tests/strategy", "tests/backtest", "--runxfail", "-q"]
            assert len(plugins) == 1
            return 0

    monkeypatch.setitem(sys.modules, "pytest", FakePytest)

    assert local_p3_pytest.main() == 0


def test_p3_wrapper_marks_collection_or_execution_skip_as_invalid() -> None:
    class SkippedReport:
        outcome = "skipped"

    plugin = local_p3_pytest._NoSkipPlugin()
    plugin.pytest_collectreport(SkippedReport())
    plugin.pytest_runtest_logreport(SkippedReport())

    assert plugin.skipped is True


def test_p3_strategy_wrapper_has_only_the_fixed_strategy_target(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.quality_gate import local_p3_strategy_pytest

    class FakePytest:
        @staticmethod
        def main(args: list[str], plugins: list[object]) -> int:
            assert args == ["tests/strategy", "--runxfail", "-q"]
            assert len(plugins) == 1
            return 0

    monkeypatch.setitem(sys.modules, "pytest", FakePytest)

    assert local_p3_strategy_pytest.main() == 0


def test_p3_fixed_test_template_is_allowed_only_inside_declared_targets(tmp_path: Path) -> None:
    executor = successful_executor()
    registry_path = tmp_path / "scripts" / "quality_gate" / "trusted_scopes.json"
    registry_path.parent.mkdir(parents=True)
    shutil.copy(PROJECT_ROOT / "scripts" / "quality_gate" / "trusted_scopes.json", registry_path)
    fixture_path = tmp_path / "tests" / "fixtures" / "phase3" / "run_p3_gold_fixture_manifest.json"
    fixture_path.parent.mkdir(parents=True)
    shutil.copy(PROJECT_ROOT / "tests" / "fixtures" / "phase3" / "run_p3_gold_fixture_manifest.json", fixture_path)
    p3_checks = [
        {
            "gate": "formatter",
            "command": [
                ".venv/Scripts/python.exe",
                "-m",
                "ruff",
                "format",
                "--check",
                "scripts/quality_gate",
                "tests/quality_gate",
                "tests/strategy",
                "tests/backtest",
            ],
        },
        {
            "gate": "lint",
            "command": [
                ".venv/Scripts/python.exe",
                "-m",
                "ruff",
                "check",
                "scripts/quality_gate",
                "tests/quality_gate",
                "tests/strategy",
                "tests/backtest",
            ],
        },
        {"gate": "type", "command": [".venv/Scripts/python.exe", "-m", "mypy", "scripts/quality_gate"]},
        {"gate": "test", "command": [".venv/Scripts/python.exe", "-m", "scripts.quality_gate.local_p3_pytest"]},
    ]
    p3_manifest = manifest(
        tmp_path,
        run_id="RUN-P3-GOLD-001",
        phase_id="phase3",
        step_id="P3-05",
        requirements=["P3-AC-01", "P3-AC-02", "P3-AC-03", "P3-AC-04", "P3-AC-05", "P3-AC-06", "P3-AC-07", "P3-AC-08"],
        design="P3-D04-P3-D05-P3-D06",
        component_lifecycle_orchestrator="AutoTradeComponentLifecycle_Orchestrator_v0_1",
        input_fixture={
            "name": "run_p3_gold_fixture_manifest.json",
            "version": "p3-gold-fixture-manifest-v1",
            "checksum": "sha256:19eff1a99d407570e73fac74d3e0e00bbaf72c3c4278e6f046dcc6723adcc314",
        },
        change_hash="sha256:" + ("a" * 64),
        target_paths=[
            "scripts/quality_gate",
            "tests/quality_gate",
            "tests/strategy",
            "tests/backtest",
            "tests/fixtures/strategy",
            "tests/fixtures/phase3",
        ],
        excluded_paths=[".env", "third_party/everything-claude-code", "research", "E:/strategy_test_data"],
        scope_mode="target_only",
        unknowns=[],
        checks=p3_checks,
    )

    result = runner(tmp_path, executor).run(p3_manifest, dry_run=True)

    assert result.state == "DRY_RUN"
    assert len(result.gates) == 4


def test_p3_m30_scope_is_h3_1r_gated_and_pins_its_v2_parent_fixture() -> None:
    registry = json.loads(
        (PROJECT_ROOT / "scripts" / "quality_gate" / "trusted_scopes.json").read_text(encoding="utf-8")
    )
    scope = registry["scopes"]["RUN-P3-M30-001"]

    assert scope["phase_id"] == "phase3"
    assert scope["step_id"] == "P3-05R"
    assert scope["fixture"] == {
        "path": "tests/fixtures/phase3/run_p3_m30_fixture_manifest_v2.json",
        "name": "run_p3_m30_fixture_manifest_v2.json",
        "version": "p3-m30-fixture-manifest-v2",
        "checksum": "sha256:224d6c54fe0fdbf039bc5819140e9d12aa23e27e55ece5de22a5f4800b2b985b",
    }
    assert scope["unknowns"] == []
    assert scope["network_isolation_required"] is True
    assert [check["gate"] for check in scope["checks"]] == ["formatter", "lint", "type", "test"]


def test_p3_strategy_scope_pins_the_approved_v1_v2_archive_and_v3_safety_manifest() -> None:
    registry = json.loads(
        (PROJECT_ROOT / "scripts" / "quality_gate" / "trusted_scopes.json").read_text(encoding="utf-8")
    )
    scope = registry["scopes"]["RUN-P3-STR-001"]

    assert scope["phase_id"] == "phase3"
    assert scope["step_id"] == "P3-06"
    assert scope["fixture"]["path"] == "tests/fixtures/phase3/run_p3_strategy_fixture_manifest_v3.json"
    assert scope["fixture"]["checksum"] == "sha256:4a410f7ac15837ebb9d899daecd56f0c6e45c3795d7f8db067daef80359531e0"
    assert scope["unknowns"] == []
    assert "src/autotrade/strategy" in scope["target_paths"]
    assert [check["gate"] for check in scope["checks"]] == ["formatter", "lint", "type", "test"]
