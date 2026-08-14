# AI部品ルール

## 目的

このプロジェクトでは、AI部品の命名、発火制御、保存先、Phase専用部品の扱いを明示的に管理する。

## 命名

- 汎用Orchestrator:
  `AutoTradeProject_*`
- 汎用Agent:
  `AutoTrade_Axx_*`
- 汎用Skill:
  `autotrade_skill_*`
- Phase専用Orchestrator:
  `AutoTradePhaseX_*`
- Phase専用Agent:
  `AutoTradePhaseX_Axx_*`
- Phase専用Skill:
  `autotrade_phaseX_skill_*`

## 作成ルール

- まず汎用Skill、汎用Agent、汎用Orchestratorで対応できるか確認する。
- 汎用部品で不足する場合だけ、Phase専用部品を作る。
- Phase専用部品を作るときは、理由、利用期限または凍結条件、HTML仕様書を必須にする。
- 既存名と衝突する場合は上書きせず、衝突として報告して停止する。
- Phase 1専用部品は `frozen / legacy / phase1証跡` として扱い、削除、移動、改名、上書きをしない。

## 発火ルール

- プロンプトには、使用するOrchestrator、Agent、Skillの完全名を明記する。
- AI部品タスクでは、既存部品を推測起動しない。
- 指定部品が存在しない場合は、現在のステップが作成ステップかどうかを確認する。
- 作成ステップでない場合は、既存部品で代替せず、不足部品名を報告して停止する。
- `default_orchestrator` は明示承認なしに変更しない。

### 資料・コード参照効率化の専用部品

- 新規・大幅変更のMarkdown／HTMLは、A07相当のmetadata-only判定へ1ファイル単位で渡せる。ただし、管理用hash、manifest hash、stale判定、hash mismatch retryは要求しない。
- A07はpath、artifact_id、title、見出し、目的、関係、変更種別、状態をstrict JSONで返し、manifestを直接書き換えない。schema、link、Secret、path、状態の非hash確認または理由付きBLOCKEDを受け取る。
- A08はschema、状態、path境界、関係、見出しを使ってprimary 1〜3件、supporting 0〜6件、JIT範囲、不足情報を返す。snapshot hash、stale hash、manifest hashを入力・出力・判定条件にしない。
- A07/A08はネットワーク、外部MCP、Secret、任意path、Git stage／commit／push、本文全量保存を禁止する。入力不整合、Secret疑い、状態不明、境界不明は`blocked`またはfail-closedとする。
- CTXMAPのA07、A08、A80は、Agent JSONの `model=gpt-5.6-luna`、`reasoning_effort=low` を正本とし、runtime dispatchとsanitized receiptにも同じ値を記録する。管理用hash receipt項目は追加しない。
- 文書作成、設計書セット作成、Python実装、AI部品変更の導線は、path、schema、link、Secret、状態、要件追跡の非hash確認へ渡す。validatorのhash PASSは完了条件にしない。
- この専用部品は日常の軽量保守用であり、保存のたびに常時Orchestratorを起動しない。AI部品自体の作成・変更だけは`AutoTradeComponentLifecycle_Orchestrator_v0_1`で統制する。

### 保護hash限定ガード（Step 07以降）

- 新規・大幅変更の文書、計画、ソース、テスト、受入条件、receipt、AI部品には、`AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1`を超軽量の静的判定として発火できる。
- A95と`autotrade_skill_protected_hash_policy_guard_v0_1`はhash値を計算・取得・保存・比較せず、manifest、stale、fingerprint、hash retryも作らない。出力は対象、候補、`ALLOW`／`NEEDS_HUMAN_GATE`／`BLOCKED`、理由、修正提案だけとする。
- `ALLOW`は安全・データ・再現性への直接因果、保護対象、失敗時停止範囲が明記された既存のprotected hashだけに限定する。用途不明は`NEEDS_HUMAN_GATE`、管理目的の再導入は`BLOCKED`とする。
- A95はA07/A08の文章manifest責務を代替・復活させず、A07/A08を起動してmanifestを追加しない。新規・大幅変更の通常確認はpath、schema、link、Secret、状態、要件追跡で行う。
- 新設・変更スクリプトには、管理用hashを強制スキップしprotected hashだけを維持する権限文を冒頭コメントまたは実行ログへ記載する。

### 管理用hash廃止移行モード（Step 00）

- CTXMAP_MANAGEMENT_HASH_POLICY の既定値は disabled とし、文章管理のwatcher、daily validator、A07/A08の管理用hash判定、context Gate、auto-commitを通常経路から起動しない。
- 移行中は、文章管理・参照効率化・実行証跡・ファイル同一性・差分許可だけを目的とするhashの取得、照合、stale判定、不一致再試行を強制スキップしてよい。スクリプトにも同じ権限を適用する。
- 安全・データ・再現性に直結するprotected hash、Secret、外部I/O、Human Gate、Unknown、Critical/High、対象範囲、権限境界、既存ユーザー変更保護はスキップしない。
- CTXMAP_MANAGEMENT_HASH_POLICY=legacy は移行rollback調査以外で使用しない。legacy経路は後続Stepで廃止し、通常の新規計画・成果物・ソースコードから参照してはならない。
- 既存manifest、receipt、Evidence、hashは履歴として保持し、現行の受入条件、routing、再実行条件には再利用しない。

### 今後の計画・成果物・ソースコードのhash追加禁止

- HASH-FUTURE-01: 安全・データ・再現性に直結すると明示できないhash管理を新規追加しない。
- HASH-FUTURE-02: Step/Phase受入条件へ管理用hash、証跡hash、差分hash、manifest hash、入力hashの一致を追加しない。
- HASH-FUTURE-03: 新規テンプレート、依頼プロンプト、Agent、Orchestrator、Skillへ管理用hash取得・保存・照合・再試行を追加しない。候補記述はA95の静的判定へ渡し、A95自体もhashを計算しない。
- HASH-FUTURE-04: protected hashを使う場合は、守る対象、直接因果、保護しない場合の失敗、失敗時停止範囲を明記する。
- HASH-FUTURE-05: 用途不明hashは新規作成せず、UnknownとしてHuman Gateへ送る。
- HASH-FUTURE-06: 管理用hash不一致を理由に再取得・再生成・再試行しない。
- HASH-FUTURE-07: 新規・大幅変更の文書フローはmanifest生成、hash取得、stale検出、hash照合を要求しない。
- HASH-FUTURE-08: 過去hashは履歴に限定し、現行受入、routing、再実行条件に再利用しない。

### 実ランタイム起動・待機・Fallback契約

- 完全名の列挙、JSONの読込、Skillの適用、ルートAgentの自己レビューは、Orchestrator／Agentの起動証跡ではない。
- 直接実行プロンプトは、変更前に `multi_agent_v1__spawn_agent` と `multi_agent_v1__wait_agent` の利用可否を確認し、指定Orchestratorを固定modelで実spawnする。CoordinatorはPromptで明示された全Agentを一体ずつ、各Agent JSONの固定modelを `model` 引数へ渡してspawnし、`reasoning_effort` が定義されている場合だけ同引数へ渡してwaitする。未定義のeffortはruntime既定値を勝手に上書きせず、receiptへ `null` を記録する。Orchestratorの `agents` map外の明示Agentも省略しない。
- 起動証跡には `runtime_backend`、`dispatch_mode`、`orchestrator_agent_id`、AgentごとのJSON path、model、`reasoning_effort`、Skills、`agent_id`、受付／完了status、出力参照、`independent`、`review_mode`を含める。
- spawn／wait、固定model受理、子出力取得ができない場合は `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、未起動Agent、理由、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`を先に記録し、ルートの責務チェックリストで継続する。起動不能は単独の停止条件にしないが、未起動を独立実行済みと偽らない。
- Human Gate未承認、外部I/O／Secret／費用／実資金の範囲逸脱、UnknownのPass、Critical／High未解決、必須Evidence欠落、`default_orchestrator`変更はFallback中もFail-closedで停止する。

## モデル割当ルール

- 現行の汎用AutoTrade Orchestratorである `AutoTradeProject_Orchestrator_v0_1`、`AutoTradePhasePlanning_Orchestrator_v0_1`、`AutoTradeComponentLifecycle_Orchestrator_v0_1`、`AutoTradeProject_UiMock_Orchestrator_v0_1`、`AutoTradeProject_DesignDocSet_Orchestrator_v0_1`、`AutoTradeProject_ImplementationDesign_Orchestrator_v0_1` の `model` は `gpt-5.6-terra` とする。
- サブエージェントの `model` は各 `.codex/agents/AutoTrade_A*.json` の個別定義を正本とする。オーケストレータのモデル変更だけを理由に、サブエージェントのモデルを変更してはならない。
- `AutoTradePhase1_Orchestrator_v0_1` はPhase 1の凍結証跡であり、この割当変更の対象外とする。`default_orchestrator` も変更しない。

## 保存ルール

### Blocked・残課題の正本

- Phase 0以降のBlocked、Unknown、残リスク、Human Gate待ちの現在状態は、`doc/00_全Phase残課題Blocked統合台帳.html` だけで管理する。
- 人間の承認・認証・利用許可が必要な事項は、H1/H2、RunのHuman Gate、外部API・Broker接続、Secret投入、entitlement、費用上限、環境変更を含め、発見時点で必ず統合台帳へ登録する。承認記録が見つからない場合も「未承認」として台帳に載せ、対象、期限、再開条件、必要証拠、関連Runを明記する。計画書・レビュー・実装ログにだけ承認待ちを残してはならない。
- 新しい作業を開始する前に統合台帳を確認し、対象作業に必要な承認が台帳で `解決済み` と確認できない限り、外部I/O、Secret、費用発生、本線への引渡しを実行しない。台帳の行と証拠リンクを更新してから、作業成果物へ反映する。
- 新しい課題は、既存の根本原因と同じか確認してから追加する。同じ原因なら新しい行を作らず、元のFinding IDと証拠リンクを既存行へ足す。
- 旧台帳、計画書、レビュー、Run証跡は削除せず、発見時点の履歴・生の証拠として保持する。ただし、現在状態の正本にはしない。
- 解消した行は削除せず、解消日、確認者、テスト、レビュー、Human Gateの証拠を付けて `解決済み` にする。
- 残課題、Unknown、Blocked、Human Gate、承認状態、再開条件のいずれかを更新したときは、統合台帳全体を点検する。主表の該当行だけでなく、Human Gate一覧、Unknown一覧、最新状態欄、件数表示、履歴リンク、関連Runの状態を検索し、現在状態の矛盾を同じ更新で直す。過去の事実は履歴として残すが、現在状態と混同しない表示にする。
- Run固有の生のテスト・レビュー証跡は `tests/evidence/{phase_id}/{run_id}/` に置き、統合台帳には短い説明とリンクだけを記録する。

### Windows・WSLの作業ツリー規則

  - 通常の編集・実装・文書更新は、Windows側の本リポジトリツリーだけで行う。Windows側を正本として先に保存する。
  - AIは `\\wsl.localhost` 経由の直接書込み、UNC経由のパッチ適用、WSL側の通常編集を行わない。ただしユーザー委譲（2026-08-10）により、実機テスト・隔離実行に必要な場合は、WSL側の未コミット変更をリポジトリ外のローカルアーカイブへ記録し、`git stash push --include-untracked`で可逆退避してから同期してよい。
  - 同期対象は事前に絶対パス、branch、origin、HEAD、clean/ignored状態を読み取り確認する。`.venv`、cache、wheelhouse、既存automationログなど`.gitignore`で許可された生成物は保持し、Secret、鍵、`.env`、認証情報らしい変更、未知のignored項目、想定外パスは停止条件とする。退避アーカイブは `C:\\Users\\ute3g\\AppData\\Local\\Codex\\wsl-archives\\strategy_test\\<UTC timestamp>\\` に置き、status、binary diff、未追跡一覧、stash refを記録する。
  - 退避後に許可される同期はnative Windowsからの `wsl.exe -d <distro> -- bash -lc "cd <repo> && git pull --ff-only"` だけである。force、reset、clean、checkout、rebase、remote変更、stash drop、stash pop、未コミット変更の上書きは禁止する。fast-forward不能や想定外状態はstashとアーカイブを保持して停止する。
  - 同期後はWSLのHEAD、branch、origin、clean状態、trusted scope、protected fixture hashを再確認し、stashは自動復元しない。WSL側の成果物を編集せず、証跡の正本はWindows側へ取得する。

### Human Gateの承認ルール

- ユーザーがチャットで対象Runについて明示的に「承認します」と伝えた場合、その意思表示をHuman Gateの正式な承認として扱う。
- 作業Agentは承認を推測してはならないが、明示された承認をRun ID、HEAD、fixtureのprotected hashとともに `human-gate-user-declaration.md` へ記録してよい。管理用change hashは記録しない。
- 秘密鍵、公開鍵、署名JSON、worktree外の承認チャネルは要求しない。
- 機械Gate、レビュー、Unknown、scope、hash、Secret、外部接続の停止条件は、ユーザー承認があっても省略しない。

- 正式な仕様書、設計書、検証結果はHTMLで `doc/` 配下に保存する。
- 計画書、実行プロンプト、ログ、台帳は `plan/` 配下に保存する。
- `doc/` 配下のHTML成果物は、すべて `doc/index.html` から到達できるようにする。
- Phase別HTMLは `doc/phaseX/` に保存する。
- AI実行基盤関連HTMLは `doc/ai_foundation/` に保存する。

## Phase実行計画ルール

- 各Phaseを開始する前に、必ずそのPhaseの実行計画書を作成する。
- 実行計画書は `plan/PhaseX_実行計画書_v0.1_YYYY-MM-DD.md` の形式で `plan/` 配下に保存する。
- 実行計画書は必ず複数ステップに分割し、各ステップにそのまま実行できるプロンプトを含める。
- Phase実行計画書を作成するときは、標準として `AutoTradePhasePlanning_Orchestrator_v0_1`、`AutoTrade_A05_PhaseExecutionPlanner_v0_1`、`autotrade_skill_phase_execution_planning_v0_1` を使用する。
- 依頼プロンプトの標準雛形は `doc/ai_foundation/10_Phase実行計画書作成依頼プロンプト.html` を参照する。
- 実行計画の補助HTMLを作る場合は `doc/phaseX/00_実行計画/` 配下に保存し、`doc/index.html` から到達できるようにする。

## AI部品作成変更ルール

- Skill、サブエージェント、オーケストレータの作成または変更では、まず既存の汎用部品の再利用可否を調査する。
- その後に、必要な実体ファイルを作成または変更し、最後に対象ドキュメントを更新する。
- AI部品の作成または変更では、標準として `AutoTradeComponentLifecycle_Orchestrator_v0_1`、`AutoTrade_A06_AiComponentEngineer_v0_1`、`autotrade_skill_ai_component_lifecycle_v0_1` を使用する。
- 依頼プロンプトの標準雛形は `doc/ai_foundation/12_AI部品作成更新依頼プロンプト.html` を参照する。
- 実体更新だけで終わらせず、`doc/ai_foundation/03` から `08`、`doc/index.html`、必要に応じて `AGENTS.md` と `README.md` を同じ変更セットで更新する。

## 設計書セット作成ルール

## UIモック専用部品ルール

- UIモックの生成では、まず `autotrade_skill_ui_mock_generation_v0_1`、`AutoTrade_A170_UiMockEngineer_v0_1`、`AutoTradeProject_UiMock_Orchestrator_v0_1` を完全名で指定する。
- 視覚・アクセシビリティの確認は生成担当と分離し、`AutoTrade_A171_UiVisualQaReviewer_v0_1` と `autotrade_skill_ui_visual_validation_v0_1`、`autotrade_skill_ui_accessibility_validation_v0_1` を使う。
- UI部品は固定Seed・固定基準日時の匿名ダミーデータだけで動かし、Broker、実市場データ、実口座、Secret、外部AIサービス、実注文へ接続しない。
- 正式合否は固定された `@playwright/test`、Storybook、Vitest/axe、受入確認表で判定する。AI向け `playwright-cli` は匿名ローカルモックの探索補助に限り、探索結果をPassへ変換しない。
- UIソース、Storybook、スクリーンショットは正式要件HTML、追跡表、機械Gate証跡の代替ではない。Unknown、未確認viewport、未確認状態、Critical/High指摘を残したまま合格にしない。
- 生成・レビュー部品は、単一運用者・認証不要という要件を変更せず、認証、ユーザー管理、権限管理を追加しない。

- Phase内で複数の正式HTML設計書をセットとして作成または更新する場合は、標準として `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`、`AutoTrade_A81_DesignDocSetWriter_v0_1`、`autotrade_skill_design_doc_set_writer_v0_1` を使用する。
- 単体HTML作成とレビュー反映には `AutoTrade_A80_DocumentIntegrator_v0_1` を使い、設計書セット全体の共通メタ、相互リンク、Unknown、レビュー履歴、`doc/index.html` 導線の整合は `AutoTrade_A81_DesignDocSetWriter_v0_1` が主担当する。
- 技術領域の設計判断は、Adapter、Architecture、Execution、QAなどの領域Agentが担当し、A81は承認済み内容の文書セット統合を担当する。
- 正式HTML成果物は `doc/index.html` から到達できるようにし、UnknownをPassにせず、レビュー指摘の採否を記録する。

## 実装詳細設計書ルール

- モジュール構成、実装単位、型付き入出力、永続化、正常・異常系シーケンス、非自明な規則のコード例または擬似コード、設定/監査、テスト対応、Run Manifest/互換性、追跡/Unknown、レビュー閉ループを満たす文書だけを「実装詳細設計書」と扱う。
- 詳細設計の構成標準は `doc/ai_foundation/14_実装詳細設計書構成標準.html` を正本とする。対象外の構成要素は、`N/A` と理由、確認者、代替成果物へのリンクを必須にする。
- 詳細設計書のHTML構成は `doc/ai_foundation/16_実装詳細設計書HTMLテンプレート.html`（AF-D16）を複製の基礎とし、作成依頼は `doc/ai_foundation/17_実装詳細設計書作成依頼プロンプト.html`（AF-D17）を使う。P2-D05 v0.6は品質の具体例であり、Phase固有の技術判断を流用するための雛形ではない。
- 実装詳細設計書は、技術詳細の前に、(1) 誰にでも分かるドメイン概要と機能、(2) ファイルツリーと各ファイルの説明、(3) モジュール構造図、(4) モジュール機能と入出力パラメータ表、(5) 正常系・主要異常系を含む処理フロー図、(6) スコープ内の全テストケース表をこの順で置く。例外は該当節で `N/A`、理由、確認者、代替リンクを明記する場合だけとする。
- テストケース表の各行は、テストID、テスト概要、テスト条件（入力値）、操作、期待結果、合否判定基準を必須列とする。「代表例」のみを記載して全テストと扱ってはならない。
- 詳細設計書の説明文・表内の文章・図内の説明は、固有名詞、コード、変数名、外部仕様の正式名称以外は日本語を基本とする。説明文で英単語を使う場合は直後に日本語の説明を添える。
- 図はローカルで参照できるMermaid資産を使って作成し、文字だけの構造図・処理図は作らない。コード例とファイルツリーは図ではないため、この制約の対象外とする。
- モジュール構造図の各実線矢印には、依頼、主なデータ型、イベント、または保存物の受渡し名を短く付ける。情報をノードへ詰め込まず、図の直後に「モジュール間データ受渡し表」を置き、送る部品、受け取る部品、渡すデータ・依頼、受け取り側の用途と停止条件を日本語の文章で記す。受渡しが存在しない場合だけ、理由付きで `N/A` とする。
- 構造図と受渡し表には、APIキー、認証値、口座情報などの秘密を載せない。固定の型名を示す場合も、受け渡す値の意味と、欠落・不明時に先へ進めない条件を表で説明する。
- 8章以降などの詳細契約表には、各表の前に「何を説明し、読者が何を判断できる表か」を平易な日本語で記す。テスト表の各セルは単語のみで済ませず、技術者以外にも条件・操作・期待結果・合否が分かる文章にする。
- `doc/phase2/03_市場データ詳細設計/05_Market_Data_Adapter詳細設計書.html` v0.5は上記読解順・日本語表現・Mermaid図・試験記述の具体的な書式参照とする。ただし、Phase 2固有の技術判断、外部仕様、Unknownを他の設計書へ自動適用してはならない。
- 実装可能な詳細設計書セットを作成・改訂する場合は、標準として `AutoTradeProject_ImplementationDesign_Orchestrator_v0_1`、`AutoTrade_A82_ImplementationDetailDesigner_v0_1`、`AutoTrade_A91_ImplementationDetailReviewer_v0_1`、`autotrade_skill_implementation_detail_design_v0_1`、`autotrade_skill_implementation_detail_review_v0_1` を使用する。
- A91の初回レビュー、A90の横断/Red Teamレビュー、A80/A81の改訂統合、A91の再レビューを完了するまで、実装詳細設計完了を宣言しない。
- A91のCriticalまたはHigh指摘が残る、必須構成要素が理由なく欠ける、UnknownをPassにする場合は、実装着手へ進めない。
- 実装言語、パッケージ配置、永続化基盤、外部依存が未確定の場合は、実在しない実装を作らず、UnknownとHuman Gateまたは縮退方針を記録する。

## 安全ルール

- 投資助言、売買推奨、特定商品の推奨をしない。
- UnknownをPassにしない。UnknownにはIDと決定タイミングを持たせる。
- Secret、APIキー、認証情報を出力しない。
- Fail-closed、監査証跡、手動介入後復旧条件を弱めない。
- 外部仕様を扱う場合は、公式一次情報を優先し、URLと確認日を記録する。

## AGENTS.md と README.md の更新ルール

`AGENTS.md` と `README.md` は常時更新ではなく、次のような変化が入ったときに追記または修正する。

- 標準のAI実行基盤が変わったとき
- ディレクトリ構成や保存ルールが変わったとき
- 最初に読むべき入口資料が変わったとき
- 人間またはAIが初回に迷いやすい構成変更が入ったとき

軽微な成果物追加やログ増加だけでは、毎回更新しなくてよい。

## AI基盤仕様書の追従更新ルール

汎用Skill、汎用サブエージェント、汎用オーケストレータに追加・変更・廃止が発生した場合は、実体ファイルだけで終わらせず、対応するAI基盤仕様書も同じ作業内で更新する。

- Skillに変更があった場合:
  `doc/ai_foundation/03_プロジェクト汎用Skill仕様.html`
- サブエージェントに変更があった場合:
  `doc/ai_foundation/04_プロジェクト汎用サブエージェント仕様.html`
- オーケストレータに変更があった場合:
  `doc/ai_foundation/05_プロジェクト汎用オーケストレータ仕様.html`
- 相関、発火制御、利用判断に影響する場合:
  `doc/ai_foundation/06_AI部品相関図発火制御図.html`

実装詳細設計の標準または専用AI基盤に変更がある場合は、加えて次を同じ変更セットで更新する。

- `doc/ai_foundation/14_実装詳細設計書構成標準.html`
- `doc/ai_foundation/15_実装詳細設計AI基盤仕様.html`

複数種別にまたがる変更では、該当する仕様書をすべて更新する。少なくとも、正式名称、責務、使用Skill、停止条件、相関図、更新対象表が実体と一致していることを確認する。
