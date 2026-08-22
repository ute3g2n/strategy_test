"""Local Backtest product service.

This module is deliberately fixture-only.  It reads the already approved local
P5 normalized files, runs a deterministic virtual-fill simulation, and exposes
plain JSON-shaped DTOs to the local HTTP boundary.  It never opens a network
connection, reads a Secret, or creates a Broker/Live object.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import threading
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from autotrade.backtest.contracts import (
    BacktestRunRequest,
    DataGateDecision,
    EngineIdentity,
    ExperimentManifest,
    ReplayInput,
    canonical_hash,
)
from autotrade.backtest.runner import BacktestRunner
from autotrade.market_data.store_contracts import DataVersionManifest, MarketEvent
from autotrade.strategy.contracts import StrategyConfig, StrategyState
from autotrade.strategy.service import process_closed_bars

from .history_catalog import HistoryCatalog
from .run_service import OperationGuard
from .storage_paths import BACKTEST_STORAGE_ROOT, HISTORICAL_DATA_ROOT, validate_storage_path

JsonObject = dict[str, Any]
RunCallback = Callable[[str, int, int], None]

ALLOWED_SYMBOLS = {"BTCUSDT", "ETHUSDT"}
P5_START = datetime(2025, 2, 24, tzinfo=UTC)
P5_END = datetime(2026, 8, 1, tzinfo=UTC)
HOLDOUT_START = datetime(2026, 7, 1, tzinfo=UTC)
HOLDOUT_END = datetime(2026, 8, 1, tzinfo=UTC)
MAX_BARS = 200_000


def _utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("UTC timestamp is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("UTC timestamp is invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("UTC timestamp is required")
    return parsed.astimezone(UTC)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal(value: object, label: str) -> Decimal:
    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = Decimal(value)
        except InvalidOperation as error:
            raise ValueError(f"{label} must be a finite decimal string") from error
    else:
        raise ValueError(f"{label} must be a finite decimal string")
    if not parsed.is_finite():
        raise ValueError(f"{label} must be finite")
    return parsed


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.0001")), "f")


def _int_parameter(parameters: Mapping[str, Any], name: str, default: int) -> int:
    value = parameters.get(name, str(default))
    try:
        parsed = int(str(value))
    except ValueError as error:
        raise ValueError(f"{name} must be an integer string") from error
    if parsed < 1 or parsed > 500:
        raise ValueError(f"{name} is outside the allowed range")
    return parsed


@dataclass(frozen=True)
class _Bar:
    timestamp: datetime
    opened: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    symbol: str


@dataclass
class _Run:
    run_id: str
    spec: JsonObject
    kind: str = "SINGLE_BACKTEST"
    parent_id: str | None = None
    status: str = "QUEUED"
    progress: int = 0
    total: int = 0
    started_at: str | None = None
    ended_at: str | None = None
    rows: list[JsonObject] = field(default_factory=list)
    metrics: JsonObject | None = None
    provenance: JsonObject = field(default_factory=dict)
    failure: JsonObject | None = None
    checkpoint: JsonObject | None = None
    resume_count: int = 0
    recovery_mode: str = "NORMAL"
    operation_revision: int = 0
    cancel_event: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None
    state: JsonObject = field(default_factory=dict)
    strategy_state: StrategyState | None = None


@dataclass
class _Sweep:
    sweep_id: str
    base_spec: JsonObject
    expected_total: int
    children: list[str] = field(default_factory=list)
    status: str = "QUEUED"
    cancel_event: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None


@dataclass
class _CsvJob:
    job_id: str
    run_id: str
    columns: tuple[str, ...]
    status: str = "QUEUED"
    progress: int = 0
    content: str = ""
    failure: JsonObject | None = None
    thread: threading.Thread | None = None


class BacktestProductService:
    """Typed local service used by tests and the browser API."""

    def __init__(self, *, data_root: Path | None = None, runtime_root: Path | None = None) -> None:
        self.data_root = (
            validate_storage_path(HISTORICAL_DATA_ROOT, purpose="historical data")
            if data_root is None
            else Path(data_root)
        )
        self.runtime_root = (
            validate_storage_path(BACKTEST_STORAGE_ROOT, purpose="backtest runtime data")
            if runtime_root is None
            else Path(runtime_root)
        )
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._runs: dict[str, _Run] = {}
        self._sweeps: dict[str, _Sweep] = {}
        self._csv_jobs: dict[str, _CsvJob] = {}
        self._holdout_consumed = False
        self._history_catalog = HistoryCatalog(self.runtime_root)
        self._operation_guard = OperationGuard()
        self._recovery_issues: list[JsonObject] = []
        self._restore_history()

    def _restore_history(self) -> None:
        restored, issues = self._history_catalog.restore()
        with self._lock:
            self._recovery_issues = [dict(issue) for issue in issues]
            for record in restored:
                run_id = record.get("run_id")
                if not isinstance(run_id, str) or run_id in self._runs:
                    self._recovery_issues.append(
                        {
                            "code": "DUPLICATE_RUN_ID",
                            "run_id": str(run_id or "UNKNOWN"),
                            "path": "catalog/runs",
                            "message": "同じRun IDが複数回見つかりました。",
                        }
                    )
                    continue
                raw_spec = record.get("spec")
                spec = dict(raw_spec) if isinstance(raw_spec, Mapping) else {}
                if not spec:
                    spec = self._legacy_spec(record)
                run = _Run(
                    run_id=run_id,
                    spec=spec,
                    kind=str(record.get("kind", "SINGLE_BACKTEST")),
                    parent_id=str(record["parent_id"]) if record.get("parent_id") is not None else None,
                    status=str(record.get("status", "RECOVERY_REQUIRED")),
                    progress=self._stored_int(record.get("progress")),
                    total=self._stored_int(record.get("total")),
                    started_at=record.get("started_at") if isinstance(record.get("started_at"), str) else None,
                    ended_at=record.get("ended_at") if isinstance(record.get("ended_at"), str) else None,
                    metrics=dict(record["metrics"]) if isinstance(record.get("metrics"), Mapping) else None,
                    provenance=dict(record.get("provenance", {}))
                    if isinstance(record.get("provenance"), Mapping)
                    else {},
                    failure=dict(record["failure"]) if isinstance(record.get("failure"), Mapping) else None,
                    checkpoint=dict(record["checkpoint"]) if isinstance(record.get("checkpoint"), Mapping) else None,
                    resume_count=self._stored_int(record.get("resume_count")),
                    recovery_mode=str(record.get("recovery_mode", "NORMAL")),
                    operation_revision=self._stored_int(record.get("operation_revision")),
                )
                rows = record.get("rows")
                if isinstance(rows, list):
                    run.rows = [dict(row) for row in rows if isinstance(row, Mapping)]
                self._runs[run_id] = run

    @staticmethod
    def _stored_int(value: object) -> int:
        try:
            parsed = int(str(value or "0"))
        except (TypeError, ValueError):
            return 0
        return max(parsed, 0)

    def _legacy_spec(self, record: Mapping[str, Any]) -> JsonObject:
        """Build only the conditions safely visible in an old result artifact."""

        raw_provenance = record.get("provenance")
        provenance: Mapping[str, Any] = raw_provenance if isinstance(raw_provenance, Mapping) else {}
        raw_metrics = record.get("metrics")
        metrics: Mapping[str, Any] = raw_metrics if isinstance(raw_metrics, Mapping) else {}
        fixture_scope = str(provenance.get("fixture_scope", ""))
        symbol = next((candidate for candidate in ALLOWED_SYMBOLS if candidate in fixture_scope), "UNKNOWN")
        explicit_symbol = provenance.get("symbol")
        if isinstance(explicit_symbol, str) and explicit_symbol in ALLOWED_SYMBOLS:
            symbol = explicit_symbol
        raw_core = provenance.get("core_validation")
        core: Mapping[str, Any] = raw_core if isinstance(raw_core, Mapping) else {}
        selected_system = core.get("selected_system")
        strategy = {"SYS1": "TURTLE_SYS1", "SYS2": "TURTLE_SYS2"}.get(str(selected_system), "UNKNOWN")
        return {
            "symbol": symbol,
            "market": "UNKNOWN",
            "timeframe": "UNKNOWN",
            "timezone": "UNKNOWN",
            "calendar": "UNKNOWN",
            "start": provenance.get("period_start_utc") or metrics.get("period_start_utc") or "UNKNOWN",
            "end": provenance.get("period_end_utc") or metrics.get("period_end_utc") or "UNKNOWN",
            "strategy": strategy,
            "parameters": {
                "entry_lookback": str(core.get("entry_lookback", "UNKNOWN")),
                "exit_lookback": str(core.get("exit_lookback", "UNKNOWN")),
                "initial_balance": "UNKNOWN",
                "fee_bps": str(provenance.get("fee_bps", "UNKNOWN")),
                "slippage_bps": str(provenance.get("slippage_bps", "UNKNOWN")),
            },
            "recovery_note": (
                "旧形式result.jsonから安全に読める情報だけを表示しています。UNKNOWNは当時の保存対象外です。"
            ),
        }

    def _persist_run(self, run: _Run) -> None:
        self._history_catalog.persist_run(self._run_view(run))

    def recovery_report(self) -> JsonObject:
        with self._lock:
            required_ids = [run.run_id for run in self._runs.values() if run.status == "RECOVERY_REQUIRED"]
            issues = [dict(issue) for issue in self._recovery_issues]
        return {
            "status": "RECOVERY_REQUIRED" if issues or required_ids else "CLEAN",
            "issues": issues,
            "recovery_required_run_ids": sorted(required_ids),
            "restored_run_count": len(self._runs),
        }

    def reset_for_local_test(self) -> None:
        """Clear only the in-memory local test service state between browser projects."""

        with self._lock:
            for run in self._runs.values():
                if run.status in {"QUEUED", "RUNNING"}:
                    run.cancel_event.set()
            self._runs.clear()
            self._sweeps.clear()
            self._csv_jobs.clear()
            self._holdout_consumed = False
            self._operation_guard.reset_for_local_test()

    def preflight(self, raw_spec: Mapping[str, Any]) -> JsonObject:
        checks: list[JsonObject] = []
        try:
            spec = self._validate_spec(raw_spec)
            checks.extend(
                [
                    {"id": "TYPE_AND_UNIT", "status": "PASS", "message": "型・単位・文字列表現を確認しました。"},
                    {"id": "P5_DATA_SCOPE", "status": "PASS", "message": "P5のローカル許可範囲内です。"},
                    {"id": "UTC_AND_CALENDAR", "status": "PASS", "message": "UTCと24時間カレンダーです。"},
                    {"id": "QUALITY", "status": "PASS", "message": "既存P5の品質PASS範囲を読み取り対象にします。"},
                    {"id": "LOOKAHEAD", "status": "PASS", "message": "終了時刻より後のBarは読みません。"},
                ]
            )
            return {"status": "PASS", "checks": checks, "normalized_spec": spec}
        except ValueError as error:
            checks.append({"id": "INPUT", "status": "FAIL", "message": str(error)})
            return {"status": "STOPPED", "checks": checks, "failure": {"code": str(error), "retryable": False}}

    def create_run(
        self, raw_spec: Mapping[str, Any], *, kind: str = "SINGLE_BACKTEST", parent_id: str | None = None
    ) -> JsonObject:
        spec = self._validate_spec(raw_spec)
        run_id = f"RUN-AUTOTRADE-{uuid.uuid4().hex[:12].upper()}"
        run = _Run(run_id=run_id, spec=spec, kind=kind, parent_id=parent_id)
        with self._lock:
            self._runs[run_id] = run
            self._persist_run(run)
            run.thread = threading.Thread(
                target=self._execute_run, args=(run_id,), daemon=True, name=f"autotrade-{run_id}"
            )
            run.thread.start()
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> JsonObject:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise KeyError("RUN_NOT_FOUND")
            return self._run_view(run)

    def list_runs(self) -> list[JsonObject]:
        with self._lock:
            values = [self._run_view(run) for run in self._runs.values()]
        return sorted(values, key=lambda item: str(item.get("run_id")), reverse=True)

    def get_rows(self, run_id: str) -> list[JsonObject]:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise KeyError("RUN_NOT_FOUND")
            return [dict(row) for row in run.rows]

    def cancel_run(self, run_id: str, reason: str = "USER_REQUESTED") -> JsonObject:
        request = {
            "run_id": run_id,
            "operation_token": f"legacy-cancel-{run_id}",
            "request_id": f"legacy-cancel-request-{run_id}",
            "actor": "local-application",
            "origin_screen": "LEGACY_SERVICE_CALL",
            "reason": reason,
        }
        result = self.request_run_cancel(request)
        run = result.get("run")
        if not isinstance(run, dict):
            raise RuntimeError("RUN_CANCEL_RESULT_INVALID")
        return run

    def request_run_cancel(self, request: Mapping[str, Any] | object) -> JsonObject:
        """Apply the shared cancel guard against the server-owned Run state."""

        if not isinstance(request, Mapping):
            raise ValueError("CANCEL_REQUEST_INVALID")
        raw_run_id = request.get("run_id")
        if not isinstance(raw_run_id, str) or not raw_run_id:
            raise ValueError("RUN_ID_REQUIRED")
        with self._lock:
            run = self._runs.get(raw_run_id)
            if run is None:
                raise KeyError("RUN_NOT_FOUND")
            operation = self._operation_guard.request_run_cancel(
                request,
                server_state=run.status,
                server_revision=run.operation_revision,
            )
            if operation.get("accepted") is True:
                run.failure = {
                    "code": "CANCELLED_BY_USER",
                    "message": str(request.get("reason", "USER_REQUESTED")),
                    "retryable": True,
                }
                run.cancel_event.set()
                run.operation_revision += 1
                if run.status == "QUEUED":
                    run.status = "CANCELLED"
                elif run.status == "RUNNING":
                    run.status = "STOP_REQUESTED"
                self._persist_run(run)
            return {"run": self._run_view(run), "operation": operation}

    def resume_run(self, run_id: str) -> JsonObject:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                raise KeyError("RUN_NOT_FOUND")
            if run.status != "CANCELLED" or run.checkpoint is None:
                raise ValueError("CHECKPOINT_RESUME_NOT_AVAILABLE")
            run.resume_count += 1
            run.cancel_event.clear()
            run.failure = None
            run.status = "QUEUED"
            self._operation_guard.reset_run(run_id)
            self._persist_run(run)
            run.thread = threading.Thread(
                target=self._execute_run, args=(run_id,), daemon=True, name=f"autotrade-resume-{run_id}"
            )
            run.thread.start()
            return self._run_view(run)

    def create_sweep(self, raw_spec: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> JsonObject:
        self._validate_spec(raw_spec)
        if not candidates or len(candidates) > 200:
            raise ValueError("SWEEP_CANDIDATE_LIMIT")
        serialized = [json.dumps(dict(candidate), sort_keys=True, separators=(",", ":")) for candidate in candidates]
        if len(serialized) != len(set(serialized)):
            raise ValueError("SWEEP_DUPLICATE")
        sweep_id = f"SWEEP-AUTOTRADE-{uuid.uuid4().hex[:10].upper()}"
        sweep = _Sweep(sweep_id=sweep_id, base_spec=dict(raw_spec), expected_total=len(candidates))
        with self._lock:
            self._sweeps[sweep_id] = sweep
            sweep.thread = threading.Thread(
                target=self._execute_sweep,
                args=(sweep_id, [dict(candidate) for candidate in candidates]),
                daemon=True,
                name=f"autotrade-{sweep_id}",
            )
            sweep.thread.start()
        return self.get_sweep(sweep_id)

    def get_sweep(self, sweep_id: str) -> JsonObject:
        with self._lock:
            sweep = self._sweeps.get(sweep_id)
            if sweep is None:
                raise KeyError("SWEEP_NOT_FOUND")
            children = [self._run_view(self._runs[run_id]) for run_id in sweep.children]
            completed = sum(child["status"] == "SUCCEEDED" for child in children)
            failed = sum(child["status"] in {"FAILED", "CANCELLED"} for child in children)
            if (
                sweep.status not in {"CANCELLED", "PARTIAL_FAILED", "SUCCEEDED"}
                and children
                and len(children) == sweep.expected_total
            ):
                if all(child["status"] in {"SUCCEEDED", "FAILED", "CANCELLED"} for child in children):
                    sweep.status = "PARTIAL_FAILED" if failed else "SUCCEEDED"
            return {
                "sweep_id": sweep_id,
                "status": sweep.status,
                "total": len(children),
                "completed": completed,
                "failed": failed,
                "children": children,
            }

    def wait_for_sweep(self, sweep_id: str, timeout: float = 10.0) -> JsonObject:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            view = self.get_sweep(sweep_id)
            if view["status"] in {"SUCCEEDED", "PARTIAL_FAILED", "CANCELLED"}:
                return view
            time.sleep(0.01)
        return self.get_sweep(sweep_id)

    def cancel_sweep(self, sweep_id: str) -> JsonObject:
        with self._lock:
            sweep = self._sweeps.get(sweep_id)
            if sweep is None:
                raise KeyError("SWEEP_NOT_FOUND")
            sweep.cancel_event.set()
            sweep.status = "CANCELLED"
            return self.get_sweep(sweep_id)

    def compare_runs(self, left_id: str, right_id: str) -> JsonObject:
        left = self.get_run(left_id)
        right = self.get_run(right_id)
        left_spec = left["spec"]
        right_spec = right["spec"]
        comparable = all(
            left_spec.get(key) == right_spec.get(key)
            for key in ("symbol", "market", "timeframe", "start", "end", "strategy")
        )
        return {
            "left_run_id": left_id,
            "right_run_id": right_id,
            "comparable": comparable,
            "reason": None if comparable else "CONDITION_MISMATCH",
            "left_metrics": left.get("metrics"),
            "right_metrics": right.get("metrics"),
        }

    def create_csv_job(self, run_id: str, columns: Sequence[str]) -> JsonObject:
        run = self.get_run(run_id)
        if run["status"] != "SUCCEEDED":
            raise ValueError("RESULT_NOT_READY")
        allowed = {
            "row_kind",
            "decision_time_utc",
            "symbol",
            "signal",
            "direction",
            "price",
            "fee",
            "slippage",
            "cash",
            "equity",
            "reason",
        }
        selected = tuple(str(column) for column in columns)
        if not selected or any(column not in allowed for column in selected):
            raise ValueError("CSV_COLUMN_INVALID")
        job_id = f"CSV-AUTOTRADE-{uuid.uuid4().hex[:10].upper()}"
        job = _CsvJob(job_id=job_id, run_id=run_id, columns=selected)
        with self._lock:
            self._csv_jobs[job_id] = job
            job.thread = threading.Thread(
                target=self._execute_csv, args=(job_id,), daemon=True, name=f"autotrade-{job_id}"
            )
            job.thread.start()
        return self.get_csv_job(job_id)

    def get_csv_job(self, job_id: str) -> JsonObject:
        with self._lock:
            job = self._csv_jobs.get(job_id)
            if job is None:
                raise KeyError("CSV_JOB_NOT_FOUND")
            return {
                "job_id": job.job_id,
                "run_id": job.run_id,
                "status": job.status,
                "progress": job.progress,
                "download_url": f"/api/backtest/csv-jobs/{job.job_id}/download" if job.status == "SUCCEEDED" else None,
                "failure": job.failure,
            }

    def wait_for_csv(self, job_id: str, timeout: float = 10.0) -> JsonObject:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            view = self.get_csv_job(job_id)
            if view["status"] in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                return view
            time.sleep(0.01)
        return self.get_csv_job(job_id)

    def download_csv(self, job_id: str) -> str:
        with self._lock:
            job = self._csv_jobs.get(job_id)
            if job is None:
                raise KeyError("CSV_JOB_NOT_FOUND")
            if job.status != "SUCCEEDED":
                raise ValueError("CSV_NOT_READY")
            return job.content

    def holdout(self, phase: str) -> JsonObject:
        if phase == "EARLY_ADJUSTMENT":
            return {
                "status": "STOPPED",
                "failure": {"code": "EARLY_HOLDOUT_ACCESS", "message": "確定前のHoldoutは読めません。"},
            }
        if phase != "FINALIZED":
            raise ValueError("HOLDOUT_PHASE_INVALID")
        with self._lock:
            if self._holdout_consumed:
                return {
                    "status": "STOPPED",
                    "failure": {"code": "HOLDOUT_ALREADY_READ", "message": "Holdoutは一度だけ読めます。"},
                }
            self._holdout_consumed = True
        row_count = 0
        try:
            row_count = len(self._load_bars("BTCUSDT", HOLDOUT_START, HOLDOUT_END))
        except ValueError:
            row_count = 0
        return {
            "status": "SUCCEEDED",
            "period": {"start": _iso(HOLDOUT_START), "end": _iso(HOLDOUT_END)},
            "row_count": row_count,
            "reused_for_adjustment": False,
        }

    def walk_forward(self, windows: Sequence[Mapping[str, Any]]) -> JsonObject:
        if not windows or len(windows) > 12:
            raise ValueError("WALK_FORWARD_WINDOW_COUNT")
        normalized: list[JsonObject] = []
        previous_evaluation_end: datetime | None = None
        for item in windows:
            try:
                train_start = _utc(item["train_start"])
                train_end = _utc(item["train_end"])
                validation_end = _utc(item["validation_end"])
                evaluation_end = _utc(item["evaluation_end"])
            except (KeyError, ValueError) as error:
                raise ValueError("WALK_FORWARD_WINDOW_INVALID") from error
            if not train_start < train_end < validation_end < evaluation_end:
                raise ValueError("WALK_FORWARD_ORDER_INVALID")
            if previous_evaluation_end is not None and (
                train_end > previous_evaluation_end or validation_end < previous_evaluation_end
            ):
                raise ValueError("WALK_FORWARD_OVERLAP")
            if train_start < P5_START or evaluation_end > P5_END:
                raise ValueError("WALK_FORWARD_OUT_OF_SCOPE")
            normalized.append(
                {
                    "id": str(item.get("id", f"W{len(normalized) + 1}")),
                    "train_start": _iso(train_start),
                    "train_end": _iso(train_end),
                    "validation_end": _iso(validation_end),
                    "evaluation_end": _iso(evaluation_end),
                }
            )
            previous_evaluation_end = evaluation_end
        results: list[JsonObject] = []
        base_spec = self._default_spec(normalized[0]["train_start"], normalized[0]["evaluation_end"])
        for window in normalized:
            evaluation_spec = dict(base_spec)
            evaluation_spec["start"] = window["validation_end"]
            evaluation_spec["end"] = window["evaluation_end"]
            try:
                bars = self._load_bars("BTCUSDT", _utc(evaluation_spec["start"]), _utc(evaluation_spec["end"]))
                metrics, rows = self._simulate_complete(bars, evaluation_spec)
                results.append(
                    {
                        "window_id": window["id"],
                        "window": window,
                        "status": "SUCCEEDED",
                        "metrics": metrics,
                        "row_count": len(rows),
                    }
                )
            except ValueError as error:
                results.append(
                    {"window_id": window["id"], "window": window, "status": "FAILED", "failure": {"code": str(error)}}
                )
        return {
            "status": "SUCCEEDED" if all(item["status"] == "SUCCEEDED" for item in results) else "PARTIAL_FAILED",
            "windows": results,
            "future_reference": False,
            "holdout_reused": False,
        }

    def _default_spec(self, start: str, end: str) -> JsonObject:
        return {
            "symbol": "BTCUSDT",
            "market": "SPOT",
            "timeframe": "1m",
            "timezone": "UTC",
            "calendar": "CRYPTO_24_7_UTC",
            "start": start,
            "end": end,
            "strategy": "TURTLE_SYS1",
            "parameters": {
                "entry_lookback": "20",
                "exit_lookback": "10",
                "initial_balance": "100000",
                "fee_bps": "1.0",
                "slippage_bps": "2.0",
            },
        }

    def _validate_spec(self, raw_spec: Mapping[str, Any]) -> JsonObject:
        if not isinstance(raw_spec, Mapping):
            raise ValueError("TYPED_INPUT_INVALID")
        spec = dict(raw_spec)
        symbol = spec.get("symbol")
        if symbol not in ALLOWED_SYMBOLS:
            raise ValueError("SYMBOL_OUT_OF_SCOPE")
        if spec.get("market") != "SPOT" or spec.get("timeframe") != "1m":
            raise ValueError("MARKET_OR_TIMEFRAME_OUT_OF_SCOPE")
        if spec.get("timezone") != "UTC" or spec.get("calendar") != "CRYPTO_24_7_UTC":
            raise ValueError("UTC_CALENDAR_REQUIRED")
        if spec.get("strategy", "TURTLE_SYS1") not in {"TURTLE_SYS1", "TURTLE_SYS2"}:
            raise ValueError("STRATEGY_OUT_OF_SCOPE")
        start = _utc(spec.get("start"))
        end = _utc(spec.get("end"))
        if start < P5_START or end > P5_END or start >= end:
            raise ValueError("PERIOD_OUT_OF_SCOPE")
        parameters = spec.get("parameters")
        if not isinstance(parameters, Mapping):
            raise ValueError("PARAMETERS_REQUIRED")
        entry = _int_parameter(parameters, "entry_lookback", 20)
        exit_lookback = _int_parameter(parameters, "exit_lookback", 10)
        if exit_lookback > entry:
            raise ValueError("EXIT_LOOKBACK_AFTER_ENTRY")
        initial = _decimal(parameters.get("initial_balance", "100000"), "initial_balance")
        fee = _decimal(parameters.get("fee_bps", "1.0"), "fee_bps")
        slippage = _decimal(parameters.get("slippage_bps", "2.0"), "slippage_bps")
        if initial <= 0 or fee < 0 or slippage < 0 or fee > 100 or slippage > 100:
            raise ValueError("COST_ASSUMPTION_OUT_OF_RANGE")
        normalized_parameters = dict(parameters)
        normalized_parameters.update(
            {
                "entry_lookback": str(entry),
                "exit_lookback": str(exit_lookback),
                "initial_balance": _money(initial),
                "fee_bps": _money(fee),
                "slippage_bps": _money(slippage),
            }
        )
        spec.update(
            {
                "symbol": str(symbol),
                "start": _iso(start),
                "end": _iso(end),
                "parameters": normalized_parameters,
                "strategy": str(spec.get("strategy", "TURTLE_SYS1")),
            }
        )
        return spec

    def _execute_run(self, run_id: str) -> None:
        with self._lock:
            run = self._runs[run_id]
            if run.cancel_event.is_set():
                run.status = "CANCELLED"
                run.ended_at = _iso(datetime.now(UTC))
                self._persist_run(run)
                return
            if run.status != "STOP_REQUESTED":
                run.status = "RUNNING"
            run.started_at = _iso(datetime.now(UTC))
            self._persist_run(run)
        try:
            spec = run.spec
            bars = self._load_bars(str(spec["symbol"]), _utc(spec["start"]), _utc(spec["end"]))
            if not bars:
                raise ValueError("DATA_EMPTY")
            if bool(spec.get("force_fail")) or bool(spec.get("parameters", {}).get("force_fail")):
                raise ValueError("CANDIDATE_FORCED_FAILURE")
            with self._lock:
                run.total = len(bars)
                if not run.state:
                    run.state = self._initial_state(spec)
                if run.strategy_state is None:
                    run.strategy_state = StrategyState(run_id=run_id)
                start_index = int(run.state.get("cursor", -1)) + 1
            if start_index == 0:
                core = self._core_validation(bars, spec, run_id)
                with self._lock:
                    run.provenance = self._provenance(spec, bars, core)
            self._run_bars(run, bars, start_index)
        except ValueError as error:
            with self._lock:
                if run.cancel_event.is_set():
                    run.status = "CANCELLED"
                    run.failure = {
                        "code": "CANCELLED_BY_USER",
                        "message": "取消要求を受付済みです。",
                        "retryable": True,
                    }
                else:
                    run.status = "FAILED"
                    run.failure = {"code": str(error), "retryable": False}
                run.ended_at = _iso(datetime.now(UTC))
                self._persist_run(run)
        except Exception:
            with self._lock:
                if run.cancel_event.is_set():
                    run.status = "CANCELLED"
                    run.failure = {
                        "code": "CANCELLED_BY_USER",
                        "message": "取消要求を受付済みです。",
                        "retryable": True,
                    }
                else:
                    run.status = "FAILED"
                    run.failure = {"code": "UNEXPECTED_LOCAL_FAILURE", "retryable": False}
                run.ended_at = _iso(datetime.now(UTC))
                self._persist_run(run)

    def _run_bars(self, run: _Run, bars: list[_Bar], start_index: int) -> None:
        parameters = run.spec["parameters"]
        entry_lookback = int(parameters["entry_lookback"])
        exit_lookback = int(parameters["exit_lookback"])
        for index in range(start_index, len(bars)):
            with self._lock:
                if run.cancel_event.is_set():
                    run.status = "CANCELLED"
                    run.checkpoint = {"cursor": index - 1, "row_count": len(run.rows), "state": dict(run.state)}
                    run.ended_at = _iso(datetime.now(UTC))
                    self._persist_run(run)
                    return
            self._step_run(run, bars, index, entry_lookback, exit_lookback)
            with self._lock:
                run.progress = index + 1
                run.state["cursor"] = index
                if index % 50 == 0:
                    self._persist_run(run)
            if len(bars) > 1_000 or index % 20 == 0:
                time.sleep(0.001)
        with self._lock:
            final_equity = _decimal(run.state["last_equity"], "last_equity")
            initial = _decimal(parameters["initial_balance"], "initial_balance")
            closed = [Decimal(value) for value in run.state.get("closed_pnl", [])]
            wins = sum(value > 0 for value in closed)
            run.metrics = {
                "total_pnl": _money(final_equity - initial),
                "maximum_drawdown": _money(Decimal(run.state["max_drawdown"])),
                "win_rate": _money(Decimal(wins) / Decimal(len(closed)) * Decimal("100") if closed else Decimal("0")),
                "trade_count": int(run.state.get("fill_count", 0)),
                "final_balance": _money(final_equity),
                "ending_balance": _money(final_equity),
                "unit": "USDT",
                "period_start_utc": str(run.spec["start"]),
                "period_end_utc": str(run.spec["end"]),
                "rounding_rule": "Decimal(0.0001)",
                "provenance": "same-run-ledger",
            }
            run.status = "SUCCEEDED"
            run.progress = run.total
            run.ended_at = _iso(datetime.now(UTC))
            self._publish_result(run)

    def _initial_state(self, spec: Mapping[str, Any]) -> JsonObject:
        initial = _decimal(spec["parameters"]["initial_balance"], "initial_balance")
        return {
            "cursor": -1,
            "cash": _money(initial),
            "position_qty": "0",
            "entry_price": None,
            "entry_cost": "0",
            "position_direction": None,
            "last_fill": None,
            "closed_pnl": [],
            "equity_peak": _money(initial),
            "max_drawdown": "0",
            "last_equity": _money(initial),
            "fill_count": 0,
        }

    def _step_run(self, run: _Run, bars: list[_Bar], index: int, _entry_lookback: int, _exit_lookback: int) -> None:
        bar = bars[index]
        state = run.state
        cash = _decimal(state["cash"], "cash")
        qty = _decimal(state["position_qty"], "position_qty")
        fee_bps = _decimal(run.spec["parameters"]["fee_bps"], "fee_bps")
        slippage_bps = _decimal(run.spec["parameters"]["slippage_bps"], "slippage_bps")
        strategy_state = run.strategy_state or StrategyState(run_id=run.run_id)
        next_strategy_state, strategy_signals, _ = process_closed_bars(
            strategy_state,
            [
                {
                    "timeframe": "M1",
                    "open_time_utc": _iso(bar.timestamp),
                    "close_time_utc": _iso(bar.timestamp + timedelta(minutes=1)),
                    "open": _money(bar.opened),
                    "high": _money(bar.high),
                    "low": _money(bar.low),
                    "close": _money(bar.close),
                    "volume": _money(bar.volume),
                    "source_event_ids": [f"{run.run_id}:bar:{index}"],
                    "is_closed": True,
                    "calendar_version": "CRYPTO_24_7_UTC",
                }
            ],
            decision_time_utc=_iso(bar.timestamp + timedelta(minutes=1)),
            instrument_id=bar.symbol,
            config=self._strategy_config(run.spec),
        )
        if next_strategy_state.is_stopped:
            raise ValueError(next_strategy_state.stopped_reason or "STRATEGY_CORE_STOPPED")
        run.strategy_state = next_strategy_state
        signal_event = strategy_signals[0] if strategy_signals else None
        signal: str | None = None
        if signal_event is not None:
            if signal_event.reason.startswith("ADD"):
                signal = "ADD"
            elif signal_event.reason.startswith("EXIT") or signal_event.reason == "TWO_N_STOP":
                signal = "EXIT"
            elif signal_event.reason.endswith("ENTRY"):
                signal = "ENTRY"
            run.rows.append(
                {
                    "row_kind": "SIGNAL",
                    "decision_time_utc": _iso(bar.timestamp + timedelta(minutes=1)),
                    "symbol": bar.symbol,
                    "signal": signal,
                    "direction": signal_event.direction,
                    "reason": signal_event.reason,
                    "signal_id": signal_event.signal_id,
                }
            )
            direction = signal_event.direction
            if signal in {"ENTRY", "ADD"} and direction in {"LONG", "SHORT"}:
                if signal == "ENTRY" and qty != 0:
                    raise ValueError("STRATEGY_POSITION_MISMATCH")
                if signal == "ADD" and (qty == 0 or state.get("position_direction") != direction):
                    raise ValueError("STRATEGY_ADD_POSITION_MISMATCH")
                execution_price = bar.close * (
                    Decimal("1") + slippage_bps / Decimal("10000")
                    if direction == "LONG"
                    else Decimal("1") - slippage_bps / Decimal("10000")
                )
                quantity = (cash / execution_price) * Decimal("0.25")
                if quantity <= 0:
                    raise ValueError("INSUFFICIENT_VIRTUAL_BALANCE")
                notional = execution_price * quantity
                fee = notional * fee_bps / Decimal("10000")
                entry_cost = _decimal(state["entry_cost"], "entry_cost")
                if direction == "LONG":
                    cash -= notional + fee
                    qty += quantity
                    entry_cost += notional + fee
                else:
                    cash += notional - fee
                    qty -= quantity
                    entry_cost += notional - fee
                state["entry_price"] = _money(execution_price)
                state["entry_cost"] = _money(entry_cost)
                state["position_direction"] = direction
                state["last_fill"] = _money(execution_price)
                state["fill_count"] = int(state["fill_count"]) + 1
                run.rows.append(
                    {
                        "row_kind": "VIRTUAL_FILL",
                        "decision_time_utc": _iso(bar.timestamp + timedelta(minutes=1)),
                        "symbol": bar.symbol,
                        "direction": direction,
                        "price": _money(execution_price),
                        "quantity": _money(quantity),
                        "fee": _money(fee),
                        "slippage": _money(abs(execution_price - bar.close)),
                        "fill_kind": signal,
                        "assumption": "fee/slippage are explicit assumptions",
                    }
                )
                run.strategy_state = replace(
                    next_strategy_state,
                    position_direction=direction,
                    last_fill=execution_price,
                    pending_add=False,
                )
            elif signal == "EXIT" and qty != 0:
                direction = "LONG" if qty > 0 else "SHORT"
                execution_price = bar.close * (
                    Decimal("1") - slippage_bps / Decimal("10000")
                    if direction == "LONG"
                    else Decimal("1") + slippage_bps / Decimal("10000")
                )
                quantity = abs(qty)
                notional = execution_price * quantity
                fee = notional * fee_bps / Decimal("10000")
                entry_cost = _decimal(state["entry_cost"], "entry_cost")
                if direction == "LONG":
                    pnl = notional - fee - entry_cost
                    cash += notional - fee
                else:
                    pnl = entry_cost - notional - fee
                    cash -= notional + fee
                state["closed_pnl"].append(_money(pnl))
                state["fill_count"] = int(state["fill_count"]) + 1
                run.rows.append(
                    {
                        "row_kind": "VIRTUAL_FILL",
                        "decision_time_utc": _iso(bar.timestamp + timedelta(minutes=1)),
                        "symbol": bar.symbol,
                        "direction": "FLAT",
                        "price": _money(execution_price),
                        "quantity": _money(quantity),
                        "fee": _money(fee),
                        "slippage": _money(abs(bar.close - execution_price)),
                        "realized_pnl": _money(pnl),
                        "fill_kind": "EXIT",
                        "assumption": "fee/slippage are explicit assumptions",
                    }
                )
                qty = Decimal("0")
                state["entry_price"] = None
                state["entry_cost"] = "0"
                state["position_direction"] = None
                state["last_fill"] = None
                run.strategy_state = replace(
                    next_strategy_state, position_direction=None, last_fill=None, pending_add=False
                )
        equity = cash + qty * bar.close
        peak = max(_decimal(state["equity_peak"], "equity_peak"), equity)
        drawdown = peak - equity
        state["cash"] = _money(cash)
        state["position_qty"] = _money(qty)
        state["equity_peak"] = _money(peak)
        state["max_drawdown"] = _money(max(Decimal(state["max_drawdown"]), drawdown))
        state["last_equity"] = _money(equity)
        if index % 30 == 0 or signal is not None or index == len(bars) - 1:
            run.rows.append(
                {
                    "row_kind": "BALANCE",
                    "decision_time_utc": _iso(bar.timestamp + timedelta(minutes=1)),
                    "symbol": bar.symbol,
                    "cash": _money(cash),
                    "equity": _money(equity),
                    "position_quantity": _money(qty),
                    "close": _money(bar.close),
                }
            )

    @staticmethod
    def _strategy_config(spec: Mapping[str, Any]) -> StrategyConfig:
        strategy_name = str(spec.get("strategy", "TURTLE_SYS1"))
        system = {"TURTLE_SYS1": "SYS1", "TURTLE_SYS2": "SYS2"}.get(strategy_name)
        if system is None:
            raise ValueError("STRATEGY_OUT_OF_SCOPE")
        parameters = spec.get("parameters")
        if not isinstance(parameters, Mapping):
            raise ValueError("PARAMETERS_REQUIRED")
        return StrategyConfig(
            primary_system=system,
            output_contract="SIGNAL_EVENT",
            enabled_timeframes=("M1",),
            m30_enabled=False,
            entry_lookback=int(str(parameters["entry_lookback"])),
            exit_lookback=int(str(parameters["exit_lookback"])),
        )

    def _simulate_complete(self, bars: list[_Bar], spec: Mapping[str, Any]) -> tuple[JsonObject, list[JsonObject]]:
        temporary = _Run(run_id="WF", spec=dict(spec), total=len(bars), state=self._initial_state(spec))
        temporary.provenance = self._provenance(spec, bars, {"status": "NOT_RUN_FOR_WINDOW"})
        for index in range(len(bars)):
            self._step_run(
                temporary,
                bars,
                index,
                int(spec["parameters"]["entry_lookback"]),
                int(spec["parameters"]["exit_lookback"]),
            )
        state = temporary.state
        final_equity = _decimal(state["last_equity"], "last_equity")
        initial = _decimal(spec["parameters"]["initial_balance"], "initial_balance")
        closed = [Decimal(value) for value in state["closed_pnl"]]
        metrics = {
            "total_pnl": _money(final_equity - initial),
            "maximum_drawdown": _money(Decimal(state["max_drawdown"])),
            "win_rate": _money(
                Decimal(sum(value > 0 for value in closed)) / Decimal(len(closed)) * Decimal("100")
                if closed
                else Decimal("0")
            ),
            "trade_count": int(state["fill_count"]),
            "ending_balance": _money(final_equity),
            "period_start_utc": str(spec["start"]),
            "period_end_utc": str(spec["end"]),
        }
        return metrics, temporary.rows

    def _core_validation(self, bars: list[_Bar], spec: Mapping[str, Any], run_id: str) -> JsonObject:
        probe = bars[: min(len(bars), 5_000)]
        events = tuple(
            MarketEvent(
                event_id=f"{run_id}-event-{index}",
                run_id=run_id,
                instrument_id=str(spec["symbol"]),
                event_time_utc=bar.timestamp,
                received_at_utc=bar.timestamp,
                exchange_time_local=None,
                bar_close_time=bar.timestamp + timedelta(minutes=1),
                event_kind="BAR_1M",
                values={
                    "open": _money(bar.opened),
                    "high": _money(bar.high),
                    "low": _money(bar.low),
                    "close": _money(bar.close),
                    "volume": _money(bar.volume),
                },
                quality_flags=(),
                data_version="P5-09-local-quality-pass-readonly",
            )
            for index, bar in enumerate(probe)
        )
        if not events:
            raise ValueError("DATA_EMPTY")
        data_identity = canonical_hash(
            {
                "run_id": run_id,
                "symbol": spec["symbol"],
                "first": _iso(probe[0].timestamp),
                "last": _iso(probe[-1].timestamp),
                "count": len(probe),
            }
        )
        strategy = self._strategy_config(spec)
        manifest = ExperimentManifest(
            run_id=run_id,
            raw_input_sha256=data_identity,
            normalized_input_sha256=data_identity,
            market_event_sequence_sha256=data_identity,
            data_version="P5-09-local-quality-pass-readonly",
            catalog_version="P5-09",
            catalog_sha256=data_identity,
            calendar_version="CRYPTO_24_7_UTC",
            calendar_sha256=data_identity,
            timeframe_rule_version="P5R-1M-V1",
            ordering_rule_version="UTC-TIME-V1",
            strategy_config_sha256=canonical_hash(vars(strategy)),
            code_revision="P5R-local",
            quality_policy_version="P5-QUALITY-PASS-WITH-OPEN-UNKNOWN",
            quality_report_sha256="P5-09-quality-report",
            split_plan_sha256="P5-09-period-split",
            cost_profile_sha256=data_identity,
            adapter_version="P5R-LOCAL-READONLY",
            adapter_artifact_sha256="P5R-LOCAL-READONLY",
            engine_identity=EngineIdentity(),
            fixture_manifest_sha256=data_identity,
            input_sha256=data_identity,
            session_anchor_utc=probe[0].timestamp,
            calendar_case="normal",
        )
        data_manifest = DataVersionManifest(
            data_version=manifest.data_version,
            raw_sha256s=(data_identity,),
            normalization_rule_version="P5R-1M-READONLY",
            catalog_version=manifest.catalog_version,
            catalog_sha256=data_identity,
            quality_report_sha256=manifest.quality_report_sha256,
            normalized_content_sha256=data_identity,
            source_mode="fixture_only",
        )
        replay = ReplayInput(
            events,
            data_manifest,
            DataGateDecision(
                data_version=manifest.data_version,
                quality_report_sha256=manifest.quality_report_sha256,
                policy_version=manifest.quality_policy_version,
            ),
            events[-1].bar_close_time,
            None,
        )
        result = BacktestRunner().run(
            BacktestRunRequest(
                run_id=run_id,
                replay=replay,
                manifest=manifest,
                strategy_config=strategy,
                engine_identity=EngineIdentity(),
                initial_strategy_state=StrategyState(run_id=run_id),
            )
        )
        if result.status != "COMMITTED":
            reason = result.failure.reason if result.failure else "CORE_VALIDATION_STOPPED"
            raise ValueError(f"CORE_VALIDATION_{reason}")
        return {
            "status": "PASS",
            "runner": "BacktestRunner",
            "probe_bar_count": len(probe),
            "signal_count": result.signal_count,
            "fill_count": result.fill_count,
            "selected_system": strategy.primary_system,
            "entry_lookback": strategy.entry_lookback,
            "exit_lookback": strategy.exit_lookback,
            "signal_source": "autotrade.strategy.service.process_closed_bars",
            "state": "validated",
        }

    def _provenance(self, spec: Mapping[str, Any], bars: list[_Bar], core: Mapping[str, Any]) -> JsonObject:
        return {
            "source_mode": "P5_LOCAL_READ_ONLY",
            "source_path": (
                "E:/strategy_test_data/autotrade/historical/spot/klines/1m/"
                "<symbol>/<yyyy-mm>/<symbol>-1m-<yyyy-mm>.csv.gz"
            ),
            "fixture_scope": "BTCUSDT/ETHUSDT Spot 1m UTC CRYPTO_24_7_UTC",
            "bar_count": len(bars),
            "period_start_utc": _iso(bars[0].timestamp),
            "period_end_utc": _iso(bars[-1].timestamp),
            "core_validation": dict(core),
            "cost_assumption": "ASSUMPTION_NOT_MARKET_MEASURE",
            "fee_bps": str(spec["parameters"]["fee_bps"]),
            "slippage_bps": str(spec["parameters"]["slippage_bps"]),
            "profitability_claim": "NOT_EVALUATED",
        }

    def _publish_result(self, run: _Run) -> None:
        self._persist_run(run)
        result_publish_id = f"RESULT-OWNER-{run.run_id}"
        payload = {
            "run_id": run.run_id,
            "metrics": run.metrics,
            "rows": run.rows,
            "provenance": run.provenance,
            "result_publish_id": result_publish_id,
        }
        self._history_catalog.write_result(run.run_id, payload)

    def _execute_sweep(self, sweep_id: str, candidates: list[JsonObject]) -> None:
        with self._lock:
            sweep = self._sweeps[sweep_id]
        for candidate in candidates:
            if sweep.cancel_event.is_set():
                return
            spec = dict(sweep.base_spec)
            base_parameters = dict(spec.get("parameters", {}))
            base_parameters.update({key: str(value) for key, value in candidate.items()})
            spec["parameters"] = base_parameters
            if "force_fail" in candidate:
                spec["force_fail"] = bool(candidate["force_fail"])
            try:
                child = self.create_run(spec, kind="SWEEP_CHILD", parent_id=sweep_id)
            except ValueError:
                continue
            with self._lock:
                sweep.children.append(str(child["run_id"]))
            while True:
                if sweep.cancel_event.is_set():
                    self.cancel_run(str(child["run_id"]), "SWEEP_CANCELLED")
                    return
                view = self.get_run(str(child["run_id"]))
                if view["status"] in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                    break
                time.sleep(0.01)
        with self._lock:
            children = [self._run_view(self._runs[run_id]) for run_id in sweep.children]
            sweep.status = (
                "PARTIAL_FAILED" if any(child["status"] != "SUCCEEDED" for child in children) else "SUCCEEDED"
            )

    def _execute_csv(self, job_id: str) -> None:
        with self._lock:
            job = self._csv_jobs[job_id]
            run = self._runs[job.run_id]
            rows = list(run.rows)
        try:
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=list(job.columns), extrasaction="ignore", lineterminator="\n")
            writer.writeheader()
            total = max(len(rows), 1)
            for index, row in enumerate(rows):
                writer.writerow({column: row.get(column, "") for column in job.columns})
                with self._lock:
                    job.progress = int((index + 1) / total * 100)
                if index % 100 == 0:
                    time.sleep(0.001)
            content = stream.getvalue()
            directory = self.runtime_root / "exports" / job_id
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "result.csv").write_text(content, encoding="utf-8", newline="")
            with self._lock:
                job.content = content
                job.progress = 100
                job.status = "SUCCEEDED"
        except (OSError, csv.Error) as error:
            with self._lock:
                job.status = "FAILED"
                job.failure = {"code": "CSV_WRITE_FAILED", "message": str(error)}

    def _load_bars(self, symbol: str, start: datetime, end: datetime) -> list[_Bar]:
        if symbol not in ALLOWED_SYMBOLS:
            raise ValueError("SYMBOL_OUT_OF_SCOPE")
        bars: list[_Bar] = []
        cursor = datetime(start.year, start.month, 1, tzinfo=UTC)
        while cursor < end:
            month = f"{cursor.year:04d}-{cursor.month:02d}"
            candidates = [
                self.data_root / f"{symbol}.csv",
                self.data_root / symbol / f"{symbol}-1m-{month}.csv.gz",
                self.data_root / symbol / month / f"{symbol}-1m-{month}.csv.gz",
                self.data_root / symbol / month / f"{symbol}-1m-{month}.csv",
            ]
            existing = next((path for path in candidates if path.is_file()), None)
            if existing is not None:
                opener: Any = gzip.open if existing.suffix == ".gz" else open
                with opener(existing, "rt", encoding="utf-8", newline="") as handle:
                    for raw in csv.DictReader(handle):
                        timestamp_value = raw.get("bar_start_utc") or raw.get("open_time_utc") or raw.get("open_time")
                        if timestamp_value is None:
                            continue
                        timestamp = _utc(timestamp_value)
                        if timestamp < start or timestamp >= end:
                            continue
                        try:
                            bar = _Bar(
                                timestamp=timestamp,
                                opened=_decimal(raw.get("open"), "open"),
                                high=_decimal(raw.get("high"), "high"),
                                low=_decimal(raw.get("low"), "low"),
                                close=_decimal(raw.get("close"), "close"),
                                volume=_decimal(raw.get("volume", "0"), "volume"),
                                symbol=symbol,
                            )
                        except ValueError:
                            raise ValueError("DATA_OHLCV_INVALID") from None
                        if (
                            bar.low > min(bar.opened, bar.close)
                            or bar.high < max(bar.opened, bar.close)
                            or bar.low > bar.high
                        ):
                            raise ValueError("DATA_OHLCV_INVALID")
                        bars.append(bar)
            next_month = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
            cursor = next_month
        bars.sort(key=lambda item: item.timestamp)
        if len({bar.timestamp for bar in bars}) != len(bars):
            raise ValueError("DATA_DUPLICATE_TIMESTAMP")
        if len(bars) > MAX_BARS:
            raise ValueError("DATA_RANGE_TOO_LARGE")
        return bars

    def _run_view(self, run: _Run) -> JsonObject:
        return {
            "run_id": run.run_id,
            "kind": run.kind,
            "parent_id": run.parent_id,
            "status": run.status,
            "progress": run.progress,
            "total": run.total,
            "progress_percent": int(run.progress / run.total * 100) if run.total else 0,
            "started_at": run.started_at,
            "ended_at": run.ended_at,
            "eta": self._eta(run),
            "spec": dict(run.spec),
            "metrics": dict(run.metrics) if run.metrics else None,
            "provenance": dict(run.provenance),
            "failure": dict(run.failure) if run.failure else None,
            "checkpoint": dict(run.checkpoint) if run.checkpoint else None,
            "resume_count": run.resume_count,
            "recovery_mode": run.recovery_mode,
            "operation_revision": run.operation_revision,
            "result_reference": f"results/{run.run_id}/result.json" if run.status == "SUCCEEDED" else None,
            "result_publish_id": f"RESULT-OWNER-{run.run_id}" if run.status == "SUCCEEDED" else None,
        }

    @staticmethod
    def _eta(run: _Run) -> str:
        if run.status == "SUCCEEDED":
            return "完了"
        if run.progress <= 0 or run.total <= 0:
            return "計算中"
        remaining = max(run.total - run.progress, 0)
        return f"約{remaining} Bar"
