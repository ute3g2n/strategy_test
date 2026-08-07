---
name: autotrade_skill_python_test_quality_v0_1
description: pytestのRED/GREEN、固定fixture、ローカル品質ゲート、証跡を統制する。
ecc_source_commit: 623f2c020f052319657674e4e6c29ab5d0ad566b
---

# Python テストと品質

## 入力

- 受入条件、DD-ID、fixture契約、Run Manifest、coverage方針。

## 実行

1. 正常・境界・異常・回帰のpytestを実装前に作り、REDを確認する。
2. formatter、lint、type、testをRun Manifestの許可順でローカル実行する。
3. コマンド、終了コード、fixture checksum、判定を `tests/evidence/{phase_id}/{run_id}/` に保存する。

## 禁止事項と停止条件

- Broker、Live、外部ネットワーク、Secret、実データのfixture化をしない。
- skip、期待値の根拠なき変更、coverageだけでのPassを禁止する。
- fixture、checksum、許容差、Unknown、必須GateのFailureがあれば停止する。
