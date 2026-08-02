---
name: autotrade_phase1_skill_official_research_v0_1
description: Phase 1専用。外部仕様を調べる場合に公式一次情報を優先し、URLと確認日を記録する。
---

# autotrade_phase1_skill_official_research_v0_1

## 目的
取引エンジン、Broker、Market Data等の外部仕様を扱うとき、追跡可能な根拠だけを設計判断に使う。

## 入力
- 調査対象
- 確認すべき仕様
- 基準日

## 出力
- 情報源一覧
- 公式情報要約
- 未確認事項
- 設計判断への影響

## 禁止事項
- 非公式情報だけで確定しない。
- 最新性が必要な事項を記憶だけで断定しない。
- 外部仕様の詳細をPhase 1で過剰固定しない。

## 品質チェック
- URL、確認日、確認対象がある。
- Unknownが残っている場合は台帳化されている。
