---
name: autotrade_skill_design_doc_set_writer_v0_1
description: Phase内で複数の正式HTML設計書をセットとして作成・更新する。共通メタ情報、相互リンク、doc/index.html導線、Unknown台帳、レビュー履歴、採否表を揃える。
---

# autotrade_skill_design_doc_set_writer_v0_1

## 目的
Phase内で複数の設計書HTMLを作成するときに、単体文書の寄せ集めではなく、1つの設計書セットとして構造、ID、相互リンク、レビュー履歴、Unknown管理を揃える。

## 入力
- Phase Runbook
- Phase実行計画書
- 要件定義、前Phase成果物、既存HTML成果物
- 作成対象の成果物一覧
- 文書アウトライン、設計判断、Unknown、レビュー指摘
- `doc/index.html`

## 出力
- 設計書セット作成方針
- 各HTML設計書の章立て、共通メタ情報、関連リンク
- 相互リンク、doc/index.html更新案
- Unknown台帳、設計判断ID、成果物ID対応表
- レビュー履歴、採否表、残課題
- 文書ごとの `run_context_maintenance` 引き渡しとmanifest receipt

## 禁止事項
- 正式HTML成果物を単独で孤立させること
- 共通メタ情報、文書状態、作成日、入力、Unknown、レビュー履歴を省略すること
- 設計書間で同じ責務やIDを矛盾した意味で使うこと
- UnknownをPass扱いすること
- Secret、API key、Account IDなどの秘匿情報をHTMLやログへ出すこと
- 外部CDNに依存するHTMLを正式成果物にすること
- A07のmanifest判定またはvalidator失敗を隠してセット完了にすること

## 品質チェック
- すべてのHTML成果物が `doc/index.html` から到達できる
- 各HTMLに文書ID、作成日、状態、入力、判断、Unknown、レビュー履歴、関連リンクがある
- 設計判断ID、Unknown ID、成果物IDが重複せず追跡可能である
- 同一Phase内の設計書間で用語、責務、保存先、Gateが矛盾していない
- レビュー指摘の採用、部分採用、保留、却下が理由付きで記録される
- 新規HTMLと大幅変更HTMLをA07へ1ファイル単位で渡し、validator PASSまたは理由付きBLOCKEDをセットの完了条件へ含める

## Phase依存パラメータ
- `phase_id`
- `step_id`
- `output_root`
- `log_root`
- `artifact_index`
- `document_set_id`
- `detail_boundary`
- `human_gate_policy`

## 参照成果物
- `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`
- `doc/ai_foundation/04_プロジェクト汎用サブエージェント仕様.html`
- `doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html`
- `doc/ai_foundation/06_AI部品相関図発火制御図.html`
- `doc/ai_foundation/13_設計書セット作成AI部品仕様.html`
