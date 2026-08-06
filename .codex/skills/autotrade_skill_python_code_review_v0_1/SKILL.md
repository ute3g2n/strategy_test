---
name: autotrade_skill_python_code_review_v0_1
description: Python品質と取引安全を独立にレビューし、Findings firstで受入可否を判断する。
ecc_source_commit: 623f2c020f052319657674e4e6c29ab5d0ad566b
---

# Python コードレビュー

## 入力

- 差分、REQ/DD追跡、テスト・verification証跡、外部入力と権限の境界。

## 実行

1. Pythonの型、例外、決定性、回帰、テスト不足を独立に確認する。
2. Secret、外部入力、Broker到達経路、Live、fail-open、監査証跡を確認する。
3. Finding、重大度、採否、残留リスク、再レビュー結果を `test/evidence/{phase_id}/{run_id}/reviews/` に残す。

## 禁止事項と停止条件

- Broker、Live、外部ネットワーク、Secretの取得・出力、自動承認をしない。
- Critical/High、Unknown、証跡不足、実取引到達経路、対象外差分があれば停止する。
