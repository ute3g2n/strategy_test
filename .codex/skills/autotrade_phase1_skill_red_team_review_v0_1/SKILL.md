---
name: autotrade_phase1_skill_red_team_review_v0_1
description: Phase 1専用。安全性、運用事故、Unknown、過剰固定、危険な先送りを批判的に監査する。
---

# autotrade_phase1_skill_red_team_review_v0_1

## 目的
自動売買システムで事故につながる設計漏れを、批判的観点で発見する。

## 入力
- 対象HTML設計書
- 要件定義
- レビュー観点チェックリスト

## 出力
- レッドチーム監査結果
- 重大リスク
- 修正要求
- Gate停止提案

## 禁止事項
- 安全停止漏れを軽視しない。
- 根拠不足をPassにしない。
- 投資助言、売買推奨にしない。

## 品質チェック
- Fail-closed、Kill Switch、監査証跡、Secrets、Broker停止、データ異常を確認している。
