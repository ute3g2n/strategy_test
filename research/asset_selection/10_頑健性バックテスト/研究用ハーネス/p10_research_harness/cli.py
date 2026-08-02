from __future__ import annotations

import argparse
from pathlib import Path

from .data_loader import aggregate_daily_bars, load_minute_bars, split_without_opening_holdout, write_continuous_minute_csv
from .databento_fetcher import check_databento_environment, fetch_databento_csv, fetch_databento_metadata
from .engine import run_backtest
from .manifest import load_data_requirements, load_experiments
from .reports import write_json, write_protocol_completion_report, write_report, write_runbook, write_summary_csv


ROOT = Path(__file__).resolve().parents[2]
HARNESS_ROOT = ROOT / "研究用ハーネス"
RUNS_ROOT = HARNESS_ROOT / "runs" / "latest"


def main() -> int:
    parser = argparse.ArgumentParser(description="P10 research-only backtest harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate")
    subparsers.add_parser("build-runbook")
    subparsers.add_parser("dry-run")
    subparsers.add_parser("check-databento-env")

    fetch_parser = subparsers.add_parser("fetch-databento")
    fetch_parser.add_argument("--start", required=True)
    fetch_parser.add_argument("--end", required=True)
    fetch_parser.add_argument("--output-dir", required=True)
    fetch_parser.add_argument("--dataset", default="GLBX.MDP3")
    fetch_parser.add_argument("--schema", default="ohlcv-1m")
    fetch_parser.add_argument("--symbols", nargs="*")

    metadata_parser = subparsers.add_parser("fetch-databento-metadata")
    metadata_parser.add_argument("--start", required=True)
    metadata_parser.add_argument("--end", required=True)
    metadata_parser.add_argument("--output-dir", required=True)
    metadata_parser.add_argument("--dataset", default="GLBX.MDP3")
    metadata_parser.add_argument("--symbols", nargs="*")
    metadata_parser.add_argument("--schemas", nargs="*", default=None)

    continuous_parser = subparsers.add_parser("build-continuous")
    continuous_parser.add_argument("--source-dir", required=True)
    continuous_parser.add_argument("--output-dir", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--bars-dir", required=True)

    args = parser.parse_args()
    if args.command == "validate":
        return validate()
    if args.command == "build-runbook":
        return build_runbook()
    if args.command == "dry-run":
        return dry_run()
    if args.command == "check-databento-env":
        return check_databento_env()
    if args.command == "fetch-databento":
        return fetch_databento(
            start=args.start,
            end=args.end,
            output_dir=Path(args.output_dir),
            dataset=args.dataset,
            schema=args.schema,
            symbols=args.symbols,
        )
    if args.command == "fetch-databento-metadata":
        return fetch_databento_metadata_command(
            start=args.start,
            end=args.end,
            output_dir=Path(args.output_dir),
            dataset=args.dataset,
            symbols=args.symbols,
            schemas=args.schemas,
        )
    if args.command == "build-continuous":
        return build_continuous(Path(args.source_dir), Path(args.output_dir))
    if args.command == "run":
        return run(Path(args.bars_dir))
    return 1


def validate() -> int:
    requirements = load_data_requirements()
    experiments = load_experiments()
    known_symbols = {item.symbol for item in requirements}
    issues: list[str] = []
    for experiment in experiments:
        if experiment.executable == "条件付き":
            continue
        missing = [symbol for symbol in experiment.symbols if symbol not in known_symbols]
        if missing:
            issues.append(f"{experiment.experiment_id}: 未定義シンボル: {', '.join(missing)}")

    payload = {
        "kind": "validation_report",
        "research_only": True,
        "requirements_count": len(requirements),
        "experiments_count": len(experiments),
        "issues": issues,
    }
    write_json(RUNS_ROOT / "validation_report.json", payload)
    return 0 if not issues else 2


def build_runbook() -> int:
    requirements = load_data_requirements()
    experiments = load_experiments()
    write_runbook(RUNS_ROOT / "runbook.json", requirements, experiments)
    return 0


def dry_run() -> int:
    requirements = load_data_requirements()
    experiments = load_experiments()
    payload = {
        "kind": "dry_run_report",
        "research_only": True,
        "symbols": [item.symbol for item in requirements],
        "experiments": [item.experiment_id for item in experiments],
        "next_step": "run --bars-dir <local_csv_directory>",
        "note": "DatabentoとIBKRの本接続は未実装。ローカルCSVが必要。",
    }
    write_json(RUNS_ROOT / "dry_run_report.json", payload)
    return 0


def check_databento_env() -> int:
    report = check_databento_environment()
    write_json(RUNS_ROOT / "databento_environment_report.json", report)
    return 0 if report["ready"] else 4


def fetch_databento(
    start: str,
    end: str,
    output_dir: Path,
    dataset: str,
    schema: str,
    symbols: list[str] | None,
) -> int:
    requirements = load_data_requirements()
    target_symbols = symbols or [item.symbol for item in requirements]
    result = fetch_databento_csv(
        symbols=target_symbols,
        start=start,
        end=end,
        output_dir=output_dir,
        dataset=dataset,
        schema=schema,
    )
    write_json(RUNS_ROOT / "databento_fetch_report.json", result)
    return 0 if result["status"] == "completed" else 4


def fetch_databento_metadata_command(
    start: str,
    end: str,
    output_dir: Path,
    dataset: str,
    symbols: list[str] | None,
    schemas: list[str] | None,
) -> int:
    requirements = load_data_requirements()
    target_symbols = symbols or [item.symbol for item in requirements]
    result = fetch_databento_metadata(
        symbols=target_symbols,
        start=start,
        end=end,
        output_dir=output_dir,
        dataset=dataset,
        schemas=schemas,
    )
    write_json(RUNS_ROOT / "databento_metadata_fetch_report.json", result)
    return 0 if result["status"] == "completed" else 4


def build_continuous(source_dir: Path, output_dir: Path) -> int:
    requirements = load_data_requirements()
    reports = {}
    missing = []
    for item in requirements:
        source_path = source_dir / f"{item.symbol}.csv"
        if not source_path.exists():
            missing.append(item.symbol)
            continue
        reports[item.symbol] = write_continuous_minute_csv(source_path, output_dir / f"{item.symbol}.csv")

    payload = {
        "kind": "continuous_build_report",
        "research_only": True,
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "reports": reports,
        "missing_symbols": missing,
        "status": "completed" if not missing else "blocked_missing_input_csv",
    }
    write_json(RUNS_ROOT / "continuous_build_report.json", payload)
    return 0 if not missing else 3


def run(bars_dir: Path) -> int:
    requirements = load_data_requirements()
    experiments = load_experiments()
    missing_symbols = [item.symbol for item in requirements if not (bars_dir / f"{item.symbol}.csv").exists()]
    if missing_symbols:
        write_report(RUNS_ROOT / "backtest_report.md", [], missing_symbols)
        write_json(
            RUNS_ROOT / "run_status.json",
            {
                "kind": "run_status",
                "research_only": True,
                "status": "blocked_missing_input_csv",
                "missing_symbols": missing_symbols,
            },
        )
        return 3

    results = []
    for experiment in experiments:
        if experiment.executable == "条件付き":
            continue
        for symbol in experiment.symbols:
            minute_bars = load_minute_bars(bars_dir / f"{symbol}.csv")
            daily_bars = aggregate_daily_bars(minute_bars)
            split = split_without_opening_holdout(daily_bars)
            runnable_bars = split.development + split.validation
            results.append(run_backtest(symbol, runnable_bars, experiment))

    write_summary_csv(RUNS_ROOT / "backtest_summary.csv", results)
    write_report(RUNS_ROOT / "backtest_report.md", results, [])
    write_json(
        RUNS_ROOT / "run_status.json",
        {
            "kind": "run_status",
            "research_only": True,
            "status": "completed",
            "results": len(results),
            "holdout_status": "sealed_not_used",
        },
    )
    write_protocol_completion_report(
        RUNS_ROOT / "p10_protocol_completion_report.md",
        results=results,
        bars_dir=bars_dir,
    )
    return 0
