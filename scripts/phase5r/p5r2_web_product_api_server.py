"""Fixed local fixture server for the P5R2-19 Web Product journey.

It seeds a small, server-owned LOCAL_FAKE 1m Catalog source so browser tests
can exercise the real P5R2 adapter without receiving OHLCV bars or contacting
an external provider.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from http.server import ThreadingHTTPServer  # noqa: E402

from autotrade.application.backtest_product import BacktestProductService  # noqa: E402
from autotrade.application.http_server import _Handler  # noqa: E402


def _bar(timestamp: datetime, close: str) -> dict[str, str]:
    return {
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": "1.00",
    }


def _source_dataset() -> dict[str, object]:
    start = datetime(2025, 2, 24, tzinfo=UTC)
    bars = [_bar(start + timedelta(minutes=index), f"100.{index:02d}") for index in range(181)]
    return {
        "dataset_id": "P5R2-19-SOURCE-BTCUSDT-1m",
        "identity": {
            "provider": "LOCAL_FAKE",
            "market": "SPOT",
            "symbol": "BTCUSDT",
            "source_timeframe": "1m",
            "schema": "ohlcv-v1",
        },
        "coverage": {"start": "2025-02-24T00:00:00Z", "end": "2025-02-24T03:00:00Z"},
        "quality": "USABLE",
        "usable": True,
        "legacy": False,
        "state": "CURRENT",
        "promotion_state": "PROMOTED",
        "bar_count": len(bars),
        "bars": bars,
        "provenance": {"source_job_id": "P5R2-19-FIXTURE-SOURCE", "source_mode": "LOCAL_FAKE"},
    }


def _seed_source(service: BacktestProductService) -> None:
    source = _source_dataset()
    catalog = service._history_catalog
    if any(item.get("dataset_id") == source["dataset_id"] for item in catalog.catalog_snapshot()):
        return
    source_job = service.create_timeframe_generation_job(
        {
            "source_dataset_id": source["dataset_id"],
            "symbol": "BTCUSDT",
            "timeframes": ["15m"],
            "requested_range": {"start": "2025-02-24T00:00:00Z", "end": "2025-02-24T01:00:00Z"},
            "request_id": "p5r2-19-fixture-source-job",
            "reason": "P5R2-19 fixed local Web Product fixture",
            "retry_of": None,
            "external_io_allowed": False,
            "source_dataset": source,
        }
    )
    if source_job.get("state") != "STAGED":
        raise RuntimeError("P5R2_19_FIXTURE_SOURCE_JOB_FAILED")
    request: dict[str, object] = {
        "identity": source["identity"],
        "existing_bars": [],
        "incoming_bars": source["bars"],
        "dataset_id": source["dataset_id"],
        "expected_revision": 0,
        "impact_confirmed": True,
        "provenance": {"source_job_id": source_job["job_id"], "source_mode": "LOCAL_FAKE"},
        "request_id": "p5r2-19-fixture-source-catalog",
        "staging_id": "p5r2-19-fixture-source-staging",
        "staging_state": "STAGED",
        "promotion_state": "VALIDATING",
        "quality": "PENDING_CATALOG_VALIDATION",
        "usable": False,
        "source_job": source_job,
    }
    request.update(catalog.stage_local_dataset(request))
    preview = catalog.preview_merge(request)
    request["preview_token"] = preview["operation_token"]
    promoted = catalog.promote_merge(request)
    if promoted.get("state") != "PROMOTED":
        raise RuntimeError("P5R2_19_FIXTURE_SOURCE_PROMOTION_FAILED")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        raise ValueError("LOOPBACK_ONLY")
    runtime_root = args.runtime_root or Path(tempfile.mkdtemp(prefix="autotrade-p5r2-19-runtime-"))
    data_root = args.data_root or runtime_root / "data"
    service = BacktestProductService(data_root=data_root, runtime_root=runtime_root)
    _seed_source(service)
    _Handler.service = service
    server = ThreadingHTTPServer((args.host, args.port), _Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
