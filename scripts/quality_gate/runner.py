"""Run-manifest driven, local-only implementation quality gates.

Step 04 authority: management change/diff/Evidence/baseline hashes are
intentionally not calculated, compared, or used as a retry/acceptance gate.
Fixture and other direct safety/data/reproducibility hashes remain protected.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from time import perf_counter
from typing import Protocol

REQUIRED_GATES = ("formatter", "lint", "type", "test")
MAX_TIMEOUT_SECONDS = 60
# Legacy S2 self-check remains supported for regression coverage. New phase
# units must be present in the repository-managed registry below.
TRUSTED_TARGET_PATHS = ("scripts/quality_gate", "tests/quality_gate")
TRUSTED_SCOPE_REGISTRY_PATH = Path("scripts/quality_gate/trusted_scopes.json")
LEGACY_BOOTSTRAP_RUN_ID = "RUN-P2-S2-001"


class ManifestValidationError(ValueError):
    """Raised when a run manifest is unsafe or incomplete."""


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    duration_ms: int


@dataclass(frozen=True)
class ChangeRecord:
    """One repository change since the manifest baseline."""

    status: str
    path: str


class CommandExecutor(Protocol):
    def run(self, command: tuple[str, ...], cwd: Path) -> CommandResult: ...


class ChangeInspector(Protocol):
    def list_changes(
        self, project_root: Path, baseline_ref: str, paths: tuple[str, ...] | None = None
    ) -> tuple[ChangeRecord, ...]: ...

    def has_new_test_skip(
        self, project_root: Path, baseline_ref: str, paths: tuple[str, ...] | None = None
    ) -> bool: ...


class NetworkIsolationProbe(Protocol):
    """Confirm an isolation boundary supplied by the trusted host harness."""

    def is_confirmed(self, project_root: Path) -> bool: ...


class EnvironmentNetworkIsolationProbe:
    """Require an explicit host-provided marker; never probe an external host."""

    def is_confirmed(self, project_root: Path) -> bool:
        del project_root
        return os.environ.get("QUALITY_GATE_NETWORK_ISOLATION_CONFIRMED") == "1"


class SubprocessExecutor:
    """Execute a validated local command without shell or inherited secrets."""

    def run(self, command: tuple[str, ...], cwd: Path) -> CommandResult:
        started = perf_counter()
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=MAX_TIMEOUT_SECONDS,
            env=_minimal_environment(cwd),
        )
        return CommandResult(completed.returncode, int((perf_counter() - started) * 1_000))


class GitChangeInspector:
    """Read git changes only; it never mutates the worktree or uses a network."""

    def list_changes(
        self, project_root: Path, baseline_ref: str, paths: tuple[str, ...] | None = None
    ) -> tuple[ChangeRecord, ...]:
        pathspecs = list(paths) if paths else []
        completed = _git(project_root, ["diff", "--name-status", "--no-renames", baseline_ref, "--", *pathspecs])
        if completed.returncode:
            raise OSError("git diff failed")
        changes = []
        for line in completed.stdout.splitlines():
            fields = line.split("\t", 1)
            if len(fields) == 2:
                changes.append(ChangeRecord(fields[0][:1], fields[1]))
        tracked = {change.path for change in changes}
        untracked = _git_paths(project_root, pathspecs or None)
        if untracked is None:
            raise OSError("git ls-files failed")
        changes.extend(ChangeRecord("A", path) for path in untracked if path not in tracked)
        return tuple(changes)

    def has_new_test_skip(self, project_root: Path, baseline_ref: str, paths: tuple[str, ...] | None = None) -> bool:
        # Skip/xfail is a test mutation only.  Do not scan quality-gate
        # implementation files themselves, which legitimately contain the
        # forbidden-token list used by this checker.
        pathspecs = [
            path for path in (list(paths) if paths else ["tests"]) if _within(_normal_path(path, "path"), "tests")
        ]
        if not pathspecs:
            return False
        completed = _git(project_root, ["diff", "--unified=0", baseline_ref, "--", *pathspecs])
        if completed.returncode:
            raise OSError("git diff failed")
        forbidden = (
            "pytest.mark.skip",
            "pytest.skip(",
            "@unittest.skip",
            "pytest.mark.xfail",
            "pytest.xfail(",
            "pytest.importorskip(",
        )
        if any(
            line.startswith("+") and any(token in line for token in forbidden) for line in completed.stdout.splitlines()
        ):
            return True
        untracked = _git_paths(project_root, pathspecs)
        if untracked is None:
            raise OSError("git ls-files failed")
        for relative_path in untracked:
            if not relative_path.endswith(".py"):
                continue
            try:
                source = (project_root / relative_path).read_text(encoding="utf-8")
            except OSError as error:
                raise OSError("untracked test file could not be inspected") from error
            if any(token in source for token in forbidden):
                return True
        return False


@dataclass(frozen=True)
class GateRecord:
    gate: str
    status: str
    command: tuple[str, ...]
    exit_code: int | None = None
    duration_ms: int | None = None


@dataclass(frozen=True)
class GateRunResult:
    state: str
    reason: str
    gates: tuple[GateRecord, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "reason": self.reason,
            "gates": [asdict(gate) for gate in self.gates],
            "generated_at": datetime.now(UTC).isoformat(),
        }


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    baseline_ref: str
    evidence_root: Path
    target_paths: tuple[str, ...]
    excluded_paths: tuple[str, ...]
    checks: tuple[tuple[str, tuple[str, ...]], ...]
    review_critical: int
    review_high: int
    unknowns: tuple[str, ...]
    network_isolation_required: bool = False
    scope_mode: str = "all_changes"


class LocalQualityGateRunner:
    """Validate a bounded Run Manifest and run only its fixed local gate templates."""

    def __init__(
        self,
        project_root: Path,
        executor: CommandExecutor | None = None,
        change_inspector: ChangeInspector | None = None,
        network_probe: NetworkIsolationProbe | None = None,
    ) -> None:
        self._project_root = project_root.resolve()
        self._executor = executor or SubprocessExecutor()
        self._change_inspector = change_inspector or GitChangeInspector()
        self._network_probe = network_probe or EnvironmentNetworkIsolationProbe()

    def run(
        self, manifest_data: Mapping[str, object], *, dry_run: bool = False, write_evidence: bool = False
    ) -> GateRunResult:
        manifest = self._validate_manifest(manifest_data)
        if manifest.unknowns:
            return self._finalize(
                GateRunResult("BLOCKED", "Unknown が未解決です", ()), manifest.evidence_root, write_evidence
            )
        if dry_run:
            planned = tuple(GateRecord(gate, "PLANNED", command) for gate, command in manifest.checks)
            return self._finalize(
                GateRunResult("DRY_RUN", "ローカル検査のみを予定として確認しました", planned),
                manifest.evidence_root,
                write_evidence,
            )
        boundary_problem = self._boundary_problem(manifest)
        if boundary_problem:
            return self._finalize(
                GateRunResult("BLOCKED", boundary_problem, ()), manifest.evidence_root, write_evidence
            )

        records: list[GateRecord] = []
        for gate, command in manifest.checks:
            try:
                command_result = self._executor.run(command, self._project_root)
            except (OSError, subprocess.TimeoutExpired):
                return self._finalize(
                    GateRunResult("INCOMPLETE", f"{gate} のローカル検査を完了できません", tuple(records)),
                    manifest.evidence_root,
                    write_evidence,
                )
            status = "PASS" if command_result.exit_code == 0 else "FAIL"
            records.append(GateRecord(gate, status, command, command_result.exit_code, command_result.duration_ms))
            if status == "FAIL":
                return self._finalize(
                    GateRunResult("FAILED", f"{gate} が失敗しました", tuple(records)),
                    manifest.evidence_root,
                    write_evidence,
                )
        if manifest.review_critical or manifest.review_high:
            return self._finalize(
                GateRunResult("REVIEW_RETURNED", "Critical または High 指摘が未解決です", tuple(records)),
                manifest.evidence_root,
                write_evidence,
            )
        if self._user_approval_present(manifest):
            return self._finalize(
                GateRunResult("PASS", "ユーザーが明示的に承認しました", tuple(records)),
                manifest.evidence_root,
                write_evidence,
            )
        return self._finalize(
            GateRunResult(
                "HUMAN_GATE_REQUIRED",
                "Human Gate はこの書込み可能 worktree 外の承認チャネルで実施します",
                tuple(records),
            ),
            manifest.evidence_root,
            write_evidence,
        )

    def _user_approval_present(self, manifest: RunManifest) -> bool:
        """Accept an explicit user approval declaration as the Human Gate."""
        if os.environ.get("QUALITY_GATE_HUMAN_APPROVED") == "1":
            return True
        declaration = self._project_root / manifest.evidence_root / "human-gate-user-declaration.md"
        try:
            text = declaration.read_text(encoding="utf-8")
        except OSError:
            return False
        return manifest.run_id in text and "ユーザー意思表示: 承認します" in text

    def _validate_manifest(self, data: Mapping[str, object]) -> RunManifest:
        run_id = _required_nonempty_string(data, "run_id")
        for field in (
            "phase_id",
            "step_id",
            "design",
            "orchestrator",
            "data_version",
            "baseline_ref",
            "human_gate_policy",
        ):
            _required_nonempty_string(data, field)
        requirements = _required_string_list(data, "requirements")
        _required_string_list(data, "agents")
        _required_string_list(data, "skills")
        target_paths = tuple(_validated_paths(_required_string_list(data, "target_paths"), "target_paths"))
        excluded_paths = tuple(_validated_paths(_required_string_list(data, "excluded_paths"), "excluded_paths"))
        evidence_root = self._validated_evidence_root(_required_nonempty_string(data, "evidence_root"))
        network_isolation_required = False
        scope_mode = "all_changes"
        if run_id == LEGACY_BOOTSTRAP_RUN_ID:
            fixture = _mapping(data.get("input_fixture"), "input_fixture")
            for field in ("name", "version", "checksum"):
                _required_nonempty_string(fixture, field)
            if target_paths != TRUSTED_TARGET_PATHS:
                raise ManifestValidationError(
                    "target_paths は品質ゲート用の信頼済み固定範囲と完全一致する必要があります"
                )
            checks = _validated_checks(data.get("checks"), target_paths, excluded_paths)
        else:
            scope = _load_trusted_scope(self._project_root, run_id)
            input_field = "input_dbn" if isinstance(scope.get("dbn_input"), Mapping) else "input_fixture"
            fixture = _mapping(data.get(input_field), input_field)
            for field in ("name", "version", "checksum"):
                _required_nonempty_string(fixture, field)
            _validate_manifest_against_scope(
                self._project_root, data, scope, requirements, fixture, target_paths, excluded_paths
            )
            network_value = scope.get("network_isolation_required")
            if not isinstance(network_value, bool):
                raise ManifestValidationError("trusted scope の network_isolation_required が不正です")
            network_isolation_required = network_value
            scope_mode = _required_nonempty_string(scope, "scope_mode")
            if scope_mode not in {"target_only", "all_changes"}:
                raise ManifestValidationError("scope_mode は target_only または all_changes で指定します")
            if data.get("scope_mode", scope_mode) != scope_mode:
                raise ManifestValidationError("scope_mode が trusted scope と一致しません")
            checks = _validated_checks(
                data.get("checks"), target_paths, excluded_paths, expected_checks=scope.get("checks")
            )
        review = _mapping(data.get("review"), "review")
        return RunManifest(
            run_id,
            _required_nonempty_string(data, "baseline_ref"),
            evidence_root,
            target_paths,
            excluded_paths,
            checks,
            _non_negative_int(review.get("critical"), "review.critical"),
            _non_negative_int(review.get("high"), "review.high"),
            tuple(_string_list(data.get("unknowns"), "unknowns", allow_empty=True)),
            network_isolation_required,
            scope_mode,
        )

    def _boundary_problem(self, manifest: RunManifest) -> str | None:
        if manifest.network_isolation_required:
            try:
                isolation_confirmed = self._network_probe.is_confirmed(self._project_root)
            except Exception:
                isolation_confirmed = False
            if not isolation_confirmed:
                return "host の outbound isolation が確認できないため実行を停止しました"
        try:
            # target_only deliberately uses the registry target list as the
            # boundary. Unrelated commits and worktree files do not decide
            # which test this Run executes.
            scoped_paths = manifest.target_paths if manifest.scope_mode == "target_only" else None
            changes = self._change_inspector.list_changes(self._project_root, manifest.baseline_ref, scoped_paths)
            if self._change_inspector.has_new_test_skip(self._project_root, manifest.baseline_ref, scoped_paths):
                return "テストの skip 追加を検出しました"
        except OSError:
            return "変更範囲を検査できません"
        for change in changes:
            path = _normal_path(change.path, "変更パス")
            if _within(path, "tests/evidence"):
                continue
            if change.status == "D" and _within(path, "tests"):
                return "テスト削除を検出しました"
            if any(_within(path, excluded) for excluded in manifest.excluded_paths):
                return "excluded_paths 配下の変更を検出しました"
            if manifest.scope_mode != "target_only" and not any(
                _within(path, target) for target in manifest.target_paths
            ):
                return "target_paths 外の変更を検出しました"
        return None

    def _validated_evidence_root(self, raw_path: str) -> Path:
        candidate = Path(raw_path)
        resolved = (self._project_root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        allowed_root = (self._project_root / "tests" / "evidence").resolve()
        try:
            resolved.relative_to(allowed_root)
        except ValueError as error:
            raise ManifestValidationError("evidence_root は project 内の tests/evidence 配下です") from error
        return resolved

    @staticmethod
    def _finalize(result: GateRunResult, evidence_root: Path, write_evidence: bool) -> GateRunResult:
        if write_evidence:
            evidence_root.mkdir(parents=True, exist_ok=True)
            (evidence_root / "verification.json").write_text(
                json.dumps(result.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        return result


def load_manifest(path: Path) -> Mapping[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestValidationError("Run Manifest JSON を読めません") from error
    return _mapping(data, "Run Manifest")


def _load_trusted_scope(project_root: Path, run_id: str) -> Mapping[str, object]:
    """Load one repository-managed scope; the manifest cannot create scopes."""
    registry_path = project_root / TRUSTED_SCOPE_REGISTRY_PATH
    try:
        registry = _mapping(json.loads(registry_path.read_text(encoding="utf-8")), "trusted scope registry")
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestValidationError("trusted scope registry を読めません") from error
    scopes = _mapping(registry.get("scopes"), "trusted scope registry.scopes")
    scope = scopes.get(run_id)
    if scope is None:
        raise ManifestValidationError("Run ID が trusted scope registry に登録されていません")
    return _mapping(scope, f"trusted scope {run_id}")


def _validate_manifest_against_scope(
    project_root: Path,
    data: Mapping[str, object],
    scope: Mapping[str, object],
    requirements: list[str],
    fixture: Mapping[str, object],
    target_paths: tuple[str, ...],
    excluded_paths: tuple[str, ...],
) -> None:
    """Require every P2 execution input to match the approved registry entry."""
    for field in (
        "phase_id",
        "step_id",
        "design",
        "orchestrator",
        "component_lifecycle_orchestrator",
        "baseline_ref",
        "scope_mode",
    ):
        expected = _required_nonempty_string(scope, field)
        if data.get(field) != expected:
            raise ManifestValidationError(f"{field} が trusted scope と一致しません")
    expected_requirements = _required_string_list(scope, "requirements")
    if requirements != expected_requirements:
        raise ManifestValidationError("requirements が trusted scope と一致しません")
    expected_targets = tuple(_validated_paths(_required_string_list(scope, "target_paths"), "trusted target_paths"))
    expected_excluded = tuple(
        _validated_paths(_required_string_list(scope, "excluded_paths"), "trusted excluded_paths")
    )
    if target_paths != expected_targets or excluded_paths != expected_excluded:
        raise ManifestValidationError("target_paths または excluded_paths が trusted scope と一致しません")
    expected_fixture = _mapping(
        scope.get("dbn_input") if isinstance(scope.get("dbn_input"), Mapping) else scope.get("fixture"),
        "trusted input",
    )
    for field in ("name", "version", "checksum"):
        if fixture.get(field) != expected_fixture.get(field):
            raise ManifestValidationError(f"input descriptor.{field} が trusted scope と一致しません")
    if isinstance(scope.get("dbn_input"), Mapping):
        if not _required_nonempty_string(expected_fixture, "protected_path").startswith("/"):
            raise ManifestValidationError("trusted DBN input はWSLの絶対保護パスです")
    else:
        fixture_path = _normal_path(_required_nonempty_string(expected_fixture, "path"), "trusted fixture.path")
        fixture_file = (project_root / fixture_path).resolve()
        try:
            fixture_file.relative_to(project_root.resolve())
            actual_checksum = "sha256:" + hashlib.sha256(fixture_file.read_bytes()).hexdigest()
        except (OSError, ValueError) as error:
            raise ManifestValidationError("trusted fixture を読み取れません") from error
        if actual_checksum != expected_fixture.get("checksum"):
            raise ManifestValidationError("fixture checksum が trusted scope と一致しません")
    unknowns = tuple(_string_list(data.get("unknowns"), "unknowns", allow_empty=True))
    expected_unknowns = tuple(_string_list(scope.get("unknowns"), "trusted unknowns", allow_empty=True))
    if unknowns != expected_unknowns:
        raise ManifestValidationError("unknowns が trusted scope と一致しません")


def _validated_checks(
    value: object,
    targets: tuple[str, ...],
    excluded: tuple[str, ...],
    *,
    expected_checks: object | None = None,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ManifestValidationError("checks は配列です")
    if len(value) != len(REQUIRED_GATES):
        raise ManifestValidationError("checks は4つの必須ゲートを全て含めます")
    expected_items: Sequence[object] | None = None
    if expected_checks is not None:
        expected_items = _sequence(expected_checks, "trusted checks")
        if len(expected_items) != len(REQUIRED_GATES):
            raise ManifestValidationError("trusted checks は4つの必須ゲートを含めます")
    checks: list[tuple[str, tuple[str, ...]]] = []
    for expected_gate, item in zip(REQUIRED_GATES, value, strict=False):
        check = _mapping(item, "checks の要素")
        if check.get("gate") != expected_gate:
            raise ManifestValidationError("checks は formatter, lint, type, test の固定順です")
        command = _command(check.get("command"))
        if expected_items is not None:
            expected_item = _mapping(expected_items[len(checks)], "trusted checks の要素")
            if command != _command(expected_item.get("command")):
                raise ManifestValidationError("command が trusted scope の固定templateと一致しません")
        _validate_gate_command(expected_gate, command, targets, excluded)
        checks.append((expected_gate, command))
    return tuple(checks)


def _validate_gate_command(
    gate: str, command: tuple[str, ...], targets: tuple[str, ...], excluded: tuple[str, ...]
) -> None:
    executable = Path(command[0]).name.lower()
    args = command[1:]
    python_module = args[1] if len(args) >= 2 and args[0] == "-m" else None
    if gate == "formatter":
        if executable == "ruff":
            valid = len(args) >= 3 and args[:2] == ("format", "--check")
            paths = args[2:]
        else:
            valid = (
                _is_project_python(command[0])
                and python_module == "ruff"
                and len(args) >= 5
                and args[2:4] == ("format", "--check")
            )
            paths = args[4:]
    elif gate == "lint":
        if executable == "ruff":
            valid = len(args) >= 2 and args[0] == "check"
            paths = args[1:]
        else:
            valid = _is_project_python(command[0]) and python_module == "ruff" and len(args) >= 3 and args[2] == "check"
            paths = args[3:]
    elif gate == "type":
        if executable in {"mypy", "pyright"}:
            valid = bool(args)
            paths = args
        else:
            valid = _is_project_python(command[0]) and python_module in {"mypy", "pyright"} and len(args) >= 3
            paths = args[2:]
    else:
        valid = _is_project_python(command[0]) and python_module in {
            "scripts.quality_gate.local_pytest",
            "scripts.quality_gate.local_p2_pytest",
            "scripts.quality_gate.local_p3_pytest",
            "scripts.quality_gate.local_p3_poc",
            "scripts.quality_gate.local_p3_lean_prep",
            "scripts.quality_gate.local_p3_r04_pytest",
            "scripts.quality_gate.local_p3_strategy_pytest",
            "scripts.quality_gate.local_p3_integration",
            "scripts.quality_gate.local_p5r_pytest",
            "scripts.quality_gate.local_p5r2_pytest",
        }
        paths = (
            ("tests/market_data",)
            if python_module in {"pytest", "scripts.quality_gate.local_p2_pytest"}
            else ("tests/strategy", "tests/backtest")
            if python_module == "scripts.quality_gate.local_p3_pytest"
            else ("scripts/quality_gate", "tests/engine_poc")
            if python_module == "scripts.quality_gate.local_p3_poc"
            else ("tests/strategy",)
            if python_module == "scripts.quality_gate.local_p3_strategy_pytest"
            else ("tests/backtest",)
            if python_module == "scripts.quality_gate.local_p3_r04_pytest"
            else ("tests/engine_prep", "tests/strategy", "tests/backtest")
            if python_module == "scripts.quality_gate.local_p3_lean_prep"
            else ("tests/strategy", "tests/backtest")
            if python_module == "scripts.quality_gate.local_p3_integration"
            else ("tests/application", "tests/backtest", "tests/phase5R")
            if python_module == "scripts.quality_gate.local_p5r_pytest"
            else ("tests/application", "tests/backtest", "tests/market_data", "tests/phase5R")
            if python_module == "scripts.quality_gate.local_p5r2_pytest"
            else ("tests/quality_gate",)
        )
        if python_module == "pytest":
            valid = _is_project_python(command[0]) and args[2:] == ("tests/market_data", "-q")
            paths = ("tests/market_data",)
    if not valid or not paths:
        raise ManifestValidationError(
            f"{gate} は target_paths を含む allowlist の固定ローカル検査テンプレートに一致しません"
        )
    for path in paths:
        normalized = _normal_path(path, f"{gate} の対象")
        if not any(_within(normalized, target) for target in targets) or any(
            _within(normalized, item) for item in excluded
        ):
            raise ManifestValidationError(f"{gate} の対象は target_paths 配下である必要があります")


def _is_project_python(value: str) -> bool:
    normalized = value.replace("\\", "/").lower()
    return normalized in {"python", "python.exe", ".venv/scripts/python.exe", ".venv/bin/python"}


def _command(value: object) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not value
        or not all(isinstance(part, str) and part for part in value)
    ):
        raise ManifestValidationError("command は空でない文字列配列です")
    return tuple(value)


def _validated_paths(values: list[str], field_name: str) -> list[str]:
    return [_normal_path(value, field_name) for value in values]


def _normal_path(value: str, field_name: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or str(path) in {"", "."}:
        raise ManifestValidationError(f"{field_name} は project 内の相対パスです")
    return path.as_posix()


def _within(path: str, boundary: str) -> bool:
    return path == boundary or path.startswith(f"{boundary}/")


def _mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ManifestValidationError(f"{field_name} は object です")
    return value


def _sequence(value: object, field_name: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ManifestValidationError(f"{field_name} は配列です")
    return value


def _required_nonempty_string(mapping: Mapping[str, object], field_name: str) -> str:
    value = mapping.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ManifestValidationError(f"{field_name} は空でない文字列です")
    return value


def _required_string_list(mapping: Mapping[str, object], field_name: str) -> list[str]:
    return _string_list(mapping.get(field_name), field_name)


def _string_list(value: object, field_name: str, *, allow_empty: bool = False) -> list[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or (not value and not allow_empty)
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        raise ManifestValidationError(f"{field_name} は文字列配列です")
    return list(value)


def _non_negative_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ManifestValidationError(f"{field_name} は0以上の整数です")
    return value


def _git(project_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={project_root}", *args],
        cwd=project_root,
        check=False,
        shell=False,
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=MAX_TIMEOUT_SECONDS,
        env=_minimal_environment(project_root),
    )


def _minimal_environment(project_root: Path) -> dict[str, str]:
    # Keep the environment minimal while retaining the user-profile variables
    # Git needs to resolve the repository's configured safe.directory entries.
    keys = (
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "MYPY_CACHE_DIR",
    )
    environment = {key: value for key in keys if (value := os.environ.get(key))}
    environment["PYTHONPATH"] = str(project_root)
    environment["QUALITY_GATE_LOCAL_ONLY"] = "1"
    return environment


def _git_paths(project_root: Path, pathspecs: list[str] | None = None) -> tuple[str, ...] | None:
    """Read untracked paths as NUL-delimited UTF-8, preserving Unicode names."""
    args = [
        "-c",
        "core.quotePath=false",
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
    ]
    if pathspecs:
        args.extend(["--", *pathspecs])
    completed = _git(project_root, args)
    if completed.returncode:
        return None
    return tuple(path for path in completed.stdout.split("\0") if path)
