---
name: autotrade_skill_phase_execution_planning_v0_1
description: Phase開始時の実行計画書を作成する。要件定義書、前Phase成果物、既存計画書、AI部品一覧を読み、複数ステップの実行計画、各ステップでそのまま実行できるプロンプト、Human Gate、成果物配置、発火制御を設計する時に使う。
---

# autotrade_skill_phase_execution_planning_v0_1

## 目的

各Phaseの最初に作成する実行計画書を、プロジェクト共通の形式で設計する。

## 入力

- 要件定義書HTMLまたはMarkdown
- 前Phaseの完了判定、引き継ぎ、詳細設計バックログ
- 既存のPhase実行計画書
- `.codex/skills/`, `.codex/agents/`, `.codex/orchestrators/`, `.codex/config.json`
- `settings/ai_component_rules.md`

## 出力

- `plan/PhaseX_実行計画書_v0.1_YYYY-MM-DD.md`
- 各ステップでそのまま実行できるプロンプト
- Phase Runbook
- 成果物一覧と保存先
- 依存関係、並列実行可否、Human Gate
- 使用するOrchestrator、Agent、Skillの完全名
- Unknown台帳と後続Phase引き継ぎ方針

## 手順

1. 対象Phaseの目的、入力条件、完了条件を抽出する。
2. 既存の汎用AI部品で対応できる作業と、新規Phase専用部品が必要な作業を分ける。
3. 実行ステップを適切な粒度に分割する。必ず複数ステップにし、過度に細かくしすぎない。
4. 各ステップに、ロール、使用オーケストレータ完全名、担当サブエージェント完全名、使用モデル、使用Skill完全名、発火制御、入力、タスク、レビュー、完了条件を含める。
5. 各ステップのプロンプトは、そのまま次のCodex実行に貼れる形にする。
6. 正式HTML成果物は `doc/phaseX/` 配下、実行計画書とプロンプトログは `plan/` 配下に置く。
7. `doc/index.html` から正式HTML成果物へ到達できる更新ルールを計画に含める。
8. UnknownをPassにせず、決定タイミングと担当Phaseを明記する。

## 必須ルール

- 実行計画書は必ず複数ステップに分ける。
- 1ステップ1成果物に固定しない。依存関係とレビュー効率で束ねる。
- 各プロンプトにはAI部品の完全名を明記する。
- 未指定の既存Skill、Agent、Orchestratorを推測起動しない。
- Phase専用部品を作る場合は、汎用部品では足りない理由、利用期限、凍結条件を書く。
- `default_orchestrator` は変更しない。

## 品質チェック

- 各ステップが入力不足で止まらない粒度になっている。
- 並列実行できるステップとシーケンシャルなステップが分かれている。
- Human Gateの位置と承認対象が明確である。
- 正式HTML成果物と `doc/index.html` 更新が抜けていない。
- レビューとレビュー反映ステップが含まれている。
- 後続Phaseへ送る詳細化項目が明確である。
