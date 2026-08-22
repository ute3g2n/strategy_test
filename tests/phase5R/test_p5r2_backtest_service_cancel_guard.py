"""P5R2-15 integration checks for the server-owned local Run cancel path."""

from __future__ import annotations

import csv
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from autotrade.application.backtest_product import BacktestProductService


def _write_fixture(root: Path, count: int = 5000) -> None:
    root.mkdir(parents=True, exist_ok=True)
    start = datetime(2025, 2, 24, tzinfo=UTC)
    with (root / "BTCUSDT.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["symbol", "bar_start_utc", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        for index in range(count):
            price = 100 + (index % 40) * 0.2 + (index // 40) * 0.8
            writer.writerow(
                {
                    "symbol": "BTCUSDT",
                    "bar_start_utc": (start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"),
                    "open": f"{price:.4f}",
                    "high": f"{price + 0.5:.4f}",
                    "low": f"{price - 0.5:.4f}",
                    "close": f"{price + 0.25:.4f}",
                    "volume": "10",
                }
            )


def _spec() -> dict[str, object]:
    return {
        "symbol": "BTCUSDT",
        "market": "SPOT",
        "timeframe": "1m",
        "timezone": "UTC",
        "calendar": "CRYPTO_24_7_UTC",
        "start": "2025-02-24T00:00:00Z",
        "end": "2025-02-27T00:00:00Z",
        "strategy": "TURTLE_SYS1",
        "parameters": {
            "entry_lookback": "8",
            "exit_lookback": "4",
            "initial_balance": "100000",
            "fee_bps": "1.0",
            "slippage_bps": "2.0",
        },
    }


def test_service_cancel_uses_server_state_and_rejects_second_tab(tmp_path: Path) -> None:
    _write_fixture(tmp_path / "data")
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")
    created = service.create_run(_spec())
    run_id = str(created["run_id"])

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        state = str(service.get_run(run_id)["status"])
        if state == "RUNNING":
            break
        if state in {"SUCCEEDED", "FAILED", "CANCELLED"}:
            raise AssertionError(f"run finished before cancel guard test: {state}")
        time.sleep(0.005)
    else:
        raise AssertionError(f"run did not reach RUNNING: {service.get_run(run_id)}")

    first = service.request_run_cancel(
        {
            "run_id": run_id,
            "operation_token": "service-cancel-token-1",
            "request_id": "service-cancel-request-1",
            "actor": "local-operator",
            "origin_screen": "PROGRESS",
            "reason": "operator requested cancel",
            "current_state": "SUCCEEDED",
            "current_revision": 999,
            "expected_revision": 999,
        }
    )
    second = service.request_run_cancel(
        {
            "run_id": run_id,
            "operation_token": "service-cancel-token-2",
            "request_id": "service-cancel-request-2",
            "actor": "local-operator",
            "origin_screen": "RESULT_SUMMARY",
            "reason": "second tab replay",
            "current_state": "QUEUED",
            "current_revision": 0,
            "expected_revision": 0,
        }
    )

    first_operation = first["operation"]
    second_operation = second["operation"]
    assert first_operation["accepted"] is True
    assert first_operation["status_before"] == "RUNNING"
    assert first_operation["status_after"] == "STOP_REQUESTED"
    assert second_operation["accepted"] is False
    assert second_operation["error_code"] == "OPERATION_IN_FLIGHT"
    assert second_operation["status_after"] == "STOP_REQUESTED"
