# Phase 5R 実行計画書 — Backtest製品完全化とバックテスト手順書

- 文書ID: P5R-PLAN-001
- 版: v0.1
- 作成日: 2026-08-16（Asia/Tokyo）
- 状態: STEP1_PROMPT_GROUP_CREATED / STEP2_PLAN_CREATION_EXECUTED / P5R-12_COMPLETED_WITH_OPEN_UNKNOWN / P5R-H2_APPROVED_BY_DELEGATED_AUTHORITY
- 上流要件: AT-REQ-003 / 要件定義書 v3.0
- 対象Phase: Phase 5R のみ
- この文書の役割: P5Rを安全に実行するためのRunbook、各工程をそのまま依頼できる詳細プロンプト、及び「バックテスト手順書」を実画面のPlaywrightスクリーンショット付きで作る計画を定める。

> 計画作成時の注意: この計画書の作成自体はP5R-H0の承認ではなかった。その後、ユーザーからP5R全実行に必要なHuman Gate承認権限の移譲を受け、委任範囲内でP5R本体を実行した。外部Data追加取得、Provider変更、Secret利用、Broker接続、注文、Paper、Live、実資金、Cloud公開は開始していない。

> この文書でいう「実画面」とは、承認済みのローカルP5由来fixtureを実際のBacktest処理とApplication APIに通した結果を表示する画面である。固定ダミー値を見せるP4 UIモックの画面やそのPNGは、P5Rの完成手順書には使用しない。

## 1. まず結論

Phase 5Rでは、利用者がUIから次の一連を最後まで行えるBacktest製品を完成させる。

1. P5で確認済みの限定ローカルDataから、BTCUSDT又はETHUSDT、期間、Strategy、仮定値を選ぶ。
2. 型、単位、未来Data、Data品質、対象外条件を開始前に検査する。
3. 単一Backtestを開始し、待機、実行中、停止、失敗、完了、checkpointからの再開を区別して確認する。
4. 実際の処理結果として、総損益、最大ドローダウン、勝率、取引数、最終残高を根拠付きで確認する。
5. 取引、Signal、仮想Fill、残高推移、CostとSlippageの仮定まで同じRunからたどる。
6. Sweep、履歴、比較、非同期CSV、Holdout、Walk-forwardを、成功時だけでなく失敗・取消・再開時も正しく操作する。
7. その全操作を、実アプリを操作するPlaywrightテストで再現し、assert成功後に撮影したPNGを使ってHTMLの「バックテスト手順書」にする。

P5Rに入れないものは、複数の継続運用Unit、Portfolio、Account、実運用Risk、OMS、Forward、Shadow、Paper、Broker、Secret、実注文、実資金、Cloudである。Sweepは「一度に複数条件を試す実験の束」であり、P6で扱う複数運用Unitとは別物である。

### 1.1 今回のAI部品に関する判断

手順書を作るためだけの新しいAI部品は作らない。既存の次の部品を使う。

| 目的 | 再利用する部品 | 使える理由 |
|---|---|---|
| Phase計画・Gate・追跡 | AutoTradePhasePlanning_Orchestrator_v0_1、AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1 | 実行計画、要件差分、Human Gateを扱える。 |
| 実装詳細設計 | AutoTradeProject_ImplementationDesign_Orchestrator_v0_1、AutoTrade_A82_ImplementationDetailDesigner_v0_1、AutoTrade_A91_ImplementationDetailReviewer_v0_1 | API、保存、例外、テストまで実装可能な設計にできる。 |
| Python側の実装と品質 | AutoTradeProject_ImplementationQuality_Orchestrator_v0_1、A110、A120、A130、A140、A150、A160 | RED、実装、検証、限定復旧、コードレビュー、安全レビューを分けられる。 |
| UIの見た目・アクセシビリティ | AutoTrade_A171_UiVisualQaReviewer_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1 | PCとスマートフォン、キーボード、focus、axe、状態表示を独立にレビューできる。 |
| HTML手順書・導線 | AutoTrade_A80_DocumentIntegrator_v0_1、必要に応じてAutoTrade_A81_DesignDocSetWriter_v0_1 | 正式HTML、相互リンク、doc/index.html、改訂履歴を統合できる。 |
| AI部品を増やす場合の統制 | AutoTradeComponentLifecycle_Orchestrator_v0_1、AutoTrade_A06_AiComponentEngineer_v0_1 | 既存再利用調査、最小変更、AI基盤HTML追従を一つの手順で行える。 |

ただし、現状の A170 は「固定ダミーデータで動くUIモック」の担当であり、A120 はPython実装担当である。したがって、React/TypeScriptの画面を「ローカルApplication APIの実結果」に接続して実装する汎用担当は、現行inventoryでは不足している。

このため、P5R-H0承認後に行う P5R-00A で再確認し、不足が変わらなければ、次の最小追加を行う。

| 区分 | 追加候補 | 判断 |
|---|---|---|
| Skill | autotrade_skill_web_product_ui_implementation_v0_1 | 作成候補。固定モックではないローカル製品UIの実装境界を定義する。 |
| Agent | AutoTrade_A172_WebProductUiEngineer_v0_1 | 作成候補。型付きローカルApplication APIに接続するWeb製品UIと、そのcomponent/E2E接続を担当する。 |
| Orchestrator | 新設しない | AutoTradeProject_ImplementationQuality_Orchestrator_v0_1を再利用し、A172を明示して起動する。 |
| 手順書・撮影専用Agent | 新設しない | 撮影品質はA171、HTML統合はA80で責務を満たす。 |

このSkillとAgentはP5R専用ではなく、P7以降にも再利用する「ローカル製品UI」の部品にする。実際の作成は P5R-00B だけで行い、P5R-00A が REUSE_ONLY と判定した場合は P5R-00B を実行しない。

加えて、AutoTradeProject_ImplementationQuality_Orchestrator_v0_1 は現在、Python中心かつ登録済みtrusted scopeだけを品質Gate対象にする。P5Rの実UI/Playwrightを同Orchestratorで検証するには、P5R-02Aで「P5R専用のRun ID、target paths、除外path、固定ローカルfixture、固定Playwrightコマンド、Evidence root」を設計し、P5R-H1で明示承認を受けた後、P5R-03AでComponentLifecycle経由のscope登録を完了しなければならない。登録前にPlaywrightを品質Gateとして実行してはならない。

## 2. 根拠と現在地

| 根拠 | 現在分かっていること | この計画での扱い |
|---|---|---|
| 要件定義書 v3、06. Phase 5R | P5R-AC-01から16が受入対象。P5RはUIから使えるBacktest製品を完成させるPhase。 | 各ACを手順書、Playwright、Evidence、完了判定まで追跡する。 |
| 要件定義書 v3、P5R-H0/H1/H2 | 計画作成時はH0未承認だった。実行追補では、H0は範囲・Data・保存・負荷・Walk-forward・UI実接続、H1は詳細設計・RED/Golden、H2は全受入とP6引渡しを委任範囲内で代理承認済み。 | Open UnknownをPassにせず、P6・Paper・Liveは別Gateで止める。 |
| P5R再構成提案 | SCREEN-08から12等のUI構造はあるが、結果の5指標・Chart・取引・比較は固定表示例である。 | 画面構成は移行元として参照するが、固定モックを実結果又は手順書写真として採用しない。 |
| ui/mock/playwright.config.ts | desktopとmobileのPlaywright project、ローカルpreviewの土台がある。 | P5R-02で実アプリ用のtest environmentとmanual capture projectへ拡張する。 |
| p4-08.spec.ts | 外部通信監視、画面巡回、PNG、axeの実装例がある。 | 外部通信0件、証跡保存、axeの設計を再利用する。 |
| rqu-ui-11.spec.ts | 操作後にpage.screenshotとtoHaveScreenshotを行う実装例がある。 | 「assert後に撮影する」形を採用する。baselineだけを手順書画像の根拠にしない。 |
| A170定義 | 固定ダミーデータのクリック可能UIモックを生成する。 | P5R実結果UIの証拠担当にしない。画面構造の移行補助に限定する。 |

P4のPlaywrightテストは、画面構造、外部通信監視、a11y、撮影コードの回帰確認には再利用できる。ただし、固定モックとローカルpreviewを対象にした既存P4のPNG、trace、PASSは、P5R-AC-14の「Application APIを通る実結果」の受入Evidenceに流用しない。P5R専用E2Eが実Data・実Application処理・実UI結果の対応を検証してから、新たに撮影する。

## 3. P5Rの完成定義と範囲

### 3.1 「Backtestが完成」と呼べる最低条件

P5Rの完了は、見た目が整ったことでも、数字が一度表示されたことでもない。次の四つがそろった状態である。

1. 実処理: 保存済み・承認済みのローカルP5範囲Dataを、UI入力からApplication API、Backtest Core、保存結果まで実際に通す。
2. 正しさ: 入力検査、5指標、取引詳細、Sweep、CSV、Holdout、Walk-forward、異常系を、独立期待値とE2Eで確認する。
3. 操作可能性: PCとスマートフォンで、名前、role、キーボード、focus、状態、エラー理由が分かり、利用者が安全に操作できる。
4. 説明可能性: どの操作をし、どの画面で何を見て、失敗時に何をするかを、実際のPlaywrightスクリーンショット付き手順書で追える。

### 3.2 P5Rに含めるもの・含めないもの

| 分類 | 含める | 含めない |
|---|---|---|
| Data | 既存ローカルP5証跡のBTCUSDT/ETHUSDT、Spot、1m、UTC、CRYPTO_24_7_UTCの承認範囲 | 外部Data取得、Provider変更、対象銘柄拡張、再配布 |
| Backtest | Single Run、queue、progress、cancel、failure、retry、checkpoint resume、5指標、詳細 | 実注文、実際の約定、利益保証、実市場コストの主張 |
| 実験 | Sweep、負荷見込み、部分失敗、履歴、比較、CSV | 継続運用Unit、Portfolio、Account、資金配分 |
| 評価 | Holdout、Walk-forward、未来参照拒否 | 結果を見て自動採用する仕組み、運用への自動昇格 |
| UI | Application APIの実結果、PC/mobile、a11y、手順書 | 固定ダミーを実結果と表示、UIから直接DB/Coreへ書込み |
| 運用 | ローカル限定、単一運用者、認証不要 | Forward、Shadow、Paper、Broker、OMS、実運用Risk、Live |

### 3.3 Gateと停止境界

| Gate | 人が確認・承認すること | 通過前に止めること | その後に許可すること |
|---|---|---|---|
| P5R-H0 | P5R対象、既存ローカルData利用範囲、保存、固定PCの標準/境界負荷、Walk-forward窓、UI実接続、Open Unknown | P5R実装、UI実接続、外部Data追加取得、完成宣言 | 詳細設計、差分追跡、RED/Golden設計 |
| P5R-H1 | 詳細設計、Data Adapter、5指標定義、Sweep/CSV/Holdout異常系、RED/Golden、manual capture設計 | 実装、テストGreen化、手順書の実画面採取、完成宣言 | 実装、ローカル統合テスト、実画面のPlaywright撮影 |
| P5R-H2 | AC-01から16、手順書、対象外、Open Unknown、P6引渡し | P6実装・実行、Paper、Live、後続への昇格 | P6-H0の正式計画と承認準備のみ |

計画作成時の規則として、H0/H1/H2はいずれも対象を明示した承認が必要であり、P5-H2の過去承認をP5R-H0へ読み替えない。今回の実行では、ユーザーが全Human Gate承認権限を明示的に移譲したため、P5R専用のEvidenceへ代理承認を記録した。

## 4. 将来作る成果物

| 成果物 | 予定場所 | 完成条件 |
|---|---|---|
| P5R要件・差分・追跡HTML | doc/phase5R/01_要件追跡/ | REQ、UC、Screen、State、API、Test、Evidence、Gate、Unknownを双方向に追える。 |
| P5R詳細設計HTMLセット | doc/phase5R/02_実装詳細設計/ | Data Adapter、Run/Job、保存、5指標、Sweep、CSV、Holdout/WF、UI契約、例外、テストが実装可能な粒度。 |
| RED/Golden・E2E設計 | doc/phase5R/03_テスト設計/ と tests/evidence/phase5R/ | 期待値、失敗注入、実行入口、対象scope、fixture、Evidenceが確定している。 |
| P5R品質Gate scope登録 | scripts/quality_gate/trusted_scopes.json と対応するP5R Run Manifest/Evidence | H1で承認された固定Run ID、target paths、fixture、固定コマンドだけがP5R実装/Playwrightの品質Gate対象である。 |
| P5R実装・品質証跡 | src/、ui/、tests/、tests/evidence/phase5R/<RunId>/ | 実Backtest結果をローカルに限定してUIへ投影し、機械Gateとレビューを通過。 |
| 手順書スクリーンショットの生証跡 | tests/evidence/phase5R/<RunId>/playwright/manual-capture/ | Playwrightの操作・assert成功後に作られ、テストID、viewport、fixture、Run IDと対応する。 |
| 手順書用の静的画像 | doc/phase5R/07_運用手順/assets/backtest_manual/ | 生証跡から機械的に採用したPNGのみ。手作業の合成・描き替え・置換をしない。 |
| バックテスト手順書 | doc/phase5R/07_運用手順/01_バックテスト手順書.html | 全UI操作が文章、画像、Test ID、AC、異常時の扱いで100%対応。 |
| 完了判定・P6再引渡し | doc/phase5R/06_完了/、plan/phase5R/、統合台帳 | AC、Unknown、境界、Evidence、H2、人の判断を隠さない。 |

正式HTMLを追加したら、doc/index.htmlから到達可能にする。P5R-H0/H1/H2、Unknown、Blocked、再開条件を変更したら、doc/00_全Phase残課題Blocked統合台帳.htmlの該当行だけでなく、同HTMLの現在状態・一覧・履歴リンクも整合させる。

## 5. バックテスト手順書と実スクリーンショットの設計

### 5.1 手順書の読者と約束

手順書は、専門用語を知らない利用者でも「どこを押すか」「その前に何を確認するか」「失敗したとき何をしてよいか」が分かる日本語HTMLにする。

各操作番号には、必ず次を載せる。

1. 目的: 何のために行う操作か。
2. 前提: Data、権限、Gate、画面状態、利用可能な操作。
3. 操作: ボタン・入力欄の可視名、入力する値の意味、順番。
4. 確認: 画面上で何が表示されれば正しいか。
5. 失敗時: 開始してはいけない条件、表示される理由、利用者が次に取る安全な行動。
6. 実画面: 同じ操作を行ったPlaywrightテストが撮影したPNG。
7. 追跡: 手順ID、P5R-AC、Screen/State、Playwright Test ID、source Run ID。

数値は「この固定fixtureでの検証結果」であり、将来の利益、実市場のコスト、実取引の結果を保証しないことを、表紙・5指標・Cost/Slippageの各節で明記する。

### 5.2 撮影してよい画面の条件

PNGを手順書に採用できるのは、すべて次を満たす場合だけである。

1. P5R-H1が明示承認済みである。
2. P5R-H0で許可された既存ローカルP5由来fixtureだけを使い、外部通信が0件である。
3. fixtureは固定されているが、結果は固定ダミーではなく、同じテスト中に実際のApplication APIとBacktest処理が返したものである。
4. PlaywrightがUI操作を行い、画面の状態・重要な値・操作可否・エラー理由をassertした後に同じページを撮影している。
5. PNGにSecret、API key、URL credential、口座情報、個人情報、実資金、注文情報、絶対path、実利益保証と読める表示がない。
6. desktop又はmobileのviewport、Test ID、fixture ID、source Run IDが画像台帳で追える。
7. visual/a11yのCritical又はHighが残っていない。

上のどれか一つでも欠けるPNGは、Evidenceとして残しても手順書の正式画像に採用しない。

### 5.3 「固定fixture」と「固定ダミー」の違い

この二つを混同するとP5R-AC-14に違反する。

| 種類 | 許可 | 理由 |
|---|---|---|
| 固定fixture | 条件付きで許可 | 同じローカルP5由来入力で、実処理を何度でも再現してテストするため。 |
| 固定ダミー結果 | 不許可 | 画面内にあらかじめ書いた損益・取引・比較表を見せても、Backtestを実行した証拠にならないため。 |
| 手作業で作った画面画像 | 不許可 | Playwrightによる実操作・assert・撮影の連鎖が失われるため。 |
| screenshot baseline | 補助として許可 | 見た目の差分検出に使える。ただし、手順書画像の根拠は同テストのassert後PNGにする。 |

### 5.4 証跡、正式画像、HTMLの三層

| 層 | 保存先 | 書いてよいもの | 役割 |
|---|---|---|---|
| 生証跡 | tests/evidence/phase5R/<RunId>/playwright/manual-capture/ | Playwright PNG、trace、HTML report、操作ログ、sanitized capture registry | テストが実際に何をしたかを残す。 |
| 採用画像 | doc/phase5R/07_運用手順/assets/backtest_manual/ | 生証跡から採用した変更なしPNG、採用台帳 | 読者がHTMLで表示する静的資産。 |
| 手順書 | doc/phase5R/07_運用手順/01_バックテスト手順書.html | 操作説明、figure、caption、AC/Test ID表、境界・Unknown | 利用者が安全に操作するための説明書。 |

Playwrightは生証跡の場所にだけPNGを出力する。その後の採用処理は、capture registryに記載されたテストID・source Run ID・viewport・PNG名が一致するものだけを静的資産へコピーする。手作業で別PNGを混ぜない。画像そのものに文字を描き足したり加工したりせず、必要な説明はHTMLのcaption、操作番号、周辺の文章で行う。

### 5.5 Playwright手順書撮影テストの共通契約

P5R-02で最終確定するが、最低限次を守る。

1. テスト開始時に、隔離されたローカル試験状態を作り、前のRun・CSV・失敗状態を持ち込まない。
2. P5R-H0で許可されたfixtureと基準時刻を明示し、UI・Application API・Coreが同じfixtureを参照する。
3. 外部request監視を有効にし、許可されていない通信が一件でもあれば失敗にする。
4. selectorは画面上の可視名、role、label、test idを使い、座標クリックや曖昧な文字列だけに依存しない。
5. 画面を操作した直後に、API由来の状態、Queue/Run/Job状態、重要数値、操作ボタンのenabled/disabled、理由表示をassertする。
6. assert成功後に page.screenshot を呼び、PNG名を手順ID・状態・viewportで安定させる。
7. 見た目の回帰検知には toHaveScreenshot を追加してよいが、baseline更新だけで手順書画像を合格にしない。
8. desktopとmobileで意味が変わる操作は両方を撮影する。画面が同一意味で、mobileでは説明のために全体が読みにくい場合は、mobile専用の実操作後画面を追加撮影する。
9. 失敗、取消、再開、拒否、比較不能、CSV失敗、future Data拒否なども正常系と同じくassert後に撮影する。
10. すべての手順番号が少なくとも一つのPlaywright Test IDと一枚以上のPNGに結び付くまで、手順書を完成扱いにしない。

### 5.6 手順書の章立てと操作範囲

| 手順章 | 主な操作 | 必ず説明する失敗・注意 |
|---|---|---|
| BT-MAN-01 この手順書でできること・できないこと | P5R対象、限定Data、Backtestと実注文の違い | Broker、Paper、Live、実資金、外部Data取得が対象外であること。 |
| BT-MAN-02 DataとStrategyを確認する | BTCUSDT/ETHUSDT、期間、Strategy、仮定値の選択 | 対象外銘柄、型/単位不正、未来Data、品質不良を開始前に拒否すること。 |
| BT-MAN-03 単一Backtestの条件を作る | preflight、設定保存の扱い、開始確認 | 未検査又は不正な条件では開始できないこと。 |
| BT-MAN-04 開始・待機・進捗を確認する | Run開始、queue、progress、残り、状態表示 | Waiting/Stopped/FailedをCompletedと読み違えないこと。 |
| BT-MAN-05 停止・失敗・再実行・再開 | cancel、stop、failure、retry、checkpoint resume | checkpoint不一致では自動再開しないこと。 |
| BT-MAN-06 5指標と結果を読む | 総損益、最大DD、勝率、取引数、最終残高 | 仮定値と実測値、検証結果と利益保証を混同しないこと。 |
| BT-MAN-07 取引・Signal・仮想Fillをたどる | detail、chart、balance、cost/slippage仮定 | 別Runの詳細を混ぜないこと。 |
| BT-MAN-08 Sweepを作る | 範囲、刻み、上限、展開、重複、件数、負荷 | 無効条件、重複、上限超過は開始しないこと。 |
| BT-MAN-09 Sweepを監視・復旧する | 行別queue、部分失敗、取消、再開 | 失敗行を隠して全件成功にしないこと。 |
| BT-MAN-10 履歴と比較を使う | all history、latest、compatible compare、差分 | 条件が違うRunを比較可能と表示しないこと。 |
| BT-MAN-11 CSVを作る | CSV job開始、進捗、取消、失敗、完了、参照 | 大量表/CSVでUIを止めず、失敗を成功と表示しないこと。 |
| BT-MAN-12 Holdoutを確認する | train/validation/holdout境界、役割、結果確認 | holdoutを調整に使い回さないこと。 |
| BT-MAN-13 Walk-forwardを実行する | 窓設定、窓別Run、窓別結果 | 未来参照、重複、隙間、境界だけの確認を拒否すること。 |
| BT-MAN-14 警告・監査・対象外を読む | warning、audit、Open Unknown、scope banner | P5R外の操作を開始しないこと。 |
| BT-MAN-15 キーボードとスマートフォン | Tab/Shift+Tab、Enter/Space/Escape、focus、mobile | colorだけに頼らず、操作不能・見切れを放置しないこと。 |

### 5.7 AC・手順・テスト・スクリーンショットの追跡表

P5R-02で最終テストIDと正確な画面遷移を決める。次の表は、計画段階で省略を防ぐための最低対応である。

| P5R AC | 手順ID | 撮影状態の最低例 | PlaywrightテストIDの予約名 | 必須viewport |
|---|---|---|---|---|
| P5R-AC-01 | BT-MAN-02、03 | 有効preflight、不正入力拒否、未来Data拒否 | P5R-MANUAL-01-PREFLIGHT | desktop、mobile |
| P5R-AC-02 | BT-MAN-02 | BTCUSDT/ETHUSDT選択、対象外理由 | P5R-MANUAL-02-DATA-SCOPE | desktop、mobile |
| P5R-AC-03 | BT-MAN-04 | queue、running、remaining、completed | P5R-MANUAL-03-SINGLE-RUN | desktop、mobile |
| P5R-AC-04 | BT-MAN-05 | cancelled、failed、retry、resume-required、resume | P5R-MANUAL-04-RECOVERY | desktop、mobile |
| P5R-AC-05 | BT-MAN-06 | 5指標とprovenance | P5R-MANUAL-05-METRICS | desktop、mobile |
| P5R-AC-06 | BT-MAN-07 | trade、signal、virtual fill、balance、cost assumption | P5R-MANUAL-06-DETAIL | desktop、mobile |
| P5R-AC-07 | BT-MAN-08 | Sweep preflight、invalid、duplicate、limit、count | P5R-MANUAL-07-SWEEP-PREFLIGHT | desktop、mobile |
| P5R-AC-08 | BT-MAN-09 | row queue、partial failure、cancel、resume | P5R-MANUAL-08-SWEEP-RECOVERY | desktop、mobile |
| P5R-AC-09 | BT-MAN-10 | all history、same-condition history、latest | P5R-MANUAL-09-HISTORY | desktop、mobile |
| P5R-AC-10 | BT-MAN-10 | compatible comparison、差分表示、比較拒否 | P5R-MANUAL-10-COMPARE | desktop、mobile |
| P5R-AC-11 | BT-MAN-11 | CSV job pending/running/cancelled/failed/completed | P5R-MANUAL-11-CSV | desktop、mobile |
| P5R-AC-12 | BT-MAN-12 | train/validation/holdout境界、再利用拒否 | P5R-MANUAL-12-HOLDOUT | desktop、mobile |
| P5R-AC-13 | BT-MAN-13 | window実行、窓別結果、future reference拒否 | P5R-MANUAL-13-WALK-FORWARD | desktop、mobile |
| P5R-AC-14 | BT-MAN-03から13 | Application API由来のRun ID/結果/状態を表示する同一操作 | P5R-MANUAL-14-REAL-APPLICATION | desktop、mobile |
| P5R-AC-15 | BT-MAN-15 | keyboard focus、dialog、error、mobile layout | P5R-MANUAL-15-A11Y-MOBILE | desktop、mobile |
| P5R-AC-16 | BT-MAN-01、14 | scope、Unknown、受入状態、P6に進まない表示 | P5R-MANUAL-16-SCOPE-AUDIT | desktop、mobile |

予約名はP5R-03で実在するテストIDへ置き換え、廃止・統合した場合は理由と新IDを追跡表に残す。操作が画面上で複数の状態を変える場合、一操作番号に複数枚を使ってよい。ただし、画像がない操作を「文章だけでよい」と判断して除外しない。

### 5.8 手順書採用Gate: P5R-MANUAL-G1

P5R-MANUAL-G1はHuman Gateではなく、手順書画像を作る直前に必ず通す機械・レビューGateである。

| 確認項目 | 不合格ならすること |
|---|---|
| P5R-H1が承認済み | 撮影・採用を始めない。 |
| P5R-AC-01から16に対応するE2Eが実アプリでGreen | 未完成のACは手順書で完成扱いにしない。 |
| 外部request、Broker、Secret、実注文、実資金が0件 | 実行を停止し、原因を統合台帳又はRun evidenceへ記録する。 |
| 各PNGがassert後に取得され、capture registryに対応する | PNGを採用しない。 |
| desktop/mobile、keyboard、axe、visualの必須範囲が確認済み | 手順書を暫定のまま止める。 |
| 操作番号、AC、Test ID、source Run IDの対応が100% | 欠けた操作を追加テスト・追加撮影する。 |
| Secret・個人情報・誤認を誘う利益表現がない | 画像と表示を修正し、再テスト・再撮影する。 |

## 6. P5R Runbook

| Step | 目的 | 主な出力 | 開始条件 | 完了条件 | Gate/停止 |
|---|---|---|---|---|---|
| P5R-00 | H0承認の準備と開始確認 | H0 packet、対象/非対象、負荷・保存・WF候補 | この計画書 | 人の明示承認、又は未承認BLOCKEDの正直な記録 | H0未承認ならP5R-01以降を始めない。 |
| P5R-00A | AI部品の再利用/不足を判定 | P5R-COMP-01 decision | H0承認後 | REUSE_ONLY又はCREATE_REQUIREDを根拠付きで決定 | 推測で部品を増やさない。 |
| P5R-00B | 必要時だけ汎用Web製品UI部品を作る | A172/Skill、関連JSON/HTML更新 | P5R-COMP-01=CREATE_REQUIRED | 既存部品と衝突せず、文書・索引・静的確認が同期 | 判定がREUSE_ONLYなら実行しない。 |
| P5R-01 | 現状差分と追跡を確定 | REQ/UC/Screen/API/Core/Test/Evidence/Gate/Unknown追跡 | H0承認 | AC-01から16全件の現在地がIMPLEMENTED/PARTIAL/NOT_IMPLEMENTED/OUT_OF_SCOPEで明確 | UnknownをPassにしない。 |
| P5R-02 | 実装詳細設計と手順書撮影設計 | 詳細設計、fixture契約、manual registry、UI/API契約 | P5R-01 | 実装者が追加判断なく着手可能、manual coverageが全ACを覆う | H1前に実装・撮影をしない。 |
| P5R-02A | P5R品質Gate scopeとRun Manifestを設計する | P5R-QG-SCOPE-01 proposal、固定Playwrightコマンド、target paths、Evidence root | P5R-02 | H1 packetに登録対象とComponentLifecycle更新内容が入る | 登録前のquality-gate実行を禁止。 |
| P5R-H1 | H1承認を得る | H1 packet、レビュー結果 | P5R-02A | 人の明示承認、又は未承認BLOCKED | H1未承認ならP5R-03A以降を始めない。 |
| P5R-03A | P5R品質Gate scopeを登録する | 承認済みtrusted scope、P5R Run Manifest、ComponentLifecycle receipt | H1承認 | 固定Run/target/fixture/commandが登録済み | 登録なしでP5R test subprocessを動かさない。 |
| P5R-03 | RED/Golden/失敗注入/E2Eを先に作る | RED evidence、Golden oracle、manual test skeleton | P5R-03A | テストが不正な現状を確実に失敗にする | skip、固定ダミー、曖昧期待値を禁止。 |
| P5R-04 | Single Run・結果・5指標・保存を実接続 | Core/Application実装、結果契約、品質証跡 | P5R-03 | 実P5由来fixtureが実処理で結果を返し、根拠まで読める | 外部Data/Broker等を追加しない。 |
| P5R-05 | 実アプリUIをSingle Runへ接続 | 実UI、PC/mobile、実API E2E | P5R-04 | SCREEN-08から12等のP5R対象画面が固定ダミーでなく実結果を表示 | A170だけで実結果UIを完成扱いにしない。 |
| P5R-06 | Sweepと停止・再開を完成 | Sweep展開、行別状態、負荷、cancel/resume | P5R-05 | AC-07/08の正常・異常がE2EでGreen | 複数運用Unit/Portfolioへ拡大しない。 |
| P5R-07 | 履歴・比較・CSVを完成 | history、compare、CSV job、失敗/取消状態 | P5R-06 | AC-09/10/11が実結果でGreen | 比較不能/失敗を隠さない。 |
| P5R-08 | Holdout/Walk-forwardを完成 | period split、window Run、future reject | P5R-07 | AC-12/13が実戦略実行でGreen | 境界表示だけで完了にしない。 |
| P5R-09 | 全操作をPlaywrightで操作・撮影 | manual capture evidence、capture registry | P5R-04から08がGreen、P5R-MANUAL-G1 | 全操作・異常系・PC/mobileがassert後PNGで覆われる | 固定モック、手作業画像、未確認操作を採用しない。 |
| P5R-10 | HTML手順書と静的画像を統合 | 01_バックテスト手順書.html、assets、doc/index導線 | P5R-09 | 全手順と画像がAC/Test/Runへ追跡可能 | 生証跡以外のPNGを混ぜない。 |
| P5R-11 | 手順書・UIの品質レビュー | a11y/visual/review/修正証跡 | P5R-10 | Critical/High=0、リンク・Secret・scope・coverage確認済み | 未確認viewport/UnknownをPassにしない。 |
| P5R-12 | P5R完了判定とH2 | 完了HTML、統合台帳、P6再引渡し、H2 packet | P5R-11 | H2の人の明示承認、又は未承認BLOCKED | P6実装、Paper、Liveへ進まない。 |

## 7. Step 1 — P5Rを実行するための直接実行プロンプト群

### 7.1 全Promptに必ず前置する共通実行契約

以下の共通実行契約を、各Stepの固有Promptの先頭に文字どおり付けて一つのPromptとして実行する。完全名の列挙、JSONを読んだだけ、Skillを読んだだけ、又はルートの自己レビューだけを、Orchestrator/Agentの起動済み・独立レビュー済みとは表現しない。

~~~text
あなたは自動トレードシステムのP5R実行担当です。

最初に、対象StepのHuman Gateが承認済みかを確認する。例外として、P5R-00はP5R-H0 packetを作るため、P5R-H1はH1 packetを作るため、P5R-12はH2 packetを作るための文書・Evidence集約だけを、対応するGateの未承認状態でも行ってよい。ただし、いずれもGateを承認済みと表示せず、次の実装/接続/撮影/後続Phaseへ進まない。その他のStepで必要Gateが未承認なら、実装・外部I/O・画面接続・撮影・完成宣言を行わず、BLOCKED、Gate ID、承認が必要な内容、再開条件を記録して停止する。

変更前に multi_agent_v1__spawn_agent と multi_agent_v1__wait_agent の利用可否を確認する。利用できる場合は、Promptで指定したOrchestratorをその定義JSON pathと固定modelでCoordinatorとして実spawnし、waitする。CoordinatorはPromptで指定された全Agentを、Orchestratorのagents map内外を問わず一体ずつ、各Agent JSONのmodel（reasoning_effortが定義されている場合だけその値）でspawnし、全件waitする。runtime_backend、dispatch_mode、orchestrator_agent_id、JSON path、model、Skill、agent_id、受付/完了status、output reference、independent、review_modeをsanitized receiptへ保存する。

spawn、wait、固定model受理、又は子出力取得のいずれかができない場合は、変更前に RUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、理由、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACK を記録する。その場合も、Promptに書かれた各責務をルートが順に自己適用するが、独立実行済みとは書かない。

外部ネットワーク、Provider変更、外部Data取得、Broker、Secret、実注文、実口座、実資金、Paper、Live、Cloud、P5R外の複数運用Unit/Portfolio/Account/実運用Risk/OMSを開始しない。既存ローカルP5範囲以外のDataを使わない。UnknownをPassにせず、Critical/High、必須Evidence欠落、scope逸脱、Secret疑いはfail-closedで停止する。

新規又は大幅変更の文書、計画、ソース、テスト、AI部品は、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1 と autotrade_skill_protected_hash_policy_guard_v0_1 による静的ポリシー判定へ渡す。管理用hash、manifest hash、stale判定、hash retry、hash receiptを新設しない。通常確認はpath、schema、link、Secret、状態、要件追跡で行う。

実行証跡は tests/evidence/phase5R/<RunId>/ にだけ保存する。正式HTMLはdoc/phase5R/配下に置き、doc/index.htmlから到達できるようにする。Human Gate、Unknown、Blocked、再開条件を変えた場合はdoc/00_全Phase残課題Blocked統合台帳.html全体を検索して整合させる。
~~~

### P5R-00 — P5R-H0の準備と開始確認

~~~text
Step ID: P5R-00
使用Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
担当Agent: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。

doc/requirements/01_自動トレードシステム要件定義書_v3.html、P5R再構成提案、P5完了判定、統合台帳、既存P5ローカルEvidenceを読取り専用で確認する。P5R-H0の承認対象を、(a)既存ローカルDataの正確な許可範囲、(b)保存方式と保持、(c)標準負荷・境界負荷・固定PC・測定方法、(d)Walk-forward窓、(e)UIが実Application APIへ接続する境界、(f)P5から継承するOpen Unknown、(g)P5R-AC-01から16、(h)P6以降へ残すもの、に分解する。

成果物として、P5R-H0 packet、対象/非対象表、未承認時の停止表、承認用の平易な説明、P5R-01へ渡す入力一覧を作る。ユーザーによるP5R-H0の明示承認がなければ、P5R-01以降を開始せず、BLOCKEDを統合台帳の既存P5R-H0へ正しく反映する。P5-H2をP5R-H0へ読み替えない。
~~~

### P5R-00A — AI部品の再利用・不足を判定する

~~~text
Step ID: P5R-00A
使用Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
担当Agent: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A06_AiComponentEngineer_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_ai_component_lifecycle_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。P5R-H0承認後にだけ着手する。

.codex/skills、.codex/agents、.codex/orchestrators、settings/ai_component_rules.md、ui/mockのUI/Playwright構成を調査する。次の責務ごとに、既存部品名、根拠、再利用可否、不足、P5R外へ持ち出さない境界を表にする。

1. 実BacktestのPython実装と品質。
2. React/TypeScriptの実製品UIとローカルApplication API接続。
3. 固定ダミーUIモックの画面構造・visual/a11yレビュー。
4. Playwrightの操作、assert、PNG取得。
5. HTML手順書、画像採用、索引、追跡。

必ず A170 の固定ダミー境界と A120 のPython境界を比較する。既存部品だけで「実Application API結果をUIへ接続する実装責務」が満たせるなら P5R-COMP-01=REUSE_ONLY と記録する。満たせないなら P5R-COMP-01=CREATE_REQUIRED と記録し、追加候補を generic Skill autotrade_skill_web_product_ui_implementation_v0_1 と generic Agent AutoTrade_A172_WebProductUiEngineer_v0_1、Orchestrator新設なしとする。手順書専用の新Agent/Skill/Orchestratorは提案しない。

作成しない場合も、判断根拠、参照したJSON path、後続Stepが使う正確な部品名を成果物に残す。名前衝突、責務不明、外部UI SDK又は外部通信が必要になる提案はBLOCKEDにする。
~~~

### P5R-00B — 条件付きでWeb製品UI部品を作る

~~~text
Step ID: P5R-00B
使用Orchestrator: AutoTradeComponentLifecycle_Orchestrator_v0_1
担当Agent: AutoTrade_A06_AiComponentEngineer_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_ai_component_lifecycle_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。P5R-COMP-01=CREATE_REQUIRED の場合だけ実行する。REUSE_ONLYなら、変更せずSKIPPEDとして理由を記録する。

既存部品との名前衝突を最初に検査する。衝突がなければ、最小変更として次を作る。

- .codex/skills/autotrade_skill_web_product_ui_implementation_v0_1/SKILL.md
- .codex/agents/AutoTrade_A172_WebProductUiEngineer_v0_1.json
- AutoTradeProject_ImplementationQuality_Orchestrator_v0_1.jsonへのA172/Skill登録

新しいSkill/Agentの境界は、型付きローカルApplication APIへのWeb UI接続、実結果の状態表示、accessible component、component/E2E接続、既存P4 UI構造の安全な移行に限定する。UIがBacktest計算を作らない、固定ダミー結果を実結果として出さない、外部通信、Broker、Secret、実注文、実口座、認証/権限追加、実資金、Cloudを扱わないことを必須にする。A171が独立レビューし、A80が手順書を統合する責務を奪わない。

同じ変更セットで、doc/ai_foundation/03_プロジェクト汎用Skill仕様.html、04_プロジェクト汎用サブエージェント仕様.html、05_プロジェクト汎用オーケストレータ仕様.html、06_AI部品相関図発火制御図.html、07_AI部品作成ルール.html、08_AI実行基盤整理検証結果.html、doc/index.html、settings/ai_component_rules.md、必要な場合のAGENTS.mdとREADME.mdを更新する。A95の静的判定、path/schema/link/Secret/状態確認、JSON parse、相互参照確認、レビューを完了し、P5R-01へ部品一覧と受領記録を渡す。
~~~

### P5R-01 — 要件・UI・実装差分を追跡する

~~~text
Step ID: P5R-01
使用Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
担当Agent: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A20_ArchitectureDomainArchitect_v0_1、AutoTrade_A30_StrategyQaArchitect_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_architecture_writer_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。P5R-H0承認後にだけ着手する。

P5R-AC-01から16、REQ-V3-0113から0118、既存P4 Screen/API、src/autotradeのApplication/Backtest実装、P5のlocal evidenceを調べる。各行を IMPLEMENTED、PARTIAL、NOT_IMPLEMENTED、OUT_OF_SCOPE のいずれかに分類し、根拠path、現在の固定ダミー箇所、必要な設計、REDテスト、実装、E2E、手順書章、Evidence、Gate、後続Phaseを結ぶ。

SCREEN-03/04、SCREEN-13から16、SCREEN-20及び複数運用Unit/Portfolio/Risk/OMS/Forward/Shadow/Paper/Broker/LiveをP5R対象外として明記する。SCREEN-08から12、17、18、19は、P5Rで実結果に接続するか、境界表示として残すかを画面ごとに決める。固定ダミーの5指標、Chart、取引、比較、未実行Walk-forward、未確定負荷を個別Gapとして登録する。

成果物は正式HTMLの要件追跡、P5R-02への差分入力、統合台帳へ反映すべきUnknown/Blocked候補である。Unknownを「実装すれば解決」と書かず、再開条件と停止範囲を残す。
~~~

### P5R-02 — 実装詳細設計、fixture、手順書撮影台帳を確定する

~~~text
Step ID: P5R-02
使用Orchestrator: AutoTradeProject_ImplementationDesign_Orchestrator_v0_1
担当Agent: AutoTrade_A82_ImplementationDetailDesigner_v0_1、AutoTrade_A91_ImplementationDetailReviewer_v0_1、AutoTrade_A20_ArchitectureDomainArchitect_v0_1、AutoTrade_A30_StrategyQaArchitect_v0_1、AutoTrade_A50_AdapterArchitect_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1
使用Skill: autotrade_skill_implementation_detail_design_v0_1、autotrade_skill_implementation_detail_review_v0_1、autotrade_skill_execution_model_v0_1、autotrade_skill_adapter_boundary_v0_1、autotrade_skill_golden_test_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。P5R-H0承認後にだけ着手し、H1承認前には実装又は実画面撮影を行わない。

次を実装者が追加判断なく実装できる詳細設計にする。

1. P5由来の読み取り専用Data Adapter。許可fixture、対象銘柄、期間、timezone、品質不良、future Data、対象外の停止を型付きで定義する。
2. Single Run、Job、Queue、checkpoint、cancel、failure、retry、resumeのBacktest専用状態遷移。P6のUnit/OMS状態を混ぜない。
3. 5指標の定義、単位、丸め、欠損、中途結果、Cost/Slippage仮定、取引/Signal/virtual Fill/残高との根拠関係。
4. Sweepの展開、型、丸め、上限、重複、開始前負荷、行別状態、部分失敗、取消、再開。
5. 履歴、latest、compare compatibility、差分、非同期CSV、CSV jobの進捗/取消/失敗/完了。
6. train/validation/holdout、Walk-forward窓、future reference/重複/隙間/holdout再利用拒否。
7. Web UIとApplication APIのtyped request/response、Loading/Waiting/Running/Completed/Cancelled/Failed/Recovery Required/Unapproved、PC/mobile/keyboard/a11yの契約。
8. 手順書の全章、操作番号、AC、Screen/State、Playwright Test ID、必要desktop/mobile PNG、capture registry schema、Evidence path、正式assetsへの採用処理。

manual captureの設計では、Playwrightが実アプリを操作し、assert後に証跡PNGを tests/evidence/phase5R/<RunId>/playwright/manual-capture/ へ保存し、採用済みPNGだけを doc/phase5R/07_運用手順/assets/backtest_manual/ へ機械的にコピーする二層構造を固定する。手作業の画像加工、固定ダミー、外部Data、real accountを禁止する。P5R-MANUAL-G1、全ACのcoverage matrix、PC/mobileのviewport、fixture識別、外部request監視、画像内Secret検査を詳細設計に含める。

さらに、P5R-QG-SCOPE-01 proposalを作る。proposalには、P5R専用Run ID、phase_id、step_id、requirements/design参照、A172を含むAgent、Skills、固定ローカルfixtureとData version、baseline ref、target paths、excluded paths、tests/evidence/phase5R/<RunId>/ のEvidence root、固定されたPython/TypeScript/Playwrightのコマンド、host outbound isolation確認、review/human gate policyを含める。既存のprotected fixture checksumを直接の再現性保護として使う必要がある場合だけ、A95のALLOW根拠と停止範囲を記載し、管理用hashを追加しない。proposalはH1 packetへ入れ、H1承認前に trusted_scopes.json や実行allowlistを変更しない。

詳細設計はA91初回レビュー、A90横断/Red Team、A80/A81の改訂、A91再レビューを通す。Critical/High、UnknownのPass、manual coverage欠落、P5R-QG-SCOPE-01 proposal欠落があればP5R-H1へ提出しない。
~~~

### P5R-02A — P5R品質Gate scopeとRun Manifestを設計する

~~~text
Step ID: P5R-02A
使用Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
担当Agent: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A06_AiComponentEngineer_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1
使用Skill: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_ai_component_lifecycle_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。P5R-H0承認後、P5R-H1承認前に、設計だけを行う。

AutoTradeProject_ImplementationQuality_Orchestrator_v0_1のtrusted scope契約を読み、P5R-QG-SCOPE-01 proposalを作る。proposalでは、P5Rの実装とPlaywright manual captureを対象にする正確なRun ID、target paths、excluded paths、fixture、Evidence root、固定4 Gateのコマンド、Playwright固定コマンド、browser project、desktop/mobile viewport、外部通信隔離、許可しないpath、失敗時の保存物を決める。

P4のmock PlaywrightテストをP5R受入Evidenceに流用しない。P5R専用の実アプリE2Eだけを対象にし、fixtureからApplication API、Backtest、UI、PNGまでの対象境界を記す。実行scopeの拡張はComponentLifecycleによる別の承認済み更新でしか行えないため、このStepでは trusted_scopes.json、quality-gate script、P5R本体、Playwrightを変更・実行しない。H1 packetに、P5R-03Aで行う正確な変更一覧と承認依頼を入れる。
~~~

### P5R-H1 — 詳細設計・RED/Golden設計の承認を得る

~~~text
Step ID: P5R-H1
使用Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
担当Agent: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A82_ImplementationDetailDesigner_v0_1、AutoTrade_A91_ImplementationDetailReviewer_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_implementation_detail_review_v0_1、autotrade_skill_golden_test_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。

P5R-01/02/02Aの成果物を、運用者が判断できるH1 packetにまとめる。Data Adapter、5指標、Sweep/CSV/Holdout/WF異常系、RED/Golden、実UI接続、manual capture registry、P5R-MANUAL-G1、P5R-QG-SCOPE-01、Open Unknown、対象外を平易に説明し、要求からTest/Evidenceへの対応表を付ける。P5R-QG-SCOPE-01は、A172を含む実UI担当、P5R専用target paths、固定local fixture、固定Playwright command、Evidence rootを登録するComponentLifecycle更新であることを明示する。

ユーザーがP5R-H1を明示承認するまで、P5R-03A以降のscope登録、実装、テストGreen化、実画面スクリーンショット採用、完成宣言を行わない。未承認時はBLOCKEDを記録し、P5R-H2又はP6へ進めない。
~~~

### P5R-03A — P5R品質Gate scopeを承認範囲内で登録する

~~~text
Step ID: P5R-03A
使用Orchestrator: AutoTradeComponentLifecycle_Orchestrator_v0_1
担当Agent: AutoTrade_A06_AiComponentEngineer_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1
使用Skill: autotrade_skill_ai_component_lifecycle_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。P5R-H1でP5R-QG-SCOPE-01が明示承認された場合だけ実行する。

P5R-QG-SCOPE-01 proposalと承認内容に厳密に一致する範囲だけを、ComponentLifecycleの変更として登録する。具体的には、ImplementationQuality OrchestratorへのA172/Skill参加（必要な場合）、scripts/quality_gate/trusted_scopes.jsonのP5R専用Run ID/target paths/excluded paths/fixed commands/Evidence root、及び対応するRun Manifest/文書導線を更新する。登録対象外のpath、任意コマンド、外部通信、別fixture、P6以降のテストは許可しない。

P5R専用scopeが登録され、JSON/schema/path/link/Secret/A95/レビュー確認がGreenになるまで、P5R-03以降のtest subprocess又はPlaywrightを実行しない。既存P4 mock scopeを再利用してP5RをPASSにしない。変更後は、登録したRun ID、固定コマンド、target paths、fixtureの境界、Evidence root、dispatch receiptをP5R-03へ渡す。
~~~

### P5R-03 — RED、Golden、失敗注入、手順書E2E骨格を作る

~~~text
Step ID: P5R-03
使用Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当Agent: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A30_StrategyQaArchitect_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1
使用Skill: autotrade_skill_python_test_quality_v0_1、autotrade_skill_golden_test_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。P5R-H1承認とP5R-03Aの承認済みP5R scope登録後にだけ着手する。

P5R-02の設計から、先に失敗するテストを作る。単一Run、5指標、取引詳細、cancel/failure/retry/resume、Sweep、history/compare/CSV、Holdout/WF、future Data拒否、外部request 0件、P5R外画面の副作用0件を対象にする。Goldenは小さく固定したP5由来fixtureと独立期待値で定義し、UIだけの固定値で通さない。

Playwrightでは、P5R-MANUAL-01から16の予約を実在テストへ落とし込む。各テストに、初期化、実UI操作、API由来状態assert、PNG capture、desktop/mobile、trace、外部request監視を入れる。現時点ではRED証跡を残すだけで、手順書assetsへPNGを採用しない。テスト削除、skip、expectの弱化、固定ダミーの注入、fake completionはfail-closedで拒否する。
~~~

### P5R-04 — 実Backtest、結果、5指標、保存を接続する

~~~text
Step ID: P5R-04
使用Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当Agent: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A120_PythonImplementer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_execution_model_v0_1、autotrade_skill_golden_test_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。P5R-H1承認とP5R-03の有効なREDが前提である。

読み取り専用P5 Data Adapter、Single Run/Job/Queue、実5指標、取引/Signal/virtual Fill/残高/provenance、cancel/failure/retry/checkpoint resume、保存済み結果のApplication API投影を最小範囲で実装する。UIに計算させず、Application APIからの実結果だけを返す。fee/slippage等は仮定値として保存・表示し、実測値又は利益保証と表示しない。

各小単位でRED→実装→ローカル検証→必要時の二回までの原因仮説別復旧→A150/A160レビューを行う。既存P5のOpen Unknownを解決済みにせず、外部Data・Broker・Secret・P6機能を追加しない。P5R-05に渡すのは、型付きAPI、fixture契約、実際にGreenになったEvidenceだけである。
~~~

### P5R-05 — 実Application APIに接続したSingle Backtest UIを完成する

~~~text
Step ID: P5R-05
使用Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当Agent: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A120_PythonImplementer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1、REUSE_ONLYならP5R-00Aで決めた既存実UI担当
使用Skill: autotrade_skill_python_test_quality_v0_1、autotrade_skill_python_implementation_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。P5R-H1承認後にだけ着手する。

P4の画面構造を必要最小限で移行し、対象Data選択、Strategy/Config、preflight、Single Run開始、queue/progress/remaining、cancel/failure/retry/resume、5指標、detailをローカルApplication APIの実結果に接続する。各画面はLoading/Waiting/Running/Completed/Cancelled/Failed/Recovery Required/Unapprovedを区別し、固定ダミーを実結果として残さない。

A170の固定ダミーUIモックは、画面構造の参照・移行補助には使ってよいが、P5R実結果UIの実装担当又は合格証拠にはしない。UIはCoreやDBへ直接書かず、型付きApplication APIだけに接続する。PC/mobile、keyboard、focus、label、role、error、scope表示をPlaywrightとaxeで確認する。P5R-MANUAL-01から06、14、15の実操作がGreenになるまでP5R-09へ進めない。
~~~

### P5R-06 — Sweep、負荷、部分失敗、取消・再開を完成する

~~~text
Step ID: P5R-06
使用Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当Agent: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A120_PythonImplementer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1
使用Skill: autotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。

P5R-H0で承認された固定PCの標準/境界負荷だけを使い、Sweepの範囲、刻み、型、丸め、上限、重複、展開件数、見込み負荷を開始前に表示・検査する。各child RunはBacktest専用の実験行として保存し、queue、部分失敗、取消、checkpoint resumeを行単位で追えるようにする。

無効行、重複、上限超過、推定不能、部分失敗、取消、resume不適合のE2Eを作り、失敗行を隠して全成功と表示しない。複数運用Unit、Portfolio、Account、Risk、OMS、注文状態を導入しない。P5R-MANUAL-07/08がdesktop/mobileでGreenになり、assert後PNGを取れる状態にする。
~~~

### P5R-07 — 履歴、比較、非同期CSVを完成する

~~~text
Step ID: P5R-07
使用Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当Agent: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A120_PythonImplementer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1
使用Skill: autotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。

全実験結果、同条件の履歴、latest表示を区別し、古いRunを上書きしない。比較はcompatibility contractに合うRunだけに限定し、Data、期間、Strategy、Config、費用仮定などの差を表示する。大量表と全件CSVは別Jobで作り、UIを止めず、開始、pending、running、cancelled、failed、completedを正しく表示する。

比較不能、CSV失敗、CSV取消、CSV完了、古いRun、条件差を含むE2EをGreenにする。結果本文、絶対path、Secret、外部exportをUIに出さない。P5R-MANUAL-09/10/11がdesktop/mobileでassert後PNGを取得できる状態にする。
~~~

### P5R-08 — HoldoutとWalk-forwardを完成する

~~~text
Step ID: P5R-08
使用Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当Agent: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A120_PythonImplementer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1
使用Skill: autotrade_skill_python_implementation_v0_1、autotrade_skill_python_test_quality_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_golden_test_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。

P5R-H0で承認された期間分割と窓ルールだけを実装する。train/validation/holdoutの境界、役割、使用履歴を保存し、holdoutを調整に使い回す操作を拒否する。Walk-forwardは各窓で実際に戦略を走らせ、窓別入力・出力・失敗理由・集計を保存する。future Data、窓重複、隙間、境界だけを表示して実行済みと見せることを拒否する。

P5R-MANUAL-12/13の実操作・拒否・窓別結果がdesktop/mobileでGreenになり、同じRunのassert後PNGを取得できる状態にする。結果に基づく自動採用、Forward、Shadow、Paper、Liveへの昇格を実装しない。
~~~

### P5R-09 — 全UI操作をPlaywrightで検証し、実スクリーンショットを取得する

~~~text
Step ID: P5R-09
使用Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当Agent: AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1、P5R-COMP-01でCREATE_REQUIREDならAutoTrade_A172_WebProductUiEngineer_v0_1
使用Skill: autotrade_skill_python_test_quality_v0_1、autotrade_skill_test_strategy_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1、P5R-COMP-01でCREATE_REQUIREDならautotrade_skill_web_product_ui_implementation_v0_1

共通実行契約を前置して実行する。P5R-03Aの承認済みP5R scope登録とP5R-MANUAL-G1の全条件を先に判定し、不成立なら撮影・採用を開始しない。

@playwright/testで、BT-MAN-01から15に対応する全操作を、正常系と異常系の両方で実行する。P5R-MANUAL-01から16の各Testは、P5R-H0で許可されたローカルfixtureを初期化し、UIの可視名/role/labelで操作し、実Application API由来のRun/Job/状態/数値/理由/操作可否をassertした後、同じページをPNGとして撮影する。

PNG、trace、HTML report、capture registryを tests/evidence/phase5R/<RunId>/playwright/manual-capture/ に保存する。registryには手順ID、AC、Screen/State、Test ID、viewport、fixture ID、source Run ID、PNG相対path、assert結果、採用可否を記録する。画像を手作業で撮らない、加工しない、固定モックで代用しない。external request監視、Secret/PII表示検査、desktop/mobile、keyboard、axe、visual comparisonを実行し、未確認状態はCapture対象外として失敗にする。

最後に、P5R-MANUAL-G1の判定、全操作coverage率、採用候補PNG一覧、未採用理由を出す。100%でなければP5R-10へ進めない。
~~~

### P5R-10 — HTMLバックテスト手順書と画像資産を統合する

~~~text
Step ID: P5R-10
使用Orchestrator: AutoTradeProject_DesignDocSet_Orchestrator_v0_1
担当Agent: AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A81_DesignDocSetWriter_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。P5R-09でP5R-MANUAL-G1がPASSし、capture registryの全操作coverageが100%である場合だけ実行する。

capture registryに記載されたassert成功済みPNGだけを、機械的に doc/phase5R/07_運用手順/assets/backtest_manual/ へ採用する。採用時はsource Run ID、Test ID、viewport、手順IDとの対応を保持し、手作業で別画像を混ぜない。HTML assetsは読者向けの表示資産であり、受入Evidenceの正本又は生証跡の代替にしない。

doc/phase5R/07_運用手順/01_バックテスト手順書.html を作成する。BT-MAN-01から15の全章に、平易な目的、前提、番号付き操作、確認、失敗時の安全な行動、実スクリーンショット、caption、AC/Test ID、対象外を載せる。HTML上の図説明は画像を加工せず、caption/legend/周辺説明で行う。表紙と各結果章で「限定ローカルfixtureのBacktest検証画面であり、利益保証・実市場コスト・実注文ではない」と明記する。

doc/index.html、P5Rの追跡HTML、手順書の相互リンクを更新する。正式HTMLの孤立、欠落画像、壊れた相対link、Secret、P5R外の操作説明、固定ダミー写真の混入が一件でもあればSTOPする。
~~~

### P5R-11 — UI・手順書の視覚、アクセシビリティ、追跡を最終レビューする

~~~text
Step ID: P5R-11
使用Orchestrator: AutoTradeProject_ImplementationQuality_Orchestrator_v0_1
担当Agent: AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A160_TradingSecurityReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_python_test_quality_v0_1、autotrade_skill_ui_visual_validation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。

Findings firstで、(a)P5R-AC-01から16、(b)BT-MAN-01から15、(c)capture registry、(d)desktop/mobile、(e)keyboard/focus/role/name/contrast/axe、(f)実結果と固定ダミーの混同、(g)外部request/Secret/PII、(h)HTML link/image/schema、(i)P5R外の機能混入、(j)Open UnknownとH2への正直な引渡し、をレビューする。

Critical/Highがあれば該当Stepへ戻し、同じ原因仮説の復旧は二回までにする。全手順操作にPNGとTest IDがあること、各PNGがassert後の実アプリ画面であること、手順書が対象外操作を開始させないことを確認する。レビュー担当が自分で画像やUIを修正して指摘を隠さない。
~~~

### P5R-12 — 完了判定、P5R-H2、P6再引渡しを行う

~~~text
Step ID: P5R-12
使用Orchestrator: AutoTradePhasePlanning_Orchestrator_v0_1
担当Agent: AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
使用Skill: autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1

共通実行契約を前置して実行する。

P5R-AC-01から16、P5R-MANUAL-G1、BT-MAN-01から15、全Evidence、A11y/visual、Open Unknown、P5R外境界、P6への入力を一つの完了判定packetにまとめる。P5Rの完了は、全受入がGreenで、Critical/Highが0件で、UnknownをPassにしておらず、手順書が実Playwright画像に全操作対応し、統合台帳とdoc/index.htmlが整合している場合に限る。

ユーザーがP5R-H2を明示承認するまで、P6の実装・実行、Paper、Liveを開始しない。承認時にも、P6は複数Unit/Portfolio/Account/Risk/OMSの固定Simulationから始まること、ForwardはP7、ShadowはP8、PaperはP9以降であることを再確認する。未承認ならBLOCKEDを正直に残し、P5Rの実装成果だけを「次の承認待ち」とする。
~~~

## 8. Step 2 — この実行計画書を完成するために順番に実行したPrompt群

この章のPrompt群は計画作成時点では「P5R本体を安全に実装できる計画書を作る」ためのものであり、その時点ではP5R本体Promptを実行していなかった。現在は第13章の実行結果追補が優先される。

### P5R-PLAN-01 — 上流要件と既存P5R計画を読む

~~~text
要件定義書v3、P5R再構成提案、P5完了判定、統合台帳、doc/index.htmlを読み、P5Rの目的、AC-01から16、H0/H1/H2、P5のOpen Unknown、P6以降へ残す範囲を抽出する。P5R実装、外部Data取得、Secret、Broker、注文、Paper、Liveは行わない。計画に必要な根拠と停止条件を出力する。
~~~

実行結果: 完了。P5Rは「UIから使えるBacktest製品」であり、AC-01から16が必要、P5R-H0は未承認であることを確認した。P6の複数Unit/Portfolio/Risk/OMS、P7以降のForward/Shadow/Paper/LiveをP5Rへ混ぜないことを計画へ固定した。

### P5R-PLAN-02 — UI、Playwright、AI部品の責務境界を調べる

~~~text
ui/mockのPlaywright設定と既存テスト、P4 UI契約、AI component rules、UI Mock Orchestrator、A170、A171、ImplementationQuality Orchestrator、A05/A06/A80/A90/A95の定義を読み取り専用で調べる。固定ダミーUIを実Backtest結果に使えない根拠、Playwright再利用点、HTML手順書/画像の担当、必要なAI部品の不足を判定する。
~~~

実行結果: 完了。desktop/mobile、外部通信監視、PNG、axe、visual baselineの土台は再利用可能である。一方、A170は固定ダミーUI、A120はPython実装であり、実Application APIに接続したWeb製品UIを実装する汎用担当は不足候補であると確認した。

### P5R-PLAN-03 — 実画面スクリーンショットの採用規則を設計する

~~~text
バックテスト手順書に載せる画面写真が、Playwrightで実アプリを操作し、assert後に取得したものだけになるよう、fixture、外部通信、証跡パス、正式assets、HTML、capture registry、PC/mobile、異常系、Secret/PII、AC対応の規則を設計する。固定fixtureと固定ダミーを区別し、手作業画像を禁止する。
~~~

実行結果: 完了。生証跡を tests/evidence/phase5R/<RunId>/playwright/manual-capture/、正式assetsを doc/phase5R/07_運用手順/assets/backtest_manual/、HTMLを doc/phase5R/07_運用手順/01_バックテスト手順書.html に分ける方針、及びP5R-MANUAL-G1を採用した。

### P5R-PLAN-04 — AI部品の追加要否を最小構成で決める

~~~text
既存の汎用Orchestrator、Agent、Skillを優先して再利用し、手順書専用部品が必要か、実Application APIに接続するWeb製品UI担当が必要かを判定する。必要な場合も、新Orchestratorの新設を避け、名前、責務、境界、ライフサイクル更新対象を提案する。
~~~

実行結果: 完了。手順書専用部品は不要とした。P5R-H0後のP5R-00Aで再確認することを前提に、generic Skill autotrade_skill_web_product_ui_implementation_v0_1 と generic Agent AutoTrade_A172_WebProductUiEngineer_v0_1 を最小追加候補とし、AutoTradeProject_ImplementationQuality_Orchestrator_v0_1を再利用する方針を採用した。

### P5R-PLAN-05 — 実行順、成果物、Gate、直接Promptを組み立てる

~~~text
P5RをH0、部品判断、差分追跡、詳細設計、P5R品質Gate scope設計、H1、scope登録、RED/Golden、Core、実UI、Sweep、履歴/CSV、Holdout/WF、Playwright撮影、HTML手順書、品質レビュー、H2に分ける。各Stepに、目的、開始条件、成果物、停止条件、担当AI部品の完全名、そのまま実行できるPromptを付ける。P4 mock Playwrightは回帰確認に限定し、P5R実結果Evidenceへ流用しない。
~~~

実行結果: 完了。第6章のRunbookと第7章のP5R-00からP5R-12のPrompt群を作成した。P5R-H0/H1/H2の間に実装・撮影・後続Phase開始を越境させない順序にした。レビュー指摘を反映し、P5R-02AでP5R品質Gate scopeを設計し、P5R-H1承認後のP5R-03Aで登録を完了するまでtest subprocess/Playwrightを動かさない構成にした。

### P5R-PLAN-06 — 読み取りレビューを行う

~~~text
P5Rのスコープ、Gate、固定ダミーUIとの区別、Playwright撮影、手順書資産の保存先、AI部品の最小追加を、ファイルを変更せずに独立レビューする。Critical/High、抜け、P6への越境、実装前提の誤りをFindings firstで返す。
~~~

実行結果: 完了。最初の読取り専用レビューの結論は「実アプリ接続のBacktestを完成してからPlaywrightで操作・assert・撮影し、HTMLへ載せる順序が必要」「現行モック写真を使ってはいけない」「手順書専用部品は不要、実製品UI担当だけが不足候補」であった。追加の固定modelレビューでは、P5R実UI/PlaywrightをImplementationQualityの品質Gateで実行する前に、P5R専用trusted scope・Run Manifest・固定Playwright command・target paths・fixtureを設計/承認/登録する必要があるというHigh指摘を受け、P5R-02AとP5R-03Aを追加して解消方針を反映した。

受領記録:

| 項目 | 記録 |
|---|---|
| root review agent | 01a00857-31d5-7972-a3bd-191ca67c3ef4 |
| 実行範囲 | 読み取り専用。ファイル変更、P5R実装、Playwright、外部接続を禁止。 |
| 子Agent dispatch | reviewer側でspawn/waitが利用できず、指定child Agentは未起動と報告。 |
| 独立性の表記 | reviewerの読取り結論は受領したが、指定child Agent全員による独立レビュー済みとは扱わない。 |
| fallback表記 | RUNTIME_DISPATCH_FALLBACK_REQUIRED / agent_id=N/A / independent=false / review_mode=SELF_REVIEW_FALLBACK を、将来のP5R実行Promptに明示した。 |

追加の固定model読取りレビューでは、P5R UI/PlaywrightをImplementationQualityへ載せる前にP5R専用のtrusted scope、Run Manifest、固定Playwright command、target paths、fixture、Evidence rootを承認・登録する必要があるというHigh指摘を受領した。この指摘を反映し、P5R-02A、P5R-03A、P5R-H1 packet、P5R-09の開始条件を追加した。

| 項目 | 記録 |
|---|---|
| fixed-model review agent | 01a0085a-f9a9-7d02-bc0e-d4d1fce1e6a5 |
| root model | gpt-5.6-terra |
| 主な結論 | P4 mockのEvidence流用禁止、A172/Skillの条件付き採用、P5R専用scope登録が必須。 |
| child Agent dispatch | reviewer側でspawn/waitが利用できず未起動。独立child review済みとは扱わない。 |

### P5R-PLAN-07 — 計画書を統合し、静的確認へ渡す

~~~text
P5R実行計画書をplan/Phase5R_実行計画書_v0.1_2026-08-16.mdに作成し、P5R再構成提案、統合台帳、doc/index.htmlへの導線を必要最小限で同期する。P5R-H0を承認済みにしない。新規計画文書と更新HTMLをA95の静的ポリシー判定、path/schema/link/Secret/状態/要件追跡確認、Git差分確認へ渡す。
~~~

実行結果: 本章まで完了。次章の検証を実施後に、導線更新とGit処理を行う。

## 9. この計画書自身の受入条件

| 観点 | 合格条件 |
|---|---|
| P5R範囲 | AC-01から16、P5限定Data、P6以降の対象外、Open Unknownが明記されている。 |
| Gate | H0/H1/H2の承認対象、停止範囲、再開条件が実装順に置かれている。 |
| UI手順書 | 全操作、正常/異常、PC/mobile、keyboard/a11y、実画面PNG、AC/Test/Run追跡を計画している。 |
| Playwright | 実アプリ操作、assert後撮影、生証跡と正式assetsの分離、外部通信0件、手作業画像禁止が明記されている。 |
| AI部品 | 手順書専用部品を増やさず、実UI担当だけを条件付き最小追加にし、Lifecycleの更新範囲を明記している。 |
| 安全 | 外部Data、Broker、Secret、注文、実資金、P5R外機能を計画対象にしていない。 |
| 直接実行性 | 各P5R Stepに、Orchestrator、Agent、Skill、runtime dispatch、成果物、停止条件を含むPromptがある。 |
| 文書整合 | 本計画への導線、統合台帳のP5R-H0参照、再構成提案の現在状態を同期する。 |

## 10. Open Unknownと残リスク

| ID/事項 | 現在の扱い | P5Rでしてよいこと | P5Rでしてはいけないこと |
|---|---|---|---|
| Provider利用・保持・再配布条件 | OPEN_NOT_PASS | 既存ローカルEvidenceをH0で許可された範囲だけ読む。 | 追加取得、再配布、Provider変更。 |
| P5-08 host isolation | NOT_VERIFIED | P5Rのローカル試験を別Evidenceとして扱う。 | 過去の外部取得隔離が検証済みと読み替える。 |
| P5当時のchild dispatch | NOT_VERIFIED | P5Rごとに新しいruntime receipt又は正直なfallbackを残す。 | 過去P5を独立レビュー済みと表現する。 |
| fee/slippage/内部実行費 | NOT_MEASURED | 仮定値、単位、根拠、感度を表示する。 | 実測値、実市場適合、利益保証と表示する。 |
| 固定PCの受入負荷 | H0で決定 | 標準/境界条件を測定し、結果を記録する。 | 「大量」とだけ書いて未測定の性能を完成扱いにする。 |
| Web実UI担当 | P5R-00Aで再確認 | 既存部品を再利用又は最小A172/Skillを作成する。 | A170固定モックを実結果UIの証拠にする。 |

## 11. 本計画作成の自己評価

agent-self-evaluationの観点で、完成前に次を自己点検する。

| 軸 | 評価 | 根拠 |
|---|---|---|
| Accuracy（正確性） | 4/5 | 要件v3、P5R提案、既存UI/Playwright/AI部品の実体を照合した。改善: P5R-H0未承認のため、最終的なAPI endpoint、P5R専用Run ID、target path、fixture名はP5R-01/02で実装実体を再確認して確定する。 |
| Completeness（網羅性） | 5/5 | AC-01から16、正常/異常、fixture、撮影、HTML、AI部品、品質Gate scope、Gate、P6境界、Open Unknownを第5〜7章へ含めた。 |
| Clarity（明確さ） | 4/5 | 先に結論、Runbook、手順書章、追跡表を置き、P5R-H0/H1/H2の停止順を明記した。改善: H0 packetでは本計画の専門語をさらに短い承認用説明へ再編集し、運用者が決める数値だけを一枚にまとめる。 |
| Actionability（実行可能性） | 5/5 | P5R-00から12の各Promptに、開始条件、完全名のAI部品、成果物、停止条件、runtime dispatch fallbackを置いた。P5R-02A/03AでPlaywright品質Gateの登録前提も実行順に固定した。 |
| Conciseness（簡潔さ） | 4/5 | ユーザーが超詳細な複数Step Prompt群を求めたため、各Promptを省略しなかった。改善: 実行時は第6章のRunbookを入口にし、該当する一つのStep Promptだけを開くことで、不要な全章の再読を避ける。 |

総合: 4.4 / 5.0。自己確認: ユーザーが求めた「実画面のPlaywrightスクリーンショットを含む、全UI操作のHTML手順書」「必要なAI部品の追加判断」「超詳細な直接Prompt」「P5R本体を未承認のまま実装しない」を満たしている。一方、P5R-H0後に確定すべき負荷、保存、Walk-forward窓、最終API/test pathを今の段階で推測していないため、実装前にP5R-01/02で確定する必要がある。

## 12. 次に必要な人の判断（計画作成時点）

この計画書の完成は、P5R実装の開始承認ではない。P5Rを開始するには、次の内容を明示してP5R-H0を承認する必要がある。

> Phase 5Rの対象範囲、既存ローカルP5 Dataの利用範囲、保存、固定PCの受入負荷、Walk-forward窓、UI実接続、P5R-AC-01から16、及びP6以降へ残す範囲を承認します。P5R-H0を開始してください。

この章の承認文は計画作成時点の開始条件である。実行時点では、ユーザーによる全Human Gate承認権限の移譲を根拠に、P5R-H0/H1/H2を委任範囲内で代理承認し、下記の実行結果追補を現在状態として優先する。

## 13. P5R本体実行結果追補（2026-08-16）

ユーザーの依頼「P5R実行計画書に記載の全プロンプトを1つずつ順番に実行」と、全Human Gate承認権限の移譲を受け、P5R-00からP5R-12までを順番に実行した。P5R-00Aで既存A170だけでは実Application API結果UIの責務を満たさないと判定し、汎用Web製品UI Skill / A172を追加し、ImplementationQuality Orchestratorへ登録した。P5R-02Aで固定Trusted ScopeとRun Manifestを設計し、P5R-H1代理承認後のP5R-03Aで登録した。

P5R-04〜08で、実P5ローカルfixtureを読むApplication API、Single、5指標、Ledger、取消・再開、Sweep、履歴・比較、CSV、Holdout、Walk-forwardを実装した。P5R-09で `ui/mock/tests/p5r-backtest.spec.ts` をデスクトップ（1280×900）とモバイル（390×844）で実行し、BT-MAN-01〜15を各15枚、assert後に撮影した。P5R-10で `doc/phase5R/07_運用手順/01_バックテスト手順書.html` と正式画像15枚を統合し、P5R-11でUI、a11y、Security、リンク、範囲、Unknownをレビューした。

最終結果は、Python 179 passed、UI単体10 passed、P4 UI回帰3 passed、P5R Playwright 2 passed、固定4 Gate PASS、Critical/High 0、外部request 0、axe blocking 0である。追加したP5R-T-15で、各完成M1 Barを既存Strategy Coreへ渡し、UIで選択した `TURTLE_SYS1` / `TURTLE_SYS2` とEntry/Exit期間、CoreのSignal理由が同じRunのVirtual Fill・Ledgerへ反映されることを確認した。`P5R-UNK-001`は `OPEN_NOT_PASS` のまま維持した。P5R-H2は、ユーザーから移譲された権限の範囲で `APPROVED_BY_DELEGATED_AUTHORITY` とし、状態を `COMPLETE_WITH_OPEN_UNKNOWN` と判定した。証拠は `tests/evidence/phase5R/RUN-P5R-12-20260816-001/` と正式完了HTMLに集約した。

P6以降は、本計画の実行結果だけで開始しない。P6-H0の別承認後に複数運用Unit・Portfolio・Account・Risk・OMSの固定Simulationを実装し、その後にForward Test、Shadow、Paper、Live候補、小規模Live、通常Liveの順で個別Gateを通す。

## 14. 実行中の是正追補（2026-08-16）

P5R本体の最終検証で、初期実装のSignal生成がApplication側の周期的な簡易判定に依存し、UIで選択したStrategyが実際のStrategy Coreの全Bar処理へ十分に伝播していない可能性を検出した。このまま完了扱いにすると「画面でStrategyを選べるが、計算の中身が同じ」という誤解を残すため、P5R-H2の最終判定前に是正した。

是正内容は、(1) `StrategyConfig`へEntry/Exit期間を明示的に渡す、(2) `TURTLE_SYS1`を`SYS1`、`TURTLE_SYS2`を`SYS2`へマッピングする、(3) 各完成M1 Barを `autotrade.strategy.service.process_closed_bars` へ順番に渡す、(4) Coreの `SignalEvent` の理由・方向・Signal IDをLedgerへ保存する、(5) LONG/SHORTのVirtual Fill、Exit、損益、残高を同じRunへ反映する、(6) cancel/resumeでもStrategyStateを保持する、である。既存 `BacktestRunner` はProbeの契約検証にも同じStrategyConfigで利用する。

是正後の証拠は、`tests/phase5R/test_backtest_product_red.py` のP5R-T-15、`RUN-P5R-04-20260816-001/application-green.md`、更新済みのP5R-11受入マトリクス、H2判定JSONへ反映した。P5Rテストは179 passed、Playwrightはdesktop/mobile各1件PASS、captureは各15枚、外部requestは0、axe blockingは0である。これにより、P5R-H2の状態は変更せず、判定根拠を強化した。
