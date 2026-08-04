---
name: autotrade_skill_implementation_detail_review_v0_1
description: 詳細設計書が実装可能な粒度を満たすかを、モジュール、API、永続化、処理順、例外、テスト、改訂閉ループの観点で監査する。
---

# autotrade_skill_implementation_detail_review_v0_1

## 目的

詳細設計書を「読める方針書」ではなく、実装・テスト・レビューに使える契約として監査する。設計書の整合性だけでなく、実装者が追加の設計判断を求められる箇所を指摘する。

## 入力

- 対象詳細設計HTML、構成標準、Phase Runbook
- 要件、既存設計、対象リポジトリ構成、テスト方針
- A90の横断レビューおよびRed Team指摘
- 改訂前後の差分と採否表

## 出力

- ID、重要度、対象ファイル、章、欠落項目、実装影響、修正方針を持つ指摘一覧
- 詳細設計構成要素の充足マトリクス
- 再レビュー判定、残Unknown、Human Gate要否

## 監査観点

1. モジュール構成、依存方向、責務、公開境界があるか。
2. APIごとに型、必須性、エラー、副作用、冪等性が定義されているか。
3. 永続化のキー、制約、version、差分、再実行、migrationが定義されているか。
4. 正常系、主要失敗系、停止・復旧のシーケンスがあるか。
5. 非自明なアルゴリズムにコード例または擬似コードがあるか。
6. 設定、Secret境界、観測、監査、HealthEventが実装責務に接続しているか。
7. テスト、fixture、failure injection、受入条件が設計契約に接続しているか。
8. REQ、DEC、UNK、ART、Run Manifest、data_versionの追跡があるか。
9. レビュー指摘を改訂後に再確認し、未解決事項を消していないか。

## 禁止事項

- 章が存在するだけで充足と判定すること
- 型・エラー・保存規則・異常系を推測で補完してPassにすること
- Unknownを実装済みまたは安全と扱うこと
- A90の横断レビューやRed Team観点を置き換えること

## 品質チェック

- Findings firstで出力する。
- 各指摘はファイル、章、構成要素、実装影響に紐付く。
- Critical/High指摘が残る場合は、詳細設計完了をPassにしない。
- 改訂後、同じ充足マトリクスで再レビューする。
- すべての `N/A` に理由と確認者がある。

## Phase依存パラメータ

- `phase_id`
- `step_id`
- `detail_boundary`
- `implementation_target`
- `document_coverage_matrix`

## 参照成果物

- `doc/ai_foundation/14_実装詳細設計書構成標準.html`
- `doc/ai_foundation/15_実装詳細設計AI基盤仕様.html`
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`
