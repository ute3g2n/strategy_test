from __future__ import annotations

import csv
from pathlib import Path

from .models import DataRequirement, Experiment


ROOT = Path(__file__).resolve().parents[3]
P09_DIR = ROOT / "09_バックテスト手順"


def load_data_requirements() -> list[DataRequirement]:
    path = P09_DIR / "09_データ要件表_v0.1_2026-08-02.csv"
    items: list[DataRequirement] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            items.append(
                DataRequirement(
                    symbol=row["シンボル"],
                    product_name=row["商品名"],
                    venue=row["会場"],
                    settlement=_extract_settlement(row["メモ"]),
                    notes=row["メモ"],
                )
            )
    return items


def load_experiments() -> list[Experiment]:
    path = P09_DIR / "09_実験マニフェスト_v0.1_2026-08-02.csv"
    items: list[Experiment] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            items.append(
                Experiment(
                    experiment_id=row["実験ID"],
                    experiment_name=row["実験名"],
                    symbols=[token.strip() for token in row["対象シンボル"].split(";") if token.strip()],
                    strategy_family=row["戦略系統"],
                    entry_rule=row["エントリー"],
                    exit_rule=row["エグジット"],
                    stop_rule=row["ストップ"],
                    unit_risk=row["Unitリスク"],
                    pyramiding_rule=row["ピラミッディング"],
                    roll_rule=row["ロール方式"],
                    cost_model=row["コストモデル"],
                    data_range=row["データ範囲"],
                    development_window=row["学習/開発期間"],
                    validation_window=row["検証期間"],
                    holdout_window=row["最終Holdout"],
                    trial_policy=row["試行回数扱い"],
                    executable=row["P10での実行可否"],
                    notes=row["メモ"],
                )
            )
    return items


def _extract_settlement(notes: str) -> str:
    if "物理決済" in notes:
        return "Physical"
    return "Financial"
