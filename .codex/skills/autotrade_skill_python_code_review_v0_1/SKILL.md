---
name: autotrade_skill_python_code_review_v0_1
description: Python品質と取引安全を独立にレビューし、Findings firstで受入可否を判断する。
source_reference: historical upstream metadata; not used as a current integrity check
---

# Python コードレビュー

このSkillは `settings/ai_component_rules.md#共通PRODUCT_ONLY部品契約` を継承する。レビューは変更リスクに応じて自動選択できるが、独立レビューやレビュー証跡は製品品質・安全上必要な場合または依頼時だけ実施する。

## 入力

- 差分、REQ/DD追跡、関連テスト、外部入力と権限の境界。verification証跡は存在する場合だけ参照する。

## 実行

1. Pythonの型、例外、決定性、回帰、テスト不足を独立に確認する。
2. Secret、外部入力、Broker到達経路、Live、fail-open、監査証跡を確認する。
3. Finding、重大度、採否、残留リスク、再レビュー結果は通常チャットで報告し、再現可能なレビュー証跡を依頼された場合だけ `tests/evidence/{phase_id}/{run_id}/reviews/` に残す。

## 禁止事項と停止条件

- Broker、Live、外部ネットワーク、Secretの取得・出力、ユーザー承認の推測をしない。ユーザーが明示的に承認した場合の記録は許可する。
- Critical/High、Unknown、証跡不足、実取引到達経路、対象外差分があれば停止する。
