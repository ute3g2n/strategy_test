"""HTTP route contracts for the local Backtest application API."""

from __future__ import annotations

import threading
from http.server import ThreadingHTTPServer
from urllib.request import urlopen

from autotrade.application.http_server import _Handler


class _CsvOnlyService:
    def download_csv(self, job_id: str) -> str:
        return f"row_kind,equity\nBALANCE,{job_id}\n"


def test_csv_download_route_returns_the_generated_csv() -> None:
    original_service = _Handler.service
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    _Handler.service = _CsvOnlyService()
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with urlopen(
            f"http://127.0.0.1:{server.server_port}/api/backtest/csv-jobs/CSV-AUTOTRADE-TEST/download",
            timeout=5,
        ) as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("text/csv")
            assert response.read().decode("utf-8") == "row_kind,equity\nBALANCE,CSV-AUTOTRADE-TEST\n"
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
        _Handler.service = original_service
