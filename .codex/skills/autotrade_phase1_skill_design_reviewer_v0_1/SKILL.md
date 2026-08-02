---
name: autotrade_phase1_skill_design_reviewer_v0_1
description: Phase 1専用。設計書の整合性、追跡性、責務境界、Phase範囲をレビューする。
---

# autotrade_phase1_skill_design_reviewer_v0_1

## 目的
Phase 1設計書間の用語、ID、責務、依存、Gateの矛盾を検出する。

## 入力
- 対象HTML設計書
- 要件追跡マトリクス
- レビュー観点チェックリスト

## 出力
- 指摘ID
- 重要度
- 対象箇所
- 問題内容
- 修正方針
- Human Gate要否

## 禁止事項
- 問題を要約だけで流さない。
- Unknownを解決済みにしない。
- Phase 1必須項目の漏れを承認しない。

## 品質チェック
- Findings firstで、重大度順に並んでいる。
- 修正可能な粒度で指摘されている。
