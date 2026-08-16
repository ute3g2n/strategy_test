# Phase 5R バックテスト操作手順書改善 実行計画書

文書ID: `P5R-MANUAL-IMPROVEMENT-PLAN-001`
版: `v0.1`
作成日: `2026-08-16`
対象: `P5R` のローカルBacktest製品と、その利用者向けHTML操作手順書
状態: `PROMPTS_EXECUTED_WITH_RUNTIME_FALLBACK`

実行結果: Step 1〜5のプロンプトを順番に実行し、Step 6の差分確認・コミット・プッシュ準備まで完了した。指定Orchestrator／Agentの実起動はAgent thread limitで受理されなかったため、Runtime receiptへ`RUNTIME_DISPATCH_FALLBACK_REQUIRED`、未起動Agent、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`を記録した。ルートでは、Web調査、ルールHTML、手順書v0.2、Playwright追加撮影、静的品質、UI回帰、リンク、A95、完了判定、自己評価を実施した。

## 1. この計画で実現すること

現在の手順書は、15個の画面操作とPlaywright画像を持っている。しかし、最初に読んだ人が「このBacktest画面で何ができるのか」「自分はどの操作を選べばよいのか」「画面に出た専門用語は何を意味するのか」を一目でたどるための機能一覧、操作へのリンク、用語説明が十分ではない。

この計画では、次の状態を完成とする。

> 投資の初心者を含む誰が読んでも、Backtestモジュールの役割、できることの全体、できないこと、安全上の限界、各機能の操作、成功の見分け方、失敗したときの直し方、画面に出る言葉の意味を、手順書だけで迷わず理解できる。

この計画の対象は文書品質と、文書が参照する既存ローカルUIの操作確認である。外部市場Dataの追加取得、Provider変更、Broker接続、Secret投入、実注文、実資金、Paper、Liveは行わない。

## 2. 入力と現状認識

### 2.1 主な入力

- `doc/phase5R/07_運用手順/01_バックテスト手順書.html`
- `doc/phase5R/02_実装詳細設計/01_P5R実装詳細設計書.html`
- `doc/requirements/01_自動トレードシステム要件定義書_v3.html`
- `ui/mock/src/P5RBacktestScreen.tsx`
- `ui/mock/src/backtestApi.ts`
- `ui/mock/tests/p5r-backtest.spec.ts`
- `tests/phase5R/test_backtest_product_red.py`
- `src/autotrade/application/backtest_product.py`
- `plan/Phase5R_実行計画書_v0.1_2026-08-16.md`
- `doc/00_全Phase残課題Blocked統合台帳.html`
- 公式Web調査結果（後述）

### 2.2 既存UIで利用者ができること（実装確認した範囲）

1. Backtest画面を開き、P5Rの安全境界と対象Data範囲を確認する。
2. 銘柄、期間、Strategy、初期残高、Entry／Exit lookback、手数料・Slippage想定値を入力する。
3. 開始前Preflightで、型・単位、Data範囲、UTC・カレンダー、Data品質、未来参照防止を確認する。
4. 1つのBacktestを開始し、Run ID、状態、進捗、Bar数、ETAを確認する。
5. 成功したRunの5指標、Data由来、期間、Core検証、Ledgerを読む。
6. 実行中のRunを取消し、checkpointから再開する。
7. Sweepで2つの候補を実行し、親Job、子Run、成功数、失敗数、部分失敗を確認する。UIにはSweep取消もある。
8. 履歴を更新し、Runを開く。
9. 比較条件が合う2つのRunを比較し、条件が合わない比較を拒否されたことも確認する。
10. 完了RunのLedgerを非同期CSV Jobにし、完了後にダウンロードする。
11. Holdoutの確定前アクセスを止め、確定後に一度だけ評価する。
12. 固定された3つの時間窓でWalk-forwardを実行し、未来参照なしとHoldout再利用なしを確認する。
13. 画面の共通状態切替は、製品Backtestを実行する機能ではなく、UI状態表示を検査するためのテスト用表示であることを区別する。

この一覧を正式な「機能一覧」とし、各行から少なくとも1つの操作手順へリンクする。上の番号は最終手順書の機能IDに置き換えてもよいが、機能の抜け、実装以上の過大な説明、APIだけにある機能のUI機能への誤表示を許さない。

## 3. Web調査で採用する手順書要件

調査日は `2026-08-16` とする。URL、確認日、採用した理由を正式なルールドキュメントに残す。

### 3.1 初心者に伝わる文章

- 最初に「この画面は何をするものか」「できること」「できないこと」「安全上の注意」を書く。
- 読者がその場で判断できるよう、重要な結論と次の操作を先に置く。
- 1文に1つの主な動作だけを書く。主語を省略して、誰が何をするか分からなくなる文を避ける。
- 初出の専門語は、短い日本語の意味、日常のたとえ、画面での役割の順に説明する。
- API名、状態名、コード、単位、日付形式は原文を残し、すぐ隣に日本語の意味を書く。
- 「成功」「失敗」だけでなく、成功したとき何が見えるか、止まったとき次に何を直すかを書く。
- 「画面の上」「右側」だけに頼らず、見出し名、ボタン名、ラベル名、タブ名を併記する。
- 「こちら」「実行」など目的が分からないリンク・ボタン説明を避ける。

### 3.2 機能一覧と操作への導線

- 手順書の上部に、機能ID、平易な機能名、「できること」、使う場面、対応手順アンカーを持つ一覧を置く。
- 各機能は、概要から該当操作へ1クリックで移動できる。
- 各手順の冒頭に「この操作で何ができるか」と「完了すると何が見えるか」を置く。
- 1つの機能が通常経路と失敗経路を持つ場合、通常操作と失敗・復旧操作の両方へリンクする。
- UIに存在しない機能は「未対応」または「この画面ではできない」と明示し、できるように見せない。
- Backtestの一時的な実験束（Sweep）と、継続して動く運用Unit、実資金運用を分けて説明する。

### 3.3 操作手順の型

すべての手順は、原則として次の順番を持つ。

1. 手順IDと、動詞から始まる短いタイトル
2. この操作でできること（1〜3文）
3. いつ使うか
4. 操作前に必要な状態と入力値
5. 画面の場所（タブ、見出し、ラベル、ボタン）
6. 1動作ずつ番号を付けた操作
7. 成功したと判断する画面表示
8. 失敗した場合の表示、原因、次の直し方
9. この結果から言ってはいけないこと（利益保証、Live昇格など）
10. 用語リンクまたは用語説明
11. Playwright検証済み画面画像、画像の代替テキスト、撮影条件、対応Evidence
12. 対応する要件ID・受入条件ID

### 3.4 エラーと状態の説明

- エラーは「何が悪いか」だけで終わらせず、「どの入力をどう直すか」を書く。
- `QUEUED`、`RUNNING`、`SUCCEEDED`、`FAILED`、`CANCELLED`を、日本語の状態説明とともに示す。
- `STOPPED`は「計算に失敗した」と決めつけず、安全条件を満たさないため開始・読込を止めた状態として説明する。
- 再試行できる場合と、担当者調査が必要な場合を分ける。
- 動的な状態は、いつ確認するか、待つ条件、待ってはいけない条件を明示する。
- 部分成功を全体成功に言い換えない。親Jobと子Runを別々に読む。

### 3.5 画像とアクセシビリティ

- 画像はPlaywrightが、画面の要素・状態・エラー・安全境界を先にassertした直後に撮影する。
- 画像ファイル名、手順ID、撮影対象、ブラウザ、viewport、EvidenceをRegistryで対応付ける。
- 画像の`alt`は「何の画面か」だけでなく、手順の判断に必要な状態を短く表す。
- 画像だけに意味を持たせず、本文にも同じ判断に必要な情報を書く。
- デスクトップとモバイルで、手順が読めること、ボタンが隠れないこと、横スクロールで重要情報が消えないことを確認する。
- 手順書自体は、意味のある見出し、意味のあるリンク名、表見出し、キーボードで移動できるリンク、十分なコントラスト、色だけに依存しない状態表示を持つ。
- 画像・外部フォント・外部CDNに依存しない。正式成果物はローカルで開けるようにする。

### 3.6 投資初心者への安全説明

- Backtestは過去のDataに仮想的にStrategyを当てはめる実験であり、実際の注文結果ではない。
- Backtestの利益や過去の成績は、将来の利益を保証しない。
- FeeとSlippageはこのP5Rでは想定値であり、市場で実際に同じ費用・価格になることを意味しない。
- 良い期間だけを選んだり、Holdoutを調整に使ったりすると、結果を都合よく見せる危険がある。
- Backtestの成功だけでForward、Shadow、Paper、Liveへ自動的に進まない。

## 4. 成果物と保存先

| ID | 成果物 | 保存先 | 完了条件 |
|---|---|---|---|
| ART-MAN-RESEARCH-001 | 手順書要件調査ログ | `plan/phase5R/manual/01_操作手順書要件調査_2026-08-16.md` | 実装棚卸し、Web URL、確認日、採用要件、未確認事項がある |
| ART-MAN-RULE-001 | 操作手順書作成ルール | `doc/phase5R/07_運用手順/00_バックテスト操作手順書作成ルール.html` | 本計画の要件をルール、テンプレート、検査項目へ落とし、indexから到達できる |
| ART-MAN-01 | 改訂バックテスト手順書 | `doc/phase5R/07_運用手順/01_バックテスト手順書.html` | 機能一覧→手順リンク、平易な説明、用語集、通常・異常・復旧、画像、Evidence、対象外を満たす |
| ART-MAN-E2E-001 | 追加Sweep取消Playwright | `ui/mock/tests/p5r-backtest-manual-improvement.spec.ts` と `tests/evidence/phase5R/RUN-P5R-MANUAL-20260816-001/` | desktop/mobileでDOM assert後にBT-MAN-16画像を撮影し、外部通信0・重大axe違反0 |
| ART-MAN-STATIC-001 | 手順書ルール準拠検査 | `tests/phase5R/test_backtest_manual_quality.py` | 機能リンク、手順アンカー、用語、alt、画像、出典、対象外表記を機械検査できる |
| ART-MAN-COMPLETE-001 | 改善完了判定 | `doc/phase5R/06_完了/03_バックテスト手順書改善完了判定.html` | 文書レビュー、Playwright、静的検査、リンク、A95、Unknownを記録する |

## 5. Human Gateと停止境界

- 新しい外部Data、Provider、Broker、Secret、費用、実注文、実資金は扱わないため、この文書改善のための外部接続Human Gateは発火させない。
- 既存P5RのローカルData、既存Application API、既存UI、既存Playwrightを参照する範囲だけを許可する。
- Web調査は公開ページを読むだけであり、プロジェクトの実行対象Dataへ接続しない。
- 出典の意味が一致しない、公式情報を確認できない、UI実装と手順書の説明が矛盾する場合は、推測で埋めず`OPEN_NOT_PASS`として完了判定を止める。
- `P5R-UNK-001`など既存Unknownは、この作業でPassに変えない。
- 本計画のプロンプトに指定したOrchestrator／Agentが起動できない場合は、`RUNTIME_DISPATCH_FALLBACK_REQUIRED`、未起動Agent、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`を証跡に残し、起動済みと偽らずルートのチェックリストで続行する。

## 6. 実行順序

Step 1からStep 6まで、前のStepの完了条件を満たしてから次へ進む。Step 1とStep 2は計画作成後に実行する。文書の大幅変更と新規テストは、同じ作業範囲としてA95へ渡す。管理用hash、manifest、stale、fingerprint、hash retryは作成しない。

```text
Step 1 調査・棚卸し
        ↓
Step 2 ルールHTML作成
        ↓
Step 3 手順書全面改訂
        ↓
Step 4 Playwright追加撮影・静的検査・index更新
        ↓
Step 5 統合レビュー・A95・自己評価・完了判定
        ↓
Step 6 git差分確認・commit・push
```

---

## 7. Step 1 実装棚卸しとWeb調査

### 目的

現行UI/APIが本当にできることを確定し、初心者向け手順書に必要な要件をWeb根拠付きで整理する。ここでは文書を書き換えず、事実と要件を分けて記録する。

### 使用部品

- Orchestrator: `AutoTradePhasePlanning_Orchestrator_v0_1`
- Agents: `AutoTrade_A05_PhaseExecutionPlanner_v0_1`, `AutoTrade_A10_RequirementsCurator_v0_1`, `AutoTrade_A90_DesignReviewer_v0_1`
- Skills: `autotrade_skill_phase_execution_planning_v0_1`, `autotrade_skill_source_reader_v0_1`, `autotrade_skill_official_research_v0_1`, `autotrade_skill_traceability_v0_1`

### そのまま実行できるプロンプト

```text
あなたはP5R-MANUAL-IMPROVEMENT-PLAN-001のStep 1を実行するルート実行Agentです。

目的:
投資初心者にも迷いなく読めるバックテスト操作手順書を作るため、既存UI/API/テスト/要件から「実際にできること」と「手順書に必要な要件」を事実ベースで棚卸しする。公開Webを調査し、URLと確認日を残す。

対象範囲:
- C:\project\strategy_test の既存ローカル成果物とP5R UI/APIのみ。
- 外部Data取得、Broker、Secret、実注文、実資金、Paper/Liveは実行しない。

実行時の起動契約:
1. multi_agent_v1__spawn_agent と multi_agent_v1__wait_agent の利用可否を最初に確認する。
2. AutoTradePhasePlanning_Orchestrator_v0_1 の定義JSONの固定model、Phase=P5R、Step=P5R-MANUAL-01、入力・出力境界を渡してCoordinatorをspawnする。
3. CoordinatorからAutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A90_DesignReviewer_v0_1を、それぞれ定義JSONの固定modelとSkills付きでspawnし、waitする。
4. orchestrator_agent_id、agent_id、受付status、完了status、出力参照、independent、review_mode、親Run IDを記録する。
5. 起動不能なら、先にRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、各Agentの確認項目をルートで順次実施する。未起動を独立実行済みと書かない。

読む資料:
- README.md、settings/language.md、settings/ai_component_rules.md
- doc/requirements/01_自動トレードシステム要件定義書_v3.html
- doc/phase5R/07_運用手順/01_バックテスト手順書.html
- doc/phase5R/02_実装詳細設計/01_P5R実装詳細設計書.html
- ui/mock/src/P5RBacktestScreen.tsx、ui/mock/src/backtestApi.ts、ui/mock/tests/p5r-backtest.spec.ts
- src/autotrade/application/backtest_product.py、tests/phase5R/test_backtest_product_red.py
- doc/00_全Phase残課題Blocked統合台帳.html

調査内容:
1. UIのタブ、入力欄、ボタン、状態表示、成功表示、停止表示、再開表示を一覧化する。
2. APIの操作とUIの操作を対応付け、APIにしかない機能をUI機能として誤記しない。
3. 既存BT-MAN-01〜15の撮影とassertの対応を確認する。
4. Sweep取消など、実装にはあるが現行手順・画像で不足している機能を抽出する。
5. 「できること」「できないこと」「結果から言ってはいけないこと」を分ける。
6. 次の公式・公的資料を優先して確認し、URL、タイトル、確認日、採用した要件、採用しなかった要件を記録する。
   - https://www.bunka.go.jp/seisaku/kokugo_nihongo/kyoiku/92484001.html
   - https://www.bunka.go.jp/koho_hodo_oshirase/hodohappyo/pdf/92488301_03.pdf
   - https://www.w3.org/TR/WCAG22/
   - https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels
   - https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html
   - https://www.w3.org/WAI/tutorials/forms/notifications/
   - https://www.w3.org/WAI/tutorials/forms/
   - https://www.buckinghamshire.gov.uk/about/design-resources/help-users-complete-a-series-of-tasks-in-a-logical-order/
   - https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-47
7. 公式URLを確認できない内容は推測でルールにしない。

成果物:
- plan/phase5R/manual/01_操作手順書要件調査_2026-08-16.md
- plan/phase5R/manual/01-runtime-dispatch.md
- plan/phase5R/manual/01-traceability.md

成果物の最低内容:
- 実装機能カタログ（機能ID、UI場所、操作、成功表示、停止・復旧、手順ID候補）
- UIにない機能とP6以降へ残す機能
- 初心者向け用語候補と説明方針
- Web出典のURL、タイトル、確認日、根拠要約、未確認事項
- ルール候補と、各ルールの根拠
- UnknownはOPEN_NOT_PASSで残す

完了条件:
- 実装の事実と文章上の改善提案が混ざっていない。
- UI機能の抜け候補と過大表示候補が明示されている。
- Web出典のURLと確認日がある。
- 外部Data、Broker、Secret、実注文、実資金に触れていない。
```

### Step 1の完了条件

- 実装機能カタログ、操作手順ID対応、用語候補、Web出典、未確認事項が保存される。
- 現行手順書の不足が「機能一覧・リンク」「平易な日本語」「用語」「異常・復旧」「画像・アクセシビリティ」「安全説明」に分類される。

---

## 8. Step 2 操作手順書作成ルールHTMLの作成

### 目的

Step 1の事実とWeb根拠を、今後の手順書作成・改訂に再利用できる正式HTMLルールへ固定する。

### 使用部品

- Orchestrator: `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`
- Agents: `AutoTrade_A81_DesignDocSetWriter_v0_1`, `AutoTrade_A90_DesignReviewer_v0_1`, `AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1`
- Skills: `autotrade_skill_design_doc_set_writer_v0_1`, `autotrade_skill_html_doc_writer_v0_1`, `autotrade_skill_official_research_v0_1`, `autotrade_skill_traceability_v0_1`, `autotrade_skill_protected_hash_policy_guard_v0_1`

### そのまま実行できるプロンプト

```text
あなたはP5R-MANUAL-IMPROVEMENT-PLAN-001のStep 2を実行するルート実行Agentです。

目的:
Step 1の調査結果を完全に反映し、初心者向けHTML操作手順書を作るための正式な「バックテスト操作手順書作成ルール」を作成する。

実行時の起動契約:
1. multi_agent_v1__spawn_agent と multi_agent_v1__wait_agent の利用可否を確認する。
2. AutoTradeProject_DesignDocSet_Orchestrator_v0_1を固定modelでspawnする。
3. AutoTrade_A81_DesignDocSetWriter_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1を個別spawnしてwaitする。
4. 固定modelは定義JSONを正本とし、代替model・default_orchestratorへの置換をしない。
5. 起動不能時はRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを先に記録する。

入力:
- plan/phase5R/manual/01_操作手順書要件調査_2026-08-16.md
- 本計画書の第3章
- doc/phase5R/07_運用手順/01_バックテスト手順書.html
- doc/index.html、doc/00_全Phase残課題Blocked統合台帳.html

作成対象:
- doc/phase5R/07_運用手順/00_バックテスト操作手順書作成ルール.html

ルールドキュメントに必ず含める章:
1. 文書ID、版、日付、状態、目的、対象読者
2. 手順書の完成ゴールとP5Rの安全境界
3. 機能カタログの必須列と機能→手順アンカーの一対一追跡ルール
4. 初心者向け文章ルール（短文、1文1動作、初出用語、原文ラベル併記、たとえ、禁止表現）
5. 手順ごとの必須テンプレート（目的、前提、場所、操作、成功表示、失敗・復旧、禁止される解釈、用語、画像、要件）
6. 機能別の通常・異常・復旧経路の書き分け
7. 状態、エラー、停止理由、再試行の説明ルール
8. Backtest固有の安全説明（仮想結果、過去成績、Fee、Slippage、Holdout、Liveへの自動昇格禁止）
9. スクリーンショットのPlaywright取得契約、assert先行、Registry、alt、caption、desktop/mobile、外部通信0
10. HTMLの見出し、リンク、表、キーボード、色、動的状態、画像代替のアクセシビリティ要件
11. 用語集の作成ルール
12. Web調査の記録方法（公式URL、確認日、根拠、採用／不採用、未確認）
13. 静的検査・Playwright・axe・リンク検査・初心者レビューの完了Gate
14. 文書変更時の版、レビュー履歴、追跡ID、Unknown、後続更新ルール

禁止:
- UIやAPIにない機能を「できる」と書かない。
- UnknownをPassにしない。
- 外部CDN、Secret、API key、Account ID、実Data取得、実注文を追加しない。
- 管理用hash、manifest、stale、fingerprint、hash retryを作らない。

doc/index.htmlに新ルール文書へのリンクを追加し、手順書と相互リンクする。既存P5R完了を覆すのではなく、「利用者向け文書を改善した追補」として状態とレビュー履歴を明記する。

完了条件:
- ルールHTML単体で読める。
- ルールが本計画とStep 1調査の全要件を含む。
- doc/index.htmlから到達できる。
- A95は対象パスの管理用hash再導入だけを静的判定し、hash値を計算・保存・比較しない。
```

### Step 2の完了条件

- ルールHTMLが作成され、機能一覧、初心者向け文章、操作テンプレート、画像、アクセシビリティ、検証、出典を網羅する。
- doc/index.htmlからルールと手順書へ到達できる。

---

## 9. Step 3 ルール準拠の手順書全面改訂

### 目的

既存15手順を単なるボタン列ではなく、初心者が機能を選び、操作し、結果を判断し、失敗から戻れる文書へ作り替える。追加でUIにあるSweep取消をBT-MAN-16として扱う。

### 使用部品

- Orchestrator: `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`
- Agents: `AutoTrade_A81_DesignDocSetWriter_v0_1`, `AutoTrade_A80_DocumentIntegrator_v0_1`, `AutoTrade_A90_DesignReviewer_v0_1`, `AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1`
- Skills: `autotrade_skill_html_doc_writer_v0_1`, `autotrade_skill_design_doc_set_writer_v0_1`, `autotrade_skill_traceability_v0_1`, `autotrade_skill_protected_hash_policy_guard_v0_1`

### そのまま実行できるプロンプト

```text
あなたはP5R-MANUAL-IMPROVEMENT-PLAN-001のStep 3を実行するルート実行Agentです。

目的:
00_バックテスト操作手順書作成ルール.htmlに完全準拠して、01_バックテスト手順書.htmlを抜本的に改訂する。初心者が「何ができるか→どの操作か→何が見えれば成功か→止まったらどうするか」を1クリックで追えるようにする。

実行時の起動契約:
1. AutoTradeProject_DesignDocSet_Orchestrator_v0_1を固定modelでspawnする。
2. AutoTrade_A81_DesignDocSetWriter_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1を個別spawnしてwaitする。
3. 起動不能なら、RUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを保存し、独立実行済みと記載しない。

入力:
- doc/phase5R/07_運用手順/00_バックテスト操作手順書作成ルール.html
- plan/phase5R/manual/01_操作手順書要件調査_2026-08-16.md
- doc/phase5R/07_運用手順/01_バックテスト手順書.html
- ui/mock/src/P5RBacktestScreen.tsx、ui/mock/src/backtestApi.ts、ui/mock/tests/p5r-backtest.spec.ts
- doc/requirements/01_自動トレードシステム要件定義書_v3.html
- doc/phase5R/02_実装詳細設計/01_P5R実装詳細設計書.html

更新対象:
- doc/phase5R/07_運用手順/01_バックテスト手順書.html

必須の文書構成:
1. 文書の読み方と初心者向け結論
2. Backtestとは何か、何のために使うか、何が分からないか
3. P5Rでできること一覧。機能ID、平易な機能名、できること、使う場面、対応BT-MANリンク、成功の見方を表にする。
4. P5Rでできないこと・後続Phaseの機能（外部Data、Broker、実注文、Paper、Live、継続運用Unitなど）
5. はじめての人向け最短コース（画面→条件→Preflight→Single→5指標→Details）
6. 画面の各部分を上から順に説明する。見出し、タブ、ラベル、ボタンを正確に書く。
7. BT-MAN-01〜15を、ルールの手順テンプレートで書き直す。
8. BT-MAN-16「Sweepを途中で取消する」を追加する。UIにあるSweep取消ボタンの操作、CANCELLEDの確認、親Jobと子Runの読み方を説明する。
9. 機能一覧から各手順へのアンカーリンク、各手順から一覧への戻りリンクを付ける。
10. 用語集（Backtest、Strategy、Turtle SYS1/SYS2、Data、銘柄、Spot、1m、UTC、Entry/Exit lookback、bps、Fee、Slippage、Preflight、Run、Queue、進捗、ETA、checkpoint、Sweep、親Job、子Run、部分失敗、Ledger、Signal、Virtual Fill、残高、Equity、総損益、最大ドローダウン、勝率、Holdout、Walk-forward、未来参照、CSV、Provenance、Application API）を初心者向けに説明する。
11. 失敗・停止理由一覧。コード、意味、直す箇所、再試行可否を示す。
12. Playwright画像とEvidenceの読み方。各画像のaltとcaptionを改善し、画像がなくても本文だけで操作が分かるようにする。
13. 「この結果から言ってはいけないこと」を独立章にする。
14. 出典と、今回の改訂履歴を追加する。

平易さの必須条件:
- 初出の専門語の直後に「つまり〜」で短く言い換える。
- 英語状態名は残し、日本語の意味を併記する。
- 「入力してください」だけで終わらせず、入力例と正しい形式を書く。
- 1ステップに複数のクリックや判断を詰め込まない。
- 失敗手順には、失敗させる理由、画面で確認する文字、元に戻す方法を書く。
- 「良い」「悪い」を数字だけで判断しないことを明記する。
- UIに存在する「2番目の候補を意図的に失敗させる」は検査用の操作であり、通常の投資判断の入力ではないと説明する。

機能の正確さ:
- UIで実際に使える操作とAPIだけに存在する操作を分ける。
- Sweepは現在のUIが生成する2候補を中心に説明し、APIの上限をUIで任意入力できるように誤解させない。
- 共通状態切替は製品Backtest機能ではなくUI検査用表示として「対象外」にする。
- P5Rの既存Open Unknownを完了扱いにしない。

完了条件:
- 機能一覧の全行に操作手順リンクがある。
- BT-MAN-01〜16がすべて、目的・前提・操作・成功・失敗・復旧・禁止解釈・用語・画像・受入IDを含む。
- 用語集と本文で、初心者が最初の1回読んだだけで操作できる。
- doc/index.htmlからルールと手順書へ到達できる。
```

### Step 3の完了条件

- 手順書が機能一覧を最初に示し、各機能から操作へ飛べる。
- 専門用語が初出で説明され、各操作に成功・失敗・復旧がある。
- UIの実装以上に「できる」と書いていない。

---

## 10. Step 4 Playwright追加撮影・静的検査・導線更新

### 目的

追加したSweep取消手順を実画面で検証し、手順書の構造を機械的に検査する。既存15画像のPlaywright証跡は保持し、追加RunでBT-MAN-16をdesktop/mobile撮影する。

### 使用部品

- Orchestrator: `AutoTradeProject_ImplementationQuality_Orchestrator_v0_1`
- Agents: `AutoTrade_A130_VerificationEngineer_v0_1`, `AutoTrade_A90_DesignReviewer_v0_1`
- Skills: `e2e-testing`, `autotrade_skill_ui_accessibility_validation_v0_1`, `autotrade_skill_html_doc_writer_v0_1`, `autotrade_skill_traceability_v0_1`

### そのまま実行できるプロンプト

```text
あなたはP5R-MANUAL-IMPROVEMENT-PLAN-001のStep 4を実行するルート実行Agentです。

目的:
BT-MAN-16のSweep取消をPlaywrightで実画面確認し、desktop/mobile画像とRegistryを保存する。また、手順書作成ルールを機械的に検査する。

実行時の起動契約:
1. AutoTradeProject_ImplementationQuality_Orchestrator_v0_1を固定modelでspawnする。
2. AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A90_DesignReviewer_v0_1を個別spawnしてwaitする。
3. 起動不能ならRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

実装・検証:
1. ui/mock/tests/p5r-backtest-manual-improvement.spec.tsを追加または更新し、既存playwright.config.tsのchromium-desktopとchromium-mobileで動くようにする。
2. http://127.0.0.1:8765/api/backtest/resetでローカル状態をリセットする。
3. Backtest画面を開き、Sweepタブを開き、Sweep開始後に「Sweep取消」を押す。
4. 「状態: CANCELLED」と、親Job・子Runが表示されることをDOM assertする。
5. assert成功後にだけ、BT-MAN-16.pngを撮影する。
6. 保存先はtests/evidence/phase5R/RUN-P5R-MANUAL-20260816-001/manual-capture/{project}/BT-MAN-16.pngとし、Registryにmanual_id、viewport、assertion_before_screenshot、screenshot path、external_requests、axe_blocking_violationsを記録する。
7. `external_requests=[]`、critical/serious axe violationが0でない場合は完了扱いにしない。
8. 必要ならBT-MAN-01〜16の新しいRegistryを作るが、既存RUN-P5R-09のEvidenceを上書きしない。
9. 新画像をdoc/phase5R/07_運用手順/assets/backtest_manual/BT-MAN-16.pngへコピーし、手順書の参照と一致させる。
10. tests/phase5R/test_backtest_manual_quality.pyを作成し、次を検査する。
   - 機能カタログの各機能行にBT-MANアンカーへのリンクがある。
   - BT-MAN-01〜16のアンカー、タイトル、目的、操作、成功、失敗・復旧がある。
   - 画像のsrcが存在し、altとcaptionが空でない。
   - 用語集に主要語があり、初出語の説明がある。
   - 出典URLと確認日がある。
   - 外部Data、Broker、実注文、実資金、Paper、Liveが対象外として説明される。
   - 相対リンクの存在確認とdoc/index.htmlからの導線を確認する。
11. UIの機能や文言を変更した場合は、npm run build、npm run test -- --run、npm run lintも実行する。文書とテストだけなら、既存UIの回帰E2Eも実行する。

完了条件:
- desktop/mobileのBT-MAN-16がassert先行で撮影される。
- screenshot、Registry、manual assetの対応が取れる。
- 静的手順書検査がPASSする。
- 外部通信0、重大axe違反0、既存P5R E2EがPASSする。
```

### Step 4の完了条件

- Sweep取消の実画面画像とRegistryがある。
- 手順書の機能リンク、アンカー、画像、用語、出典、対象外が機械検査できる。
- 既存15操作の証跡を壊していない。

---

## 11. Step 5 統合レビュー・A95・自己評価・完了判定

### 目的

ルール、手順書、UI実装、画像、Evidence、要件の整合性を最後に確認し、ユーザーのゴールを満たすかを初心者視点で判定する。

### 使用部品

- Orchestrator: `AutoTradeProject_DesignDocSet_Orchestrator_v0_1`
- Agents: `AutoTrade_A80_DocumentIntegrator_v0_1`, `AutoTrade_A90_DesignReviewer_v0_1`, `AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1`
- Skills: `autotrade_skill_design_doc_set_writer_v0_1`, `autotrade_skill_html_doc_writer_v0_1`, `autotrade_skill_traceability_v0_1`, `autotrade_skill_protected_hash_policy_guard_v0_1`, `agent-self-evaluation`

### そのまま実行できるプロンプト

```text
あなたはP5R-MANUAL-IMPROVEMENT-PLAN-001のStep 5を実行するルート実行Agentです。

目的:
初心者を含む誰でもBacktestモジュールの全機能と操作を理解できるというゴールに対し、成果物を横断レビューし、問題を修正してから完了判定HTMLを作る。

実行時の起動契約:
1. AutoTradeProject_DesignDocSet_Orchestrator_v0_1を固定modelでspawnする。
2. AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1を個別spawnしてwaitする。
3. 起動不能ならRUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

レビュー観点:
1. 機能一覧が実装機能を網羅し、機能ごとに操作アンカーへ飛べる。
2. 操作手順が、目的→前提→画面場所→1動作ずつの操作→成功→失敗・復旧→禁止解釈→用語→画像→要件の順になっている。
3. 中学生が読んでも理解できる短文になっている。英語略語・コード・単位・UTC・Backtest固有語が説明されている。
4. Backtestの仮想性、将来利益非保証、Fee/Slippage想定、Holdout再利用禁止、Live自動昇格禁止が見える。
5. UIでできないことをできると書いていない。SweepのUI上の候補制限、共通状態切替のテスト用途を明示している。
6. 画像は本文の代わりになっておらず、alt/caption/撮影根拠がある。
7. desktop/mobile、キーボード、リンク目的、見出し、表、動的状態、色依存を確認できる。
8. Web出典URL、確認日、採用内容、未確認事項がある。
9. 既存P5R-UNK-001をPassにしていない。
10. A95は新規・大幅変更対象だけを走査し、管理用hashを計算・保存・比較しない。管理hash候補はBLOCKED、用途不明はNEEDS_HUMAN_GATEと記録する。

初心者レビュー:
- 手順書を最初から最後まで、コードを知らない投資初心者の立場で読み、最初に分からない語、押す場所が分からない手順、成功判断ができない手順、危険な誤解を一覧化する。
- 見つけた修正可能な問題は手順書とルールへ反映し、再検査する。
- それでも実ユーザー確認が必要な点はUnknownとして残し、Passにしない。

作成対象:
- doc/phase5R/06_完了/03_バックテスト手順書改善完了判定.html
- plan/phase5R/manual/05_統合レビュー_2026-08-16.md
- tests/evidence/phase5R/RUN-P5R-MANUAL-20260816-001/manual-quality-report.json
- tests/evidence/phase5R/RUN-P5R-MANUAL-20260816-001/agent-self-evaluation.md

完了条件:
- 重大な未解決指摘が0である。
- 文書、画像、Registry、テスト、要件、indexのリンクが通る。
- 手順書のゴールを満たす根拠と、満たしていない範囲が完了HTMLに明記される。
```

### Step 5の完了条件

- 初心者視点のレビュー記録と修正結果がある。
- 完了判定が「文書改善完了」と「システム全体のBacktest完成・将来利益保証」を混同していない。
- Open UnknownはOpenのまま記録される。

---

## 12. Step 6 Git確認・コミット・プッシュ

### そのまま実行できるプロンプト

```text
あなたはP5R-MANUAL-IMPROVEMENT-PLAN-001のStep 6を実行するルート実行Agentです。

1. git status --shortで変更を確認する。
2.今回作成・変更したファイルだけを一覧化する。既存のユーザー変更を混ぜない。
3. git diff --check、テスト結果、リンク検査、Secretスキャン、A95対象結果を確認する。
4. 新規・大幅変更HTML、Markdown、テスト、画像、Evidenceの内容を確認する。
5. 意味のある単位でcommitする。reset --hard、checkout、force pushは使わない。
6. 現在のブランチの追跡先へpushする。失敗したら変更を保持して理由を記録する。
7. push後にgit status --short、git log -1 --oneline --decorate、追跡先を確認する。
8. 最終報告には、更新ファイル、機械検証結果、Open Unknown、ブランチ、commit、push先を記載する。
```

## 13. 最終受入チェックリスト

- [x] 機能一覧が手順書の冒頭にある。
- [x] 機能一覧の各行から対応操作へ1クリックで移動できる。
- [x] 各操作に「何ができるか」「いつ使うか」「どこを押すか」「成功表示」「失敗・復旧」がある。
- [x] 専門用語は初出で説明され、用語集にもある。
- [x] Backtestの仮想性、利益非保証、費用想定、Live非自動昇格が明示される。
- [x] UIにない機能をできると書いていない。
- [x] BT-MAN-01〜16の画像とPlaywright Evidenceが対応している。
- [x] 画像はassert成功後に撮影されている。
- [x] desktop/mobile、外部通信0、重大axe違反0を確認している。
- [x] HTML相対リンク、index導線、画像参照が通る。
- [x] A95の静的ポリシー判定が対象範囲付きで記録されている。
- [x] UnknownをPassにしていない。
- [x] Gitの変更範囲、commit、push結果をStep 6で確認する。

## 14. Web調査の初期出典

最終ルールHTMLでは、URL、タイトル、確認日、採用した要件を表で記録する。

| 出典 | URL | 採用する要件 |
|---|---|---|
| 文化庁「在留支援のためのやさしい日本語ガイドラインほか」 | `https://www.bunka.go.jp/seisaku/kokugo_nihongo/kyoiku/92484001.html` | 読者に必要な情報へ絞る、情報を整理する |
| 文化庁・出入国在留管理庁「在留支援のためのやさしい日本語ガイドライン」 | `https://www.bunka.go.jp/koho_hodo_oshirase/hodohappyo/pdf/92488301_03.pdf` | 簡潔な文、情報の優先順位、不足情報の補足、図・表の活用 |
| W3C WCAG 2.2 | `https://www.w3.org/TR/WCAG22/` | 見出し・ラベル、キーボード、画像代替、色だけに依存しない情報 |
| W3C Understanding Headings and Labels | `https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels` | 見出し・ラベルだけで目的が分かること |
| W3C Understanding Link Purpose | `https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html` | リンク文字から移動先の目的が分かること |
| W3C Forms / User Notification | `https://www.w3.org/WAI/tutorials/forms/notifications/` | エラーの原因と直し方、成功・状態通知を明示すること |
| Buckinghamshire Council Step by Step | `https://www.buckinghamshire.gov.uk/about/design-resources/help-users-complete-a-series-of-tasks-in-a-logical-order/` | 全体を先に見せ、順番のある作業を番号付きで案内すること |
| Investor.gov Performance Claims | `https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-47` | Backtestは仮想結果であり、将来の利益を保証しないこと |
