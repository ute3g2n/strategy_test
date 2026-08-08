# P2-06 Trading Safety Review

## 判定

`P2-06`の設計・RED段階として受入可能。P2-07実装とP2-09検証への昇格は保留する。

## 確認事項

- Broker、Live、Databento、外部ネットワーク、Secret、実データへ到達するコードやfixtureは追加していない。
- `MISSING_DATA`、`DUPLICATE_CONFLICT`、`OUT_OF_ORDER`、`PRICE_INVALID`、`VOLUME_INVALID`、`CHECKSUM_MISMATCH`、`DEGRADED`は通常のSignal生成へ渡さない契約になっている。
- 同一fixture hash、Catalog版、変換規則版、品質報告確認値を使うReplay入力を固定し、`generated_at`を版番号の入力にしていない。
- 条件付き候補`MZC/MZS/MZW`と本線候補`MCL/M6A`をfixture上で分離している。
- P2-06のREDは、未実装境界を確認するための停止状態であり、Passへ書き換えていない。

## 残留リスク

`MarketEvent`の未来足不変性はまだ実装前の契約値確認である。P2-07でReplay境界を実装し、未来足追加前後の過去イベント比較を実行するまで、P2-09のData GateをPassにしない。
