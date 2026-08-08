# RUN-P2-DQR-001 / P2-06 RED証跡

## 判定

- 状態: `RED_DESIGN`
- 実行日: 2026-08-08
- 入力モード: 固定fixtureのみ
- 外部ネットワーク、Databento、Broker、Secret、実データ: 使用なし
- P2-05既存テスト: `9 passed`
- P2-06追加契約テスト: collection時に `ModuleNotFoundError: autotrade.market_data.manifest` でRED

## P2-05完了範囲の確認

`RUN-P2-IC-001-WSL/wsl-verification-capture.json` の4 Gate PASSと、既存の
`tests/market_data/test_catalog_resolver.py` 9件を確認した。現時点の実装は
`CatalogResolver`、固定fixture、テスト、およびその品質Gateに限られる。
Raw / Normalized Store、MarketEvent、DataVersion、ManifestはP2-06の契約テストで
未実装境界として固定した。

## 固定した品質ケース

| ケース | 期待する品質印 | データ版発行 | Signal生成 |
|---|---|---:|---:|
| 欠損 | `MISSING_DATA` | 不可 | 停止 |
| 同一内容の重複 | `DUPLICATE` | 可（重複数を記録） | 継続可 |
| 内容が異なる重複 | `DUPLICATE_CONFLICT` | 不可 | 停止 |
| 時刻逆行 | `OUT_OF_ORDER` | 不可 | 停止 |
| 異常価格 | `PRICE_INVALID` | 不可 | 停止 |
| 異常出来高 | `VOLUME_INVALID` | 不可 | 停止 |
| checksum不一致 | `CHECKSUM_MISMATCH` | 不可 | 停止 |
| degraded品質 | `DEGRADED` | 不可 | 停止 |

## Replay契約

同一のRaw内容確認値、変換規則版、Catalog版、品質報告確認値を使う場合、
`data_version`、`MarketEvent`系列、品質報告確認値は一致しなければならない。
`generated_at`や現在時刻を版番号の入力にしない。未来の足を追加して過去の公開済み
Signalを変更してはならない。`MZC/MZS/MZW` は本線`MCL/M6A`と別Universeに隔離する。

## 次の停止条件

P2-07で契約テストをGREENにするまで、Data Quality / ReplayのPass判定、P2-D10の
検証結果確定、Phase 3への入力昇格を行わない。P2-07実装後、trusted scopeを登録し、
WSL `networkingMode=none`で固定4 Gateを再実行する。
