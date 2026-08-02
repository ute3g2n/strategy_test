# 10 Databento取得補助レポート v0.1

- Step: P10
- 作成日: 2026-08-02
- 状態: 実装完了、実取得確認済み

## 位置づけ

Databento取得補助は、P10研究用ハーネスへ投入するローカルCSVを作るための仮実装である。

本番運用システムのデータアダプタではない。

## 追加したCLI

```powershell
python research/asset_selection/10_頑健性バックテスト/研究用ハーネス/run_p10.py check-databento-env
python research/asset_selection/10_頑健性バックテスト/研究用ハーネス/run_p10.py fetch-databento --start 2026-01-01 --end 2026-02-01 --output-dir C:\path\to\bars
```

## 取得対象

P09データ要件表から対象シンボルを読み込む。

- `MCL.FUT`
- `MZC.FUT`
- `MZS.FUT`
- `MZW.FUT`
- `M6A.FUT`

## 取得仕様

- dataset: `GLBX.MDP3`
- schema: `ohlcv-1m`
- stype_in: `parent`
- stype_out: Databento APIデフォルトの `instrument_id`
- output: `MCL.csv`, `MZC.csv`, `MZS.csv`, `MZW.csv`, `M6A.csv`

## 2026-08-02 実行確認

- 専用仮想環境: `research/asset_selection/10_頑健性バックテスト/研究用ハーネス/.venv`
- パッケージ: `databento 0.82.0`
- 環境確認: `ready: true`
- スモークテスト: `MCL`, `2026-07-01` から `2026-07-02`, `ohlcv-1m`, 成功
- 5銘柄取得: `MCL`, `MZC`, `MZS`, `MZW`, `M6A`, `2026-07-01` から `2026-08-01`, `ohlcv-1m`, 成功
- 出力先: `research/asset_selection/10_頑健性バックテスト/研究用ハーネス/data/databento_5symbols_2026-07`
- P10実行: 5銘柄CSVを入力として `run` 成功

## 取得行数

| シンボル | 行数 |
|---|---:|
| MCL | 108704 |
| MZC | 3321 |
| MZS | 4508 |
| MZW | 4661 |
| M6A | 14623 |

## 未解決

- 親シンボル取得のため、同時に複数限月が含まれている可能性がある。P10の本格評価前に、限月選択・ロール規則を明示して連続足を作る必要がある。
- `definition` と `statistics` の取得・保存は未実装。
- IBKRでの銘柄単位取扱可否と現行証拠金は未確認。

## 参考にした公式仕様

- Databento Python client: `pip install -U databento`
- Historical API: `Historical.timeseries.get_range`
- dataset: `GLBX.MDP3`
- schema例: `ohlcv-1s`, `ohlcv-1m`
- futures parent symbology: `ES.FUT` 形式
