"""P5R2-19 RED contracts for the local Web Product API adapter."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from autotrade.application.backtest_product import BacktestProductService
from autotrade.application.http_server import _Handler


def _bar(timestamp: datetime, close: str) -> dict[str, str]:
    value = timestamp.isoformat().replace("+00:00", "Z")
    return {
        "timestamp": value,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": "1.00",
    }


def _source_dataset() -> dict[str, object]:
    start = datetime(2025, 2, 24, tzinfo=UTC)
    bars = [_bar(start + timedelta(minutes=index), f"100.{index:02d}") for index in range(61)]
    return {
        "dataset_id": "fixture-source-1m",
        "identity": {
            "provider": "LOCAL_FAKE",
            "market": "SPOT",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "schema": "ohlcv-v1",
        },
        "coverage": {
            "start": "2025-02-24T00:00:00Z",
            "end": "2025-02-24T01:01:00Z",
        },
        "quality": "USABLE",
        "usable": True,
        "legacy": False,
        "state": "CURRENT",
        "promotion_state": "PROMOTED",
        "bar_count": len(bars),
        "bars": bars,
        "provenance": {"source_job_id": "fixture-job-001", "source_mode": "LOCAL_FAKE"},
    }


def _generation_request() -> dict[str, object]:
    return {
        "source_dataset_id": "fixture-source-1m",
        "symbol": "BTCUSDT",
        "timeframes": ["15m", "30m"],
        "requested_range": {
            "start": "2025-02-24T00:00:00Z",
            "end": "2025-02-24T01:00:00Z",
        },
        "request_id": "p5r2-ui-generation-001",
        "reason": "P5R2-19 local UI test",
        "retry_of": None,
        "external_io_allowed": False,
        "source_dataset": _source_dataset(),
    }


def _spec(timeframe: str = "15m") -> dict[str, object]:
    return {
        "symbol": "BTCUSDT",
        "market": "SPOT",
        "timeframe": timeframe,
        "timezone": "UTC",
        "calendar": "CRYPTO_24_7_UTC",
        "start": "2025-02-24T00:00:00Z",
        "end": "2025-02-24T01:00:00Z",
        "strategy": "TURTLE_SYS1",
        "parameters": {
            "entry_lookback": "8",
            "exit_lookback": "4",
            "initial_balance": "100000",
            "fee_bps": "1.0",
            "slippage_bps": "2.0",
        },
    }


def test_p5r2_preflight_reports_missing_derived_data_for_ui_dialog(tmp_path: Path) -> None:
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")

    result = service.p5r2_preflight(_spec("30m"))

    assert result["status"] == "STOPPED"
    assert result["failure"]["code"] == "DATA_INSUFFICIENT"
    assert result["data_requirement"] == {
        "symbol": "BTCUSDT",
        "timeframe": "30m",
        "requested_range": {
            "start": "2025-02-24T00:00:00Z",
            "end": "2025-02-24T01:00:00Z",
        },
        "source_timeframe": "1m",
    }


def test_p5r2_generation_and_catalog_are_exposed_as_local_service_contract(tmp_path: Path) -> None:
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")

    created = service.create_timeframe_generation_job(_generation_request())
    snapshot = service.get_timeframe_generation_job(str(created["job_id"]))

    assert created["state"] == "STAGED"
    assert snapshot["job_id"] == created["job_id"]
    assert snapshot["input"]["timeframes"] == ["15m", "30m"]
    assert service.catalog_snapshot() == []


def test_p5r2_external_download_is_blocked_without_host_level_isolation(tmp_path: Path) -> None:
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")

    result = service.create_historical_download_job(
        {
            "symbol": "BTCUSDT",
            "timeframes": ["1m"],
            "requested_range": {
                "start": "2025-02-24T00:00:00Z",
                "end": "2025-03-01T00:00:00Z",
            },
            "request_id": "p5r2-ui-download-001",
        }
    )

    assert result["state"] == "REJECTED"
    assert result["reason"] == "HOST_LEVEL_ISOLATION_NOT_VERIFIED"
    assert result["external_io_performed"] is False


def test_p5r2_delete_adapter_returns_delete_gate_without_physical_io(tmp_path: Path) -> None:
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")

    result = service.delete_result_artifact(
        {
            "logical_artifact_id": "RESULT-P5R2-UI-001",
            "artifact_kind": "RESULT",
            "run_state": "SUCCEEDED",
            "operation_token": "delete-token-ui-001",
            "request_id": "delete-request-ui-001",
            "confirmation": True,
        }
    )

    assert result["accepted"] is False
    assert result["error_code"] == "DELETE_GATE_REQUIRED"
    assert result["physical_io_performed"] is False


def test_p5r2_http_routes_expose_local_catalog_and_blocked_download(tmp_path: Path) -> None:
    service = BacktestProductService(data_root=tmp_path / "data", runtime_root=tmp_path / "runtime")
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    original_service = _Handler.service
    _Handler.service = service
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=2)
        connection.request("GET", "/api/p5r2/catalog")
        catalog_response = connection.getresponse()
        catalog = json.loads(catalog_response.read().decode("utf-8"))
        assert catalog_response.status == 200
        assert catalog["strategy_timeframes"] == ["15m", "30m", "1h", "4h", "1d"]
        assert catalog["source_timeframe"] == "1m"

        payload = json.dumps(
            {
                "symbol": "BTCUSDT",
                "timeframes": ["1m"],
                "requested_range": {
                    "start": "2025-02-24T00:00:00Z",
                    "end": "2025-03-01T00:00:00Z",
                },
                "request_id": "p5r2-http-download-001",
            }
        )
        connection.request(
            "POST",
            "/api/p5r2/historical-download-jobs",
            body=payload,
            headers={"Content-Type": "application/json"},
        )
        download_response = connection.getresponse()
        download = json.loads(download_response.read().decode("utf-8"))
        assert download_response.status == 409
        assert download["reason"] == "HOST_LEVEL_ISOLATION_NOT_VERIFIED"
        connection.close()
    finally:
        _Handler.service = original_service
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
