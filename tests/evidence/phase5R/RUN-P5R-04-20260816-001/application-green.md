# P5R-04〜08 Application Green Evidence

- Run ID: `RUN-P5R-04-20260816-001`
- 実行日: 2026-08-16（Asia/Tokyo）
- 対象: P5R local Backtest Application API / Backtest Core接続
- 入力: 既存P5品質確認済みローカルfixtureのみ

## 実行結果

| 検査 | コマンド・証拠 | 結果 |
|---|---|---|
| 固定4 Gate | `tests/evidence/phase5R/RUN-P5R-03-20260816-001/verification.json` | formatter / lint / type / test = PASS |
| Application・Backtest・P5Rテスト | `.venv/Scripts/python.exe -m scripts.quality_gate.local_p5r_pytest` | 179 passed |
| P5Rテスト単体の静的確認 | `.venv/Scripts/python.exe -m ruff format --check tests/phase5R` / `ruff check tests/phase5R` | PASS |
| A95保護ポリシー | `scripts/ai_foundation/protected_hash_policy_guard.py` | 新規対象は全て ALLOW。データ再現性用の保護対象識別だけを維持 |

## 実装済みの受入対象

- Preflight: 銘柄、Spot、1分足、UTC、24時間Calendar、P5期間、品質PASS、未来参照なしを確認し、範囲外はSTOPPED。
- Single Run: QUEUED / RUNNING / SUCCEEDED / FAILED / CANCELLED、進捗、ETA、checkpoint、resumeを保持。
- Strategy Core: 各完成M1 Barを `autotrade.strategy.service.process_closed_bars` へ順番に渡し、UIで選んだ `TURTLE_SYS1` / `TURTLE_SYS2` とEntry/Exit期間を `StrategyConfig` として実行する。CoreのSignal理由、方向、Signal IDをLedgerへ残し、Core停止時はRunを成功扱いにしない。
- 結果: 総損益、最大ドローダウン、勝率、取引数、最終残高、Signal / Virtual Fill / Balance Ledger、Data由来、費用・Slippage仮定を同一Runから取得。
- Sweep: 候補重複、上限、親Job、子Run、部分失敗、取消を扱う。Sweepを継続運用Unitへ昇格しない。
- 履歴・比較・CSV: Runを上書きせず、条件不一致を `CONDITION_MISMATCH` として表示し、CSVは非同期Jobにする。
- Holdout / Walk-forward: 確定前Holdoutを拒否し、確定後は一度だけ評価。3窓を実戦略処理し、未来参照なしを返す。

## 境界

外部Data追加取得、Provider変更、Broker、Secret、実注文、実資金、Paper / Live、複数Unit・Portfolio・Account・実運用Risk・OMSは実装・実行していない。`P5R-UNK-001`（Provider条件、P5-08 host isolation、過去child dispatch、実行費用）は `OPEN_NOT_PASS` のまま残す。
