from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .models import BacktestResult, DataRequirement, Experiment


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_runbook(path: Path, requirements: list[DataRequirement], experiments: list[Experiment]) -> None:
    payload = {
        "kind": "p10_research_runbook",
        "research_only": True,
        "requirements": [asdict(item) for item in requirements],
        "experiments": [asdict(item) for item in experiments],
    }
    write_json(path, payload)


def write_summary_csv(path: Path, results: list[BacktestResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()) if results else [
            "experiment_id", "symbol", "bars_used", "trades", "gross_pnl", "final_equity", "max_drawdown", "notes"
        ])
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def write_report(path: Path, results: list[BacktestResult], missing_symbols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P10 研究用ハーネス実行レポート",
        "",
        "- 位置づけ: 研究用仮実装",
        "- 本番運用コードではない",
        "",
        "## 実行結果",
        "",
    ]
    if results:
        lines.extend([
            "| 実験ID | シンボル | bars_used | trades | gross_pnl | final_equity | max_drawdown |",
            "|---|---|---:|---:|---:|---:|---:|",
        ])
        for result in results:
            lines.append(
                f"| {result.experiment_id} | {result.symbol} | {result.bars_used} | {result.trades} | "
                f"{result.gross_pnl} | {result.final_equity} | {result.max_drawdown} |"
            )
    else:
        lines.append("結果はありません。入力データ不足または dry-run のため未実行です。")

    lines.extend(["", "## 未解決", ""])
    if missing_symbols:
        for symbol in missing_symbols:
            lines.append(f"- 入力CSV不足: `{symbol}.csv`")
    else:
        lines.append("- なし")

    path.write_text("\n".join(lines), encoding="utf-8")
