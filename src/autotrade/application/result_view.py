"""Read-only result reference and metric view contracts."""

from __future__ import annotations

import json
import os
import shutil
import threading
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass
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

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._delete_lock = threading.RLock()
        self._delete_sequence = 0
        self._delete_cache: dict[tuple[str, str], dict[str, object]] = {}
        self._delete_audits: dict[str, dict[str, object]] = {}

    def _next_delete_audit(
        self,
        *,
        request_id: str,
        operation_token: str,
        logical_artifact_id: str,
        artifact_kind: str,
        error_code: str,
        reason: str,
    ) -> tuple[str, dict[str, object]]:
        self._delete_sequence += 1
        audit_id = f"AUDIT-RESULT-DELETE-{self._delete_sequence:06d}"
        audit = {
            "audit_id": audit_id,
            "aggregate_kind": "RESULT_ARTIFACT",
            "aggregate_id": logical_artifact_id,
            "event_type": "RESULT_DELETE_REJECTED",
            "request_id": request_id,
            "operation_token": operation_token,
            "artifact_kind": artifact_kind,
            "error_code": error_code,
            "reason": reason,
            "physical_io_performed": False,
        }
        self._delete_audits[audit_id] = dict(audit)
        return audit_id, audit

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
        """Reject ResultArtifact deletion until DELETE-G1 is approved.

        The request accepts only a logical artifact identifier.  It never
        accepts a caller-supplied path and deliberately contains no unlink or
        tombstone branch.  P5R2-15 proves the guard and negative cases; the
        physical deletion workflow is a later, separately gated change.
        """

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
            elif request.get("confirmation") is not True:
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="CONFIRMATION_REQUIRED",
                    reason="明示的な確認が必要です。",
                )
            else:
                # DELETE-G1 is intentionally a hard boundary in this step.
                # Even physical_io_allowed=True cannot bypass the gate.
                result = self._delete_rejection(
                    request_id=request_id,
                    operation_token=operation_token,
                    logical_artifact_id=logical_artifact_id,
                    artifact_kind=artifact_kind,
                    error_code="DELETE_GATE_REQUIRED",
                    reason="DELETE-G1未承認のため物理削除は実行できません。",
                )

            result["request_reason"] = reason
            if operation_token and logical_artifact_id:
                self._delete_cache[(logical_artifact_id, operation_token)] = dict(result)
            return result

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
