---
name: autotrade_skill_python_implementation_v0_1
description: 承認済み詳細設計とREDテストの範囲で、安全な最小Python実装を行う。
source_reference: historical upstream metadata; not used as a current integrity check
---

# Python 実装

このSkillは `settings/ai_component_rules.md#共通PRODUCT_ONLY部品契約` を継承する。ユーザーに部品名の指定を求めず、管理専用のmanifest、evidence、receipt、台帳、index同期を通常の完了条件にしない。

## 入力

- 承認済み DD-IDまたは依頼された動作、関連テスト、対象・除外パス。Run Manifestは再現可能な実行を依頼された場合だけ使う。

## 実行

1. REDテストと対象境界を確認し、最小差分だけを実装する。
2. 型、UTC、Decimal、ID、例外、Adapter境界の不明点は Unknown として停止する。
3. 変更理由とテスト結果は通常チャットで報告し、再現可能な証跡を依頼された場合だけ `tests/evidence/{phase_id}/{run_id}/` に残す。
4. 構造変更を含む差分も、管理用manifest/index更新を完了条件にしない。関連するpath、schema、state、テストを確認する。

## 禁止事項と停止条件

- Broker、Live、外部ネットワーク、Secret、実データへ接続・出力しない。
- テスト削除、skip、閾値緩和、対象外ファイル変更をしない。
- 設計外の判断、数値型・時刻契約の不明、Secret検出時は停止する。
- 管理用manifest、hash、構造抽出、validatorを、製品安全に直接必要でない限り要求しない。
