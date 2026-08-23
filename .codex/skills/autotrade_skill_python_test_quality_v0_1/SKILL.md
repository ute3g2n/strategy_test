---
name: autotrade_skill_python_test_quality_v0_1
description: pytestのRED/GREEN、固定fixture、ローカル品質ゲート、証跡を統制する。
source_reference: historical upstream metadata; not used as a current integrity check
---

# Python テストと品質

このSkillは `settings/ai_component_rules.md#共通PRODUCT_ONLY部品契約` を継承する。関連テストによる製品品質は維持するが、Run Manifest、evidence、receipt、Gate packetは依頼または安全上必要な場合だけ作成する。

## 入力

- 受入条件、DD-ID、fixture契約、coverage方針。Run Manifestは再現可能な実行を依頼された場合だけ入力する。

## 実行

1. 変更リスクに応じて正常・境界・異常・回帰のpytestを作成または実行し、必要な場合はREDを確認する。
2. formatter、lint、type、testを関連範囲に合わせてローカル実行する。Run Manifestは存在する場合だけその許可順に従う。
3. コマンド、終了コード、fixture条件、判定は通常チャットで報告し、再現可能な証跡を依頼された場合だけ `tests/evidence/{phase_id}/{run_id}/` に保存する。

## 禁止事項と停止条件

- Broker、Live、外部ネットワーク、Secret、実データのfixture化をしない。
- skip、期待値の根拠なき変更、coverageだけでのPassを禁止する。
- fixture、checksum、許容差、Unknown、必須GateのFailureがあれば停止する。
