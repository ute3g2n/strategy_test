"""Local-only HTTP adapter for the P5R Application API."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlparse

from .backtest_product import BacktestProductService

MAX_JSON_BODY_BYTES = 1_000_000
ALLOWED_UI_ORIGIN = "http://127.0.0.1:4173"


class _Handler(BaseHTTPRequestHandler):
    service = BacktestProductService()

    def _send(self, status: int, payload: Any, *, content_type: str = "application/json; charset=utf-8") -> None:
        if content_type.startswith("application/json"):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        else:
            body = str(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", ALLOWED_UI_ORIGIN)
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: int, code: str, message: str | None = None) -> None:
        self._send(status, {"ok": False, "error": {"code": code, "message": message or code}})

    def _body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            raise ValueError("JSON_BODY_INVALID") from None
        if length < 0 or length > MAX_JSON_BODY_BYTES:
            raise ValueError("JSON_BODY_TOO_LARGE")
        try:
            decoded = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("JSON_BODY_INVALID") from None
        if not isinstance(decoded, dict):
            raise ValueError("JSON_OBJECT_REQUIRED")
        return decoded

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, "", content_type="text/plain")

    def do_GET(self) -> None:  # noqa: N802
        path = [unquote(part) for part in urlparse(self.path).path.split("/") if part]
        try:
            if path == ["health"]:
                self._send(200, {"status": "ok", "external_io": "disabled"})
            elif path == ["api", "capabilities"]:
                self._send(
                    200,
                    {
                        "contract_version": "P5R-APPLICATION-API-V1",
                        "backtest": "SUPPORTED_LOCAL_P5_READ_ONLY",
                        "paper": "OUT_OF_SCOPE",
                        "live": "OUT_OF_SCOPE",
                    },
                )
            elif path == ["api", "p5r2", "catalog"]:
                self._send(
                    200,
                    {
                        "items": self.service.catalog_snapshot(),
                        "available_items": self.service.available_catalog(),
                        "strategy_timeframes": ["15m", "30m", "1h", "4h", "1d"],
                        "source_timeframe": "1m",
                    },
                )
            elif len(path) == 4 and path[:3] == ["api", "p5r2", "timeframe-generation-jobs"]:
                self._send(200, self.service.get_timeframe_generation_job(path[3]))
            elif path == ["api", "backtest", "runs"]:
                self._send(200, {"items": self.service.list_runs()})
            elif path == ["api", "backtest", "runs", "history"]:
                self._send(200, {"items": self.service.list_runs()})
            elif path == ["api", "backtest", "recovery"]:
                self._send(200, self.service.recovery_report())
            elif len(path) == 4 and path[:3] == ["api", "backtest", "runs"]:
                self._send(200, self.service.get_run(path[3]))
            elif len(path) == 5 and path[:3] == ["api", "backtest", "runs"] and path[4] == "rows":
                self._send(200, {"items": self.service.get_rows(path[3])})
            elif len(path) == 4 and path[:3] == ["api", "backtest", "sweeps"]:
                self._send(200, self.service.get_sweep(path[3]))
            elif len(path) == 5 and path[:3] == ["api", "backtest", "csv-jobs"] and path[4] == "download":
                self._send(200, self.service.download_csv(path[3]), content_type="text/csv; charset=utf-8")
            elif len(path) == 4 and path[:3] == ["api", "backtest", "csv-jobs"]:
                self._send(200, self.service.get_csv_job(path[3]))
            else:
                self._error(404, "NOT_FOUND")
        except KeyError as error:
            self._error(404, str(error).strip("'"))
        except ValueError as error:
            self._error(409, str(error))

    def do_POST(self) -> None:  # noqa: N802
        path = [unquote(part) for part in urlparse(self.path).path.split("/") if part]
        try:
            body = self._body()
            if path == ["api", "p5r2", "backtest", "preflight"]:
                result = self.service.p5r2_preflight(body.get("spec", body))
                self._send(200 if result["status"] == "PASS" else 422, result)
            elif path == ["api", "p5r2", "backtest", "runs"]:
                result = self.service.p5r2_preflight(body.get("spec", body))
                if result["status"] != "PASS":
                    self._send(422, result)
                else:
                    self._send(201, self.service.create_run(body.get("spec", body)))
            elif path == ["api", "p5r2", "historical-download-jobs"]:
                result = self.service.create_historical_download_job(body)
                self._send(409, result)
            elif path == ["api", "p5r2", "timeframe-generation-jobs"]:
                result = self.service.create_timeframe_generation_job(body)
                self._send(201 if result.get("state") == "STAGED" else 422, result)
            elif len(path) == 5 and path[:3] == ["api", "p5r2", "timeframe-generation-jobs"]:
                snapshot = dict(body)
                snapshot.setdefault("job_id", path[3])
                if path[4] == "advance":
                    result = self.service.advance_timeframe_generation_job(
                        snapshot, str(body.get("target_state", "RUNNING"))
                    )
                elif path[4] == "cancel":
                    result = self.service.cancel_timeframe_generation_job(snapshot)
                elif path[4] == "restart":
                    result = self.service.restart_timeframe_generation_job(snapshot)
                elif path[4] == "retry":
                    result = self.service.retry_timeframe_generation_job(snapshot)
                else:
                    self._error(404, "NOT_FOUND")
                    return
                self._send(200 if result.get("state") != "REJECTED" else 409, result)
            elif path == ["api", "p5r2", "result-artifacts", "delete"]:
                result = self.service.delete_result_artifact(body)
                self._send(200 if result.get("accepted") is True else 409, result)
            elif path == ["api", "backtest", "preflight"]:
                result = self.service.preflight(body.get("spec", body))
                self._send(200 if result["status"] == "PASS" else 422, result)
            elif path == ["api", "backtest", "runs"]:
                self._send(201, self.service.create_run(body.get("spec", body)))
            elif len(path) == 5 and path[:3] == ["api", "backtest", "runs"] and path[4] == "cancel":
                cancel_request = dict(body)
                cancel_request["run_id"] = path[3]
                cancel_request.setdefault("operation_token", f"http-cancel-{path[3]}")
                cancel_request.setdefault("request_id", f"http-cancel-request-{path[3]}")
                operation_result = self.service.request_run_cancel(cancel_request)
                run_view = operation_result.get("run")
                operation = operation_result.get("operation")
                if not isinstance(run_view, dict) or not isinstance(operation, dict):
                    raise RuntimeError("RUN_CANCEL_RESULT_INVALID")
                response = dict(run_view)
                response["operation"] = operation
                self._send(202, response)
            elif len(path) == 5 and path[:3] == ["api", "backtest", "runs"] and path[4] == "resume":
                self._send(202, self.service.resume_run(path[3]))
            elif path == ["api", "backtest", "sweeps"]:
                self._send(201, self.service.create_sweep(body.get("spec", {}), body.get("candidates", [])))
            elif len(path) == 5 and path[:3] == ["api", "backtest", "sweeps"] and path[4] == "cancel":
                self._send(202, self.service.cancel_sweep(path[3]))
            elif path == ["api", "backtest", "compare"]:
                self._send(200, self.service.compare_runs(str(body["left_run_id"]), str(body["right_run_id"])))
            elif path == ["api", "backtest", "csv-jobs"]:
                self._send(202, self.service.create_csv_job(str(body["run_id"]), body.get("columns", [])))
            elif path == ["api", "backtest", "holdout"]:
                result = self.service.holdout(str(body.get("phase", "")))
                self._send(200 if result["status"] == "SUCCEEDED" else 409, result)
            elif path == ["api", "backtest", "walk-forward"]:
                self._send(200, self.service.walk_forward(body.get("windows", [])))
            elif path == ["api", "backtest", "reset"]:
                self.service.reset_for_local_test()
                self._send(200, {"status": "RESET"})
            else:
                self._error(404, "NOT_FOUND")
        except KeyError as error:
            self._error(422, str(error).strip("'"))
        except ValueError as error:
            self._error(422, str(error))
        except (OSError, RuntimeError):
            self._error(500, "LOCAL_API_FAILURE")

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve the local API.  Binding is intentionally loopback-only by default."""

    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("LOOPBACK_ONLY")
    server = ThreadingHTTPServer((host, port), _Handler)
    server.serve_forever()
