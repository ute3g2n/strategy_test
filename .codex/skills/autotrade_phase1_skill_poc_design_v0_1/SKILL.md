---
name: autotrade_phase1_skill_poc_design_v0_1
description: Phase 1専用。取引エンジンPoCの評価軸、検証シナリオ、採点方法を設計する。
---

# autotrade_phase1_skill_poc_design_v0_1

## 目的
NautilusTrader、LEAN等の取引エンジン候補を、決め打ちではなくPoC証拠で評価する。

## 入力
- 取引エンジンPoC要件
- 公式一次情報
- 共通実行モデル

## 出力
- PoC評価設計
- 採点表
- 検証シナリオ
- Human Gate項目

## 禁止事項
- PoCなしで最終決定しない。
- 実資金取引をPoCに含めない。
- 外部仕様を記憶だけで断定しない。

## 品質チェック
- 1分足リプレイ、Entry/Add/Stop/Exit、再起動復旧、IBKR Paper接続、Heartbeatが含まれる。
- 採点軸と重みが明確である。
