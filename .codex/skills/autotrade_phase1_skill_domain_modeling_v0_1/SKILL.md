---
name: autotrade_phase1_skill_domain_modeling_v0_1
description: Phase 1専用。境界づけられたコンテキスト、共通ドメインモデル、イベント、ID、時系列を設計する。
---

# autotrade_phase1_skill_domain_modeling_v0_1

## 目的
BacktestからLiveまで共通で扱うドメイン概念を固定する。

## 入力
- 全体設計
- 要件追跡
- 注文、口座、リスク、戦略要件

## 出力
- 境界づけられたコンテキスト
- 共通ドメインモデル
- イベント、Command、State、ID、Time定義

## 禁止事項
- Strategy、OMS、Risk、Account、Adapter責務を混ぜない。
- 実API固有IDを内部IDとして直接使わない。
- UnknownをPassにしない。

## 品質チェック
- 再現性と監査証跡に必要なIDがある。
- UTC、取引所時刻、営業日の意味が分離されている。
