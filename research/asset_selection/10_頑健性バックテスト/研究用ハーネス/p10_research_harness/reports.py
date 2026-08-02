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


def write_protocol_completion_report(path: Path, results: list[BacktestResult], bars_dir: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P10 Protocol完了レポート",
        "",
        "- 位置づけ: 第0段階アセット選定用の研究用ハーネス",
        "- 本番運用コードではない",
        "- H3承認: 正式承認済み",
        "- Holdout: 未開封。開発期間60%と検証期間20%だけを使用",
        f"- 入力ディレクトリ: `{bars_dir}`",
        "",
        "## 完了したProtocol項目",
        "",
        "- Databento `GLBX.MDP3` の親シンボル解決",
        "- `ohlcv-1m` の取得",
        "- `definition` と `statistics` の保存",
        "- スプレッドを除外した代表限月系列の生成",
        "- 1分足からの日足生成",
        "- P09実験マニフェストの4主実験を実行",
        "- Holdoutを使わない状態で結果を保存",
        "",
        "## 実行結果",
        "",
        "| 実験ID | シンボル | bars_used | trades | gross_pnl | final_equity | max_drawdown |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result.experiment_id} | {result.symbol} | {result.bars_used} | {result.trades} | "
            f"{result.gross_pnl} | {result.final_equity} | {result.max_drawdown} |"
        )
    lines.extend(
        [
            "",
            "## 残課題",
            "",
            "- ロール損益、手数料、証拠金不足日は研究用簡易エンジンでは未反映。",
            "- IBKR/IBSJの銘柄単位取扱可否と現行証拠金は未確定。",
            "- この結果だけで採用判断や本番移行判断を行わない。",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
