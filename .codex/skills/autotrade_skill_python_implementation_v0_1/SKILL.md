---
name: autotrade_skill_python_implementation_v0_1
description: 承認済み詳細設計とREDテストの範囲で、安全な最小Python実装を行う。
ecc_source_commit: 623f2c020f052319657674e4e6c29ab5d0ad566b
---

# Python 実装

## 入力

- 承認済み DD-ID、REDテスト、対象・除外パス、Run Manifest。

## 実行

1. REDテストと対象境界を確認し、最小差分だけを実装する。
2. 型、UTC、Decimal、ID、例外、Adapter境界の不明点は Unknown として停止する。
3. 変更理由とテスト結果を `test/evidence/{phase_id}/{run_id}/` に残す。

## 禁止事項と停止条件

- Broker、Live、外部ネットワーク、Secret、実データへ接続・出力しない。
- テスト削除、skip、閾値緩和、対象外ファイル変更をしない。
- 設計外の判断、数値型・時刻契約の不明、Secret検出時は停止する。
