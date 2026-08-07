---
name: autotrade_skill_debug_recovery_v0_1
description: ローカル失敗を再現し、原因仮説ごとの最小修正と再検証を上限付きで行う。
ecc_source_commit: 623f2c020f052319657674e4e6c29ab5d0ad566b
---

# デバッグと回復

## 入力

- 失敗署名、ローカル再現コマンド、差分、Run Manifest、既存の仮説履歴。

## 実行

1. 失敗をローカルで再現し、仕様・実装・テスト・環境に分類する。
2. 原因仮説ごとに最小修正を一度だけ行い、同一仮説は最大2回まで再検証する。
3. 仮説、差分、結果、BLOCKED理由を `tests/evidence/{phase_id}/{run_id}/debug/` に残す。

## 禁止事項と停止条件

- Broker、Live、外部ネットワーク、Secretの出力、無制限リトライ、テスト削除をしない。
- 再現不能、2回の同一仮説失敗、設計Unknown、対象外変更が必要な場合は停止する。
