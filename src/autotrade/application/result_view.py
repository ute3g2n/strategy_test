"""Read-only result reference and metric view contracts."""

from __future__ import annotations

import json
import os
import shutil
import stat
import threading
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .contracts import ResultReference, canonical_json, is_safe_id

_PROTECTED_ARTIFACT_KINDS = frozenset(
    {
        "CSV",
        "HISTORICAL_DATA",
        "DATA",
        "RUN",
        "RUN_MANIFEST",
        "AUDIT",
        "EVIDENCE",
    }
)
_ACTIVE_RUN_STATES = frozenset({"QUEUED", "RUNNING", "STOP_REQUESTED", "CANCEL_REQUESTED", "RECOVERY_REQUIRED"})
_UNSAFE_PATH_KINDS = frozenset({"SYMLINK", "REPARSE", "SYMLINK_OR_REPARSE", "TOCTOU", "TRAVERSAL", "ABSOLUTE"})
_TERMINAL_RESULT_STATES = frozenset({"SUCCEEDED"})


@dataclass(frozen=True)
class MetricSet:
    total_pnl: str
    maximum_drawdown: str
    trade_count: int
    win_rate: str
    ending_balance: str
    unit: str
    period_start_utc: str
    period_end_utc: str
    rounding_rule: str
    # Optional protected Core result identity.  Local result-file identity is
    # deliberately not generated here.
    source_result_sha256: str | None


class LocalResultArtifacts:
    """Relative, atomic result files owned outside metadata persistence."""

    def __init__(self, root: Path, *, physical_delete_enabled: bool = False) -> None:
        raw_root = Path(root)
        if raw_root.exists() and self._is_link_or_reparse(raw_root):
            raise ValueError("RESULT_PATH_UNSAFE")
        self.root = raw_root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.results_root = self.root / "results"
        self.audit_root = self.root / "audit" / "result-delete"
        self._ensure_directory_safe(self.results_root)
        self._ensure_directory_safe(self.audit_root)
        self._physical_delete_enabled = physical_delete_enabled
        self._delete_lock = threading.RLock()
        self._delete_sequence = 0
        self._delete_cache: dict[tuple[str, str], dict[str, object]] = {}
        self._delete_audits: dict[str, dict[str, object]] = {}
        self._delete_tombstones: dict[str, dict[str, object]] = {}
        self._load_delete_audits()

    @staticmethod
    def _is_link_or_reparse(path: Path) -> bool:
        try:
            attributes = getattr(path.lstat(), "st_file_attributes", 0)
            return path.is_symlink() or bool(attributes & 0x0400)
        except FileNotFoundError:
            return False
        except OSError:
            return True

    @classmethod
    def _ensure_directory_safe(cls, path: Path) -> None:
        if path.exists() and cls._is_link_or_reparse(path):
            raise ValueError("RESULT_PATH_UNSAFE")
        path.mkdir(parents=True, exist_ok=True)
        if cls._is_link_or_reparse(path):
            raise ValueError("RESULT_PATH_UNSAFE")

    @classmethod
    def _assert_path_chain_safe(cls, path: Path, root: Path) -> None:
        if cls._is_link_or_reparse(root):
            raise ValueError("RESULT_PATH_UNSAFE")
        root_resolved = root.resolve(strict=False)
        path_resolved = path.resolve(strict=False)
        try:
            path_resolved.relative_to(root_resolved)
        except ValueError as error:
            raise ValueError("RESULT_PATH_OUT_OF_SCOPE") from error
        current = root
        relative_parts = path.relative_to(root).parts
        for part in relative_parts:
            current = current / part
            if current.exists() and cls._is_link_or_reparse(current):
                raise ValueError("RESULT_PATH_UNSAFE")

    @staticmethod
    def _artifact_run_id(logical_artifact_id: str) -> str | None:
        for prefix in ("RESULT-OWNER-", "RESULT-"):
            if logical_artifact_id.startswith(prefix):
                run_id = logical_artifact_id[len(prefix) :]
                if run_id and is_safe_id(run_id):
                    return run_id
        return None

    @staticmethod
    def _stat_signature(path: Path) -> tuple[int, int, int, int, int, int]:
        file_stat = path.lstat()
        return (
            int(file_stat.st_mode),
            int(file_stat.st_size),
            int(file_stat.st_mtime_ns),
            int(file_stat.st_ino),
            int(file_stat.st_dev),
            int(getattr(file_stat, "st_file_attributes", 0)),
        )

    def _tree_snapshot(self, target: Path) -> dict[str, tuple[int, int, int, int, int, int]]:
        self._assert_path_chain_safe(target, self.results_root)
        if not target.exists():
            raise ValueError("RESULT_ARTIFACT_NOT_FOUND")
        if self._is_link_or_reparse(target) or not target.is_dir():
            raise ValueError("PATH_SAFETY_REJECTED")
        snapshot: dict[str, tuple[int, int, int, int, int, int]] = {}
        pending = [target]
        while pending:
            current = pending.pop()
            if self._is_link_or_reparse(current):
                raise ValueError("PATH_SAFETY_REJECTED")
            try:
                signature = self._stat_signature(current)
            except OSError as error:
                raise ValueError("PATH_SAFETY_REJECTED") from error
            relative = current.relative_to(self.results_root).as_posix()
            snapshot[relative] = signature
            if stat.S_ISDIR(signature[0]):
                try:
                    with os.scandir(current) as entries:
                        pending.extend(Path(entry.path) for entry in entries)
                except OSError as error:
                    raise ValueError("PATH_SAFETY_REJECTED") from error
            elif not stat.S_ISREG(signature[0]):
                raise ValueError("PATH_SAFETY_REJECTED")
        return snapshot

    def _persist_delete_audit(self, audit: Mapping[str, object]) -> None:
        audit_id = audit.get("audit_id")
        if not isinstance(audit_id, str) or not is_safe_id(audit_id):
            raise ValueError("AUDIT_ID_INVALID")
        self._assert_path_chain_safe(self.audit_root, self.root)
        target = self.audit_root / f"{audit_id}.json"
        if self._is_link_or_reparse(target):
            raise ValueError("RESULT_PATH_UNSAFE")
        temporary = self.audit_root / f".{audit_id}.{uuid.uuid4().hex}.tmp"
        payload = json.dumps(dict(audit), ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
        try:
            with temporary.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    def _load_delete_audits(self) -> None:
        if not self.audit_root.exists():
            return
        for path in sorted(self.audit_root.glob("AUDIT-RESULT-DELETE-*.json")):
            if self._is_link_or_reparse(path) or not path.is_file():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict) or not isinstance(payload.get("audit_id"), str):
                continue
            audit_id = str(payload["audit_id"])
            self._delete_audits[audit_id] = dict(payload)
            try:
                self._delete_sequence = max(self._delete_sequence, int(audit_id.rsplit("-", 1)[-1]))
            except ValueError:
                pass
            if payload.get("event_type") == "RESULT_DELETED":
                aggregate_id = payload.get("aggregate_id")
                if isinstance(aggregate_id, str):
                    self._delete_tombstones[aggregate_id] = dict(payload)

    def _next_delete_audit(
        self,
        *,
        request_id: str,
        operation_token: str,
        logical_artifact_id: str,
        artifact_kind: str,
        error_code: str,
        reason: str,
        event_type: str = "RESULT_DELETE_REJECTED",
        artifact_state: str = "PRESENT",
        physical_io_performed: bool = False,
    ) -> tuple[str, dict[str, object]]:
        self._delete_sequence += 1
        audit_id = f"AUDIT-RESULT-DELETE-{self._delete_sequence:06d}"
        audit = {
            "audit_id": audit_id,
            "aggregate_kind": "RESULT_ARTIFACT",
            "aggregate_id": logical_artifact_id,
            "event_type": event_type,
            "request_id": request_id,
            "operation_token": operation_token,
            "artifact_kind": artifact_kind,
            "error_code": error_code,
            "reason": reason,
            "artifact_state": artifact_state,
            "physical_io_performed": physical_io_performed,
        }
        self._delete_audits[audit_id] = dict(audit)
        self._persist_delete_audit(audit)
        return audit_id, audit

    def _update_delete_audit(self, audit_id: str, **updates: object) -> dict[str, object]:
        current = dict(self._delete_audits[audit_id])
        current.update(updates)
        self._delete_audits[audit_id] = current
        self._persist_delete_audit(current)
        return current

    @staticmethod
    def _delete_text(value: object, default: str = "") -> str:
        return value.strip() if isinstance(value, str) else default

    def _delete_rejection(
        self,
        *,
        request_id: str,
        operation_token: str,
        logical_artifact_id: str,
        artifact_kind: str,
        error_code: str,
        reason: str,
        artifact_state: str = "PRESENT",
        replayed: bool = False,
    ) -> dict[str, object]:
        audit_id, audit = self._next_delete_audit(
            request_id=request_id,
            operation_token=operation_token,
            logical_artifact_id=logical_artifact_id,
            artifact_kind=artifact_kind,
            error_code=error_code,
            reason=reason,
        )
        return {
            "logical_artifact_id": logical_artifact_id,
            "artifact_kind": artifact_kind,
            "accepted": False,
            "deleted": False,
            "status": "REJECTED",
            "artifact_state": artifact_state,
            "error_code": error_code,
            "reason": reason,
            "request_id": request_id,
            "operation_token": operation_token,
            "audit_id": audit_id,
            "audit": dict(audit),
            "physical_io_performed": False,
            "replayed": replayed,
        }

    def delete_result_artifact(self, request: Mapping[str, object] | object) -> dict[str, object]:
        """Delete one approved terminal ResultArtifact without cascading."""

        if not isinstance(request, Mapping):
            with self._delete_lock:
                return self._delete_rejection(
                    request_id="UNKNOWN",
                    operation_token="UNKNOWN",
                    logical_artifact_id="UNKNOWN",
                    artifact_kind="UNKNOWN",
                    error_code="INVALID_REQUEST",
                    reason="削除要求の形式が不正です。",
                )

        logical_artifact_id = self._delete_text(request.get("logical_artifact_id"))
        artifact_kind = self._delete_text(request.get("artifact_kind"), "UNKNOWN").upper()
        operation_token = self._delete_text(request.get("operation_token"))
        request_id = self._delete_text(request.get("request_id"), operation_token)
        run_state = self._delete_text(request.get("run_state", request.get("current_state"))).upper()
        path_kind = self._delete_text(request.get("path_kind"), "NORMAL").upper()
        reason = self._delete_text(request.get("reason"), "operator requested result display removal")

        with self._delete_lock:
            if operation_token and logical_artifact_id:
                cached = self._delete_cache.get((logical_artifact_id, operation_token))
                if cached is not None:
                    replay = dict(cached)
                    replay["request_id"] = request_id
                    replay["replayed"] = True
                    return replay

            if not logical_artifact_id or not operation_token or not request_id:
                result = self._delete_rejection(
                    request_id=request_id or "UNKNOWN",
                    operation_token=operation_token or "UNKNOWN",
                    logical_artifact_id=logical_artifact_id or "UNKNOWN",
                    artifact_kind=artifact_kind,
                    error_code="INVALID_REQUEST",
                    reason="logical_artifact_id、operation_token、request_idは必須です。",
                )
            elif any(key in request for key in ("path", "absolute_path", "relative_path", "target_path")):
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="PATH_SAFETY_REJECTED",
                    reason="削除要求に呼出元指定のpathを含めることはできません。",
                )
            elif not is_safe_id(logical_artifact_id) or path_kind in _UNSAFE_PATH_KINDS:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="PATH_SAFETY_REJECTED",
                    reason="論理Artifact ID又はpath安全検査に失敗しました。",
                )
            elif path_kind == "ID_MISMATCH":
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="ARTIFACT_ID_MISMATCH",
                    reason="解決したArtifactの論理IDが要求対象と一致しません。",
                )
            elif "allowed_root" in request and not self._is_allowed_root(request.get("allowed_root")):
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="PATH_SAFETY_REJECTED",
                    reason="許可rootがResult Artifact rootと一致しません。",
                )
            elif request.get("_server_run_missing") is True:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="RUN_NOT_FOUND",
                    reason="サーバーが管理する対象Runを解決できないため、削除を拒否しました。",
                )
            elif artifact_kind in _PROTECTED_ARTIFACT_KINDS:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="PROTECTED_ARTIFACT",
                    reason="CSV、Historical Data、Run、Audit、Evidenceは保護対象です。",
                )
            elif run_state in _ACTIVE_RUN_STATES:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="ACTIVE_RUN",
                    reason="実行中又は回復確認中のRunに紐づくArtifactは削除できません。",
                )
            elif artifact_kind != "RESULT":
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="UNSUPPORTED_ARTIFACT_KIND",
                    reason="物理削除できるArtifact種別はterminal Resultだけです。",
                )
            elif run_state not in _TERMINAL_RESULT_STATES:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="TERMINAL_STATE_REQUIRED",
                    reason="terminal状態のResultArtifactだけを削除できます。",
                )
            elif request.get("confirmation") is not True:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="CONFIRMATION_REQUIRED",
                    reason="明示的な確認が必要です。",
                )
            elif not self._physical_delete_enabled:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="DELETE_GATE_REQUIRED",
                    reason="DELETE-G1未承認のため物理削除は実行できません。",
                )
            elif request.get("physical_io_allowed") is not True:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="PHYSICAL_IO_NOT_ALLOWED",
                    reason="物理削除を実行する明示的なlocal受入許可がありません。",
                )
            else:
                run_id = self._artifact_run_id(logical_artifact_id)
                if run_id is None:
                    result = self._delete_rejection(
                        request_id=request_id,
                        operation_token=operation_token,
                        logical_artifact_id=logical_artifact_id,
                        artifact_kind=artifact_kind,
                        error_code="ARTIFACT_ID_MISMATCH",
                        reason="ResultArtifactのlogical IDから安全なRunを解決できません。",
                    )
                elif logical_artifact_id in self._delete_tombstones:
                    tombstone = self._delete_tombstones[logical_artifact_id]
                    result = {
                        "logical_artifact_id": logical_artifact_id,
                        "artifact_kind": artifact_kind,
                        "accepted": True,
                        "deleted": False,
                        "status": "RESULT_DELETED",
                        "artifact_state": "DELETED",
                        "error_code": None,
                        "reason": "ResultArtifactは既に削除済みです。",
                        "request_id": request_id,
                        "operation_token": operation_token,
                        "audit_id": tombstone["audit_id"],
                        "audit": dict(tombstone),
                        "physical_io_performed": False,
                        "replayed": True,
                    }
                else:
                    target = self.results_root / run_id
                    try:
                        snapshot = self._tree_snapshot(target)
                    except ValueError as error:
                        code = str(error)
                        if code not in {"RESULT_ARTIFACT_NOT_FOUND", "PATH_SAFETY_REJECTED"}:
                            code = "PATH_SAFETY_REJECTED"
                        result = self._delete_rejection(
                            request_id=request_id,
                            operation_token=operation_token,
                            logical_artifact_id=logical_artifact_id,
                            artifact_kind=artifact_kind,
                            error_code=code,
                            reason="ResultArtifactの物理対象を安全に解決できません。",
                        )
                    else:
                        audit_id, pending = self._next_delete_audit(
                            request_id=request_id,
                            operation_token=operation_token,
                            logical_artifact_id=logical_artifact_id,
                            artifact_kind=artifact_kind,
                            error_code="DELETE_PENDING",
                            reason="安全検査を通過し、ResultArtifactだけの削除を開始します。",
                            event_type="RESULT_DELETE_PENDING",
                            artifact_state="DELETE_PENDING",
                        )
                        physical_io_performed = False
                        try:
                            current = self._tree_snapshot(target)
                            if not self._snapshots_match(snapshot, current):
                                raise ValueError("TOCTOU_DETECTED")
                            for relative in sorted(snapshot, key=lambda value: len(Path(value).parts), reverse=True):
                                path = self.results_root / Path(relative)
                                if self._is_link_or_reparse(path) or not path.exists():
                                    raise ValueError("TOCTOU_DETECTED")
                                current_signature = self._stat_signature(path)
                                if not self._signatures_match(snapshot[relative], current_signature):
                                    raise ValueError("TOCTOU_DETECTED")
                                if stat.S_ISDIR(current_signature[0]):
                                    path.rmdir()
                                else:
                                    path.unlink()
                                physical_io_performed = True
                            if target.exists():
                                raise ValueError("DELETE_INCOMPLETE")
                        except (OSError, ValueError) as error:
                            error_code = str(error) if isinstance(error, ValueError) else "DELETE_FAILED"
                            if error_code not in {"TOCTOU_DETECTED", "DELETE_INCOMPLETE"}:
                                error_code = "DELETE_FAILED"
                            failed_audit = self._update_delete_audit(
                                audit_id,
                                event_type="RESULT_DELETE_FAILED",
                                status="DELETE_FAILED",
                                artifact_state="PARTIAL" if physical_io_performed else "PRESENT",
                                error_code=error_code,
                                reason="物理削除に失敗したためcascadeを行わず停止しました。",
                                physical_io_performed=physical_io_performed,
                            )
                            result = {
                                "logical_artifact_id": logical_artifact_id,
                                "artifact_kind": artifact_kind,
                                "accepted": False,
                                "deleted": False,
                                "status": "DELETE_FAILED",
                                "artifact_state": "PARTIAL" if physical_io_performed else "PRESENT",
                                "error_code": error_code,
                                "reason": "物理削除に失敗したためcascadeを行わず停止しました。",
                                "request_id": request_id,
                                "operation_token": operation_token,
                                "audit_id": audit_id,
                                "audit": dict(failed_audit),
                                "physical_io_performed": physical_io_performed,
                                "replayed": False,
                            }
                        else:
                            deleted_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
                            deleted_audit = self._update_delete_audit(
                                audit_id,
                                event_type="RESULT_DELETED",
                                status="RESULT_DELETED",
                                artifact_state="DELETED",
                                error_code=None,
                                reason="terminal ResultArtifactだけを物理削除しました。",
                                physical_io_performed=True,
                                deleted_at=deleted_at,
                                run_id=run_id,
                            )
                            self._delete_tombstones[logical_artifact_id] = dict(deleted_audit)
                            result = {
                                "logical_artifact_id": logical_artifact_id,
                                "artifact_kind": artifact_kind,
                                "accepted": True,
                                "deleted": True,
                                "status": "RESULT_DELETED",
                                "artifact_state": "DELETED",
                                "error_code": None,
                                "reason": "terminal ResultArtifactだけを物理削除しました。",
                                "request_id": request_id,
                                "operation_token": operation_token,
                                "audit_id": audit_id,
                                "audit": dict(deleted_audit),
                                "physical_io_performed": True,
                                "replayed": False,
                            }

            result["request_reason"] = reason
            if operation_token and logical_artifact_id:
                self._delete_cache[(logical_artifact_id, operation_token)] = dict(result)
            return result

    @classmethod
    def _signatures_match(
        cls,
        expected: tuple[int, int, int, int, int, int],
        actual: tuple[int, int, int, int, int, int],
    ) -> bool:
        if stat.S_ISDIR(expected[0]) or stat.S_ISDIR(actual[0]):
            return (
                stat.S_ISDIR(expected[0])
                and stat.S_ISDIR(actual[0])
                and expected[3:] == actual[3:]
            )
        return expected == actual

    @classmethod
    def _snapshots_match(
        cls,
        expected: Mapping[str, tuple[int, int, int, int, int, int]],
        actual: Mapping[str, tuple[int, int, int, int, int, int]],
    ) -> bool:
        if expected.keys() != actual.keys():
            return False
        return all(cls._signatures_match(expected[key], actual[key]) for key in expected)

    def _is_allowed_root(self, candidate: object) -> bool:
        if not isinstance(candidate, str):
            return False
        try:
            supplied = Path(candidate)
            return supplied.is_absolute() and supplied.resolve() == self.root
        except (OSError, RuntimeError, ValueError):
            return False

    def delete_audit_log(self) -> tuple[dict[str, object], ...]:
        with self._delete_lock:
            return tuple(dict(item) for item in self._delete_audits.values())

    def publish(self, run_id: str, output: Any, manifest_sha256: str | None = None) -> ResultReference:
        if (
            not isinstance(run_id, str)
            or not is_safe_id(run_id)
            or not hasattr(output, "metrics")
            or not hasattr(output, "rows")
        ):
            raise ValueError("RESULT_OUTPUT_INVALID")
        relative_root = f"results/{run_id}"
        directory = self._directory(relative_root, create=False)
        payload = canonical_json(
            {
                "metric_definition_version": "P4-METRICS-V1",
                "metrics": asdict(output.metrics),
                "rows": [dict(row) for row in output.rows],
            }
        ).encode("utf-8")
        del manifest_sha256
        marker_payload = canonical_json(
            {"run_id": run_id, "status": "COMMITTED", "version": "P4-RESULT-MARKER-V2"}
        ).encode("utf-8")
        parent = directory.parent
        parent.mkdir(parents=True, exist_ok=True)
        temporary = parent / f".{directory.name}.{uuid.uuid4().hex}.tmp"
        if directory.exists() or temporary.exists():
            raise FileExistsError("RESULT_OVERWRITE_FORBIDDEN")
        try:
            temporary.mkdir()
            self._atomic_write(temporary / "result.json", payload)
            self._atomic_write(temporary / "result.commit.json", marker_payload)
            if directory.exists():
                raise FileExistsError("RESULT_OVERWRITE_FORBIDDEN")
            os.replace(temporary, directory)
        except Exception:
            if temporary.exists():
                shutil.rmtree(temporary, ignore_errors=True)
            raise
        return ResultReference(run_id, relative_root)

    def read(self, reference: ResultReference) -> dict[str, Any]:
        validate_result_reference(reference)
        directory = self._directory(reference.relative_root, create=False)
        result_path = directory / "result.json"
        marker_path = directory / "result.commit.json"
        if not result_path.is_file() or not marker_path.is_file():
            raise ValueError("RESULT_ARTIFACT_MISSING")
        payload = result_path.read_bytes()
        marker_payload = marker_path.read_bytes()
        try:
            marker = json.loads(marker_payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("RESULT_MARKER_MISMATCH") from error
        if marker.get("run_id") != reference.run_id or marker.get("status") != "COMMITTED":
            raise ValueError("RESULT_MARKER_MISMATCH")
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("RESULT_ARTIFACT_INVALID") from error
        if not isinstance(decoded, dict) or not isinstance(decoded.get("metrics"), dict):
            raise ValueError("RESULT_ARTIFACT_INVALID")
        rows = decoded.get("rows")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("RESULT_ARTIFACT_INVALID")
        return decoded

    def _directory(self, relative_root: str, *, create: bool) -> Path:
        relative = Path(relative_root)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not relative_root
            or relative_root.startswith(("\\\\", "//"))
        ):
            raise ValueError("RESULT_PATH_INVALID")
        target = (self.root / relative_root).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as error:
            raise ValueError("RESULT_PATH_INVALID") from error
        if create:
            target.mkdir(parents=True, exist_ok=True)
        return target

    @staticmethod
    def _atomic_write(target: Path, payload: bytes) -> None:
        if target.exists():
            raise FileExistsError("RESULT_OVERWRITE_FORBIDDEN")
        temporary = target.with_name(f".{target.name}.tmp")
        if temporary.exists():
            raise FileExistsError("RESULT_STALE_TEMPORARY")
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


def validate_result_reference(reference: ResultReference) -> None:
    if (
        not reference.relative_root
        or reference.relative_root.startswith(("/", "\\", "//"))
        or ".." in reference.relative_root.split("/")
        or "\\" in reference.relative_root
    ):
        raise ValueError("RESULT_PATH_INVALID")
