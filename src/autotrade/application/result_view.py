"""Read-only result reference and metric view contracts."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contracts import ResultReference, canonical_json, is_safe_id


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
