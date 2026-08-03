---
name: autotrade_skill_revision_integration_v0_1
description: レビュー指摘を反映し、変更履歴を残す。
---

# autotrade_skill_revision_integration_v0_1

## 目的
レビュー指摘の採否と理由を明示しながら、正式HTMLを更新する。

## 入力
- レビュー指摘
- 対象HTML
- 採否方針

## 出力
- 修正版HTML
- 採否表
- 変更履歴
- 残課題

## 禁止事項
- 未解決リスクの削除
- 安全要件の弱体化

## 品質チェック
- 採用、部分採用、保留、却下が記録される
- 変更理由が残る
- 残課題が消えない

## Phase依存パラメータ
- `phase_id`
- `output_root`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`
