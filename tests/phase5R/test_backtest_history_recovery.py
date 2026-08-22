"""RED contracts for restart-safe Backtest history recovery.

These tests intentionally describe the user-visible contract before the
implementation exists.  They must fail against the pre-recovery service.
"""

from __future__ import annotations

import csv
import json
import threading
import time
from datetime import UTC, datetime, timedelta
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

from autotrade.application import storage_paths
from autotrade.application.backtest_product import BacktestProductService
from autotrade.application.http_server import _Handler


def _write_fixture(root: Path, symbol: str = "BTCUSDT", count: int = 180) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{symbol}.csv"
    start = datetime(2025, 2, 24, tzinfo=UTC)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["symbol", "bar_start_utc", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        for index in range(count):
            price = 100 + (index % 40) * 0.2 + (index // 40) * 0.8
            opened = start + timedelta(minutes=index)
            writer.writerow(
                {
                    "symbol": symbol,
                    "bar_start_utc": opened.isoformat().replace("+00:00", "Z"),
                    "open": f"{price:.4f}",
                    "high": f"{price + 0.5:.4f}",
                    "low": f"{price - 0.5:.4f}",
                    "close": f"{price + 0.25:.4f}",
                    "volume": "10",
                }
            )


def _spec(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "symbol": "BTCUSDT",
        "market": "SPOT",
        "timeframe": "1m",
        "timezone": "UTC",
        "calendar": "CRYPTO_24_7_UTC",
        "start": "2025-02-24T00:00:00Z",
        "end": "2025-02-24T02:30:00Z",
        "strategy": "TURTLE_SYS1",
        "parameters": {
            "entry_lookback": "8",
            "exit_lookback": "4",
            "initial_balance": "100000",
            "fee_bps": "1.0",
            "slippage_bps": "2.0",
        },
    }
    payload.update(overrides)
    return payload


def _service(tmp_path: Path) -> BacktestProductService:
    _write_fixture(tmp_path / "data")
    return BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")


def _wait(service: BacktestProductService, run_id: str, timeout: float = 5.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        view = service.get_run(run_id)
        if view["status"] in {"SUCCEEDED", "FAILED", "CANCELLED", "PARTIAL_FAILED"}:
            return view
        time.sleep(0.01)
    raise AssertionError(f"timed out: {service.get_run(run_id)}")


def _write_legacy_result(runtime_root: Path, run_id: str = "RUN-AUTOTRADE-LEGACY") -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "row_kind": "BALANCE",
            "decision_time_utc": "2025-02-24T00:00:00Z",
            "symbol": "BTCUSDT",
            "equity": "100000.0000",
        },
        {
            "row_kind": "SIGNAL",
            "decision_time_utc": "2025-02-24T00:01:00Z",
            "symbol": "BTCUSDT",
            "signal": "ENTER_LONG",
            "equity": "100000.0000",
        },
    ]
    result_dir = runtime_root / "results" / run_id
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "result.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "legacy_import": True,
                "metrics": {
                    "total_pnl": "0.0000",
                    "maximum_drawdown": "0.0000",
                    "win_rate": "0.0000",
                    "trade_count": 0,
                    "ending_balance": "100000.0000",
                },
                "rows": rows,
                "provenance": {
                    "source_mode": "P5_LOCAL_READ_ONLY",
                    "symbol": "BTCUSDT",
                    "period_start_utc": "2025-02-24T00:00:00Z",
                    "period_end_utc": "2025-02-24T02:30:00Z",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return rows


def test_new_service_restores_completed_run_detail_and_rows(tmp_path: Path) -> None:
    first_service = _service(tmp_path)
    created = first_service.create_run(_spec())
    run_id = str(created["run_id"])
    before_restart = _wait(first_service, run_id)
    rows_before_restart = first_service.get_rows(run_id)

    second_service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")
    restored = second_service.get_run(run_id)

    assert restored["status"] == "SUCCEEDED"
    assert restored["spec"] == before_restart["spec"]
    assert restored["metrics"] == before_restart["metrics"]
    assert second_service.get_rows(run_id) == rows_before_restart
    assert restored["recovery_mode"] == "NORMAL"
    assert (tmp_path / "runtime" / "catalog" / "runs" / f"{run_id}.json").is_file()


def test_legacy_result_is_restored_with_explicit_legacy_mode(tmp_path: Path) -> None:
    rows = _write_legacy_result(tmp_path / "runtime")
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")

    restored = service.get_run("RUN-AUTOTRADE-LEGACY")

    assert restored["status"] == "SUCCEEDED"
    assert restored["recovery_mode"] == "LEGACY_RESULT_ONLY"
    assert service.get_rows("RUN-AUTOTRADE-LEGACY") == rows
    assert restored["spec"]["symbol"] == "BTCUSDT"


def test_unowned_result_requires_recovery_instead_of_implicit_success(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    result_dir = runtime_root / "results" / "RUN-AUTOTRADE-ORPHAN"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "result.json").write_text(
        json.dumps({"run_id": "RUN-AUTOTRADE-ORPHAN", "metrics": {}, "rows": [], "provenance": {}}),
        encoding="utf-8",
    )

    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=runtime_root)

    restored = service.get_run("RUN-AUTOTRADE-ORPHAN")
    assert restored["status"] == "RECOVERY_REQUIRED"
    assert restored["failure"]["code"] == "ORPHAN_RESULT_UNOWNED"


def test_incomplete_after_restart_is_recovery_required_not_success(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    catalog_path = runtime_root / "catalog" / "runs" / "RUN-AUTOTRADE-RUNNING.json"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(
            {
                "schema": "autotrade-backtest-history/v1",
                "run_id": "RUN-AUTOTRADE-RUNNING",
                "kind": "SINGLE_BACKTEST",
                "status": "RUNNING",
                "progress": 7,
                "total": 100,
                "spec": _spec(),
                "recovery_mode": "NORMAL",
                "result_reference": None,
            }
        ),
        encoding="utf-8",
    )
    _write_fixture(tmp_path / "data")
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=runtime_root)

    restored = service.get_run("RUN-AUTOTRADE-RUNNING")
    report = service.recovery_report()

    assert restored["status"] == "RECOVERY_REQUIRED"
    assert restored["failure"]["code"] == "INCOMPLETE_AFTER_RESTART"
    assert any(item["run_id"] == "RUN-AUTOTRADE-RUNNING" for item in report["issues"])


def test_corrupt_and_mismatched_history_are_reported_without_hiding_other_runs(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    runs_root = runtime_root / "catalog" / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    (runs_root / "corrupt.json").write_text("{not-json", encoding="utf-8")
    (runs_root / "RUN-AUTOTRADE-MISMATCH.json").write_text(
        json.dumps(
            {
                "schema": "autotrade-backtest-history/v1",
                "run_id": "RUN-AUTOTRADE-MISMATCH",
                "status": "SUCCEEDED",
                "spec": _spec(),
                "result_reference": "results/RUN-AUTOTRADE-MISMATCH/result.json",
            }
        ),
        encoding="utf-8",
    )
    mismatch_result_dir = runtime_root / "results" / "RUN-AUTOTRADE-MISMATCH"
    mismatch_result_dir.mkdir(parents=True, exist_ok=True)
    (mismatch_result_dir / "result.json").write_text(
        json.dumps(
            {
                "run_id": "RUN-AUTOTRADE-OTHER",
                "metrics": {},
                "rows": [],
                "provenance": {},
            }
        ),
        encoding="utf-8",
    )
    _write_legacy_result(runtime_root, "RUN-AUTOTRADE-VALID-LEGACY")
    _write_fixture(tmp_path / "data")
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=runtime_root)

    report = service.recovery_report()
    run_ids = {item["run_id"] for item in service.list_runs()}
    issue_codes = {item["code"] for item in report["issues"]}

    assert "RUN-AUTOTRADE-VALID-LEGACY" in run_ids
    assert (
        "RUN-AUTOTRADE-MISMATCH" not in run_ids
        or service.get_run("RUN-AUTOTRADE-MISMATCH")["status"] == "RECOVERY_REQUIRED"
    )
    assert "CATALOG_JSON_INVALID" in issue_codes
    assert "RESULT_REFERENCE_MISMATCH" in issue_codes
    assert all(not Path(str(item["path"])).is_absolute() for item in report["issues"])


def test_catalog_path_is_application_scoped_and_never_phase_named() -> None:
    catalog_root = getattr(storage_paths, "BACKTEST_CATALOG_ROOT", None)
    assert catalog_root is not None
    assert catalog_root.drive.upper() == "E:"
    assert "phase5r" not in str(catalog_root).casefold()
    assert "temp" not in {part.casefold() for part in catalog_root.parts}


def test_recovery_report_is_available_from_local_http_api(tmp_path: Path) -> None:
    service = _service(tmp_path)
    previous_service = _Handler.service
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    _Handler.service = service
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=2)
        connection.request("GET", "/api/backtest/recovery")
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        _Handler.service = previous_service

    assert response.status == 200
    assert payload["status"] in {"CLEAN", "RECOVERY_REQUIRED"}
    assert "issues" in payload


def test_restored_run_supports_compare_csv_and_reset_keeps_disk_artifacts(tmp_path: Path) -> None:
    first_service = _service(tmp_path)
    first = first_service.create_run(_spec())
    second = first_service.create_run(_spec(strategy="TURTLE_SYS2"))
    _wait(first_service, str(first["run_id"]))
    _wait(first_service, str(second["run_id"]))
    first_id = str(first["run_id"])
    second_id = str(second["run_id"])

    restarted = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")
    comparison = restarted.compare_runs(first_id, second_id)
    job = restarted.create_csv_job(first_id, ["row_kind", "equity"])
    csv_view = restarted.wait_for_csv(str(job["job_id"]))
    csv_content = restarted.download_csv(str(job["job_id"]))
    restarted.reset_for_local_test()

    assert comparison["left_run_id"] == first_id
    assert comparison["right_run_id"] == second_id
    assert comparison["comparable"] is False
    assert csv_view["status"] == "SUCCEEDED"
    assert "row_kind,equity" in csv_content
    assert (tmp_path / "runtime" / "results" / first_id / "result.json").is_file()
    assert (tmp_path / "runtime" / "catalog" / "runs" / f"{first_id}.json").is_file()
