# 管理用hash廃止・保護hash限定運用 全体導入実行計画書

| 項目 | 内容 |
|---|---|
| 文書ID | PLAN-HASH-POLICY-RETIRE-2026-08-15 |
| 版 | v0.1 |
| 作成日 | 2026-08-15 |
| 状態 | Step 00〜09 実行完了（指定runtimeはAgent thread上限によりfallback記録） |
| 対象 | Markdown、HTML、ソースコード、テスト、スクリプト、AI部品、Orchestrator、実行計画、実行証跡、今後作成される成果物 |
| 目的 | 管理・参照効率化・実行証跡目的のhash管理を廃止し、安全・データ・再現性に直結するhashだけを明示的に残す |
| 実行順 | 文章管理基盤の停止 → 文章管理基盤の規則 → context runtime → AI実行基盤 → 品質基盤 → 既存計画 → ソースコード → 将来ルール → パイロット・引渡し |
| 作成時の扱い | ユーザー委譲権限により、文章管理基盤が要求するhash取得・照合・manifest更新・stale判定・不一致再試行を行わずに本計画書を作成する |

## 0. 結論と最重要ルール

本計画では、本プロジェクトのhash運用を次の原則へ変更する。

> 「原則維持候補：安全・データ・再現性に直結するhash」だけを維持候補とし、それ以外のhash管理は廃止する。今後作成される計画、成果物、ソースコード、テスト、AI部品、実行プロンプトにも、保護対象以外のhash管理を決して追加しない。

ここでいうhash管理とは、hash値を単に文字列として記載することではなく、次のいずれかを管理フローへ組み込むことをいう。

- ファイル、文書、ソースコード、成果物、証跡、manifest、snapshot、receiptの同一性を管理目的で確認すること。
- source_hash、input_hash、artifact_hash、finding_hash、change_hash、manifest_hash、evidence_hash、checksum、SHA-256等を、管理用Gateの条件にすること。
- hash不一致、stale、fingerprint差異を理由に作業を止め、再取得、再生成、再試行すること。
- Phase、Step、レビュー、引渡しの完了条件として、管理用hashの一致を要求すること。

上記に該当するhashは、保護対象として明示的に分類されない限り使用してはならない。

### 0.1 保護対象の定義

次のように、hashの欠落・改ざん・不一致が、実際の安全事故、データ破壊・取り違え、再現不能を直接引き起こす場合だけを保護対象とする。

- 安全停止、取引対象、注文、ポジション、権限境界などの安全制御に直結するデータ。
- raw data、catalog、入力データ、DBN、正規化前後のデータ内容を取り違えないためのデータ保全。
- fixture、依存artifact、エンジン入力、Replay入力、再現環境など、同一条件の再現性に直接必要なもの。
- 実行結果の改ざんが安全判断または再現性を壊す場合の改ざん検知。

単に「証跡が存在する」「ファイルが同じ」「レビュー対象が変わっていない」という理由だけでは保護対象にしない。

### 0.2 今後の計画・成果物への禁止ルール

次のルールを、プロジェクトの現行規範として、実行計画、成果物、ソースコード、テスト、AI部品仕様、Agentプロンプト、Orchestrator仕様、HTML説明資料へ明記する。

| ルールID | 規範 |
|---|---|
| HASH-FUTURE-01 | 新規文書・新規ソースコード・新規テスト・新規AI部品は、保護対象として分類されていないhash管理を追加してはならない |
| HASH-FUTURE-02 | 実行計画のStep/Phase受入条件に、管理用hashの一致、証跡hash、差分hash、manifest hash、入力hashを追加してはならない |
| HASH-FUTURE-03 | 新規成果物のテンプレート、依頼プロンプト、Agent定義、Orchestrator定義は、管理用hashの取得・保存・照合・再試行を要求してはならない |
| HASH-FUTURE-04 | hashを使う場合は、目的、守る安全・データ・再現性、保護しない場合の具体的な失敗、失敗時の停止範囲を明記する |
| HASH-FUTURE-05 | 用途が保護対象か不明な場合は、新しいhashを作らず、Unknownとして人間の判断へ送る |
| HASH-FUTURE-06 | hash不一致を理由に管理作業を再試行してはならない。再試行できるのは、保護対象hashの失敗が安全・データ・再現性に直結する場合だけである |
| HASH-FUTURE-07 | 文書追加・大幅変更の通常フローはmanifest生成、hash取得、stale検出、hash照合を要求しない |
| HASH-FUTURE-08 | 過去のhashを含む証跡は履歴として保持できるが、現行フローの受入条件、再実行条件、ルーティング条件として再利用してはならない |

Step 01でこの規範を settings/ai_component_rules.md、AI部品仕様、依頼プロンプト、正式HTMLへ反映し、Step 07で新設する軽量ガードの判定ルールにも反映する。

## 1. 廃止対象、維持対象、維持する非hash確認

### 1.1 廃止対象

| 領域 | 現行の代表例 | 廃止後 |
|---|---|---|
| 文章管理基盤 | CTXMAPの source_hash、manifest hash、snapshot hash、stale判定、A07/A08 hash不一致BLOCKED | hashなしのpath、schema、link、状態管理またはmanifest縮小 |
| context runtime | run_context_maintenance.py、validate_context_index.py、context_router.py、context_mcp_server.py、context_watch.pyのhash比較 | path境界、Secret、schema、link、状態だけを確認 |
| 自動commit | auto-commit.shのreport fingerprint、approved hash、staged byte hash | hash一致で自動許可・拒否しない。人間確認を使う |
| AI実行receipt | input_hash、artifact_hash、finding_hashを独立証跡の必須条件にすること | Run ID、Agent ID、model、skill、status、入力・出力、review mode |
| Phase受入 | Evidence hash、change hash、管理用baseline hash、manifest hashの一致 | 成果物、テスト、レビュー、非hash構造、Human Gate |
| 差分・成果物管理 | diff SHA、artifact fingerprint、証跡hashの一致 | 変更一覧、要件追跡、Schema、リンク、実行結果 |
| 将来成果物 | hash欄、hash一致Gate、hash再試行を含むテンプレート | 保護対象でないhashを追加しない |

### 1.2 原則維持候補

以下は無条件に残すのではなく、Step 06で直接の安全・データ・再現性を説明できたものだけを残す。

| 区分 | 維持候補 |
|---|---|
| 安全 | 安全停止、取引対象、注文、権限、保護入力の改ざん・取り違え検知 |
| データ | raw/catalog/DBN/normalized dataの内容同一性、データ供給元や入力の取り違え防止 |
| 再現性 | fixture、依存artifact、Replay入力、エンジン入力、再現環境の固定 |
| 条件 | hashがなくなると上記の失敗が現実化し、別の非hash手段だけでは防げないこと |

### 1.3 維持する非hashの品質確認

- JSON schema、型、必須項目、列名、状態遷移。
- HTMLのリンク、見出し、doc/index.html導線、相互参照。
- AI部品の完全名、保存先、model設定、trigger、依存関係、権限境界。
- 要件ID、設計判断ID、Unknown、Human Gate、Blocked、残課題。
- Secret、鍵、個人情報、外部I/O、Live/Broker接続、対象範囲逸脱。
- テスト、レビュー、再現手順、変更理由。

## 2. 棚卸し済みのhash発火ケース

### 2.1 文章管理基盤

- doc/ai_foundation/21_資料コード参照基盤システム詳細解説.htmlの変更検知、path/hash取得、A07/parser、validator、receipt、allowlist。
- settings/ai_component_rules.mdの軽微変更時hash更新、stale hash、input inconsistency、hash mismatch BLOCKED。
- .codex/skills/autotrade_skill_context_manifest_maintenance_v0_1のminor hash更新、source_hash入力、hash mismatch BLOCKED。
- .codex/skills/autotrade_skill_context_routing_v0_1のsnapshot hash、stale拒否、unverified/stale停止。
- scripts/context_index/の以下の処理。
  - run_context_maintenance.py
  - build_context_index.py
  - build_code_manifest.py
  - detect_context_delta.py
  - validate_context_index.py
  - context_watch.py
  - check_context_gate.py
  - context_router.py
  - context_mcp_server.py
  - auto-commit.sh

### 2.2 AI実行基盤とreceipt

- doc/ai_foundation/09_Phase実行計画作成AI部品仕様.html
- doc/ai_foundation/10_Phase実行計画書作成依頼プロンプト.html
- doc/ai_foundation/11_AI部品作成更新AI部品仕様.html
- doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html
- autotrade_skill_phase_execution_planning_v0_1
- autotrade_skill_ai_component_lifecycle_v0_1

これらの input_hash、artifact_hash、finding_hash、generic hash必須条件は管理用hashとして廃止する。

### 2.3 品質Gate、WSL、実装計画

- doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html
- doc/ai_foundation/18_Phase2-5本実装AI実行基盤設計書.html
- doc/ai_foundation/19_Phase2-5実装品質基盤実装検証.html
- scripts/quality_gate/runner.py
- scripts/quality_gate/trusted_scopes.json
- scripts/wsl_quality_gate/prepare_offline_wsl_env.sh
- scripts/wsl_quality_gate/run_isolated_p2.sh
- scripts/wsl_quality_gate/run_isolated_p3.sh
- scripts/wsl_quality_gate/run_isolated_p2.ps1
- Phase 2、P2-12、Phase 3、Phase 4、Phase 5、Phase 2-5実装基盤の計画書

change_hash、管理用diff hash、Evidence hash、証跡fingerprint、単なるbaseline一致は廃止する。fixture、raw data、依存artifact、Replay入力、保護されたWSL入力などは分類後に残す。

### 2.4 ソースコード

- src/autotrade/application/config.py
- src/autotrade/application/run_manifest.py
- src/autotrade/application/evidence.py
- src/autotrade/application/result_view.py
- src/autotrade/application/api.py
- src/autotrade/market_data/
- src/autotrade/backtest/result_store.py
- src/autotrade/backtest/replay_order.py
- scripts/phase5_external_data/run_databento_historical.py

実装上のhashを名前だけで一括削除しない。用途が保護対象かを分類し、管理用なら撤去、保護対象なら理由と失敗動作を文書化して維持する。

## 3. 実行順序

~~~mermaid
flowchart LR
  S0[Step 00 文章管理hash Gateを停止] --> S1[Step 01 文章管理基盤の規則]
  S1 --> S2[Step 02 context runtime]
  S2 --> S3[Step 03 AI receipt・計画標準]
  S3 --> S4[Step 04 品質Gate・WSL]
  S4 --> S5[Step 05 既存計画]
  S5 --> S6[Step 06 ソースコード]
  S6 --> S7[Step 07 将来ルール・軽量Agent]
  S7 --> S8[Step 08 パイロット]
  S8 --> S9[Step 09 正式HTML・引渡し]
~~~

最初に文章管理基盤を停止する。これにより、hash制度自身の仕様やスクリプトを変更する際に、そのhash制度が自分自身をBLOCKEDにする循環を避ける。

### 3.1 共通実行条件

- 作業正本は C:/project/strategy_test とする。
- WSL実機Run、外部接続、Secret、Broker、Live、クラウド、費用、権限変更は実行しない。
- 既存ユーザー変更を上書きしない。
- 歴史的receipt、manifest、Evidenceは削除・改ざんせず、現行フローから参照しない状態にする。
- 管理用hashの取得、照合、stale判定、不一致再試行は実行しない。
- 保護対象hashの失敗だけは停止し、原因を報告して修正後に再実行できる。
- 目的が不明なhashはUnknownに登録し、推測で削除・維持しない。
- Agentは定義JSONの固定modelを使用する。完全名の列挙だけで起動済みとは扱わない。
- 指定Orchestratorを multi_agent_v1__spawn_agent で起動し、multi_agent_v1__wait_agent で完了を待つ。指定Agentは個別spawn/waitする。起動不能時は RUNTIME_DISPATCH_FALLBACK_REQUIRED、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACK を記録する。

## 4. 全Step共通の権限文

各Stepの実行プロンプトと、そのStepで実行・変更するスクリプトへ、次の権限文を省略せず記載する。

~~~text
【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。
~~~

## 5. Step別実行計画

## Step 00 - 文章管理hash Gateの先行停止と移行モード固定

### 目的

以後の計画実行を文章管理基盤のhash不一致で止めない。停止対象を管理用hashに限定し、安全・データ・再現性の保護条件は残す。

### 対象とスクリプト

- scripts/context_index/context_watch.py
- scripts/context_index/check_context_gate.py
- scripts/context_index/run_context_maintenance.py
- scripts/context_index/auto-commit.sh
- settings/ai_component_rules.md
- 移行状態記録

スクリプトはwatcher、daily validator、auto-commit、A07/A08 hash Gateの通常発火を停止する。管理用hashを計算しない明示的な移行モードを設けるが、Secret、外部I/O、対象範囲逸脱、権限逸脱、保護対象hash失敗を許可するモードにしてはならない。4章の権限文を各スクリプトの冒頭コメントまたは実行ログへ記載する。

### 完了条件

- 文章・HTML・ソースコード変更で、管理用hash取得、stale判定、hash不一致BLOCKED、hash再試行が通常発火しない。
- 保護対象hash、Secret、外部I/O、対象範囲逸脱、Human Gateは停止条件として残る。
- 移行モード、解除条件、rollbackが文書化される。

### そのまま渡せる実行プロンプト

~~~text
あなたはhash管理廃止移行のStep 00担当リードである。目的は、以後の計画実行を文章管理基盤の管理用hash Gateから解放することであり、保護対象hashの安全性を弱めることではない。

起動部品:
- Orchestrator: AutoTradeProject_Orchestrator_v0_1
- Agents: AutoTrade_A06_AiComponentEngineer_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_ai_component_lifecycle_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_traceability_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
最初に AutoTradeProject_Orchestrator_v0_1 を multi_agent_v1__spawn_agent で起動し、multi_agent_v1__wait_agent で完了を待つ。上記Agentは一件ずつ個別spawn/waitする。agent_id、model、skill、status、開始・終了、入力パス、出力パス、independent、review_modeをreceiptへ記録する。起動不能時は RUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、独立実行済みと偽らない。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- AGENTS.md、README.md、settings/ai_component_rules.md
- doc/ai_foundation/21_資料コード参照基盤システム詳細解説.html
- scripts/context_index/の対象スクリプト
- 本計画書の0〜4章

作業:
1. watcher、daily validator、auto-commit、A07/A08 hash Gateの発火経路を、hash値を再取得せず静的に確認する。
2. 管理用hash Gateだけを停止する明示的な移行モードを設計する。
3. 保護対象hash、Secret、外部I/O、対象範囲逸脱、Human Gateは停止条件として残す。
4. 移行モードが既存ユーザー変更を上書きしないことを確認する。
5. 移行状態、停止対象、保護対象、rollbackを記録する。

禁止:
- 管理用hashの再計算・照合・不一致再試行。
- WSL、外部サービス、Broker、Live、Secretへの接続。
- 歴史的manifest、receipt、Evidenceの削除・改ざん。
- 保護対象hashの停止条件の解除。

レビューと完了:
AutoTrade_A90_DesignReviewer_v0_1に、管理用hashだけが停止され、保護対象と安全停止条件が残っているかをレビューさせる。完了は変更一覧、非hash確認、protected境界、rollback、Unknown、Agent receiptで判断し、管理用hashの一致は完了条件にしない。
~~~

## Step 01 - 文章管理基盤の仕様・AI部品ルールを保護hash限定へ変更

### 目的

文書追加や大幅変更のたびにmanifest、hash、stale、hash一致を要求する規範を廃止し、今後の計画・成果物にも保護対象以外のhash管理を追加しない現行ルールを正式化する。

### 対象とスクリプト

- settings/ai_component_rules.md
- doc/ai_foundation/09〜12の仕様・依頼HTML
- doc/ai_foundation/21_資料コード参照基盤システム詳細解説.html
- .codex/skills/autotrade_skill_context_manifest_maintenance_v0_1/
- .codex/skills/autotrade_skill_context_routing_v0_1/
- CTXMAP Agent/Orchestrator定義

CTXMAP更新は管理用hashを取得せず、path、schema、link、状態だけで確認する。A07/A08を新規文書のmanifest hash担当として発火させない。各スクリプトへ4章の権限文を記載する。

### 完了条件

- source_hash必須、stale hash BLOCKED、manifest hash一致、hash mismatch retryが現行規範から除去される。
- HASH-FUTURE-01〜08がsettings、AI部品仕様、依頼プロンプト、正式HTMLへ記載される。
- 歴史的hashは履歴として残り、現行Gateに使われない。

### そのまま渡せる実行プロンプト

~~~text
あなたは文章管理基盤の規範を保護hash限定へ移行するStep 01担当である。Step 00の移行モードを前提に、仕様・AI部品ルール・依頼プロンプトを更新する。

起動部品:
- Orchestrator: AutoTradeComponentLifecycle_Orchestrator_v0_1
- Agents: AutoTrade_A06_AiComponentEngineer_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_ai_component_lifecycle_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_traceability_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradeComponentLifecycle_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。指定Agentを全件個別spawn/waitする。agent_id、model、skill、status、入力、出力、independent、review_modeをreceiptへ記録する。起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- Step 00の移行状態
- settings/ai_component_rules.md
- doc/ai_foundation/09〜12、21
- CTXMAP Skill、Agent、Orchestrator定義

作業:
1. 文書管理目的のhash必須、source_hash、snapshot hash、stale BLOCKED、manifest hash一致、hash mismatch retryを除去する。
2. HASH-FUTURE-01〜08を仕様・テンプレート・プロンプトへ明記する。
3. manifest、routing、receiptをhashなしのpath、schema、link、ID、状態で扱う設計へ変更する。
4. A07/A08のtrigger、入力、出力、completionを管理用hash要求なしへ変更またはinactive化する。
5. 保護hashを使う別系統の結果は、保護目的と失敗動作を明示して受け渡せるようにする。
6. HTML相互リンク、AI部品名、入口導線、Unknown/Human Gateを更新する。

禁止:
- 文書管理hashの再生成、manifest照合、stale解消retry。
- 歴史的証跡の削除・改ざん。
- 保護hashを文書管理hashへ拡大すること。

レビューと完了:
AutoTrade_A90_DesignReviewer_v0_1が、未来の成果物へ管理hashが再導入されないこと、protected範囲が過大でないことをレビューする。完了は更新一覧、非hash確認、future rule、inactive部品、Unknown、receiptで判断する。
~~~

## Step 02 - context runtimeと自動commitから管理用hash強制を除去

### 目的

context runtimeから管理用hashの計算・比較・stale停止・不一致再試行・自動commit許可判定を除去する。非hashの安全境界・schema・link・Secret検査は残す。

### 対象とスクリプト

- scripts/context_index/run_context_maintenance.py
- scripts/context_index/build_context_index.py
- scripts/context_index/build_code_manifest.py
- scripts/context_index/detect_context_delta.py
- scripts/context_index/validate_context_index.py
- scripts/context_index/context_watch.py
- scripts/context_index/check_context_gate.py
- scripts/context_index/context_router.py
- scripts/context_index/context_mcp_server.py
- scripts/context_index/auto-commit.sh
- activeな context schema、state、routing定義

管理用hashの作成、expected hash比較、staleエラー、approved hash allowlist、report fingerprintを削除またはinactive化する。代替判定はpath境界、schema、HTML link、Secret、状態、Human Gateだけにする。全スクリプトへ4章の権限文を記載する。

### 完了条件

- 文書・コード変更イベントがhash計算なしで処理される。
- context routing/MCPがsnapshot hash staleを理由に停止しない。
- check_context_gate.pyが管理用approved hashを要求しない。
- 非hashのschema、link、Secret、path、状態確認が動作する。

### そのまま渡せる実行プロンプト

~~~text
あなたはcontext runtimeの管理用hash強制を撤去するStep 02担当である。文書参照効率化目的のhashを実行経路から外し、非hashの安全境界だけを残す。

起動部品:
- Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- Agents: AutoTrade_A120_PythonImplementer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1
- Skills: autotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ops_security_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradeProject_ImplementationQuality_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。指定Agentを個別spawn/waitし、receiptを作る。起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- Step 01の仕様とAI部品ルール
- scripts/context_index/の全対象スクリプト
- context/のschema、state、relation、routing
- 既存テスト

作業:
1. 管理用hashの計算、比較、stale、approved hash、fingerprint、hash retryの発火点を列挙する。
2. path境界、schema、HTML link、Secret、状態、Human Gateで代替する。
3. context_watch.pyをhash snapshotなしのイベント・path・状態処理へ変更する。
4. context_router.pyとcontext_mcp_server.pyからsnapshot hash、double-read hash、STALE_HASH停止を除去する。
5. check_context_gate.pyからapproved_hashes、report hash、staged byte hash判定を除去する。
6. auto-commit.shを管理用hash一致で自動許可・拒否しない運用へ変更する。
7. 新規Markdown/HTML、既存HTML大幅変更、source変更の3ケースを管理用hashなしで通すテストを作成する。

禁止:
- SHA、checksum、source_hash等を別名の管理代替として実装すること。
- protected data/repro経路を壊すこと。
- 外部接続、WSL実機Run、Live、Broker、Secret。

レビューと完了:
AutoTrade_A150_PythonCodeReviewer_v0_1は管理用hash残存を、AutoTrade_A160_TradingSecurityReviewer_v0_1はprotected境界をレビューする。完了はテスト、変更一覧、非hashGate、protected一覧、Unknown、receiptで判断する。
~~~

## Step 03 - AI実行receipt・Phase計画標準から管理用hash必須条件を除去

### 目的

AI実行基盤が、独立実行の証拠やPhase受入条件として管理用input/artifact/finding hashを要求しないようにする。Agent起動、status、model、skill、入力・出力、レビュー状態は維持する。

### 対象とスクリプト

- doc/ai_foundation/09〜12
- autotrade_skill_phase_execution_planning_v0_1
- autotrade_skill_ai_component_lifecycle_v0_1
- Phase Planning / Component Lifecycle Orchestrator・Agent定義

receiptはRun ID、Agent ID、model、skill、status、入力パス、出力パス、review mode、independent、fallbackで構成する。各スクリプトへ4章の権限文を記載する。

### 完了条件

- input_hash、artifact_hash、finding_hashの存在・一致が独立実行・レビュー・完了条件になっていない。
- 未起動Agentを区別でき、fallbackを正直に記録できる。
- 今後生成する計画・プロンプトが管理用hashを受入条件へ入れない。

### そのまま渡せる実行プロンプト

~~~text
あなたはAI実行基盤のreceiptとPhase計画標準を変更するStep 03担当である。管理用hashを独立性・レビュー・完了の必須条件から外し、実ランタイムの透明性を維持する。

起動部品:
- Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
- Agents: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradePhasePlanning_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。指定Agentを個別spawn/waitする。receiptへAgent ID、model、skill、status、入力・出力、independent、review mode、fallbackを記録する。起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- HASH-FUTURE-01〜08
- Step 02のcontext runtime変更
- doc/ai_foundation/09〜12
- Phase planningとcomponent lifecycleのSkill、Agent、Orchestrator定義

作業:
1. receipt、child-run ledger、completion Gateから管理用input/artifact/finding hash必須条件を削除する。
2. 実行ID、Agent ID、model、skill、status、入力・出力、独立実行可否、review mode、fallbackを正本とする。
3. Phase計画生成・AI部品作成プロンプトへfuture ruleを必須記載する。
4. schema、link、完全名、依存、Human Gate、Unknown、Secret、外部I/Oの非hash確認を残す。
5. historical receiptのhashは履歴に限定し、現行完了Gateへ再利用しない。

禁止:
- genericなhash存在条件。
- 管理hashの代替となるfingerprint/checksum。
- 未起動Agentの起動済み報告。

レビューと完了:
AutoTrade_A90_DesignReviewer_v0_1とAutoTrade_A80_DocumentIntegrator_v0_1が、future artifactに管理hashが混入しないこと、dispatchの正直な記録が残ることを確認する。
~~~

## Step 04 - 品質Gate・WSL・実装基盤の管理用hash受入を廃止

### 目的

コード差分、Evidence、baseline、manifest一致を管理用hashとして受入条件にする仕組みを廃止する。fixture、raw data、依存artifact、WSL保護入力、Replayなどのprotected hashは維持する。

### 対象とスクリプト

- doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html
- doc/ai_foundation/18_Phase2-5本実装AI実行基盤設計書.html
- doc/ai_foundation/19_Phase2-5実装品質基盤実装検証.html
- scripts/quality_gate/runner.py
- scripts/quality_gate/trusted_scopes.json
- scripts/wsl_quality_gate/prepare_offline_wsl_env.sh
- scripts/wsl_quality_gate/run_isolated_p2.sh
- scripts/wsl_quality_gate/run_isolated_p3.sh
- scripts/wsl_quality_gate/run_isolated_p2.ps1

change_hash、管理用diff/Evidence/baseline hash、report fingerprintを削除またはinactive化する。fixture、raw/catalog/input data、依存artifact、Replay入力、再現環境のhashは目的と失敗動作を明示して残す。各スクリプトへ4章の権限文を記載する。

### 完了条件

- 管理用change/diff/Evidence hash一致がquality Gateやhandoff条件でない。
- protected hashは対象・目的・失敗動作つきで維持される。
- scope、Secret、固定コマンド、テスト、レビュー、protected input/dataを非hashで検証できる。

### そのまま渡せる実行プロンプト

~~~text
あなたは品質Gate・WSL・実装AI基盤の管理用hashを廃止するStep 04担当である。安全・データ・再現性に直接必要なhashだけを残し、コード差分やEvidenceの管理hashを受入条件から外す。

起動部品:
- Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- Agents: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1
- Skills: autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_traceability_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradeProject_ImplementationQuality_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。指定Agentを個別spawn/waitする。起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- Step 03のAI実行receipt・計画標準
- doc/ai_foundation/05、18、19
- scripts/quality_gate/、scripts/wsl_quality_gate/
- trusted_scopes.json

作業:
1. quality Gateのhashを管理用、安全、データ、再現性、依存artifact、Unknownへ分類する。
2. 管理用change/diff/Evidence/baseline hashの計算・比較・BLOCKED・retryを除去する。
3. protected hashだけを目的・失敗動作つきで残す。
4. trusted_scopes.jsonから管理用change hashを受入条件として扱う経路を除去する。
5. target path、scope、fixed command、Secret、外部接続制限を非hashで検証する。
6. Phase handoffをテスト、レビュー、成果物存在、非hash構造、Human Gate、protected結果で判定する。

禁止:
- protectedと説明できないhashを残すこと。
- 管理hashの代替としてmtime、fingerprint、UUIDを同一性Gateにすること。
- WSL実機Run、外部接続、Live、Broker、Secret。

レビューと完了:
AutoTrade_A160_TradingSecurityReviewer_v0_1が安全境界、AutoTrade_A150_PythonCodeReviewer_v0_1が管理hash残存、AutoTrade_A130_VerificationEngineer_v0_1が非hashGateをレビューする。
~~~

## Step 05 - 既存Phase計画・受入条件・実行プロンプトを更新

### 目的

既存計画が今後の実行時に管理用hashを要求しないようにする。過去のhash値は履歴として残すが、現行受入条件から外す。

### 対象とスクリプト

- plan/Phase2-5_本実装AI実行基盤構築計画_v0.1_2026-08-06.md
- plan/Phase2_P2-12_実行計画書_v0.1_2026-08-08.md
- plan/Phase3_実行計画書_v0.1_2026-08-09.md
- plan/Phase4_実行計画書_v0.1_2026-08-11.md
- plan/Phase5_実行計画書_v0.1_2026-08-12.md
- その他activeな plan/、実行プロンプト、runbook

各計画からhash一致をStep/Phase完了条件、実行前提、retry、BLOCKEDにしている箇所を抽出する。管理用hash条件を成果物、テスト、レビュー、schema、link、Human Gateへ置換し、各計画へHASH-FUTURE-01〜08と4章の権限文を記載する。

### 完了条件

- active計画の受入条件に管理用hash一致が残っていない。
- protected data/repro/safety hashは残っている。
- 各Phaseの受入条件が成果物、テスト、レビュー、非hash構造、Human Gate、protected結果で読める。

### そのまま渡せる実行プロンプト

~~~text
あなたは既存Phase計画を保護hash限定へ更新するStep 05担当である。計画を実行可能なまま保ち、管理用hash一致を受入・handoff・retry条件から外す。

起動部品:
- Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
- Agents: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_design_review_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradePhasePlanning_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。Agentを個別spawn/waitする。receiptへAgent ID、model、skill、status、入力・出力、independent、review_mode、fallbackを記録する。起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- Step 04後のAI実行基盤と品質Gate
- 上記Phase計画、activeなplan/、要件、Human Gate/Unknown台帳

作業:
1. hash、checksum、SHA、fingerprint、manifest、Evidence hashを管理用/protected/Unknownに分類する。
2. 管理用hashの受入、前提、retry、BLOCKEDを非hash条件へ置換する。
3. protected hashは目的、入力、失敗停止範囲を明記して維持する。
4. historical hashは履歴表示に限定し、active Gateから切り離す。
5. 今後の計画へ貼り付ける各promptへ、ユーザー委譲権限とfuture ruleを入れる。

禁止:
- 保護目的を確認せず一括削除。
- 管理hashの代替となるchecksum/fingerprint。
- Unknown/Human Gateの無断Pass。
- 過去証跡の削除。

レビューと完了:
AutoTrade_A90_DesignReviewer_v0_1が受入条件を、AutoTrade_A10_RequirementsCurator_v0_1が要件・protected data/repro欠落をレビューする。管理用hashの一致は要求しない。
~~~

## Step 06 - ソースコード・テスト・外部データ処理を用途別に監査・変更

### 目的

application、market data、backtest、replay、外部データrunnerに残るhashを目的で分類し、管理用hashだけを撤去する。protected hashは維持する。

### 対象とスクリプト

- src/autotrade/application/
- src/autotrade/market_data/
- src/autotrade/backtest/
- scripts/phase5_external_data/run_databento_historical.py
- 関連テスト、fixture、schema、migration

各hashの入力、比較相手、不一致時の影響、安全・データ・再現性との直接因果を記録する。管理用manifest/evidence/result/file identity hashは撤去し、raw/catalog/input/fixture/replay/dependency hashは目的と失敗停止を残す。全スクリプトへ4章の権限文を記載する。

### 完了条件

- 管理用hashの計算・保存・比較・retryが通常実行経路から除去される。
- protected hashの意味、入力境界、失敗動作、テストが残る。
- application、market data、backtest、replay、external dataの回帰がない。
- future rule違反の新hashを追加していない。

### そのまま渡せる実行プロンプト

~~~text
あなたはソースコード内のhashを用途別に監査・変更するStep 06担当である。hashの名前だけで削除・維持を決めず、安全・データ・再現性への直接因果で判定する。

起動部品:
- Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- Agents: AutoTrade_A120_PythonImplementer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1
- Skills: autotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_traceability_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradeProject_ImplementationQuality_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。指定Agentを個別spawn/waitする。起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- Step 04〜05のprotected境界とactive受入条件
- src/autotrade/application、market_data、backtest
- scripts/phase5_external_data/run_databento_historical.py
- 関連テスト、fixture、schema、migration

作業:
1. hash利用箇所を管理用、安全、データ、再現性、Unknownへ分類する。
2. 管理用manifest/evidence/result/file identity hashを非hashのID、schema、状態、意味的検証へ置換する。
3. raw/catalog/DBN/normalized data、fixture、dependency、Replay、engine inputのprotected hashは維持する。
4. protected hashごとに、守る対象、不一致時の停止、再試行が必要な理由を仕様とテストへ記載する。
5. API、result store、replay、external data runnerを回帰確認する。管理用hash生成・一致確認は実行しない。
6. Unknownは推測で解消せず、台帳へ登録する。

禁止:
- hash名だけの一括削除。
- protected hashの削除。
- 管理hashの代替となるUUID、mtime、fingerprint、checksum。
- 外部データ取得、Broker、Live、Secret。

レビューと完了:
AutoTrade_A160_TradingSecurityReviewer_v0_1が安全境界、AutoTrade_A150_PythonCodeReviewer_v0_1が管理hash撤去、AutoTrade_A130_VerificationEngineer_v0_1が回帰を確認する。
~~~

## Step 07 - 今後の計画・成果物への保護hash限定ルールと軽量AI部品を追加

### 目的

新規文書、大幅変更文書、ソースコード、テスト、計画、AI部品が、protected以外のhash管理を再導入しないようにする。文章manifestを追加するのではなく、hash管理を追加しようとする記述だけを超軽量に検出する。

### 新設・更新部品

- 新Skill: .codex/skills/autotrade_skill_protected_hash_policy_guard_v0_1/SKILL.md
  - hash値を計算しない。
  - manifestを作らない。
  - source_hash、artifact_hash、change_hash等を保存しない。
  - 保護対象以外のhash管理導入だけを判定する。
- 新超軽量Agent: .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json
  - 出力は対象パス、候補箇所、ALLOW / NEEDS_HUMAN_GATE / BLOCKED、理由、修正提案だけの小さなJSON。
  - hash値、manifest、receipt hash、fingerprintを生成しない。
- 更新: settings/ai_component_rules.md、Phase planning、component lifecycle、design doc set、implementation qualityの各AI部品、doc/ai_foundation/09〜21、必要ならREADME.mdとAGENTS.md。

### 発火条件

- 新規Markdown/HTML、計画書、実行プロンプト、ソースコード、テスト、AI部品。
- 既存文書の大幅変更。
- Phase/Step受入条件、quality Gate、receipt schema、Orchestrator/Agent/Skill仕様の変更。

### 実行スクリプト指示

ガードは候補語句を静的に確認するだけで、hash値を取得・比較・保存しない。ALLOWはprotected目的と失敗動作が明記されている場合だけ、NEEDS_HUMAN_GATEは用途不明hashがある場合、BLOCKEDは管理用hash導入が明白な場合に返す。hash不一致retryはしない。ガードスクリプトへ4章の権限文を記載する。

### 完了条件

- 新SkillとA95 Agentが登録され、文書・計画・AI部品作成経路から発火できる。
- A95がmanifest、hash取得、stale、hash retryを要求しない。
- 新規テンプレートへHASH-FUTURE-01〜08が組み込まれる。
- A07/A08の文章manifest責務が復活しない。

### そのまま渡せる実行プロンプト

~~~text
あなたは、今後の成果物へ管理用hashを再導入させないStep 07担当である。新しいmanifest管理を作るのではなく、超軽量な保護hashポリシー判定だけを追加する。

起動部品:
- Orchestrator: AutoTradeComponentLifecycle_Orchestrator_v0_1
- Agents: AutoTrade_A06_AiComponentEngineer_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_ai_component_lifecycle_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_traceability_v0_1
- 新設: autotrade_skill_protected_hash_policy_guard_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradeComponentLifecycle_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。既存Agentを個別spawn/waitし、新設A95も定義後に個別spawn/waitする。起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- HASH-FUTURE-01〜08
- settings/ai_component_rules.md
- 既存Orchestrator、Agent、Skill一覧
- 文書追加、大幅変更、source変更の発火点

作業:
1. autotrade_skill_protected_hash_policy_guard_v0_1を作成する。
2. AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.jsonを作成し、固定model、超軽量trigger、入力、出力、停止条件を定義する。
3. A95はhash計算、manifest作成、hash一致、stale、retryをしないと定義する。
4. protected候補には目的、直接因果、失敗時停止範囲が必要とする。
5. 不明用途はNEEDS_HUMAN_GATEまたはBLOCKEDとし、推測で追加・削除しない。
6. 全作成経路へHASH-FUTURE-01〜08を組み込む。
7. A07/A08の文章manifest責務を再発火させない。

禁止:
- 新しいmanifest、source_hash、artifact_hash、change_hash、receipt hash。
- A95へのhash一致要求。
- ガード失敗をhash不一致としてretry。

レビューと完了:
AutoTrade_A90_DesignReviewer_v0_1が、A95自体が管理hashを増やしていないか、future ruleが全経路へ届くかをレビューする。
~~~

## Step 08 - 非hash運用パイロットとprotected境界確認

### 目的

新規文書、HTML大幅変更、source変更、Phase完了を管理用hashなしで通す。protected hashが必要なケースだけを維持・実行する。

### パイロットケース

1. 新規Markdown追加。
2. 新規HTML追加とdoc/index.htmlリンク。
3. 既存HTML大幅変更。
4. context対象source変更。
5. Phase/Step受入条件変更。
6. fixture/raw/replay等のprotected hashを必要とするテスト。
7. 用途不明hashを含む仮成果物のA95判定。

各ケースのスクリプトへ4章の権限文を記載する。ケース1〜5では管理用hashを計算・比較・保存しない。ケース6のprotected hash失敗は停止し、ケース7はNEEDS_HUMAN_GATEとする。

### 完了条件

- ケース1〜5が管理用hashなしで完了する。
- ケース6のprotected hash失敗が必要に応じて停止する。
- ケース7が自動許可されない。
- 実行時間、token消費、停止回数、retry回数の変化を、hashなしの観測記録でまとめる。
- 将来成果物へ管理用hashを導入しないことを確認する。

### そのまま渡せる実行プロンプト

~~~text
あなたはhash管理廃止後の代表シナリオを検証するStep 08担当である。管理用hashなしで文書・コード・計画を通せることと、protected hashの安全境界が残ることを確認する。

起動部品:
- Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
- Agents: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1
- Skills: autotrade_skill_python_test_quality_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ops_security_v0_1、autotrade_skill_traceability_v0_1
- A95: AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradeProject_ImplementationQuality_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。指定Agentを個別spawn/waitし、A95も個別起動する。未起動時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- Step 07のfuture ruleとA95
- Step 02〜06の変更済み文書、runtime、quality Gate
- 隔離されたパイロット用ファイルまたはfixture

作業:
1. 新規Markdown、HTML index link、HTML大幅変更、source変更、Phase受入変更を検証する。
2. 各ケースで管理用hashが計算・保存・比較・retryされていないことを非hash確認する。
3. protected hashだけを必要なテストで確認し、目的と失敗動作を記録する。
4. 用途不明hashをA95へ入力し、NEEDS_HUMAN_GATEを確認する。
5. schema、link、path、Secret、状態、Agent receiptを非hashで確認する。
6. 実行時間、token消費、停止回数、retry回数の変化をhashなしで記録する。

禁止:
- パイロット成果物へ管理manifestやhashを追加。
- protected hash失敗の無視。
- 管理hash失敗の再現retry。
- WSL、外部接続、Live、Broker、Secret。

レビューと完了:
AutoTrade_A130_VerificationEngineer_v0_1がシナリオ、AutoTrade_A150_PythonCodeReviewer_v0_1が管理hash不在、AutoTrade_A160_TradingSecurityReviewer_v0_1がprotected境界を確認する。
~~~

## Step 09 - 正式HTML説明・index・ルール引渡し

### 目的

廃止後のシステムを正式資料へ反映し、今後のAIと人間が誤って管理用hashへ戻さないようにする。

### 対象とスクリプト

- doc/ai_foundation/21_資料コード参照基盤システム詳細解説.html
- doc/index.html
- settings/ai_component_rules.md
- AGENTS.md
- README.md
- .codex/skills/、.codex/agents/、.codex/orchestrators/の導線
- 本計画書と実行ログ

HTML/link/schema確認はhashなしで実行する。protected hashの具体値を新しい管理用manifestへ転記しない。旧制度は履歴として説明し、現行手順・受入条件から除去する。各スクリプトへ4章の権限文を記載する。

### 完了条件

- 正式HTMLに管理用hash廃止、protected hash限定、将来禁止ルール、A95、Human Gate、rollbackが記載される。
- doc/index.htmlから正式説明資料へリンクされる。
- AGENTS/READMEを変更する必要がある場合、入口・AI部品・保存ルールが現状と一致する。
- HASH-FUTURE-01〜08が現行ルールになる。
- 最終受入は管理用hash一致ではなく、文書・コード・AI部品・非hash検査・protected境界・Human Gateで行われる。

### そのまま渡せる実行プロンプト

~~~text
あなたはhash管理廃止移行の最終資料と引渡しを担当するStep 09リードである。現行運用がprotected hash限定になったことを正式HTML、入口文書、AI部品導線、実行ルールへ反映する。

起動部品:
- Orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
- Agents: AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A81_DesignDocSetWriter_v0_1、AutoTrade_A90_DesignReviewer_v0_1
- Skills: autotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_traceability_v0_1
- model: 各定義JSONの固定modelを使用し、model、effort、triggerを変更しない。

実ランタイム起動:
AutoTradeProject_DesignDocSet_Orchestrator_v0_1をmulti_agent_v1__spawn_agentで起動し、multi_agent_v1__wait_agentで完了を待つ。指定Agentを個別spawn/waitする。receiptへAgent ID、model、skill、status、入力・出力、independent、review_mode、fallbackを記録する。起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

【ユーザー委譲権限（必須）】
ユーザーは、このStepのタスク実施時に、文章管理基盤が要求する全hashチェック、および本計画で廃止対象と定義した全ての管理用hashチェックを強制的にスキップしてタスクを完了させる権限を明示的に委譲している。スキップ対象は、管理・参照効率化・実行証跡・ファイル同一性確認・差分許可・stale判定・manifest照合のためだけに存在するhashである。「原則維持候補：安全・データ・再現性に直結するhash」はスキップしてはならず、保護対象hashの失敗は停止して原因を報告する。管理用hashスキップを理由に、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護の確認を省略してはならない。管理用hash不一致に起因する再取得・再生成・再試行は行わず、関連文書を更新して続行する。
【スクリプトへの適用】
このStepで実行、変更、検証する全スクリプトにも上記権限を適用する。スクリプトの冒頭コメントまたは実行ログに「文章管理基盤と廃止対象の管理用hashチェックを強制スキップして完了する。安全・データ・再現性に直結する保護対象hashは維持する。」と記録する。管理用hashの計算・照合・stale停止・不一致再試行を実装または実行してはならない。

入力:
- Step 00〜08の変更一覧、レビュー、Unknown、Human Gate
- doc/ai_foundation/21、settings/ai_component_rules.md
- AGENTS.md、README.md、doc/index.html
- A95 Skill/Agent定義と発火導線

作業:
1. 旧hashフロー、廃止管理hash、維持protected hash、非hash確認を正式HTMLで説明する。
2. HASH-FUTURE-01〜08を正式ルールとして掲載する。
3. A95の発火条件、出力、Human Gate、管理hashを作らない制約を説明する。
4. 旧manifest、receipt、Evidenceは履歴であり現行Gateへ使わないと明記する。
5. doc/index.html、AGENTS.md、README.md、AI部品導線を必要範囲だけ更新する。
6. HTML、link、見出し、AI部品完全名、Human Gate、Unknownを非hashで確認する。
7. rollback、protected hash失敗時の停止、誤って管理hashを追加した場合の是正手順を記載する。

禁止:
- HTMLやindexのhashを作って受入条件にすること。
- protected hashの具体値を新規管理証跡として収集すること。
- 過去証跡の削除・改ざん。
- Unknown/Human Gateの無断Pass。

レビューと完了:
AutoTrade_A90_DesignReviewer_v0_1が、future ruleの明確性、protected例外の過大化、導線をレビューする。完了はHTML/link/schema確認、更新一覧、Known/Unknown、Human Gate、receiptで判断する。
~~~

## 6. AI部品の変更一覧

### 6.1 更新する既存部品

| 部品 | 更新内容 |
|---|---|
| AutoTradeProject_Orchestrator_v0_1 | 文書管理hash Gateを通常発火させず、future ruleを作成経路へ伝播 |
| AutoTradePhasePlanning_Orchestrator_v0_1 | 管理用hashをPhase/Step受入条件へ生成しない |
| AutoTradeComponentLifecycle_Orchestrator_v0_1 | 新規・更新部品へ管理用hashを追加しない |
| AutoTradeProject_ImplementationQuality_Orchestrator_v0_1 | 管理用diff/Evidence hashをquality Gateにしない |
| AutoTradeProject_DesignDocSet_Orchestrator_v0_1 | HTML/index導線を非hashで検査 |
| AutoTrade_A05/A06 | 生成計画・部品へHASH-FUTURE-01〜08を組み込む |
| AutoTrade_A07/A08相当部品 | 文書manifest/hash通常責務をinactive化またはprotected限定化 |
| AutoTrade_A80/A81 | 正式HTMLとdoc setへprotected限定ルールを反映 |
| AutoTrade_A90/A91 | 管理hash再導入と過大なprotected分類をレビュー |
| AutoTrade_A110/A120/A130/A140/A150/A160 | test、実装、verification、debug、code/security reviewの受入条件をprotected限定化 |

### 6.2 新設部品

| 部品 | 役割 | 作らないもの |
|---|---|---|
| autotrade_skill_protected_hash_policy_guard_v0_1 | protected以外のhash管理導入を軽量検出 | hash値、manifest、fingerprint、stale |
| AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1 | ALLOW / NEEDS_HUMAN_GATE / BLOCKEDと理由を返す | hash一致証跡、hash retry、文書manifest |

新設部品も、完全名、JSON schema、trigger、model、skill、保存先、入力・出力、Human Gate、Unknown、権限境界を非hashで確認する。

## 7. Human Gate、Unknown、停止条件

### 7.1 Human Gate

| Gate | 時点 | 判定内容 |
|---|---|---|
| H0 | Step 00開始 | ユーザーの強制スキップ権限を移行記録へ反映 |
| H1 | Step 04開始前 | safety/data/reproに直結するprotected hash境界を確認 |
| H2 | Step 06完了後 | Unknown hashを個別判断し、自動削除・自動維持しない |
| H3 | Step 08完了後 | 管理hashが発火せず、protected hashが残ることを確認 |
| H4 | Step 09引渡し前 | HASH-FUTURE-01〜08、A95、正式HTML、index、入口文書を承認 |

### 7.2 Unknown

- manifest_hash、commit_marker_sha256、evidence hashが安全・データ・再現性のどれに該当するか不明。
- WSL archive、fixture、dependency、DBN catalogのhashが管理証跡か保護入力か不明。
- DB schemaや外部データの既存hash列を削除すると互換性を壊す可能性。
- historical evidenceをactive flowからどこまで切り離すか不明。

Unknownはhash不一致のretryで解消しない。対象、影響、判断材料、選択肢、必要な人間を記録する。

### 7.3 即時停止条件

- protected hashをスキップしようとした。
- Secret、鍵、個人情報、外部I/O、Broker、Live、費用、権限変更が発生しそうになった。
- 既存ユーザー変更を上書きする。
- A95やfuture ruleが管理hashを作成・保存・照合しようとした。
- 不明なhashを推測で削除・維持した。
- Agent未起動を独立実行済みと報告した。

## 8. rollbackと履歴方針

- protectedの安全・データ・再現性が壊れた場合は、そのStepの新規変更だけを戻し、管理用hash制度全体を復活させずprotected欠落を修正する。
- 管理用hash旧コードを復活させる場合はHuman Gateを要求し、復活範囲・期間・理由を明記する。
- 既存未コミット変更、歴史的manifest、receipt、Evidenceはreset、checkout、削除で戻さない。
- 本計画の実行中に新たな管理用hashを生成しない。既存hashは履歴として保全し、active flowから参照しない。
- rollback判定はhash一致ではなく、保護対象の安全性、データ取り違え、再現性、機能回帰、非hash構造で行う。

## 9. 計画書自体の完了条件

- 文章管理基盤を最初に停止する順序が明記されている。
- 廃止対象、維持候補、Unknownが分離されている。
- Step 00〜09に、順序、入力、対象、スクリプト、完了条件がある。
- 各Stepのpromptに、ユーザーの「全hashチェックを強制スキップしてタスクを完了させる」委譲権限とprotected例外がある。
- 各Stepのスクリプトへ同じ権限を適用する指示がある。
- 今後作成される計画、成果物、ソースコード、AI部品へprotected以外のhash管理を決して追加しないHASH-FUTURE-01〜08がある。
- 新設Skill/Agentがhash値・manifestを作らず、future rule違反だけを検出する。
- 非hashのschema、link、path、Secret、状態、要件追跡、レビュー、Human Gateが維持される。
- protected hashを無条件に削除しない停止条件がある。
- 本計画書作成中に文章管理基盤のhashチェックを実行しない扱いが明記されている。

## 10. 実行開始時の最終チェックリスト

- [ ] H0を記録した
- [ ] Step 00の移行モードを先に有効化した
- [ ] 管理用hashとprotected hashの境界を確認した
- [ ] 各Step promptの完全名、固定model、Skill、triggerを現行定義と照合した
- [ ] multi_agent_v1__spawn_agent / multi_agent_v1__wait_agentの実起動を要求した
- [ ] 未起動時のfallback記録を要求した
- [ ] 各Stepのスクリプトへ権限文を記載した
- [ ] Secret、外部I/O、WSL実機Run、Live、Brokerを実行しない
- [ ] 既存ユーザー変更を混ぜない
- [ ] 歴史的hashを削除・改ざんしない
- [ ] HASH-FUTURE-01〜08を今後の作成経路へ伝播する
- [ ] A95がmanifest/hash値を生成しないことを確認した
- [ ] protected hash失敗だけは停止する
