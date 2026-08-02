from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any


def check_databento_environment() -> dict[str, Any]:
    package_available = importlib.util.find_spec("databento") is not None
    api_key_available = bool(os.environ.get("DATABENTO_API_KEY"))
    return {
        "kind": "databento_environment_report",
        "research_only": True,
        "package": "databento",
        "package_available": package_available,
        "api_key_env": "DATABENTO_API_KEY",
        "api_key_available": api_key_available,
        "ready": package_available and api_key_available,
        "install_command": "pip install -U databento",
        "note": "This helper only creates research CSV inputs for P10 asset selection.",
    }


def fetch_databento_csv(
    symbols: list[str],
    start: str,
    end: str,
    output_dir: Path,
    dataset: str = "GLBX.MDP3",
    schema: str = "ohlcv-1m",
) -> dict[str, Any]:
    env_report = check_databento_environment()
    if not env_report["ready"]:
        return {
            "kind": "databento_fetch_report",
            "research_only": True,
            "status": "blocked_environment_not_ready",
            "environment": env_report,
            "requested_symbols": symbols,
        }

    import databento as db  # type: ignore[import-not-found]

    output_dir.mkdir(parents=True, exist_ok=True)
    client = db.Historical()
    outputs: list[dict[str, str]] = []

    for symbol in symbols:
        parent_symbol = _to_parent_symbol(symbol)
        data = client.timeseries.get_range(
            dataset=dataset,
            symbols=parent_symbol,
            schema=schema,
            stype_in="parent",
            start=start,
            end=end,
        )
        frame = data.to_df(price_type="float", pretty_ts=True, map_symbols=True)
        normalized = _normalize_ohlcv_frame(frame)
        path = output_dir / f"{symbol}.csv"
        normalized.to_csv(path, index=False)
        outputs.append({"symbol": symbol, "parent_symbol": parent_symbol, "path": str(path)})

    return {
        "kind": "databento_fetch_report",
        "research_only": True,
        "status": "completed",
        "dataset": dataset,
        "schema": schema,
        "start": start,
        "end": end,
        "outputs": outputs,
    }


def fetch_databento_metadata(
    symbols: list[str],
    start: str,
    end: str,
    output_dir: Path,
    dataset: str = "GLBX.MDP3",
    schemas: list[str] | None = None,
) -> dict[str, Any]:
    env_report = check_databento_environment()
    if not env_report["ready"]:
        return {
            "kind": "databento_metadata_fetch_report",
            "research_only": True,
            "status": "blocked_environment_not_ready",
            "environment": env_report,
            "requested_symbols": symbols,
        }

    import databento as db  # type: ignore[import-not-found]

    output_dir.mkdir(parents=True, exist_ok=True)
    client = db.Historical()
    outputs: list[dict[str, str]] = []
    target_schemas = schemas or ["definition", "statistics"]
    for schema in target_schemas:
        schema_dir = output_dir / schema
        schema_dir.mkdir(parents=True, exist_ok=True)
        for symbol in symbols:
            parent_symbol = _to_parent_symbol(symbol)
            data = client.timeseries.get_range(
                dataset=dataset,
                symbols=parent_symbol,
                schema=schema,
                stype_in="parent",
                start=start,
                end=end,
            )
            frame = data.to_df(price_type="float", pretty_ts=True, map_symbols=True)
            path = schema_dir / f"{symbol}_{schema}.csv"
            frame.reset_index().to_csv(path, index=False)
            outputs.append({"symbol": symbol, "schema": schema, "path": str(path)})

    return {
        "kind": "databento_metadata_fetch_report",
        "research_only": True,
        "status": "completed",
        "dataset": dataset,
        "start": start,
        "end": end,
        "outputs": outputs,
    }


def _to_parent_symbol(symbol: str) -> str:
    if symbol.endswith(".FUT"):
        return symbol
    return f"{symbol}.FUT"


def _normalize_ohlcv_frame(frame: Any) -> Any:
    data = frame.reset_index()
    timestamp_column = _first_existing_column(data, ["ts_event", "ts_recv", "index"])
    data = data.rename(columns={timestamp_column: "timestamp"})
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Databento OHLCV output is missing columns: {', '.join(missing)}")
    if "symbol" not in data.columns:
        data["symbol"] = ""
    return data[required + ["symbol"]]


def _first_existing_column(frame: Any, candidates: list[str]) -> str:
    for column in candidates:
        if column in frame.columns:
            return column
    raise ValueError(f"Cannot find timestamp column. Candidates: {', '.join(candidates)}")
