---
name: autotrade_skill_python_implementation_v0_1
description: 承認済み詳細設計とREDテストの範囲で、安全な最小Python実装を行う。
source_reference: historical upstream metadata; not used as a current integrity check
---

# Python 実装

## 入力

- 承認済み DD-ID、REDテスト、対象・除外パス、Run Manifest。

## 実行

1. REDテストと対象境界を確認し、最小差分だけを実装する。
2. 型、UTC、Decimal、ID、例外、Adapter境界の不明点は Unknown として停止する。
3. 変更理由とテスト結果を `tests/evidence/{phase_id}/{run_id}/` に残す。
4. 構造変更を含む差分は、任意pathを読ませず決定的なコードmanifest/index更新へ渡し、validator PASSまたは理由付きBLOCKEDを受領する。

## 禁止事項と停止条件

- Broker、Live、外部ネットワーク、Secret、実データへ接続・出力しない。
- テスト削除、skip、閾値緩和、対象外ファイル変更をしない。
- 設計外の判断、数値型・時刻契約の不明、Secret検出時は停止する。
- コードmanifestの対象境界、hash、構造抽出、validator結果が不明なまま完了宣言しない。
