---
name: autotrade_skill_ai_component_lifecycle_v0_1
description: Skill、サブエージェント、オーケストレータの作成・変更を進めるための汎用Skill。既存部品の再利用調査、必要最小限の新設または明示変更、関連HTML仕様書と共通ルールの追従更新を一連で行うときに使う。
---

# autotrade_skill_ai_component_lifecycle_v0_1

## 目的
AI実行基盤の部品追加や変更を、PRODUCT_ONLY部品契約に従って必要最小限に進める。部品名は依頼内容から自動選択でき、実体変更、必要な仕様更新、関連確認だけを行う。

## PRODUCT_ONLY部品契約

- ユーザーにAgent、Skill、Orchestratorの完全名を指定させない。依頼内容、変更範囲、品質リスクから適切な既存部品を自動選択する。
- 部品変更そのもの、関連する製品仕様、必要なテストだけを対象にする。AI部品の利用を証明するためのreceipt、Agent一覧、runtime記録、Gate packet、台帳、index同期を自動作成しない。
- AI基盤HTML仕様書は、ユーザーが正式な仕様書更新を依頼した場合、またはAI部品の利用者向け契約が実際に変わる場合だけ更新する。
- A95は管理用hash再導入の直接的な疑いがある場合だけ自動選択する。hash値、manifest、stale、fingerprint、retry、hash receiptを作成しない。
- `multi_agent_v1__spawn_agent`／`multi_agent_v1__wait_agent`は独立作業が製品品質または安全上必要な場合だけ使う。通常は単一Agentの直接実行を優先し、spawn/waitの証跡を作成しない。
- 次のPhase、Step、Gate、レビューをこのSkillだけで自動開始しない。必要な提案はチャットで返す。

## 入力
- 変更対象または新設対象の要件
- `.codex/skills/`, `.codex/agents/`, `.codex/orchestrators/`, `.codex/config.json`
- `settings/ai_component_rules.md`
- `doc/ai_foundation/03` から `08`（正式なAI基盤仕様書の更新または参照が依頼に含まれる場合だけ）
- `AGENTS.md`, `README.md`, `doc/index.html`

## 出力
- 新規または更新された Skill / Agent / Orchestrator
- 追従更新された HTML仕様書、共通ルール、導線
- 再利用判断、変更理由、停止条件、残課題

## 標準フロー
1. 既存の汎用Skill、汎用Agent、汎用Orchestratorを調査し、再利用候補と不足責務を分ける。
2. 新設か変更かを明示し、対象の完全名、責務、境界条件、使用Skillを確定する。
3. Skill、Agent、Orchestratorの実体を作成または更新する。
4. ユーザーが正式仕様書更新を依頼した場合だけ、該当するAI基盤仕様書、`doc/index.html`、共通ルールを必要最小限で更新する。
5. 変更対象のJSON整合、必要な参照整合、Secret・path・状態を確認し、結果をチャットで報告する。

## 保護hash限定ルール（HASH-FUTURE-01〜08）

- 新設・更新するSkill、Agent、Orchestrator、prompt、receipt、HTML仕様へ管理・参照効率化・実行証跡目的のhashを追加しない。
- Phase/Step受入条件へinput、artifact、finding、evidence、diff、baseline、manifest、snapshot、reportのhash一致を追加しない。
- hash用途が安全・データ・再現性に直結するか不明な場合は、新しいhashを作らずUnknown/Human Gateへ送る。
- protected hashを扱う場合だけ、目的、保護対象、保護しない場合の具体的失敗、失敗時の停止範囲を記録する。hash不一致を管理作業のretry理由にしない。
- 実行receiptはruntime backend、dispatch、ID、JSON path、model、Skill、status、入出力参照、independent、review_mode、fallbackを正本とし、管理hash fieldsを含めない。
- 新規・大幅変更の成果物は`autotrade_skill_protected_hash_policy_guard_v0_1`と`AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1`へ静的判定を渡す。A95はhash値、manifest、fingerprint、stale、retryを生成しない。

## 実ランタイム起動契約（任意）

独立作業が製品品質または安全上必要な場合に限り、ルート実行Agentは適切なOrchestrator、Agent、Skillを自動選択し、`multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` を使える。通常の部品変更では単一Agentの直接実行を優先し、runtime receiptやfallback記録を作成しない。

spawn/waitを使用した場合も、起動状況はチャットで正直に報告する。起動不能を独立実行済みと表現しない。receipt、fallback packet、子run台帳はユーザーが成果物として求めた場合だけ保存する。UnknownのPass、Secret、default変更、Critical／High未解決は、部品の自動選択とは無関係にFail-closedで扱う。

## 禁止事項
- 既存部品を推測で流用しない。
- 明示されていない部品名へ勝手にリネームしない。
- 新規作成時に既存名と衝突したまま上書きしない。
- ユーザーが依頼していない仕様書更新を追加しない。利用者向け契約が変わる場合だけ必要な正本を更新する。
- `default_orchestrator` を変更しない。
- UnknownをPassにしない。
- A95を文章manifest管理へ拡張しない。管理目的hashの候補は`BLOCKED`、用途不明は`NEEDS_HUMAN_GATE`、直接の保護対象hashだけを目的・停止範囲付きで`ALLOW`とする。

## 品質チェック
- 再利用した既存部品と新設した部品の境界が説明されている。
- Skill、Agent、Orchestratorの完全名が全成果物で一致している。
- `settings/ai_component_rules.md`のPRODUCT_ONLY部品契約と実体変更が整合している。
- ユーザーが仕様書更新を依頼した場合だけ、該当HTMLと`doc/index.html`の導線を確認する。
- 実行結果はチャットで報告し、追補検証HTML、receipt、台帳を自動作成しない。

## Phase依存パラメータ
- `step_id`
- `output_root`
- `artifact_index`
- `change_scope`

## 参照成果物
- `doc/ai_foundation/07_AI部品作成ルール.html`
- `doc/ai_foundation/11_AI部品作成更新AI部品仕様.html`
- `doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html`
