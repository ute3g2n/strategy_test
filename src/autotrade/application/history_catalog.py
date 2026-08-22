"""Durable, restart-safe storage for local Backtest history.

The catalog deliberately uses ordinary JSON files under the application-owned
runtime root and does not fall back to C: or the Windows temporary directory.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

CATALOG_SCHEMA = "autotrade-backtest-history/v1"
DATASET_SCHEMA = "autotrade-historical-dataset/v1"
LEGACY_IMPORT_TICKET = "P5R-LEGACY-MIGRATION-V1"
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_CATALOG_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DATA_IDENTITY_FIELDS = ("provider", "market", "symbol", "source_timeframe", "schema")
_BAR_FIELDS = frozenset({"timestamp", "open", "high", "low", "close", "volume"})
_USABLE_QUALITIES = frozenset({"USABLE", "USABLE_WITH_WARNING"})
_MAX_BARS = 200_000
_PROVENANCE_FIELDS = frozenset(
    {"source_job_id", "source_job_ids", "source_mode", "catalog_revision", "request_id", "merge_mode", "origin"}
)


class HistoryCatalog:
    """Read and atomically write Backtest history records and result artifacts."""

    def __init__(self, runtime_root: Path) -> None:
        self.runtime_root = Path(runtime_root)
        self._ensure_directory_safe(self.runtime_root)
        self.catalog_root = self.runtime_root / "catalog"
        self.runs_root = self.catalog_root / "runs"
        self.results_root = self.runtime_root / "results"
        self.datasets_root = self.catalog_root / "datasets"
        self.versions_root = self.datasets_root / "versions"
        self._preview_lock = threading.RLock()
        self._preview_tokens: dict[str, JsonObject] = {}
        for directory in (self.catalog_root, self.runs_root, self.results_root, self.datasets_root, self.versions_root):
            self._ensure_directory_safe(directory)

    def persist_run(self, view: JsonObject) -> None:
        run_id = self._safe_run_id(view.get("run_id"))
        record = dict(view)
        record["schema"] = CATALOG_SCHEMA
        record["run_id"] = run_id
        self._write_json_atomic(self.runs_root / f"{run_id}.json", record)

    def write_result(self, run_id: str, payload: JsonObject) -> None:
        safe_run_id = self._safe_run_id(run_id)
        if payload.get("run_id") != safe_run_id:
            raise ValueError("RESULT_RUN_ID_MISMATCH")
        result_path = self.results_root / safe_run_id / "result.json"
        self._assert_path_chain_safe(result_path.parent, self.results_root)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        if result_path.exists():
            existing = self._read_json(result_path)
            if existing == payload:
                return
            raise ValueError("RESULT_ALREADY_PUBLISHED")
        self._write_json_atomic(result_path, payload)

    def preview_merge(self, request: Mapping[str, object]) -> JsonObject:
        """Build a user-reviewable merge result without changing the catalog."""

        return self._preview_merge(request, issue_token=True)

    def _preview_merge(self, request: Mapping[str, object], *, issue_token: bool) -> JsonObject:

        if not isinstance(request, Mapping):
            return self._merge_rejection("MERGE_REQUEST_INVALID", {})
        try:
            identity = self._identity_payload(request.get("identity"))
            self._assert_provider_boundary(identity)
            self._assert_identity_compatibility(request, identity)
            raw_provenance = request.get("provenance")
            provenance = self._safe_provenance(raw_provenance)
            self._assert_provenance_identity(provenance, identity)
            self._assert_staging_request(request)
            dataset_id = self._request_dataset_id(request)
            current_record = self._load_current_dataset(dataset_id) if dataset_id is not None else None
            if current_record is not None:
                current_identity = self._identity_payload(current_record.get("identity"))
                if self._identity_key(current_identity) != self._identity_key(identity):
                    raise ValueError("DATA_IDENTITY_MISMATCH")
                existing_bars = self._normalise_bars(current_record.get("bars"), allow_empty=True)
                current_revision = self._revision(current_record)
            else:
                existing_bars = self._normalise_bars(request.get("existing_bars"), allow_empty=True)
                current_revision = 0
            incoming_bars = self._normalise_bars(request.get("incoming_bars"))
            if dataset_id is not None:
                self._safe_catalog_id(dataset_id)
            request_id = request.get("request_id")
            if not isinstance(request_id, str) or self._safe_catalog_id(request_id) is None:
                raise ValueError("MERGE_REQUEST_ID_INVALID")
        except ValueError as error:
            return self._merge_rejection(str(error), request)

        explicit_replace = request.get("explicit_replace") is True
        try:
            existing_by_timestamp = self._index_bars(existing_bars)
        except ValueError as error:
            return self._merge_rejection(str(error), request)
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
        operation_token = uuid.uuid4().hex if issue_token else None
        preview = {
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
            "dataset_id": dataset_id,
            "current_revision": current_revision,
            "expected_revision": request.get("expected_revision", current_revision),
            "operation_token": operation_token,
            "provenance": provenance,
        }
        if issue_token and operation_token is not None:
            with self._preview_lock:
                self._preview_tokens[operation_token] = {
                    "binding": self._preview_binding(preview),
                    "dataset_id": dataset_id,
                    "revision": current_revision,
                }
        return preview

    def promote_merge(self, request: Mapping[str, object]) -> JsonObject:
        """Atomically promote a reviewed local merge while preserving protected records."""

        if not isinstance(request, Mapping):
            return self._merge_rejection("MERGE_REQUEST_INVALID", {})
        try:
            lock_dataset_id = self._promotion_dataset_id(request)
            with self._dataset_operation_lock(lock_dataset_id):
                preview = self._preview_merge(request, issue_token=False)
                if preview.get("state") == "REJECTED":
                    preview["promoted"] = False
                    return preview

                provided_token = request.get("preview_token")
                if request.get("impact_confirmed") is not True or not isinstance(provided_token, str):
                    preview.update({"state": "REJECTED", "reason": "MERGE_CONFIRMATION_REQUIRED", "promoted": False})
                    return preview
                with self._preview_lock:
                    token_record = self._preview_tokens.get(provided_token)
                if token_record is None or token_record.get("binding") != self._preview_binding(preview):
                    preview.update({"state": "REJECTED", "reason": "PREVIEW_TOKEN_MISMATCH", "promoted": False})
                    return preview
                if preview.get("promotable") is not True:
                    preview["promoted"] = False
                    return preview

                expected_revision = request.get("expected_revision")
                current_revision = preview.get("current_revision")
                if (
                    not isinstance(expected_revision, int)
                    or isinstance(expected_revision, bool)
                    or expected_revision < 0
                ):
                    preview.update({"state": "REJECTED", "reason": "DATASET_REVISION_INVALID", "promoted": False})
                    return preview
                if not isinstance(current_revision, int) or expected_revision != current_revision:
                    preview.update({"state": "REJECTED", "reason": "STALE_DATASET_REVISION", "promoted": False})
                    return preview

                raw_dataset_id = preview.get("dataset_id")
                dataset_id = raw_dataset_id if isinstance(raw_dataset_id, str) and raw_dataset_id else lock_dataset_id
                if self._safe_catalog_id(dataset_id) is None:
                    preview.update({"state": "REJECTED", "reason": "DATASET_ID_INVALID", "promoted": False})
                    return preview
                if request.get("legacy") is True:
                    preview.update({"state": "REJECTED", "reason": "LEGACY_DATASET_FORBIDDEN", "promoted": False})
                    return preview

                identity = preview["identity"]
                assert isinstance(identity, dict)
                new_revision = expected_revision + 1
                current_record = self._load_current_dataset(dataset_id)
                if current_record is not None:
                    version_path = self.versions_root / f"{dataset_id}.r{expected_revision}.json"
                    self._assert_path_chain_safe(version_path, self.versions_root)
                    if version_path.exists():
                        preview.update({"state": "REJECTED", "reason": "DATASET_VERSION_CONFLICT", "promoted": False})
                        return preview
                    self._write_json_atomic(version_path, current_record)
                request_provenance = preview.get("provenance")
                assert isinstance(request_provenance, Mapping)
                output: JsonObject = {
                    "schema": DATASET_SCHEMA,
                    "dataset_id": dataset_id,
                    "identity": identity,
                    "coverage": preview["merged_coverage"],
                    "bar_count": preview["merged_bar_count"],
                    "bars": preview["merged_bars"],
                    "quality": "USABLE",
                    "usable": True,
                    "legacy": False,
                    "state": "CURRENT",
                    "promotion_state": "PROMOTED",
                    "current_revision": new_revision,
                    "data_version": f"{dataset_id}.v{new_revision}",
                    "provenance": {
                        **dict(request_provenance),
                        "request_id": request.get("request_id"),
                        "source_job_ids": self._reference_list(request.get("source_job_ids")),
                        "merge_mode": "REPLACE" if request.get("explicit_replace") is True else "MERGE",
                    },
                }
                self._write_json_atomic(self._dataset_path(dataset_id), output)
                with self._preview_lock:
                    self._preview_tokens.pop(provided_token, None)
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
        except (OSError, ValueError) as error:
            return self._merge_rejection(
                "PROMOTION_RECOVERY_REQUIRED" if isinstance(error, OSError) else str(error), request
            )

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
            try:
                self._assert_path_chain_safe(path, self.datasets_root)
            except ValueError:
                continue
            if self._is_link_or_reparse(path) or not path.is_file():
                continue
            record = self._read_json(path)
            if record is None:
                continue
            identity = record.get("identity")
            identity_map = identity if isinstance(identity, dict) else {}
            coverage = record.get("coverage")
            dataset_valid = self._dataset_is_current_usable(record, path)
            views.append(
                {
                    "dataset_id": record.get("dataset_id", path.stem),
                    "identity": dict(identity_map),
                    "provider": identity_map.get("provider"),
                    "market": identity_map.get("market"),
                    "symbol": identity_map.get("symbol"),
                    "source_timeframe": identity_map.get("source_timeframe"),
                    "data_timeframe": identity_map.get("data_timeframe") or identity_map.get("source_timeframe"),
                    "timeframe": identity_map.get("data_timeframe") or identity_map.get("source_timeframe"),
                    "period": coverage,
                    "coverage": coverage,
                    "quality": record.get("quality") if dataset_valid else record.get("quality"),
                    "usable": dataset_valid,
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
    def _assert_provider_boundary(identity: JsonObject) -> None:
        if identity.get("provider") != "LOCAL_FAKE":
            raise ValueError("EXTERNAL_PROVIDER_GATE_REQUIRED")

    @staticmethod
    def _require_provenance(value: object) -> None:
        if not isinstance(value, Mapping) or not value:
            raise ValueError("PROVENANCE_REQUIRED")

    @classmethod
    def _safe_provenance(cls, value: object) -> JsonObject:
        cls._require_provenance(value)
        assert isinstance(value, Mapping)
        if len(value) > 16:
            raise ValueError("PROVENANCE_INVALID")
        safe: JsonObject = {}
        for key, item in value.items():
            if not isinstance(key, str) or key not in _PROVENANCE_FIELDS:
                raise ValueError("PROVENANCE_INVALID")
            if isinstance(item, str):
                if not item or len(item) > 256:
                    raise ValueError("PROVENANCE_INVALID")
                safe[key] = item
            elif key == "source_job_ids":
                references = cls._reference_list(item)
                if any(len(reference) > 128 for reference in references):
                    raise ValueError("PROVENANCE_INVALID")
                safe[key] = references
            elif isinstance(item, int) and not isinstance(item, bool):
                safe[key] = item
            else:
                raise ValueError("PROVENANCE_INVALID")
        if not safe.get("source_job_id") and not safe.get("source_job_ids"):
            raise ValueError("PROVENANCE_REQUIRED")
        return safe

    @staticmethod
    def _assert_provenance_identity(provenance: Mapping[str, object], identity: JsonObject) -> None:
        source_mode = provenance.get("source_mode")
        if source_mode is not None and source_mode != identity.get("provider"):
            raise ValueError("DATA_PROVENANCE_MISMATCH")

    @staticmethod
    def _assert_staging_request(request: Mapping[str, object]) -> None:
        if request.get("staging_state") in {"ORPHAN_STAGING", "PARTIAL", "FAILED", "RECOVERY_REQUIRED"}:
            raise ValueError("PROMOTION_RECOVERY_REQUIRED")
        if request.get("promotion_state") in {"ORPHAN_STAGING", "RECOVERY_REQUIRED"}:
            raise ValueError("PROMOTION_RECOVERY_REQUIRED")
        if request.get("usable") is False or request.get("quality") in {"UNUSABLE", "PENDING_CATALOG_VALIDATION"}:
            raise ValueError("DATASET_NOT_USABLE")

    @classmethod
    def _normalise_bars(cls, value: object, *, allow_empty: bool = False) -> list[JsonObject]:
        if not isinstance(value, (list, tuple)):
            raise ValueError("BARS_INVALID")
        if len(value) > _MAX_BARS:
            raise ValueError("BARS_TOO_LARGE")
        if not value and not allow_empty:
            raise ValueError("BARS_EMPTY")
        bars: list[JsonObject] = []
        previous_timestamp: datetime | None = None
        for bar in value:
            if not isinstance(bar, Mapping) or set(bar) != _BAR_FIELDS:
                raise ValueError("BAR_SCHEMA_INVALID")
            timestamp = cls._normalise_timestamp(bar.get("timestamp"))
            if previous_timestamp is not None and timestamp < previous_timestamp:
                raise ValueError("BAR_ORDER_INVALID")
            previous_timestamp = timestamp
            numeric_values: dict[str, str] = {}
            for field in ("open", "high", "low", "close", "volume"):
                numeric_values[field] = cls._normalise_numeric(bar.get(field), field)
            open_value = Decimal(numeric_values["open"])
            high_value = Decimal(numeric_values["high"])
            low_value = Decimal(numeric_values["low"])
            close_value = Decimal(numeric_values["close"])
            volume_value = Decimal(numeric_values["volume"])
            if (
                high_value < max(open_value, close_value)
                or low_value > min(open_value, close_value)
                or volume_value < 0
            ):
                raise ValueError("BAR_VALUES_INVALID")
            bars.append({"timestamp": cls._timestamp_text(timestamp), **numeric_values})
        return bars

    @staticmethod
    def _normalise_timestamp(value: object) -> datetime:
        if not isinstance(value, str) or not value:
            raise ValueError("BAR_TIMESTAMP_INVALID")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("BAR_TIMESTAMP_INVALID") from error
        offset = parsed.utcoffset()
        if parsed.tzinfo is None or offset is None or offset.total_seconds() != 0:
            raise ValueError("BAR_TIMESTAMP_NOT_UTC")
        return parsed.astimezone(UTC)

    @staticmethod
    def _timestamp_text(value: datetime) -> str:
        return value.isoformat().replace("+00:00", "Z")

    @staticmethod
    def _normalise_numeric(value: object, field: str) -> str:
        if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
            raise ValueError("BAR_VALUES_INVALID")
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("BAR_VALUES_INVALID") from None
        if not decimal_value.is_finite():
            raise ValueError("BAR_VALUES_INVALID")
        return str(value)

    @staticmethod
    def _index_bars(bars: list[JsonObject]) -> dict[str, JsonObject]:
        indexed: dict[str, JsonObject] = {}
        for bar in bars:
            timestamp = str(bar["timestamp"])
            previous = indexed.get(timestamp)
            if previous is not None and HistoryCatalog._bar_signature(previous) != HistoryCatalog._bar_signature(bar):
                raise ValueError("DATA_CONFLICT")
            indexed[timestamp] = bar
        return indexed

    @staticmethod
    def _bar_signature(bar: JsonObject) -> str:
        signature = {
            "timestamp": bar.get("timestamp"),
            "values": {
                field: HistoryCatalog._canonical_decimal(bar.get(field))
                for field in ("open", "high", "low", "close", "volume")
            },
        }
        return json.dumps(signature, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _canonical_decimal(value: object) -> str:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return str(value)
        if not decimal_value.is_finite():
            return str(value)
        return format(decimal_value.normalize(), "f")

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

    @classmethod
    def _safe_catalog_id(cls, value: object) -> str | None:
        if not isinstance(value, str) or _CATALOG_ID_PATTERN.fullmatch(value) is None:
            return None
        if value.endswith((".", " ")):
            return None
        stem = value.split(".", 1)[0].upper()
        if stem in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }:
            return None
        return value

    def _request_dataset_id(self, request: Mapping[str, object]) -> str | None:
        raw_dataset_id = request.get("dataset_id")
        if raw_dataset_id is None:
            return None
        if self._safe_catalog_id(raw_dataset_id) is None:
            raise ValueError("DATASET_ID_INVALID")
        assert isinstance(raw_dataset_id, str)
        return raw_dataset_id

    @staticmethod
    def _preview_binding(preview: JsonObject) -> JsonObject:
        return {
            key: json.loads(json.dumps(preview.get(key), ensure_ascii=False, default=str))
            for key in (
                "dataset_id",
                "current_revision",
                "identity",
                "merged_bars",
                "conflicts",
                "affected_runs",
                "affected_results",
                "explicit_replace",
                "provenance",
            )
        }

    def _promotion_dataset_id(self, request: Mapping[str, object]) -> str:
        raw_dataset_id = request.get("dataset_id")
        if raw_dataset_id is None:
            request_id = request.get("request_id")
            raw_dataset_id = f"DATASET-MERGED-{request_id}" if isinstance(request_id, str) and request_id else None
        safe_dataset_id = self._safe_catalog_id(raw_dataset_id)
        if safe_dataset_id is None:
            raise ValueError("DATASET_ID_INVALID")
        return safe_dataset_id

    @contextmanager
    def _dataset_operation_lock(self, dataset_id: str) -> Iterator[None]:
        safe_dataset_id = self._safe_catalog_id(dataset_id)
        if safe_dataset_id is None:
            raise ValueError("DATASET_ID_INVALID")
        lock_path = self.datasets_root / f".{safe_dataset_id}.lock"
        self._assert_path_chain_safe(lock_path, self.datasets_root)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with lock_path.open("a+b") as handle:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    fcntl: Any = __import__("fcntl")

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                with self._preview_lock:
                    yield
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError as error:
            raise ValueError("DATASET_LOCK_FAILED") from error

    @staticmethod
    def _revision(record: JsonObject) -> int:
        value = record.get("current_revision", 0)
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    def _dataset_path(self, dataset_id: str) -> Path:
        safe_id = self._safe_catalog_id(dataset_id)
        if safe_id is None:
            raise ValueError("DATASET_ID_INVALID")
        path = self.datasets_root / f"{safe_id}.json"
        self._assert_path_chain_safe(path, self.datasets_root)
        return path

    def _load_current_dataset(self, dataset_id: str | None) -> JsonObject | None:
        if dataset_id is None:
            return None
        path = self._dataset_path(dataset_id)
        if not path.exists():
            return None
        if self._is_link_or_reparse(path) or not path.is_file():
            raise ValueError("DATASET_PATH_UNSAFE")
        record = self._read_json(path)
        if record is None or not self._dataset_is_current_usable(record, path):
            raise ValueError("DATASET_CURRENT_INVALID")
        return record

    def _dataset_is_current_usable(self, record: JsonObject, path: Path | None = None) -> bool:
        if path is not None and (self._is_link_or_reparse(path) or not path.is_file()):
            return False
        if record.get("schema") != DATASET_SCHEMA:
            return False
        dataset_id = record.get("dataset_id")
        if self._safe_catalog_id(dataset_id) is None:
            return False
        if path is not None and path.stem != dataset_id:
            return False
        if record.get("state") != "CURRENT" or record.get("promotion_state") != "PROMOTED":
            return False
        if record.get("quality") not in _USABLE_QUALITIES or record.get("usable") is not True:
            return False
        if record.get("legacy") is True:
            return False
        try:
            identity = self._identity_payload(record.get("identity"))
            self._assert_provider_boundary(identity)
            self._safe_provenance(record.get("provenance"))
            coverage = record.get("coverage")
            if not isinstance(coverage, Mapping):
                return False
            coverage_start = coverage.get("start")
            coverage_end = coverage.get("end")
            if not isinstance(coverage_start, str) or not isinstance(coverage_end, str):
                return False
            if not self._valid_coverage(coverage_start, coverage_end):
                return False
            bars = self._normalise_bars(record.get("bars"), allow_empty=False)
            return len(bars) == record.get("bar_count")
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _valid_coverage(start: str, end: str) -> bool:
        try:
            start_dt = HistoryCatalog._normalise_timestamp(start)
            end_dt = HistoryCatalog._normalise_timestamp(end)
        except ValueError:
            return False
        return start_dt <= end_dt

    @staticmethod
    def _merge_rejection(reason: str, request: Mapping[str, object]) -> JsonObject:
        return {
            "state": "REJECTED",
            "reason": reason,
            "identity": HistoryCatalog._safe_identity_for_error(request.get("identity")),
            "promotable": False,
            "promoted": False,
            "dedupe_count": 0,
            "conflict_count": 0,
            "affected_runs": HistoryCatalog._reference_list(request.get("affected_runs")),
            "affected_results": HistoryCatalog._reference_list(request.get("affected_results")),
            "requires_explicit_replace": False,
        }

    @staticmethod
    def _safe_identity_for_error(value: object) -> JsonObject | None:
        if not isinstance(value, Mapping):
            return None
        return {
            key: item
            for key in (*_DATA_IDENTITY_FIELDS, "data_timeframe")
            if isinstance(item := value.get(key), str) and len(item) <= 128
        }

    @classmethod
    def _is_link_or_reparse(cls, path: Path) -> bool:
        try:
            is_junction = getattr(path, "is_junction", None)
            if path.is_symlink() or os.path.islink(path) or (callable(is_junction) and bool(is_junction())):
                return True
            if not path.exists():
                return False
            attributes = getattr(os.lstat(path), "st_file_attributes", 0)
            return bool(attributes & 0x400)
        except OSError:
            return True

    @classmethod
    def _ensure_directory_safe(cls, path: Path) -> None:
        if path.exists() and cls._is_link_or_reparse(path):
            raise ValueError("RUNTIME_PATH_UNSAFE")
        path.mkdir(parents=True, exist_ok=True)
        if cls._is_link_or_reparse(path):
            raise ValueError("RUNTIME_PATH_UNSAFE")

    @classmethod
    def _assert_path_chain_safe(cls, path: Path, root: Path) -> None:
        if cls._is_link_or_reparse(root):
            raise ValueError("RUNTIME_PATH_UNSAFE")
        root_resolved = root.resolve()
        path_resolved = path.resolve(strict=False)
        try:
            path_resolved.relative_to(root_resolved)
        except ValueError as error:
            raise ValueError("RUNTIME_PATH_OUT_OF_SCOPE") from error
        current = root
        relative_parts = path.relative_to(root).parts
        for part in relative_parts:
            current = current / part
            if current.exists() and cls._is_link_or_reparse(current):
                raise ValueError("RUNTIME_PATH_UNSAFE")

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
            try:
                self._assert_path_chain_safe(path, self.runs_root)
            except ValueError:
                issues.append(self._issue("RUNTIME_PATH_UNSAFE", path.stem, path))
                continue
            if self._is_link_or_reparse(path) or not path.is_file():
                issues.append(self._issue("RUNTIME_PATH_UNSAFE", path.stem, path))
                continue
            record = self._read_json(path)
            if record is None:
                issues.append(self._issue("CATALOG_JSON_INVALID", path.stem, path))
                continue
            run_id = record.get("run_id")
            if not isinstance(run_id, str) or path.stem != run_id:
                issues.append(self._issue("CATALOG_RUN_ID_INVALID", str(run_id or path.stem), path))
                continue
            try:
                self._safe_run_id(run_id)
            except ValueError:
                issues.append(self._issue("CATALOG_RUN_ID_INVALID", run_id, path))
                continue
            if record.get("schema") not in {None, CATALOG_SCHEMA}:
                issues.append(self._issue("CATALOG_SCHEMA_UNSUPPORTED", run_id, path))
                continue
            catalog_ids.add(run_id)
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
            try:
                self._assert_path_chain_safe(result_path, self.results_root)
            except ValueError:
                issues.append(self._issue("RUNTIME_PATH_UNSAFE", folder_run_id, result_path))
                continue
            if (
                self._is_link_or_reparse(result_path.parent)
                or self._is_link_or_reparse(result_path)
                or not result_path.is_file()
            ):
                issues.append(self._issue("RUNTIME_PATH_UNSAFE", folder_run_id, result_path))
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
            if (
                result.get("legacy_import") is not True
                or result.get("legacy_import_ticket") != LEGACY_IMPORT_TICKET
                or not isinstance(result.get("provenance"), dict)
                or result["provenance"].get("source_mode") != "P5_LOCAL_READ_ONLY"
            ):
                restored.append(
                    self._orphan_result_record(
                        result_run_id,
                        f"results/{result_run_id}/result.json",
                    )
                )
                issues.append(self._issue("ORPHAN_RESULT_UNOWNED", folder_run_id, result_path))
                continue
            restored.append(
                self._legacy_record(
                    result_run_id,
                    result,
                    f"results/{result_run_id}/result.json",
                )
            )
        return restored, issues

    @staticmethod
    def _orphan_result_record(run_id: str, reference: str) -> JsonObject:
        return {
            "schema": CATALOG_SCHEMA,
            "run_id": run_id,
            "kind": "SINGLE_BACKTEST",
            "parent_id": None,
            "status": "RECOVERY_REQUIRED",
            "progress": 0,
            "total": 0,
            "started_at": None,
            "ended_at": None,
            "spec": {},
            "metrics": None,
            "provenance": {},
            "failure": {
                "code": "ORPHAN_RESULT_UNOWNED",
                "message": "Run recordがないResultはlegacy importの明示印がないため成功扱いにしません。",
                "retryable": False,
            },
            "checkpoint": None,
            "resume_count": 0,
            "recovery_mode": "RECOVERY_REQUIRED",
            "result_reference": reference,
            "rows": [],
        }

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
        if self._is_link_or_reparse(result_path.parent) or self._is_link_or_reparse(result_path):
            raise ValueError("RUNTIME_PATH_UNSAFE")
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
        if value.endswith((".", " ")):
            raise ValueError("RUN_ID_INVALID")
        if value.split(".", 1)[0].upper() in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }:
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

    def _write_json_atomic(self, path: Path, payload: JsonObject) -> None:
        self._assert_path_chain_safe(path.parent, self.runtime_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._is_link_or_reparse(path):
            raise ValueError("RUNTIME_PATH_UNSAFE")
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
            self._fsync_directory(path.parent)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        try:
            descriptor = os.open(directory, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        except OSError:
            pass
        finally:
            os.close(descriptor)
