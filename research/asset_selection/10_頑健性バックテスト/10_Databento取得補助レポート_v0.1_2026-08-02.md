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

## 2026-08-02時点の未解決

- IBKRでの銘柄単位取扱可否と現行証拠金は未確認。
- `statistics` は直近1か月分のみ保存した。長期全期間の建玉系列が必要な場合は別工程で取得する。
- 代表限月系列は研究用の簡易ルールであり、正式なロール損益計算ではない。

## P10 Protocol完了時の追加実行

- Raw OHLCVをP09指定期間で取得した。
- `MCL`, `M6A` は `2015-01-01` から `2026-08-01` まで取得した。
- `MZC`, `MZS`, `MZW` は `2025-02-24` から `2026-08-01` まで取得した。
- `definition` は5銘柄分保存した。
- `statistics` は直近1か月分を保存した。
- 親シンボルの複数限月・スプレッド混在を避けるため、スプレッドを除外し、同一分で出来高最大の限月を代表系列として採用した。
- Databentoから一部日付の `degraded` 品質警告が出たため、P11以降では品質注意として扱う。

## 参考にした公式仕様

- Databento Python client: `pip install -U databento`
- Historical API: `Historical.timeseries.get_range`
- dataset: `GLBX.MDP3`
- schema例: `ohlcv-1s`, `ohlcv-1m`
- futures parent symbology: `ES.FUT` 形式
