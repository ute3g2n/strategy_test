"""P5R RED contracts for the real local Backtest product boundary."""

from __future__ import annotations

import csv
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from autotrade.application.backtest_product import BacktestProductService


def _write_fixture(root: Path, symbol: str = "BTCUSDT", count: int = 180) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{symbol}.csv"
    start = datetime(2025, 2, 24, tzinfo=UTC)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["symbol", "bar_start_utc", "open", "high", "low", "close", "volume"]
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
    return path


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


def test_preflight_rejects_out_of_scope_and_non_utc(tmp_path: Path) -> None:
    service = _service(tmp_path)
    assert service.preflight(_spec(symbol="MCL"))["status"] == "STOPPED"
    assert service.preflight(_spec(start="2025-02-24T00:00:00", end="2025-02-24T02:00:00Z"))["status"] == "STOPPED"


def test_single_run_returns_real_metrics_and_ledger_provenance(tmp_path: Path) -> None:
    service = _service(tmp_path)
    created = service.create_run(_spec())
    view = _wait(service, str(created["run_id"]))
    assert view["status"] == "SUCCEEDED"
    metrics = view["metrics"]
    assert set(metrics) >= {"total_pnl", "maximum_drawdown", "win_rate", "trade_count", "ending_balance"}
    assert metrics["period_start_utc"] != "UNKNOWN"
    assert metrics["period_end_utc"] != "UNKNOWN"
    rows = service.get_rows(str(created["run_id"]))
    assert {row["row_kind"] for row in rows} >= {"SIGNAL", "VIRTUAL_FILL", "BALANCE"}
    assert view["provenance"]["source_mode"] == "P5_LOCAL_READ_ONLY"
    assert view["provenance"]["cost_assumption"] == "ASSUMPTION_NOT_MARKET_MEASURE"


def test_cancel_then_resume_uses_checkpoint_state(tmp_path: Path) -> None:
    service = _service(tmp_path)
    created = service.create_run(_spec(end="2025-02-24T02:30:00Z"))
    run_id = str(created["run_id"])
    service.cancel_run(run_id, "USER_REQUESTED")
    cancelled = _wait(service, run_id)
    assert cancelled["status"] == "CANCELLED"
    assert cancelled["checkpoint"] is not None
    service.resume_run(run_id)
    resumed = _wait(service, run_id)
    assert resumed["status"] == "SUCCEEDED"
    assert resumed["resume_count"] == 1


def test_sweep_rejects_duplicates_and_keeps_partial_failure(tmp_path: Path) -> None:
    service = _service(tmp_path)
    with pytest.raises(ValueError, match="SWEEP_DUPLICATE"):
        service.create_sweep(_spec(), [{"entry_lookback": "8"}, {"entry_lookback": "8"}])
    created = service.create_sweep(_spec(), [{"entry_lookback": "8"}, {"entry_lookback": "9", "force_fail": True}])
    view = service.wait_for_sweep(str(created["sweep_id"]))
    assert view["status"] == "PARTIAL_FAILED"
    assert {child["status"] for child in view["children"]} == {"SUCCEEDED", "FAILED"}


def test_history_compare_csv_holdout_and_walk_forward(tmp_path: Path) -> None:
    service = _service(tmp_path)
    first = service.create_run(_spec())
    second = service.create_run(_spec(strategy="TURTLE_SYS2"))
    _wait(service, str(first["run_id"]))
    _wait(service, str(second["run_id"]))
    assert service.compare_runs(str(first["run_id"]), str(second["run_id"]))["comparable"] is False
    job = service.create_csv_job(str(first["run_id"]), ["row_kind", "decision_time_utc", "equity"])
    assert service.wait_for_csv(str(job["job_id"]))["status"] == "SUCCEEDED"
    assert service.holdout("EARLY_ADJUSTMENT")["status"] == "STOPPED"
    assert service.holdout("FINALIZED")["status"] == "SUCCEEDED"
    windows = [
        {
            "id": "W1",
            "train_start": "2025-02-24T00:00:00Z",
            "train_end": "2025-02-24T01:00:00Z",
            "validation_end": "2025-02-24T01:30:00Z",
            "evaluation_end": "2025-02-24T02:00:00Z",
        },
        {
            "id": "W2",
            "train_start": "2025-02-24T00:30:00Z",
            "train_end": "2025-02-24T01:30:00Z",
            "validation_end": "2025-02-24T02:00:00Z",
            "evaluation_end": "2025-02-24T02:30:00Z",
        },
    ]
    result = service.walk_forward(windows)
    assert result["status"] == "SUCCEEDED"
    assert len(result["windows"]) == 2
    with pytest.raises(ValueError, match="WALK_FORWARD_OVERLAP"):
        service.walk_forward([windows[0], {**windows[1], "validation_end": "2025-02-24T01:45:00Z"}])


def test_result_and_csv_artifacts_use_application_scoped_names_and_directories(tmp_path: Path) -> None:
    service = _service(tmp_path)
    created = service.create_run(_spec())
    run_id = str(created["run_id"])
    view = _wait(service, run_id)
    assert view["status"] == "SUCCEEDED"
    assert run_id.startswith("RUN-AUTOTRADE-")
    assert "P5R" not in run_id
    assert (tmp_path / "runtime" / "results" / run_id / "result.json").is_file()

    job = service.create_csv_job(run_id, ["row_kind", "equity"])
    job_id = str(job["job_id"])
    assert service.wait_for_csv(job_id)["status"] == "SUCCEEDED"
    assert job_id.startswith("CSV-AUTOTRADE-")
    assert "P5R" not in job_id
    assert (tmp_path / "runtime" / "exports" / job_id / "result.csv").is_file()


def test_selected_turtle_system_is_executed_by_strategy_core(tmp_path: Path) -> None:
    service = _service(tmp_path)
    sys1 = service.create_run(_spec(strategy="TURTLE_SYS1"))
    sys2 = service.create_run(_spec(strategy="TURTLE_SYS2"))
    first = _wait(service, str(sys1["run_id"]))
    second = _wait(service, str(sys2["run_id"]))
    first_core = first["provenance"]["core_validation"]
    second_core = second["provenance"]["core_validation"]
    assert first_core["selected_system"] == "SYS1"
    assert second_core["selected_system"] == "SYS2"
    assert first_core["signal_source"] == "autotrade.strategy.service.process_closed_bars"
    assert second_core["signal_source"] == "autotrade.strategy.service.process_closed_bars"
    first_reasons = {row["reason"] for row in service.get_rows(str(sys1["run_id"])) if row["row_kind"] == "SIGNAL"}
    second_reasons = {row["reason"] for row in service.get_rows(str(sys2["run_id"])) if row["row_kind"] == "SIGNAL"}
    assert any(str(reason).startswith("SYS1_") for reason in first_reasons)
    assert not any(str(reason).startswith("SYS1_") for reason in second_reasons)
