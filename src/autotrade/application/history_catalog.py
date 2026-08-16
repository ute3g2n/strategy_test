"""Durable, restart-safe storage for local Backtest history.

The catalog deliberately uses ordinary JSON files under the application-owned
runtime root and does not fall back to C: or the Windows temporary directory.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

CATALOG_SCHEMA = "autotrade-backtest-history/v1"
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class HistoryCatalog:
    """Read and atomically write Backtest history records and result artifacts."""

    def __init__(self, runtime_root: Path) -> None:
        self.runtime_root = Path(runtime_root)
        self.catalog_root = self.runtime_root / "catalog"
        self.runs_root = self.catalog_root / "runs"
        self.results_root = self.runtime_root / "results"
        self.runs_root.mkdir(parents=True, exist_ok=True)

    def persist_run(self, view: JsonObject) -> None:
        run_id = self._safe_run_id(view.get("run_id"))
        record = dict(view)
        record["schema"] = CATALOG_SCHEMA
        record["run_id"] = run_id
        self._write_json_atomic(self.runs_root / f"{run_id}.json", record)

    def write_result(self, run_id: str, payload: JsonObject) -> None:
        safe_run_id = self._safe_run_id(run_id)
        result_path = self.results_root / safe_run_id / "result.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_json_atomic(result_path, payload)

    def restore(self) -> tuple[list[JsonObject], list[JsonObject]]:
        """Return recoverable run records and isolated recovery issues.

        One invalid file never aborts the scan.  A terminal catalog record is
        only treated as successful when its referenced result is present and
        its run_id agrees with the catalog.
        """

        restored: list[JsonObject] = []
        issues: list[JsonObject] = []
        catalog_ids: set[str] = set()
        for path in sorted(self.runs_root.glob("*.json")):
            record = self._read_json(path)
            if record is None:
                issues.append(self._issue("CATALOG_JSON_INVALID", path.stem, path))
                continue
            run_id = record.get("run_id")
            if not isinstance(run_id, str) or not _RUN_ID_PATTERN.fullmatch(run_id) or path.stem != run_id:
                issues.append(self._issue("CATALOG_RUN_ID_INVALID", str(run_id or path.stem), path))
                continue
            catalog_ids.add(run_id)
            if record.get("schema") not in {None, CATALOG_SCHEMA}:
                issues.append(self._issue("CATALOG_SCHEMA_UNSUPPORTED", run_id, path))
                continue
            status = str(record.get("status", "UNKNOWN"))
            if status in {"QUEUED", "RUNNING", "CANCELLED"}:
                restored.append(
                    self._recovery_required_record(
                        record,
                        run_id,
                        "INCOMPLETE_AFTER_RESTART",
                        "アプリ終了前に完了していないため、結果を成功扱いにできません。",
                    )
                )
                issues.append(self._issue("INCOMPLETE_AFTER_RESTART", run_id, path))
                continue
            if status == "SUCCEEDED":
                result, result_issue = self._read_referenced_result(record, run_id, path)
                if result_issue is not None:
                    restored.append(
                        self._recovery_required_record(
                            record,
                            run_id,
                            result_issue["code"],
                            result_issue["message"],
                        )
                    )
                    issues.append(result_issue)
                    continue
                restored.append(self._merge_result(record, result or {}, recovery_mode="NORMAL"))
                continue
            if status in {"FAILED", "PARTIAL_FAILED", "RECOVERY_REQUIRED"}:
                restored.append(dict(record))
                continue
            restored.append(
                self._recovery_required_record(
                    record,
                    run_id,
                    "CATALOG_STATUS_INVALID",
                    "履歴の状態が認識できないため、復旧確認が必要です。",
                )
            )
            issues.append(self._issue("CATALOG_STATUS_INVALID", run_id, path))

        for result_path in sorted(self.results_root.glob("*/result.json")):
            folder_run_id = result_path.parent.name
            if folder_run_id in catalog_ids:
                continue
            result = self._read_json(result_path)
            if result is None:
                issues.append(self._issue("RESULT_JSON_INVALID", folder_run_id, result_path))
                continue
            result_run_id = result.get("run_id")
            if not isinstance(result_run_id, str) or result_run_id != folder_run_id or not _RUN_ID_PATTERN.fullmatch(
                result_run_id
            ):
                issues.append(self._issue("RESULT_RUN_ID_MISMATCH", folder_run_id, result_path))
                continue
            if not self._result_payload_is_usable(result):
                issues.append(self._issue("RESULT_JSON_INVALID", folder_run_id, result_path))
                continue
            restored.append(
                self._legacy_record(
                    result_run_id,
                    result,
                    f"results/{result_run_id}/result.json",
                )
            )
        return restored, issues

    def _read_referenced_result(
        self, record: JsonObject, run_id: str, catalog_path: Path
    ) -> tuple[JsonObject | None, JsonObject | None]:
        reference = record.get("result_reference")
        if not isinstance(reference, str) or not reference:
            return None, self._issue("RESULT_REFERENCE_MISSING", run_id, catalog_path)
        try:
            result_path = self._safe_result_reference(reference, run_id)
        except ValueError as error:
            return None, self._issue(str(error), run_id, catalog_path)
        result = self._read_json(result_path)
        if result is None:
            return None, self._issue("RESULT_JSON_INVALID", run_id, result_path)
        if result.get("run_id") != run_id:
            return None, self._issue("RESULT_REFERENCE_MISMATCH", run_id, result_path)
        if not self._result_payload_is_usable(result):
            return None, self._issue("RESULT_JSON_INVALID", run_id, result_path)
        return result, None

    def _safe_result_reference(self, reference: str, run_id: str) -> Path:
        reference_path = Path(reference)
        if reference_path.is_absolute() or reference_path.parts != ("results", run_id, "result.json"):
            raise ValueError("RESULT_REFERENCE_OUT_OF_SCOPE")
        result_path = (self.runtime_root / reference_path).resolve()
        results_root = self.results_root.resolve()
        try:
            result_path.relative_to(results_root)
        except ValueError as error:
            raise ValueError("RESULT_REFERENCE_OUT_OF_SCOPE") from error
        if result_path.name != "result.json":
            raise ValueError("RESULT_REFERENCE_OUT_OF_SCOPE")
        return result_path

    @staticmethod
    def _result_payload_is_usable(payload: JsonObject) -> bool:
        return isinstance(payload.get("metrics"), dict) and isinstance(payload.get("rows"), list) and isinstance(
            payload.get("provenance"), dict
        )

    @staticmethod
    def _merge_result(record: JsonObject, result: JsonObject, *, recovery_mode: str) -> JsonObject:
        merged = dict(record)
        for key in ("metrics", "rows", "provenance"):
            merged[key] = result.get(key, merged.get(key))
        merged["recovery_mode"] = recovery_mode
        merged["result_reference"] = str(record.get("result_reference"))
        return merged

    @staticmethod
    def _legacy_record(run_id: str, result: JsonObject, reference: str) -> JsonObject:
        return {
            "schema": CATALOG_SCHEMA,
            "run_id": run_id,
            "kind": "SINGLE_BACKTEST",
            "parent_id": None,
            "status": "SUCCEEDED",
            "progress": len(result.get("rows", [])),
            "total": len(result.get("rows", [])),
            "started_at": None,
            "ended_at": None,
            "spec": {},
            "metrics": dict(result.get("metrics", {})),
            "provenance": dict(result.get("provenance", {})),
            "failure": None,
            "checkpoint": None,
            "resume_count": 0,
            "recovery_mode": "LEGACY_RESULT_ONLY",
            "result_reference": reference,
            "rows": list(result.get("rows", [])),
        }

    @staticmethod
    def _recovery_required_record(record: JsonObject, run_id: str, code: str, message: str) -> JsonObject:
        recovered = dict(record)
        recovered["run_id"] = run_id
        recovered["status"] = "RECOVERY_REQUIRED"
        recovered["recovery_mode"] = "RECOVERY_REQUIRED"
        recovered["failure"] = {"code": code, "message": message, "retryable": False}
        recovered.setdefault("spec", {})
        recovered.setdefault("metrics", None)
        recovered.setdefault("provenance", {})
        recovered.setdefault("rows", [])
        return recovered

    @staticmethod
    def _safe_run_id(value: object) -> str:
        if not isinstance(value, str) or _RUN_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("RUN_ID_INVALID")
        return value

    @staticmethod
    def _read_json(path: Path) -> JsonObject | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _issue(self, code: str, run_id: str, path: Path) -> JsonObject:
        try:
            display_path = path.resolve().relative_to(self.runtime_root.resolve()).as_posix()
        except ValueError:
            display_path = path.name
        return {"code": code, "run_id": run_id, "path": display_path, "message": code}

    @staticmethod
    def _write_json_atomic(path: Path, payload: JsonObject) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        writing_path = path.with_name(f".{path.name}.writing")
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        with writing_path.open("wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(writing_path, path)
