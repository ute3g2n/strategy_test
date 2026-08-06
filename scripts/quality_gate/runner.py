"""Run-manifest driven, local-only implementation quality gates."""

from __future__ import annotations

import json
import os
import hashlib
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from time import perf_counter
from typing import Protocol


REQUIRED_GATES = ("formatter", "lint", "type", "test")
MAX_TIMEOUT_SECONDS = 60
TRUSTED_TARGET_PATHS = ("scripts/quality_gate", "tests/quality_gate")


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
    def list_changes(self, project_root: Path, baseline_ref: str) -> tuple[ChangeRecord, ...]: ...

    def has_new_test_skip(self, project_root: Path, baseline_ref: str) -> bool: ...

    def change_hash(self, project_root: Path, baseline_ref: str) -> str: ...


class SubprocessExecutor:
    """Execute a validated local command without shell or inherited secrets."""

    def run(self, command: tuple[str, ...], cwd: Path) -> CommandResult:
        started = perf_counter()
        completed = subprocess.run(
            command, cwd=cwd, check=False, shell=False, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=MAX_TIMEOUT_SECONDS, env=_minimal_environment(cwd),
        )
        return CommandResult(completed.returncode, int((perf_counter() - started) * 1_000))


class GitChangeInspector:
    """Read git changes only; it never mutates the worktree or uses a network."""

    def list_changes(self, project_root: Path, baseline_ref: str) -> tuple[ChangeRecord, ...]:
        completed = _git(project_root, ["diff", "--name-status", "--no-renames", baseline_ref, "--"])
        if completed.returncode:
            raise OSError("git diff failed")
        changes = []
        for line in completed.stdout.splitlines():
            fields = line.split("\t", 1)
            if len(fields) == 2:
                changes.append(ChangeRecord(fields[0][:1], fields[1]))
        tracked = {change.path for change in changes}
        untracked = _git(project_root, ["ls-files", "--others", "--exclude-standard"])
        if untracked.returncode:
            raise OSError("git ls-files failed")
        changes.extend(ChangeRecord("A", path) for path in untracked.stdout.splitlines() if path not in tracked)
        return tuple(changes)

    def has_new_test_skip(self, project_root: Path, baseline_ref: str) -> bool:
        completed = _git(project_root, ["diff", "--unified=0", baseline_ref, "--", "tests"])
        if completed.returncode:
            raise OSError("git diff failed")
        forbidden = ("pytest.mark.skip", "pytest.skip(", "@unittest.skip")
        return any(line.startswith("+") and any(token in line for token in forbidden) for line in completed.stdout.splitlines())

    def change_hash(self, project_root: Path, baseline_ref: str) -> str:
        diff = _git(project_root, ["diff", "--binary", baseline_ref, "--"])
        untracked = _git(project_root, ["ls-files", "--others", "--exclude-standard"])
        if diff.returncode or untracked.returncode:
            raise OSError("git change hash failed")
        digest = hashlib.sha256(diff.stdout.encode("utf-8"))
        for relative in sorted(untracked.stdout.splitlines()):
            path = project_root / relative
            digest.update(relative.encode("utf-8"))
            digest.update(path.read_bytes())
        return f"sha256:{digest.hexdigest()}"


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
        return {"state": self.state, "reason": self.reason, "gates": [asdict(gate) for gate in self.gates], "generated_at": datetime.now(UTC).isoformat()}


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    change_hash: str
    baseline_ref: str
    evidence_root: Path
    target_paths: tuple[str, ...]
    excluded_paths: tuple[str, ...]
    checks: tuple[tuple[str, tuple[str, ...]], ...]
    review_critical: int
    review_high: int
    unknowns: tuple[str, ...]


class LocalQualityGateRunner:
    """Validate a bounded Run Manifest and run only its fixed local gate templates."""

    def __init__(self, project_root: Path, executor: CommandExecutor | None = None, change_inspector: ChangeInspector | None = None) -> None:
        self._project_root = project_root.resolve()
        self._executor = executor or SubprocessExecutor()
        self._change_inspector = change_inspector or GitChangeInspector()

    def run(self, manifest_data: Mapping[str, object], *, dry_run: bool = False, write_evidence: bool = False) -> GateRunResult:
        manifest = self._validate_manifest(manifest_data)
        if manifest.unknowns:
            return self._finalize(GateRunResult("BLOCKED", "Unknown が未解決です", ()), manifest.evidence_root, write_evidence)
        if dry_run:
            planned = tuple(GateRecord(gate, "PLANNED", command) for gate, command in manifest.checks)
            return self._finalize(GateRunResult("DRY_RUN", "ローカル検査のみを予定として確認しました", planned), manifest.evidence_root, write_evidence)
        boundary_problem = self._boundary_problem(manifest)
        if boundary_problem:
            return self._finalize(GateRunResult("BLOCKED", boundary_problem, ()), manifest.evidence_root, write_evidence)

        records: list[GateRecord] = []
        for gate, command in manifest.checks:
            try:
                command_result = self._executor.run(command, self._project_root)
            except (OSError, subprocess.TimeoutExpired):
                return self._finalize(GateRunResult("INCOMPLETE", f"{gate} のローカル検査を完了できません", tuple(records)), manifest.evidence_root, write_evidence)
            status = "PASS" if command_result.exit_code == 0 else "FAIL"
            records.append(GateRecord(gate, status, command, command_result.exit_code, command_result.duration_ms))
            if status == "FAIL":
                return self._finalize(GateRunResult("FAILED", f"{gate} が失敗しました", tuple(records)), manifest.evidence_root, write_evidence)
        if manifest.review_critical or manifest.review_high:
            return self._finalize(GateRunResult("REVIEW_RETURNED", "Critical または High 指摘が未解決です", tuple(records)), manifest.evidence_root, write_evidence)
        return self._finalize(GateRunResult("HUMAN_GATE_REQUIRED", "Human Gate はこの書込み可能 worktree 外の承認チャネルで実施します", tuple(records)), manifest.evidence_root, write_evidence)

    def _validate_manifest(self, data: Mapping[str, object]) -> RunManifest:
        run_id = _required_nonempty_string(data, "run_id")
        for field in ("phase_id", "step_id", "design", "orchestrator", "data_version", "change_hash", "baseline_ref", "human_gate_policy"):
            _required_nonempty_string(data, field)
        _required_string_list(data, "requirements")
        _required_string_list(data, "agents")
        _required_string_list(data, "skills")
        fixture = _mapping(data.get("input_fixture"), "input_fixture")
        for field in ("name", "version", "checksum"):
            _required_nonempty_string(fixture, field)
        target_paths = tuple(_validated_paths(_required_string_list(data, "target_paths"), "target_paths"))
        if target_paths != TRUSTED_TARGET_PATHS:
            raise ManifestValidationError("target_paths は品質ゲート用の信頼済み固定範囲と完全一致する必要があります")
        excluded_paths = tuple(_validated_paths(_required_string_list(data, "excluded_paths"), "excluded_paths"))
        evidence_root = self._validated_evidence_root(_required_nonempty_string(data, "evidence_root"))
        checks = _validated_checks(data.get("checks"), target_paths, excluded_paths)
        review = _mapping(data.get("review"), "review")
        return RunManifest(run_id, _required_nonempty_string(data, "change_hash"), _required_nonempty_string(data, "baseline_ref"), evidence_root, target_paths, excluded_paths, checks, _non_negative_int(review.get("critical"), "review.critical"), _non_negative_int(review.get("high"), "review.high"), tuple(_string_list(data.get("unknowns"), "unknowns", allow_empty=True)))

    def _boundary_problem(self, manifest: RunManifest) -> str | None:
        try:
            changes = self._change_inspector.list_changes(self._project_root, manifest.baseline_ref)
            if self._change_inspector.has_new_test_skip(self._project_root, manifest.baseline_ref):
                return "テストの skip 追加を検出しました"
            if self._change_inspector.change_hash(self._project_root, manifest.baseline_ref) != manifest.change_hash:
                return "change_hash が実際のローカル差分と一致しません"
        except OSError:
            return "変更範囲を検査できません"
        for change in changes:
            path = _normal_path(change.path, "変更パス")
            if _within(path, "test/evidence"):
                continue
            if change.status == "D" and _within(path, "tests"):
                return "テスト削除を検出しました"
            if any(_within(path, excluded) for excluded in manifest.excluded_paths):
                return "excluded_paths 配下の変更を検出しました"
            if not any(_within(path, target) for target in manifest.target_paths):
                return "target_paths 外の変更を検出しました"
        return None

    def _validated_evidence_root(self, raw_path: str) -> Path:
        candidate = Path(raw_path)
        resolved = (self._project_root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        allowed_root = (self._project_root / "test" / "evidence").resolve()
        try:
            resolved.relative_to(allowed_root)
        except ValueError as error:
            raise ManifestValidationError("evidence_root は project 内の test/evidence 配下です") from error
        return resolved

    @staticmethod
    def _finalize(result: GateRunResult, evidence_root: Path, write_evidence: bool) -> GateRunResult:
        if write_evidence:
            evidence_root.mkdir(parents=True, exist_ok=True)
            (evidence_root / "verification.json").write_text(json.dumps(result.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result


def load_manifest(path: Path) -> Mapping[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ManifestValidationError("Run Manifest JSON を読めません") from error
    return _mapping(data, "Run Manifest")


def _validated_checks(value: object, targets: tuple[str, ...], excluded: tuple[str, ...]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ManifestValidationError("checks は配列です")
    if len(value) != len(REQUIRED_GATES):
        raise ManifestValidationError("checks は4つの必須ゲートを全て含めます")
    checks: list[tuple[str, tuple[str, ...]]] = []
    for expected_gate, item in zip(REQUIRED_GATES, value, strict=False):
        check = _mapping(item, "checks の要素")
        if check.get("gate") != expected_gate:
            raise ManifestValidationError("checks は formatter, lint, type, test の固定順です")
        command = _command(check.get("command"))
        _validate_gate_command(expected_gate, command, targets, excluded)
        checks.append((expected_gate, command))
    return tuple(checks)


def _validate_gate_command(gate: str, command: tuple[str, ...], targets: tuple[str, ...], excluded: tuple[str, ...]) -> None:
    executable = Path(command[0]).name.lower()
    args = command[1:]
    if gate == "formatter":
        valid = executable == "ruff" and len(args) >= 3 and args[:2] == ("format", "--check")
        paths = args[2:]
    elif gate == "lint":
        valid = executable == "ruff" and len(args) >= 2 and args[0] == "check"
        paths = args[1:]
    elif gate == "type":
        valid = executable in {"mypy", "pyright"} and bool(args)
        paths = args
    else:
        valid = _is_project_python(command[0]) and args == ("-m", "scripts.quality_gate.local_pytest")
        paths = ("tests/quality_gate",)
    if not valid or not paths:
        raise ManifestValidationError(f"{gate} は target_paths を含む allowlist の固定ローカル検査テンプレートに一致しません")
    for path in paths:
        normalized = _normal_path(path, f"{gate} の対象")
        if not any(_within(normalized, target) for target in targets) or any(_within(normalized, item) for item in excluded):
            raise ManifestValidationError(f"{gate} の対象は target_paths 配下である必要があります")


def _is_project_python(value: str) -> bool:
    normalized = value.replace("\\", "/").lower()
    return normalized in {"python", "python.exe", ".venv/scripts/python.exe", ".venv/bin/python"}


def _command(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value or not all(isinstance(part, str) and part for part in value):
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


def _required_nonempty_string(mapping: Mapping[str, object], field_name: str) -> str:
    value = mapping.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ManifestValidationError(f"{field_name} は空でない文字列です")
    return value


def _required_string_list(mapping: Mapping[str, object], field_name: str) -> list[str]:
    return _string_list(mapping.get(field_name), field_name)


def _string_list(value: object, field_name: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or (not value and not allow_empty) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ManifestValidationError(f"{field_name} は文字列配列です")
    return list(value)


def _non_negative_int(value: object, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ManifestValidationError(f"{field_name} は0以上の整数です")
    return value


def _git(project_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=project_root, check=False, shell=False, text=True, capture_output=True, timeout=MAX_TIMEOUT_SECONDS, env=_minimal_environment(project_root))


def _minimal_environment(project_root: Path) -> dict[str, str]:
    keys = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
    environment = {key: value for key in keys if (value := os.environ.get(key))}
    environment["PYTHONPATH"] = str(project_root)
    environment["QUALITY_GATE_LOCAL_ONLY"] = "1"
    return environment
