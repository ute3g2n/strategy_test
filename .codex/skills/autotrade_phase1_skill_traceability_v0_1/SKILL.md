---
name: autotrade_phase1_skill_traceability_v0_1
description: Phase 1専用。要件ID、設計判断ID、未確定事項ID、成果物IDの追跡性を維持する。
---

# autotrade_phase1_skill_traceability_v0_1

## 目的
Phase 1設計書全体で、要件、判断、未確定事項、成果物の対応関係を追跡可能にする。

## 入力
- 要件定義書
- Phase方針
- 各HTML設計書

## 出力
- 要件追跡マトリクス
- 設計判断一覧
- 未確定事項台帳
- 成果物対応表

## 禁止事項
- IDを重複させない。
- 未対応要件を隠さない。
- UnknownをPassにしない。

## 品質チェック
- 各設計判断に根拠がある。
- 各未確定事項に決定タイミングがある。
- Phase 2以降への引き継ぎ先がある。
