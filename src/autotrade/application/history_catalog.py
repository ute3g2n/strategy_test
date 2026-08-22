"""Durable, restart-safe storage for local Backtest history.

The catalog deliberately uses ordinary JSON files under the application-owned
runtime root and does not fall back to C: or the Windows temporary directory.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

CATALOG_SCHEMA = "autotrade-backtest-history/v1"
DATASET_SCHEMA = "autotrade-historical-dataset/v1"
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_CATALOG_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_DATA_IDENTITY_FIELDS = ("provider", "market", "symbol", "source_timeframe", "schema")


class HistoryCatalog:
    """Read and atomically write Backtest history records and result artifacts."""

    def __init__(self, runtime_root: Path) -> None:
        self.runtime_root = Path(runtime_root)
        self.catalog_root = self.runtime_root / "catalog"
        self.runs_root = self.catalog_root / "runs"
        self.results_root = self.runtime_root / "results"
        self.datasets_root = self.catalog_root / "datasets"
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

    def preview_merge(self, request: Mapping[str, object]) -> JsonObject:
        """Build a user-reviewable merge result without changing the catalog."""

        try:
            identity = self._identity_payload(request.get("identity"))
            self._assert_identity_compatibility(request, identity)
            existing_bars = self._normalise_bars(request.get("existing_bars"))
            incoming_bars = self._normalise_bars(request.get("incoming_bars"))
        except ValueError as error:
            return {
                "state": "REJECTED",
                "reason": str(error),
                "identity": request.get("identity"),
                "promotable": False,
                "promoted": False,
                "dedupe_count": 0,
                "conflict_count": 0,
                "affected_runs": self._reference_list(request.get("affected_runs")),
                "affected_results": self._reference_list(request.get("affected_results")),
                "requires_explicit_replace": False,
            }

        explicit_replace = request.get("explicit_replace") is True
        existing_by_timestamp = {str(bar["timestamp"]): bar for bar in existing_bars}
        merged_by_timestamp = dict(existing_by_timestamp)
        seen_incoming: dict[str, JsonObject] = {}
        dedupe_count = 0
        conflict_count = 0
        conflicts: list[JsonObject] = []
        additional_count = 0

        for bar in incoming_bars:
            timestamp = str(bar["timestamp"])
            prior_incoming = seen_incoming.get(timestamp)
            if prior_incoming is not None:
                if self._bar_signature(prior_incoming) == self._bar_signature(bar):
                    dedupe_count += 1
                    continue
                conflict_count += 1
                conflicts.append({"timestamp": timestamp, "existing": prior_incoming, "incoming": bar})
                if explicit_replace:
                    seen_incoming[timestamp] = bar
                    merged_by_timestamp[timestamp] = bar
                continue
            seen_incoming[timestamp] = bar

            existing = existing_by_timestamp.get(timestamp)
            if existing is None:
                additional_count += 1
                merged_by_timestamp[timestamp] = bar
                continue
            if self._bar_signature(existing) == self._bar_signature(bar):
                dedupe_count += 1
                continue
            conflict_count += 1
            conflicts.append({"timestamp": timestamp, "existing": existing, "incoming": bar})
            if explicit_replace:
                merged_by_timestamp[timestamp] = bar

        merged_bars = [merged_by_timestamp[key] for key in sorted(merged_by_timestamp)]
        affected_runs = self._reference_list(request.get("affected_runs"))
        affected_results = self._reference_list(request.get("affected_results"))
        requires_explicit_replace = conflict_count > 0 and not explicit_replace
        state = "CONFLICT" if requires_explicit_replace else "PREVIEW_READY"
        return {
            "state": state,
            "reason": "DATA_CONFLICT" if requires_explicit_replace else None,
            "identity": identity,
            "existing_coverage": self._coverage(existing_bars),
            "incoming_coverage": self._coverage(incoming_bars),
            "merged_coverage": self._coverage(merged_bars),
            "existing_bar_count": len(existing_bars),
            "incoming_bar_count": len(incoming_bars),
            "merged_bar_count": len(merged_bars),
            "additional_count": additional_count,
            "dedupe_count": dedupe_count,
            "conflict_count": conflict_count,
            "conflicts": conflicts,
            "affected_runs": affected_runs,
            "affected_results": affected_results,
            "affected_artifacts": list(affected_results),
            "explicit_replace": explicit_replace,
            "requires_explicit_replace": requires_explicit_replace,
            "promotable": not requires_explicit_replace,
            "promoted": False,
            "merged_bars": merged_bars,
        }

    def promote_merge(self, request: Mapping[str, object]) -> JsonObject:
        """Atomically promote a reviewed local merge while preserving protected records."""

        preview = self.preview_merge(request)
        if preview.get("promotable") is not True:
            preview["promoted"] = False
            return preview

        raw_dataset_id = request.get("dataset_id")
        dataset_id = raw_dataset_id if isinstance(raw_dataset_id, str) and raw_dataset_id else None
        if dataset_id is None:
            request_id = request.get("request_id")
            dataset_id = (
                f"DATASET-MERGED-{request_id}" if isinstance(request_id, str) and request_id else "DATASET-MERGED-LOCAL"
            )
        if _CATALOG_ID_PATTERN.fullmatch(dataset_id) is None:
            preview.update({"state": "REJECTED", "reason": "DATASET_ID_INVALID", "promoted": False})
            return preview

        identity = preview["identity"]
        assert isinstance(identity, dict)
        output: JsonObject = {
            "schema": DATASET_SCHEMA,
            "dataset_id": dataset_id,
            "identity": identity,
            "coverage": preview["merged_coverage"],
            "bar_count": preview["merged_bar_count"],
            "bars": preview["merged_bars"],
            "quality": "USABLE",
            "usable": True,
            "legacy": request.get("legacy") is True,
            "state": "CURRENT",
            "promotion_state": "PROMOTED",
            "provenance": {
                "request_id": request.get("request_id"),
                "source_job_ids": self._reference_list(request.get("source_job_ids")),
                "merge_mode": "REPLACE" if request.get("explicit_replace") is True else "MERGE",
            },
        }
        self._write_json_atomic(self.datasets_root / f"{dataset_id}.json", output)
        promoted = dict(preview)
        promoted.update(
            {
                "state": "PROMOTED",
                "reason": "DATASET_PROMOTED",
                "dataset_id": dataset_id,
                "output": output,
                "promoted": True,
            }
        )
        return promoted

    def list_available_datasets(self) -> list[JsonObject]:
        """Return the user-facing list of currently usable local datasets."""

        return [view for view in self._list_dataset_views() if view.get("usable") is True]

    def list_datasets(self) -> list[JsonObject]:
        """Return all catalog entries, including entries that need recovery."""

        return self._list_dataset_views()

    def catalog_snapshot(self) -> list[JsonObject]:
        return self.list_datasets()

    def _list_dataset_views(self) -> list[JsonObject]:
        views: list[JsonObject] = []
        for path in sorted(self.datasets_root.glob("*.json")):
            record = self._read_json(path)
            if record is None:
                continue
            identity = record.get("identity")
            identity_map = identity if isinstance(identity, dict) else {}
            coverage = record.get("coverage")
            views.append(
                {
                    "dataset_id": record.get("dataset_id", path.stem),
                    "symbol": identity_map.get("symbol"),
                    "source_timeframe": identity_map.get("source_timeframe"),
                    "data_timeframe": identity_map.get("data_timeframe") or identity_map.get("source_timeframe"),
                    "timeframe": identity_map.get("data_timeframe") or identity_map.get("source_timeframe"),
                    "period": coverage,
                    "coverage": coverage,
                    "quality": record.get("quality"),
                    "usable": record.get("usable") is True,
                    "legacy": record.get("legacy") is True,
                    "provenance": record.get("provenance") if isinstance(record.get("provenance"), dict) else {},
                    "state": record.get("state"),
                    "promotion_state": record.get("promotion_state"),
                }
            )
        return views

    @staticmethod
    def _identity_payload(value: object) -> JsonObject:
        if not isinstance(value, Mapping):
            raise ValueError("DATA_IDENTITY_INVALID")
        identity = {key: value.get(key) for key in _DATA_IDENTITY_FIELDS}
        if any(not isinstance(identity[key], str) or not identity[key] for key in _DATA_IDENTITY_FIELDS):
            raise ValueError("DATA_IDENTITY_INVALID")
        if "data_timeframe" in value:
            data_timeframe = value.get("data_timeframe")
            if not isinstance(data_timeframe, str) or not data_timeframe:
                raise ValueError("DATA_IDENTITY_INVALID")
            identity["data_timeframe"] = data_timeframe
        return identity

    @classmethod
    def _identity_key(cls, value: object) -> tuple[str, ...]:
        identity = cls._identity_payload(value)
        return tuple(str(identity[key]) for key in _DATA_IDENTITY_FIELDS) + (str(identity.get("data_timeframe", "")),)

    @classmethod
    def _assert_identity_compatibility(cls, request: Mapping[str, object], identity: JsonObject) -> None:
        base_key = cls._identity_key(identity)
        for field in ("existing_identity", "incoming_identity"):
            candidate = request.get(field)
            if candidate is not None and cls._identity_key(candidate) != base_key:
                raise ValueError("DATA_IDENTITY_MISMATCH")

    @staticmethod
    def _normalise_bars(value: object) -> list[JsonObject]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("BARS_INVALID")
        bars: list[JsonObject] = []
        for bar in value:
            if not isinstance(bar, Mapping) or not isinstance(bar.get("timestamp"), str) or not bar.get("timestamp"):
                raise ValueError("BAR_TIMESTAMP_INVALID")
            bars.append(dict(bar))
        return bars

    @staticmethod
    def _bar_signature(bar: JsonObject) -> str:
        return json.dumps(bar, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _coverage(bars: list[JsonObject]) -> JsonObject | None:
        if not bars:
            return None
        timestamps = sorted(str(bar["timestamp"]) for bar in bars)
        return {"start": timestamps[0], "end": timestamps[-1]}

    @staticmethod
    def _reference_list(value: object) -> list[str]:
        if not isinstance(value, (list, tuple)):
            return []
        return [item for item in value if isinstance(item, str) and item]

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
            if (
                not isinstance(result_run_id, str)
                or result_run_id != folder_run_id
                or not _RUN_ID_PATTERN.fullmatch(result_run_id)
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
        return (
            isinstance(payload.get("metrics"), dict)
            and isinstance(payload.get("rows"), list)
            and isinstance(payload.get("provenance"), dict)
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
