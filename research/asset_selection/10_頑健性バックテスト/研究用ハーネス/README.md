# P10 研究用ハーネス

このディレクトリは、アセット選定と比較検証のための仮実装です。

本番運用システムではありません。

## 役割

- P09の `09_実験マニフェスト` と `09_データ要件表` を読む
- 実験定義を検証する
- ローカルCSVのOHLCVデータを読み、日足へ集約する
- タートル系の簡易バックテストを走らせる
- 実行結果を `runs/` 配下へ出力する

## 前提

- Python 3.11 以上
- 入力データはローカルCSV
- Databento / IBKR の本接続は未実装

## 使い方

```powershell
python research/asset_selection/10_頑健性バックテスト/研究用ハーネス/run_p10.py validate
python research/asset_selection/10_頑健性バックテスト/研究用ハーネス/run_p10.py build-runbook
python research/asset_selection/10_頑健性バックテスト/研究用ハーネス/run_p10.py dry-run
python research/asset_selection/10_頑健性バックテスト/研究用ハーネス/run_p10.py run --bars-dir C:\path\to\bars
```

## 入力CSV

各シンボルごとに、次の列を持つCSVを想定します。

- `timestamp`
- `open`
- `high`
- `low`
- `close`
- `volume`

ファイル名は `MCL.csv` のようにシンボル名と一致させます。

## 出力

- `runs/latest/runbook.json`
- `runs/latest/validation_report.json`
- `runs/latest/backtest_summary.csv`
- `runs/latest/backtest_report.md`

## 注意

- `MZC`, `MZS`, `MZW` は P08から補正済みシンボルを使います。
- `M6A` は物理決済なので、満期持ち越し禁止の前提をレポートに明示します。
- 本ハーネスの結果だけで本番候補を確定しません。
