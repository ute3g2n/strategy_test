# Phase 5R：バックテスト製品完全化 — 再構成提案・実行計画書

- 文書ID: P5R-PLAN-PROPOSAL-001
- 版: v0.1
- 作成日: 2026-08-16（Asia/Tokyo）
- 状態: **PROPOSAL_NOT_ADOPTED**
- 目的: UIから想定するバックテスト機能を、Phase 6より先に、限定した安全な範囲で本当に動く状態へ完成させるための再構成案。
- この文書がすること: Step 1の詳細プロンプトを示し、その同じ目的で実施したStep 2の判断結果と、採用する場合のPhase 5R実行計画を示す。
- この文書がしないこと: 現行の正式要件、正式HTML、統合台帳、Phase 6計画入力を勝手に書き換えない。Broker、Paper、Live、Secret、実資金、外部接続も開始しない。

> 重要: ここでいう「完璧」は、「絶対に壊れない」「必ず儲かる」という意味ではない。
> **最初に決めた範囲・操作・異常時の動き・テストを全部満たし、画面の見せかけではなく実際のデータと実際の計算で最後まで動く**、という意味で使う。

---

## 0. まず結論

### 推奨する再構成

**Phase 5の後、Phase 6の前にPhase 5Rを追加する。**

ただし、Phase 6を丸ごとPhase 5Rに移してはいけない。推奨する順番は次のとおりである。

~~~text
完了済み P4: 固定ローカルの製品土台・UIモック・API契約
        ↓
完了済み P5: 限定した市場データの品質確認（Open Unknown付き）
        ↓
追加する P5R: UIから本当に使える「バックテスト製品」を完成させる
        ↓
現行の P6: 複数の運用Unit、Portfolio、Risk、OMS、Forward/Shadowの安全土台
        ↓
P7: Broker Adapter / Paper
        ↓
P8以降: 長期運用、Live候補、Small Live、通常Live
~~~

### 「複数のUnitを管理」はP5Rに入れるべきか

**結論: 本来の「複数の運用Unitを管理」はP5Rに入れず、Phase 6に残す。**

ただし、バックテストのためだけの「複数の実験をまとめて走らせる」仕組みはP5Rに入れる。名前も意味も分ける。

| 名前 | たとえ | 入れるPhase | 中身 |
|---|---|---|---|
| Backtest Experiment Set / Sweep | 宿題の条件を少しずつ変えて、100通りの答案を採点する箱 | **P5R** | 単一Run、網羅検証、待ち行列、取消、再開、結果表、比較、CSV |
| 運用Unit | 複数のロボットが同じ家計からお金を使い、同時に外で働く単位 | **P6** | Unit開始・停止、共有Portfolio、Account、Risk、Order、Fill、Position、競合、Kill、照合、復旧 |

つまりP5Rの「複数」は、**独立した実験の束**である。P6の「複数」は、**同じ資金・同じ安全ルールを共有して動く運用単位**である。この二つを同じUnitという名前で混ぜると、バックテスト完成のために、まだ不要な注文・資金・安全停止の大工事まで先に作ることになる。

---

## 1. 中学生でも分かる言葉の整理

| 言葉 | やさしい説明 | P5Rでの扱い |
|---|---|---|
| Backtest | 昔の値動きの記録を使い、「このルールなら昔どうなったか」をコンピューターで試すこと | 主役。実際の注文は出さない |
| Run | 1回分の実験 | 画面から作る。入力・進み具合・結果・失敗理由を保存する |
| Sweep / 網羅検証 | 設定を少しずつ変え、たくさんのRunをまとめて試すこと | P5Rで完成させる |
| Experiment Set | Sweepを含む「実験の束」。運用Unitとは別物 | P5R専用の言葉として扱う |
| Data Manifest | 「どのデータを、どの期間・時間足・ルールで使ったか」の実験用の名札 | Runに固定して、後から勝手に入れ替えない |
| 5指標 | 総損益、最大の落ち込み、取引回数、勝率、総残高 | 画面に表示するだけでなく、根拠の取引明細までたどれるようにする |
| Holdout | 調整に使わず、最後の答え合わせ用に残しておく期間 | 見た結果を見てから設定をいじる用途に使わせない |
| Walk-forward | 時間を少しずつ前へずらしながら、毎回「過去で調整・次の期間で評価」を繰り返す試験 | P5Rで実際に戦略を走らせ、窓ごとの結果を残す |
| Risk入力の検査 | 数字・単位・必要な項目がそろっているかを確認する | P5Rに入れる。ただし実運用の注文拒否はしない |
| 運用Risk | 複数の運用Unitが合計で使いすぎないよう、注文前に止める安全装置 | P6に残す |
| OMS | Signalから注文、約定、保有までを間違えないようにつなぐ注文管理 | P6に残す |
| Portfolio | 複数Unit全体の資産・損益・リスクをまとめた財布 | P6に残す |

---

## 2. なぜP5Rが必要なのか — 現在地の事実

### 2.1 いま出来ていることと、まだ「画面から実際に使える」と言えないこと

Phase 4は、固定ローカル範囲での製品土台、API契約、UIモック、保存境界、品質確認を完了している。しかし、それは「本物の市場データを使ってUIからBacktestを走らせ、正しい結果を見られる」完成ではない。

| 現在の場所 | できている事実 | P5Rで埋める差 |
|---|---|---|
| P4完了記録 | 19 API、21画面、固定ローカル品質の範囲は確認済み | 実データ→実Core→実結果→UIの一本の流れは未完成 |
| UIモック | Backtest設定、進捗、結果、詳細、比較の画面と操作の見た目がある | 表示内容は固定匿名ダミー。画面操作が本当のRunを作っていない |
| Application API | 入力検査、Run、Job、結果、比較、CSVの契約がある | capabilityはBACKTEST_LOCAL = SUPPORTED_DESIGN。実行経路を完成させる必要がある |
| LocalWorker | Jobを取り出し、Core adapterと結果ファイル境界につなぐ骨組みがある | adapter / artifactsが無い場合はRECOVERY_REQUIREDで止まる。実用の常設実行ではない |
| BacktestCoreAdapter | 型付きCore requestを渡し、BacktestRunnerを呼べる経路がある | 最大ドローダウン、勝率、総残高、期間が実結果として完成していない |
| BacktestRunner | 型付きReplay、未来参照拒否、Calendar、Fill、snapshot / resumeなどのCore契約がある | P5の市場データを入力にして、UIの画面結果へ正しく投影する接続が必要 |
| P5データ品質 | BTCUSDT / ETHUSDT、Spot、1分足、UTC、指定期間、派生時間足、期間分割の品質確認がある | 実際のBacktestとWalk-forwardを走らせ、UIから確認する用途はまだ実証されていない |

### 2.2 いまのUIは「試作品の見本」であり、完成品ではない

UIモックには、Backtestに必要そうな画面がすでにある。

- SCREEN-08: Backtest条件設定
- SCREEN-09: Backtest実行一覧・進捗
- SCREEN-10: Backtest結果サマリー
- SCREEN-11: チャート・取引・Signal詳細
- SCREEN-12: Run比較

しかしUI実装は固定データを画面内で表示するモックである。例えば結果画面の5指標、チャート、取引明細、比較表は固定の表示例であり、実際にP5の市場データを読み、BacktestRunnerの結果から作ったものではない。

これは悪い実装という意味ではない。P4の目的は、先に「必要な画面・状態・安全境界・アクセシビリティ」を確認することだった。P5Rの目的は、そのモックを、**本当に動くローカルBacktest製品へ置き換えること**である。

### 2.3 P5は市場データの土台を作ったが、Backtest製品の完成ではない

P5の現在状態はP5-11_COMPLETE_WITH_OPEN_UNKNOWNである。確認済みの限定範囲は次のとおり。

| 項目 | 現在確認済みの範囲 |
|---|---|
| 市場 | Binance Data Visionの履歴データ、Crypto Spot |
| Symbol | BTCUSDT、ETHUSDT |
| 基底データ | 1分足、Raw / Normalized / Quality |
| 時間 | UTC、CRYPTO_24_7_UTC |
| 期間 | 2025-02-24以上、2026-08-01未満 |
| 派生時間足 | D1、H4、H1、M30、M15 |
| 品質 | 各Symbol 753,120本、重複0、観測Gap 0、ゼロ埋め0 |
| 期間分割 | train / validation / holdoutを重複なしで分離 |

一方で、次は未解消である。

| 未解消事項 | P5Rでの正しい扱い |
|---|---|
| Providerの利用・保持・再配布条件 | Passにしない。追加取得・再配布・Provider変更をしない。既存ローカル証跡の利用はP5R-H0で明示的に範囲確認する |
| P5-08のhost isolation | Passにしない。P5Rでは外部取得をしないため、P5-09 local evidenceで置換もしない |
| P5当時のchild Agent未起動 | 過去の事実をPassにしない。P5R自身の計画・レビューでは別に実ランタイム確認を行う |
| fee / slippage / 内部実行費 | 実測済みと表示しない。P5Rで使う場合は「明示した仮定」と表示し、実市場コストと混同しない |
| Walk-forward | P5では期間境界だけを検査した。戦略を実行した窓別結果はまだない |

### 2.4 要件が求めているBacktestの残り

要件定義書のREQ-V2-0044からREQ-V2-0055は、単一Backtestだけでなく、Sweep、比較、CSV、Holdout、Walk-forwardまでを一まとまりとして求めている。

| 要件 | 現在の状態 | P5Rでの完成条件 |
|---|---|---|
| REQ-V2-0044 入力固定 | 固定Replayの契約はある。UI統合は未実装 | UI / JSON / YAMLの入力が同じ型付きRun入力になり、実行前に全入力を確認できる |
| REQ-V2-0045 開始・進捗・停止 | 固定Run契約はある。UIと長時間Workerは未実装 | ValidatingからCompleted / Failed / Cancelled / Recovery Requiredまで本当の状態を表示する |
| REQ-V2-0046 5指標と根拠 | 固定fixtureで確認済み | 実P5データのRunで5指標、Chart、取引、Signal、Data、Evidenceを相互にたどれる |
| REQ-V2-0047 Sweepの組合せ | 未実装 | 下限・上限・刻み・丸め・上限包含・無効行を表示する |
| REQ-V2-0048 Sweep開始前の負荷確認 | 未実装 | 件数、無効件数、推定時間、推定容量、Backtest専用資源状態、明示確認を表示する |
| REQ-V2-0049 全組合せの結果 | 固定結果契約のみ | 完了・失敗・取消・未実行を含む全行を、実際の結果で保存・表示する |
| REQ-V2-0050 Sweep取消・失敗・再開 | 未実装 | 個別失敗、全体停止、取消、再開、失敗行だけの再試行を別々に扱う |
| REQ-V2-0051 同条件Runの履歴 | 未実装 | 最新表示と過去Runを分け、過去を消さない |
| REQ-V2-0052 比較可能性 | 未実装 | 入力差を示し、比較不能なRunを同じ順位表に混ぜない |
| REQ-V2-0053 大量表とCSV | 未実装 | 表示の絞込み・並べ替え・詳細と、非同期CSVの進捗・取消・失敗を実装する |
| REQ-V2-0054 Holdout / Walk-forward | 期間境界は固定範囲で確認済み | P5データで窓ごとの実Backtestを実行し、未来参照・不良Dataを停止する |
| REQ-V2-0055 Holdout再利用制限 | 未実装 | Holdoutの結果を見てからの自動設定変更・自動最良採用を禁止し、明示記録なしに使い回せない |

---

## 3. 検討した3案と判定

| 案 | 何をするか | 良い点 | 問題点 | 判定 |
|---|---|---|---|---|
| A. 薄いP5Rをそのまま挿入 | UIの表示を少し直し、P5のデータを選べるようにする | 短く見える | 実Coreへの接続、正しい5指標、Sweep、履歴、比較、CSV、実行済みWalk-forwardが残る。「完成」と言えない | 不採用 |
| B. P6全体をP5Rへ吸収 | 複数運用Unit、Portfolio、Risk、OMS、Forward/Shadow、Kill、照合まで先に作る | 将来の本番機能まで一気に進むように見える | 共有資金、注文状態、競合、復旧という別の巨大課題が入り、Backtest完成が遅れる。P6→P7の安全順序もぼやける | 不採用 |
| C. P6からBacktest専用の一部だけ切り出す | UI実行、Run / Sweep、Backtest専用Queue、結果・比較・CSV、Holdout / Walk-forwardをP5Rへ。運用Unit / Portfolio / Risk / OMSはP6に残す | ユーザーが求める「UIから全部動くBacktest」を最短で完成させつつ、本番安全機能の境界を守れる | P5Rの受入範囲と負荷条件を先に明確化する必要がある | **採用** |

### 採用理由を一言でいうと

バックテストを完成させるために必要なのは、**実験を正しく作る・走らせる・止める・結果を見る・比べる**仕組みである。
本番運用に必要なのは、**複数のロボットが同じ財布と安全ルールを共有しても事故を起こさない**仕組みである。

前者をP5R、後者をP6に分けるのが、目的と安全の両方に合う。

---

## 4. P5Rへ移すもの、P6に残すもの

### 4.1 P5Rの対象

P5Rは、外部注文を一切出さない、ローカルで再現できるBacktest製品を完成させる。

| 区分 | P5Rへ入れる具体的なもの | なぜ必要か |
|---|---|---|
| 実データ接続 | P5で確認したNormalizedデータを、型付きのBacktest入力へ変換する読み取り専用Adapter | モックではなくP5の市場データで計算するため |
| 入力 | Symbol、期間、時間足、Strategy / Config版、初期資金、Risk入力、費用・滑りの仮定、Calendar、Holdout条件 | 「何を試したか」が後から分かるようにするため |
| 入力検査 | 型、単位、必須関係、基本範囲、期間、未来参照、Data品質、Calendar、許可範囲 | 壊れた実験をQueueへ入れないため |
| 単一Run | preflight、Run作成、Job、Queue、進捗、取消、停止、失敗、再実行、checkpointからの再開 | UIから実際に1回のBacktestを最後まで扱うため |
| 5指標 | 総損益、最大ドローダウン、取引回数、勝率、総残高を、実際の取引・残高変化から計算する | 現在の固定値投影をなくし、結果を信頼できる形にするため |
| 詳細表示 | Chart、Entry、追加、Stop、Exit、Signal、Position、損益、設定、Data、Evidenceの相互リンク | 数字だけを見て誤解しないため |
| Sweep | 組合せ展開、上限包含、無効理由、件数・負荷見積り、明示確認、子Run、部分失敗、取消、再開 | UIで網羅検証を本当に使えるようにするため |
| 結果分析 | 全件表、検索、絞込み、並べ替え、ページングまたは仮想化、詳細、履歴、比較可能性判定 | 大量の結果を誤解せず確認するため |
| CSV | 非同期Job、進捗、取消、失敗、完了、ローカル出力 | 大きな表でUIを固めないため |
| Holdout / Walk-forward | 期間分割、未来参照拒否、Holdout再利用制限、実戦略の窓別Run | 「都合の良い期間だけ選ぶ」ごまかしを防ぐため |
| UI品質 | 実ブラウザのE2E、固定データのGolden、a11y、キーボード、失敗状態、ローカル外部通信なしの確認 | 画面が見えるだけでなく、使えることを確認するため |

### 4.2 P6に残すもの

| 区分 | P6に残す具体的なもの | P5Rに移さない理由 |
|---|---|---|
| 運用Unit | Unitの作成・開始・停止・版管理・重複・競合 | 実験Runとは別の、継続運用の概念だから |
| Portfolio / Account | 複数Unitの資金、保有、損益、資金配分の集約 | Backtest実験を1件ずつ評価するだけなら不要だから |
| 運用Risk | Risk Version、合計上限、注文前判定、拒否理由 | 実資金・実注文へ向かう安全装置であり、P5Rで見せる仮定と混ぜてはいけないから |
| OMS | Signal → Target Position → OrderIntent → Order → Fill → Positionの共通状態 | Backtestの仮想Fillの表示と、将来の外部注文管理は別の責務だから |
| Idempotency /競合 | 複数Unit・複数モード・再起動時の重複注文防止 | 実験のRun再実行とは危険度も対象も異なるから |
| Forward / Shadow | 実時間データを使う仮想運用 | 時間が流れる運用であり、過去データを読むBacktestと別だから |
| Kill / Reconcile | 全体停止、外部・内部状態の照合、既存Positionの扱い | これを未完成のまま本番寄りの機能へ進めないため |
| 20〜40運用Unit | 運用構造としての負荷制御 | P5RのSweep負荷と、継続運用の負荷は別の試験だから |

### 4.3 P5Rに「限定して」入れるP6由来の要素

| 元のP6テーマ | P5Rへ切り出す最小部分 | 絶対にP5Rへ持ち込まない部分 |
|---|---|---|
| Run / Job / Queue | Backtest専用の待ち行列、優先度、取消、checkpoint、再開 | Forward / Shadowや運用Unitと同じQueueを共有すること |
| Resource制御 | Sweep開始前の件数・推定時間・推定容量・同時Backtest数の上限 | Portfolioや実時間Unitに優先順位を付けること |
| Fill | BacktestCoreの仮想約定結果を、取引明細として表示すること | OrderIntent / Order / Broker Fillの一般OMS化 |
| Risk | Backtest入力の型・単位・関係・基本範囲を検査すること | 実Risk値、Portfolio集約、注文前Reject |
| 再開 | 同じBacktest Jobの安全なcheckpoint再開 | 外部状態を照合しないまま運用Unitを自動再開すること |

---

## 5. P5Rで「バックテストが完成した」と判定する範囲

### 5.1 固定する製品範囲

P5R-H0で最終承認する前提の推奨範囲は、次のとおりである。

| 項目 | P5Rの推奨範囲 |
|---|---|
| 実行場所 | 開発PC上のローカルアプリケーション。外部公開しない |
| UI | ローカルブラウザで操作する実UI。固定モックのボタン表示だけでは合格にしない |
| 市場データ | P5で確認済みのローカル証跡のみ。BTCUSDT / ETHUSDT、Spot、1分足、UTC、CRYPTO_24_7_UTC、指定期間、派生時間足 |
| 戦略 | 既存の凍結済みStrategy / Configの選択と実行。戦略ソースを画面で自由に編集しない |
| 実行モード | Backtestだけ。Forward、Shadow、Paper、Liveは開始不可表示を維持する |
| 費用・滑り | UIで明示した「仮定値」を入力・保存・結果に表示できる。ただし実測値・実市場適合と表示しない |
| 保存 | ローカルのRun、Job、結果、操作記録、Evidence参照。保存方式と保持期間はP5R-H0で明示する |
| 外部I/O | 新規取得、Provider変更、Broker接続、API key / Secret読取り、外部送信をしない |

### 5.2 画面の対象範囲

P5Rで「UIからバックテスト機能が全部動く」と言う対象を、21画面全体と混同しない。

| 画面 | P5Rでの状態 | P5Rで実際に動かすもの |
|---|---|---|
| SCREEN-01 システム状態・禁止事項 | 支援画面 | Backtest専用モード、外部接続なし、対象外を正しく表示 |
| SCREEN-02 ホーム | 支援画面 | Backtest Run / Job / 結果の実集計を表示 |
| SCREEN-05 市場データ・品質 | **読み取り専用でP5R対象** | P5データの範囲・品質・停止理由を表示。取得・再取得・Provider変更は不可 |
| SCREEN-06 / 07 Strategy | **読み取り専用でP5R対象** | 実行可能な凍結済みStrategy / Config版の選択・説明。画面からソース変更は不可 |
| SCREEN-08 Backtest条件設定 | **主対象** | 単一Run / Sweepの実入力、preflight、開始前確認 |
| SCREEN-09 Backtest実行一覧・進捗 | **主対象** | 実Run / Job / Queue、取消、失敗、再開、進捗 |
| SCREEN-10 結果サマリー | **主対象** | 実5指標、履歴、CSV起動、Evidenceへの導線 |
| SCREEN-11 詳細 | **主対象** | 実Chart、取引、Signal、Position、設定、Dataへの導線 |
| SCREEN-12 比較 | **主対象** | 実結果の比較、比較不能理由、採否メモ。自動最良採用なし |
| SCREEN-17 警告・障害 | 支援画面 | 実行失敗、Data不良、取消、再開不可、CSV失敗の次操作 |
| SCREEN-18 Human Gate・移行確認 | 支援画面 | Holdout再利用に関する要確認記録。P6 / Paper / Liveへの自動昇格は不可 |
| SCREEN-19 監査ログ・証跡 | 支援画面 | Run、Job、入力、結果、操作、停止理由、Evidence参照 |
| SCREEN-03 / 04 Unit、SCREEN-13〜16、SCREEN-20 | **P5R対象外** | P6以降の未承認・開始不可を正しく表示し続ける |

### 5.3 完成判定のE2E受入シナリオ

次の各シナリオが、固定ダミーではなく、実P5データ・実Core・実保存結果で通ることをP5Rの完了条件にする。

| ID | 利用者がすること | システムが本当にすること | 合格条件 |
|---|---|---|---|
| P5R-AC-01 | 許可されたSymbol、期間、時間足、Strategy / Configを選ぶ | P5のローカルカタログと品質状態だけを候補に出す | 範囲外Symbol、未来期間、未品質Dataは選択・開始できない |
| P5R-AC-02 | 初期資金、Risk入力、費用・滑りの仮定を入れる | 型、単位、必須関係、基本範囲を検査し、入力値をRun候補へ固定する | どの入力が悪いか画面で分かり、悪いRunはQueueへ入らない |
| P5R-AC-03 | 開始前確認を開く | 全入力、Data範囲、Calendar、費用仮定、Holdout属性、実行見込みを一画面に出す | 確認なしに実行開始しない |
| P5R-AC-04 | 単一Backtestを開始する | Validating → Queued → Running → Completedまたは失敗状態を、実Jobから表示する | 固定表示だけで成功にしない。実Core結果が保存される |
| P5R-AC-05 | 実行中に取消する | 安全なcheckpointで止め、中途結果を参考用として区別する | Cancelled / Stopped / Failed / Recovery Requiredを混同しない |
| P5R-AC-06 | 再開可能なJobを再開する | checkpoint、入力、データ範囲の整合を確認して、許可される場合だけ新Jobを作る | 不整合なら成功表示せずRecovery Requiredで止める |
| P5R-AC-07 | 結果を開く | 総損益、最大ドローダウン、取引回数、勝率、総残高を実計算して出す | 5指標の定義、単位、丸め、期間、費用仮定、根拠に戻れる |
| P5R-AC-08 | Chart・取引・Signal詳細を見る | 価格、Signal、仮想Fill、Position、損益の同じRunの明細を表示する | 存在しない取引・Signalを画面が作り出さない |
| P5R-AC-09 | Sweepを設定する | 下限、上限、刻み、型、丸め、条件を展開し、無効行も理由付きで残す | 上限漏れ、重複、無効組合せの黙殺がない |
| P5R-AC-10 | Sweep開始前の確認をする | 全件数、実行可能数、無効数、推定時間、推定容量、Backtest専用資源状態を表示する | 明示確認なしの開始、推定不能時の強行開始をしない |
| P5R-AC-11 | Sweep中に個別失敗・取消・全体停止を経験する | 組合せごとの状態、失敗理由、途中結果、再開位置を保存する | 失敗行を消して「全件成功」と表示しない |
| P5R-AC-12 | 同条件で再Runし、比較画面を開く | 最新表示と過去履歴を分け、比較入力の同一・差分を出す | 比較不能Runを同じ順位表へ混ぜず、最良値を自動採用しない |
| P5R-AC-13 | 大量結果を絞込み、CSVを出力する | 表をUI停止なしに扱い、CSVを別Jobで作る | CSVの開始、進捗、取消、失敗、完了が画面と記録で一致する |
| P5R-AC-14 | Holdout / Walk-forwardを実行する | 窓ごとに実Backtestを実行し、未来参照、重複、隙間、Data不良を止める | Holdoutの結果を自動で設定変更・自動採用に使わない |
| P5R-AC-15 | キーボードだけで主要操作をする | 入力、開始確認、取消、結果、比較、CSV、失敗理由へ移動する | name / role / focus / コントラストがテストで確認できる |
| P5R-AC-16 | P5R対象外の画面へ行く | Forward、Paper、Live、Portfolio、Order、Secret設定は開始不可と表示する | Backtest完成を理由に対象外機能を有効化しない |

### 5.4 「完璧に完成」と言える表示

P5Rの完了時に言ってよいことは、次だけである。

> 承認されたP5Rの限定範囲では、運用者がローカルUIからBacktest条件を作り、P5の承認済みローカルデータで単一RunとSweepを実行し、取消・再開・失敗・履歴・比較・CSV・Holdout / Walk-forwardを、根拠付きで確認できる。

P5Rの完了時に言ってはいけないことは、次である。

- この戦略は儲かる。
- 手数料・滑りが実市場と一致する。
- PaperやLiveでも安全に動く。
- 複数Unitの合算Riskが安全である。
- Brokerへ接続してよい。
- Providerの利用・保持・再配布条件が解決した。

---

## 6. P5Rの構成方針

### 6.1 依存方向

P5Rでは、画面がCoreの答えを作ってはいけない。画面は入力を集め、状態と結果を表示するだけにする。

~~~text
ローカルUI
  ↓ 型付きCommand
Application API / Preflight
  ↓ 許可されたRun / Jobだけ
Backtest専用Queue / Worker
  ↓ 読み取り専用のP5 Data Adapter
型付きBacktestCore request
  ↓
既存BacktestRunner
  ↓
結果・取引・Signal・状態
  ↓
結果Artifact / 監査参照
  ↓
Application API
  ↓
ローカルUIの結果・比較・CSV・Evidence画面
~~~

### 6.2 P5Rで直すべき現在の技術的な差

1. P5のNormalizedデータを、許可範囲外へ広げずにBacktestCore requestへ渡す。
2. BacktestCoreAdapterが、実行結果から5指標を完全に投影できるようにする。
3. LocalWorkerを、意図的に有効化したBacktest専用のadapter / artifact構成で動かす。
4. UIモックの固定Run行、固定5指標、固定Chart、固定比較を、Application APIの実結果へ置き換える。
5. SweepとCSVを「ボタンを押したら文言が変わる」ではなく、実Jobとして動かす。
6. Holdout境界だけで終わらせず、実際の窓ごとのBacktestを実行する。

### 6.3 RiskをP5Rでどこまで扱うか

P5Rでは、Risk入力を捨てたり、存在確認だけにしてはいけない。要件どおり、型、単位、必須関係、基本範囲、項目間整合性を開始前に検査する。

ただし、P5Rでは「この実運用注文は危険だから拒否する」という実Risk判断を作らない。

| P5Rで行う | P6以降で行う |
|---|---|
| 入力が数字か、単位が正しいか、必要な組合せがそろうかを確認 | 複数Unit合計のExposure、資金配分、実Risk上限 |
| 仮想Backtest内で使った初期資金・想定数量・費用仮定を結果に残す | Order前Risk Reject、Kill、実Accountとの照合 |
| 不正・未確定の入力ならRun開始を拒否 | 実Risk値、1N、初回Order上限の確定 |

---

## 7. 推奨するPhase 5R実行Runbook

この節は、ユーザーが採用を承認した後に使うPhase実行計画の骨格である。正式開始前に、この提案を基に正式HTMLと計画を作る。

### 7.1 P5R開始前のHuman Gate

P5-H2の承認は、P5R開始承認ではない。P5R-H0として、次を承認対象にする。

| Gate | 運用者が確認すること | 未承認なら止める範囲 |
|---|---|---|
| P5R-H0 | P5Rの目的、対象UI、P5データのローカル限定利用、追加取得なし、完了シナリオ、保存方式、固定PCでの受入負荷、P6に残す範囲 | P5Rの実装・UI接続・新しいRun |
| P5R-H1 | 詳細設計、Backtest Data Adapter、5指標の定義、Sweep / CSV / Holdoutの異常系、テスト設計 | 実装とテストのGreen化 |
| P5R-H2 | 全P5R受入シナリオ、対象外境界、Open Unknown、P6への引渡し内容 | P6開始。Paper / Liveは承認しない |

### 7.2 推奨ステップ

| Step | 目的 | 主な成果物 | 依存 | P6へ持ち込まないもの |
|---|---|---|---|---|
| P5R-00 | 採用判断とP5R-H0準備 | 正式P5R計画案、Human Gate、対象・非対象表 | この提案の採用指示 | P6全体の前倒し |
| P5R-01 | 現状差分と追跡を確定 | REQ / UC / Screen / Test / Unknown追跡、現行UI・API・Core差分表 | P5R-H0 | 推測での要件追加 |
| P5R-02 | 詳細設計 | Data Adapter、実行・保存、5指標、Sweep、CSV、Holdout / Walk-forward詳細設計 | P5R-01 | Portfolio / Account / OMS |
| P5R-03 | REDテストとGolden設計 | 実P5データの入力fixture、独立オラクル、失敗注入、UI E2E設計 | P5R-02、P5R-H1 | 収益性の主張 |
| P5R-04 | Core結果を製品へ接続 | 実5指標、結果投影、Worker、Artifact、Run / Jobの実行接続 | P5R-03 | Broker注文 |
| P5R-05 | 単一Backtest UIを実接続 | SCREEN-05〜12、17〜19のBacktest範囲を実APIへ接続 | P5R-04 | Unit CRUD / Portfolio UI |
| P5R-06 | Sweepと回復を完成 | 組合せ展開、資源確認、取消、部分失敗、再開、履歴 | P5R-04 | 運用Unit間の競合 |
| P5R-07 | 分析・比較・CSVを完成 | 表、比較可能性、履歴、非同期CSV、監査導線 | P5R-05、P5R-06 | 自動最良採用 |
| P5R-08 | Holdout / Walk-forwardを実行 | 実窓別Run、再利用制限、画面・記録、停止条件 | P5R-04、P5R-05 | Forward / Shadow |
| P5R-09 | 統合品質・レビュー | Contract / Integration / E2E / a11y / visual / failure injection / static review | P5R-05〜08 | 未測定性能のPass化 |
| P5R-10 | 完了判定とP6再引渡し | 完了HTML、統合台帳更新、P6入力再発行、P5R-H2 | P5R-09、P5R-H2 | P7開始、外部接続 |

### 7.3 並列化の考え方

| 並列にしてよい | 理由 |
|---|---|
| P5R-01の要件追跡とP5R-02の現行実装差分調査 | 読み取り中心で、成果物の書き込み場所を分けられる |
| P5R-03のGolden / failure injection設計とP5R-05のUI詳細設計 | 実装前の設計として並列にできる |
| P5R-06のSweep仕様とP5R-07の比較 / CSV仕様 | 同じ結果契約を共有するが、設計責務は分離できる |

| 必ず順番にする | 理由 |
|---|---|
| P5R-H0 → P5R-01 | 何を完成と呼ぶかを決めずに実装を始めない |
| P5R-02 → P5R-03 → P5R-04 | 結果・入力・異常系の契約を決めてから実装する |
| P5R-04 → P5R-05〜08 | 本当の実行結果がない状態でUIやWalk-forwardを完成扱いにしない |
| P5R-05〜08 → P5R-09 → P5R-H2 | 全E2Eとレビューを通すまでP6へ渡さない |

### 7.4 各Stepで使うAI部品

P5Rの正式計画では、次を既存の汎用部品として使用する。Phase 1専用部品は使わない。

| Step群 | Orchestrator | Agent | Skill |
|---|---|---|---|
| P5R-00〜01 | AutoTradePhasePlanning_Orchestrator_v0_1 | AutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1 | autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1 |
| P5R-02 | AutoTradeProject_ImplementationDesign_Orchestrator_v0_1 | AutoTrade_A82_ImplementationDetailDesigner_v0_1、AutoTrade_A91_ImplementationDetailReviewer_v0_1、AutoTrade_A20_ArchitectureDomainArchitect_v0_1、AutoTrade_A30_StrategyQaArchitect_v0_1 | autotrade_skill_implementation_detail_design_v0_1、autotrade_skill_implementation_detail_review_v0_1、autotrade_skill_architecture_writer_v0_1、autotrade_skill_golden_test_v0_1、autotrade_skill_test_strategy_v0_1 |
| P5R-03〜09 | AutoTradeProject_ImplementationQuality_Orchestrator_v0_1 | AutoTrade_A110_PythonTestEngineer_v0_1、AutoTrade_A120_PythonImplementer_v0_1、AutoTrade_A130_VerificationEngineer_v0_1、AutoTrade_A140_DebugEngineer_v0_1、AutoTrade_A150_PythonCodeReviewer_v0_1、AutoTrade_A170_UiMockEngineer_v0_1、AutoTrade_A171_UiVisualQaReviewer_v0_1 | autotrade_skill_python_test_quality_v0_1、autotrade_skill_python_implementation_v0_1、autotrade_skill_debug_recovery_v0_1、autotrade_skill_python_code_review_v0_1、autotrade_skill_ui_mock_generation_v0_1、autotrade_skill_ui_accessibility_validation_v0_1、autotrade_skill_ui_visual_validation_v0_1 |
| P5R-10 | AutoTradeProject_DesignDocSet_Orchestrator_v0_1 | AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1 | autotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1 |

### 7.5 各Stepの実行プロンプト骨子

以下は、正式P5R計画にそのまま貼れる程度の粒度で書いた実行指示の骨子である。各Stepの実行時には、指定Orchestratorと指定Agentを実際に起動し、待機結果または起動不能のFallbackを、事実どおりに記録する。

#### P5R-00：範囲とGateを正式化する

~~~text
Phase ID: P5R
Step: P5R-00
目的: Backtest製品完全化の範囲を承認可能な形に固定する。

最初に、AutoTradePhasePlanning_Orchestrator_v0_1を定義JSONの固定modelで実起動する。
CoordinatorはAutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、
AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1を個別起動し、
完了を待機する。起動不能ならRUNTIME_DISPATCH_FALLBACK_REQUIREDと理由、未起動Agent、
agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。

入力:
- doc/requirements/01_自動トレードシステム要件定義書_v2.html
- doc/phase4/05_完了/07_Phase4完了判定・Phase5計画引渡し.html
- doc/phase5/06_完了/08_Phase5完了判定・Phase6計画引渡し.html
- plan/phase5/Phase6計画入力一覧_2026-08-12.md
- doc/00_全Phase残課題Blocked統合台帳.html
- plan/Phase5R_バックテスト製品完全化_再構成提案・実行計画書_v0.1_2026-08-16.md

必須判断:
1. P5Rの対象を、ローカルBacktest、P5の既存データ、UI、Run/Sweep、結果、比較、CSV、
   Holdout/Walk-forwardに限る。
2. Portfolio、Account、運用Risk、OMS、運用Unit、Forward/Shadow、Broker、Paper、LiveをP6以降に残す。
3. P5R-H0で、既存ローカルデータ利用の許容範囲、固定PCの受入負荷、保存方式、完了シナリオを承認対象にする。
4. Provider条件、host isolation、P5当時のchild dispatch、実行費用をPassにしない。
5. 外部I/O、Secret、実注文、実資金、Cloudを開始しない。

成果物:
- plan/Phase5R_実行計画書_v0.1_YYYY-MM-DD.md
- doc/phase5R/配下の正式HTML成果物一覧案
- P5R-H0のHuman Gate文案
- 統合台帳へ追加すべきP5R行の案

停止:
- P5RをP6全体へ拡大しようとする場合
- P5-H2をP5R-H0の承認と読み替える場合
- 不明事項をPassにする場合
~~~

#### P5R-01：要件・UI・実装差分を追跡する

~~~text
Phase ID: P5R
Step: P5R-01
目的: REQ-V2-0044〜0055と、P5R-AC-01〜16を、既存UI・API・Core・テストの差分へ一対一に結ぶ。

入力:
- P5R-00の承認済み範囲
- UI mockのSCREEN-05〜12、17〜19
- src/autotrade/application/
- src/autotrade/backtest/
- P5のQuality / period split evidence

実施:
1. 各要件ごとに、現在の実装状態をIMPLEMENTED / PARTIAL / NOT_IMPLEMENTED / OUT_OF_SCOPEに分ける。
2. 固定ダミー表示、実Core未接続、固定値指標、未実行Walk-forwardを個別のGapとして登録する。
3. Gapごとに、設計、REDテスト、実装、E2E、正式HTML、Evidence、後続Phaseを結ぶ。
4. SCREEN-03 / 04とSCREEN-13〜16 / 20をP5R対象外と明記する。

完了:
- P5R-REQ-TRACE-001として、要求→画面→API→Core→Test→Evidence→Gateを追える。
- 不明事項を実装済みと表示しない。
~~~

#### P5R-02：実装詳細設計を作る

~~~text
Phase ID: P5R
Step: P5R-02
目的: 実装者が追加判断なしに、P5データから実Backtest結果をUIへ出す詳細設計を作る。

必須設計:
- 読み取り専用P5 Data Adapterの入力・出力・許可範囲・Data Quality停止
- Run / Job / Queue / checkpoint / resumeのBacktest専用状態遷移
- 5指標の式、単位、丸め、欠損・中途結果の扱い
- Chart / trade / Signal / Positionの結果スキーマ
- Sweepの展開、無効行、開始前資源確認、部分失敗、取消、再開
- history / comparison / CSVの状態・保存・異常系
- Holdout / Walk-forwardの窓作成、未来参照、再利用制限
- UIの画面ごとの実API接続、Loading / Failed / Recovery Required / Unapproved

禁止:
- Broker、Secret、Paper、Live、実Account、Portfolio、OrderIntent、Order、外部I/Oを詳細設計へ入れない。
- 実測されていない費用・滑りを実市場値として固定しない。

完了:
- doc/phase5R/に正式HTML詳細設計を置き、doc/index.htmlから到達できる計画を含める。
- AutoTrade_A91_ImplementationDetailReviewer_v0_1のFindingを反映し、Critical / Highを残さない。
~~~

#### P5R-03：REDテストとGoldenを先に作る

~~~text
Phase ID: P5R
Step: P5R-03
目的: 実装より先に、間違ったBacktest結果・画面の見せかけ・過学習を検出できるテストを作る。

必須:
- P5データから小さく切り出した固定入力で、独立オラクルにより5指標を検証する。
- 実P5範囲の少なくとも代表ケースで、Data Adapter → Runner → Result → APIのE2Eを検証する。
- UIで、入力不正、Data不良、取消、checkpoint不整合、CSV失敗、比較不能、Holdout再利用を確認する。
- Sweepの上限包含、丸め、無効組合せ、部分失敗、再開を確認する。
- Walk-forwardは「窓が表示される」だけでなく、各窓に実Runが存在することを確認する。

停止:
- 同じ実装の関数で期待値を作り、自己採点だけでPassにする場合
- P5データの未知事項を収益性・実取引適合へ一般化する場合
~~~

#### P5R-04：実行・結果経路をGreenにする

~~~text
Phase ID: P5R
Step: P5R-04
目的: P5のローカルデータを実Coreへ渡し、正しい5指標と明細を結果Artifactへ保存する。

実施:
- BacktestCoreAdapterの固定値投影を、定義済みの実計算へ置き換える。
- LocalWorkerをBacktest専用の承認済みAdapter / Artifactで動かす。
- 結果不整合、Data Quality不良、未来参照、入力不正、保存失敗では成功を返さない。
- 結果の各行をChart / trade / Signal画面が読める型へ投影する。

完了:
- P5R-AC-01〜08のサーバ側契約とGoldenがGreen。
- 既存Coreの責務を画面やApplication層へコピーしない。
~~~

#### P5R-05：単一BacktestのUIを実接続する

~~~text
Phase ID: P5R
Step: P5R-05
目的: SCREEN-05〜12、17〜19のBacktest範囲を、固定ダミーから実API表示へ置き換える。

実施:
- SCREEN-08から実preflight、実Run、実Sweep候補を作る。
- SCREEN-09で実Jobの進捗、取消、失敗、再開を表示する。
- SCREEN-10 / 11で実5指標・Chart・取引・Signal・根拠を表示する。
- SCREEN-17 / 19で失敗理由・操作・Evidence参照を表示する。
- 対象外の画面は開始不可のままにする。

完了:
- ブラウザE2Eで、P5R-AC-01〜08を固定環境で確認する。
- 外部接続は発生させない。
~~~

#### P5R-06：Sweepと回復を実接続する

~~~text
Phase ID: P5R
Step: P5R-06
目的: 実験の束を安全に実行・取消・再開できるようにする。

実施:
- 値展開、無効組合せ、件数、推定、確認Dialogを実装する。
- 子Runごとの成功、失敗、取消、未実行、要確認を保存・表示する。
- checkpointからの再開を許可条件付きで実装する。
- Sweepの同時実行はBacktest専用の資源枠内だけにする。

禁止:
- 実験の子RunをP6の運用Unitとして扱わない。
- 失敗行を削除して完了に見せない。
~~~

#### P5R-07：結果分析・比較・CSVを実接続する

~~~text
Phase ID: P5R
Step: P5R-07
目的: 多数のBacktest結果を、誤解なく閲覧・比較・出力できるようにする。

実施:
- 最新表示と全履歴を分ける。
- 比較対象のData、期間、時間足、Strategy / Config、費用仮定、Calendar、Mode差を表示する。
- 比較不能なRunを同じ順位表へ混ぜない。
- 自動最良採用を実装しない。
- CSVを非同期Jobとして実装し、開始・進捗・取消・失敗・完了を追跡する。

完了:
- P5R-AC-12 / 13のE2EがGreen。
~~~

#### P5R-08：Holdout / Walk-forwardを実行する

~~~text
Phase ID: P5R
Step: P5R-08
目的: 期間境界だけでなく、実戦略を窓ごとに実行し、過学習を防ぐ。

実施:
- train / validation / holdout / walk-forward窓を固定ルールで作る。
- 窓ごとに実Runと結果を残す。
- 未来参照、重複、隙間、期間不足、Data Quality不良を停止する。
- Holdout結果を見た後の設定変更を自動採用しない。

完了:
- P5R-AC-14のE2EとGoldenがGreen。
- 「Walk-forwardの境界だけ確認済み」を完成扱いしない。
~~~

#### P5R-09〜10：品質・完了判定・P6引渡し

~~~text
Phase ID: P5R
Step: P5R-09〜10
目的: P5Rを見せかけの完成にせず、P6へ正しい入力だけを渡す。

必須確認:
- Contract、Integration、Golden、failure injection、ブラウザE2E、a11y、visual、static policyの結果
- P5R-AC-01〜16の実施結果
- P5R対象外画面が誤って有効化されていないこと
- Provider条件、host isolation、費用、過去P5のdispatch UnknownがPass化されていないこと
- 20〜40運用Unit、Portfolio、Risk、OMS、Forward/ShadowがP6へ残っていること

成果物:
- doc/phase5R/の完了HTML
- doc/index.htmlの導線
- doc/00_全Phase残課題Blocked統合台帳.htmlのP5R現在状態・Unknown・Human Gate整合
- plan/phase5R/のP6再引渡し入力

停止:
- Critical / Highが残る
- UIモックだけで受入にする
- 外部I/O、Secret、Broker、Paper、Live、実資金を混ぜる
~~~

### 7.6 P5Rの成果物配置

採用後の正本配置は、次を推奨する。

| 種別 | 保存先 |
|---|---|
| P5R正式HTML | doc/phase5R/ |
| P5R実行計画・ログ | plan/Phase5R_実行計画書_v0.1_YYYY-MM-DD.md、plan/phase5R/ |
| 実装詳細設計 | doc/phase5R/02_実装詳細設計/ |
| テスト・実行証跡 | tests/evidence/phase5R/RunId/ |
| 残課題の現在状態 | doc/00_全Phase残課題Blocked統合台帳.html |
| HTML入口 | doc/index.html |

---

## 8. Phase 6以降をどう変えるか

### 8.1 新しいロードマップ

| 順番 | Phase | 役割 | 完了して初めて次へ渡すもの |
|---|---|---|---|
| 1 | P4 完了済み | 固定ローカルの製品土台・UI契約 | API、UI設計、固定品質、Core境界 |
| 2 | P5 完了済み | 限定市場データの品質・期間分割 | P5データ契約とOpen Unknown |
| 3 | **P5R 新設** | UIから実際に使えるBacktest製品 | 実P5データでのRun / Sweep / 結果 / 比較 / CSV / Walk-forward |
| 4 | P6 | 複数運用Unit、Portfolio、Risk、OMS、Forward / Shadow | 本番前の安全な運用土台 |
| 5 | P7 | Broker AdapterとPaper | P6の安全土台を使った外部Paper検証 |
| 6 | P8 | 長期Paper、Soak、Backup、端末・運用堅牢化 | 実機・長期の運用証拠 |
| 7 | P9〜P11 | Live候補、Small Live、通常Live | 別Human Gateごとの段階的拡大 |

### 8.2 P6の目的は縮めない

P5Rの追加は、P6を弱くする変更ではない。P6は次の責務をそのまま持つ。

- 複数の運用Unitを同時に管理する。
- Portfolio / Account / 資金配分を集約する。
- すべてのOrderの前にRiskを判定する。
- SignalからPositionまでのOMS状態を一貫させる。
- Duplicate、Partial、Reject、Expire、競合、再起動、照合、Killを固定Simulationで試す。
- 外部OrderなしのForward / Shadowを試す。

P5Rは、P6がこの安全機能を作る前に、未完成のBacktest結果を土台にしないようにするための前提整備である。

### 8.3 公式文書へ反映するのは採用後

この提案を採用する場合だけ、次を一つの変更セットとして更新する。

1. 要件定義書のPhase 4〜11ロードマップにP5Rを追加する。
2. Phase 6の開始条件を「P5RのBacktest製品完了」に更新する。
3. Phase 5のP6引渡し入力を、P5R向け入力とP6向け再引渡しに分ける。
4. 統合台帳にP5R-H0 / H1 / H2、Open Unknown、再開条件、証拠先を追加する。
5. doc/index.htmlにP5Rの正式HTML導線を追加する。

この提案書を作っただけでは、上の正式文書を更新しない。

---

## 9. Step 1 — この再構成案を作るために生成した超詳細プロンプト

次のプロンプトを、そのままの目的・範囲・判定基準で実行した。出力先はこのMarkdownである。

~~~text
あなたは、自動トレードシステムのPhase再構成を担当する主任アーキテクトです。

## 依頼

ユーザーは、Broker、Paper、Live、実資金、外部運用へ進む前に、
「UIから想定しているバックテスト機能がすべて本当に動く」
ローカルBacktest製品を最優先で完成させたいと考えています。

現行ロードマップではPhase 5の次がPhase 6です。
Phase 6の手前にPhase 5Rを新設するべきか、
またPhase 6のサブ機能をどこまでPhase 5Rへ移すべきかを、
根拠付きで提案してください。

特に、Phase 6で予定されている「複数のUnitを管理できるようにする」機能を
Phase 5Rに入れるかを、曖昧にせず決めてください。

## 最優先の判断原則

1. 「完璧」は、収益性、将来相場、Broker接続、Live安全性の保証ではない。
   承認された限定範囲で、UI操作、実計算、保存、異常時、テストがそろうこととして定義する。
2. UIの固定ダミー表示、設計済みAPI、固定fixtureの単体テストだけで「完成」と言ってはいけない。
3. Phase 5Rは、外部注文・外部接続なしのローカルBacktest製品を完成させるPhaseに限定する。
4. Portfolio、Account、実運用Risk、OMS、運用Unit、Forward、Shadow、Kill、Reconcileを
   安易にP5Rへ移してはいけない。必要なら「Backtest専用の最小部分」として切り出し、
   P6の本来の責務と混同しない。
5. UnknownをPassにしない。P5-H2をP5R開始承認へ読み替えない。
6. Provider、Secret、Broker、Paper、Live、実資金、Cloud、追加市場データ取得、外部I/Oを開始しない。
7. 文書作成はWindows側の作業ツリーだけで行い、既存のユーザー変更を混ぜない。

## 必ず読む一次資料

1. README.md
2. settings/language.md
3. settings/ai_component_rules.md
4. doc/index.html
5. doc/00_全Phase残課題Blocked統合台帳.html
6. doc/requirements/01_自動トレードシステム要件定義書_v2.html
   - REQ-V2-0044〜0055
   - Phase 6の目的、開始条件、完了条件
   - P7以降への依存
7. doc/phase4/05_完了/07_Phase4完了判定・Phase5計画引渡し.html
8. doc/phase5/06_完了/08_Phase5完了判定・Phase6計画引渡し.html
9. plan/phase5/Phase6計画入力一覧_2026-08-12.md
10. ui/mock/src/p4Contract.ts と ui/mock/src/App.tsx
11. src/autotrade/application/api.py
12. src/autotrade/application/worker.py
13. src/autotrade/application/core_adapter.py
14. src/autotrade/backtest/runner.py
15. tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/quality-report.json
16. tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/period-split.json
17. tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/cost-gap.json

## 実ランタイムの確認

ファイルを変更する前に、multi_agent_v1__spawn_agentとmulti_agent_v1__wait_agentの可用性を確認する。
利用可能なら次を実行する。

- AutoTradePhasePlanning_Orchestrator_v0_1を、定義JSONの固定modelでCoordinatorとして起動する。
- Coordinatorから次のAgentを定義JSONの固定modelで個別起動し、完了を待機する。
  - AutoTrade_A10_RequirementsCurator_v0_1
  - AutoTrade_A20_ArchitectureDomainArchitect_v0_1
  - AutoTrade_A30_StrategyQaArchitect_v0_1
  - AutoTrade_A90_DesignReviewer_v0_1
  - AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1
- それぞれに、書き込み禁止、根拠ファイル、Phase境界、Unknown、停止条件を調査させる。

Coordinatorまたは子Agentを起動できない場合は、RUNTIME_DISPATCH_FALLBACK_REQUIREDとして、
理由、未起動Agent、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録する。
未起動のAgentを独立レビュー済みと書いてはいけない。

## 必ず使うSkill

- autotrade_skill_phase_execution_planning_v0_1
- autotrade_skill_source_reader_v0_1
- autotrade_skill_architecture_writer_v0_1
- autotrade_skill_traceability_v0_1
- autotrade_skill_design_review_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1

新しい計画文書には、管理・差分・証跡・manifest・stale・retryのための管理用hashを導入しない。
安全・データ・再現性に直接関係する既存の保護対象は、目的と停止範囲を明記する場合だけ維持する。

## 実施手順

1. 現在のP4 / P5 / P6の事実を、設計と実装を分けて整理する。
   - UIモックで見えている機能
   - 実API契約に存在する機能
   - 実Coreと実P5データがつながっている機能
   - 未実装または固定値の機能
2. REQ-V2-0044〜0055を、単一Run、Sweep、結果、比較、CSV、Holdout / Walk-forwardに分ける。
3. 「薄いP5R」「P6全体を吸収」「P6からBacktest専用部分を切り出す」の3案を比較する。
4. 複数Unitについて、次を別物として定義する。
   - Backtest Experiment Set / Sweep: 独立した実験の束
   - 運用Unit: 共有Portfolio / Risk / Orderを持つ継続運用単位
5. P5Rへ入れるもの、P6に残すもの、P7以降に残すものを表にする。
6. UIから完成と判定できるE2E受入シナリオを、正常系だけでなく、
   入力不正、Data不良、取消、停止、checkpoint再開、部分失敗、CSV失敗、比較不能、
   Holdout再利用、対象外画面まで含めて作る。
7. P5Rの複数Step Runbookを作る。
   各Stepには、目的、入力、成果物、依存、並列可否、Human Gate、停止条件、
   対象外、指定Orchestrator / Agent / Skillの完全名、直接実行プロンプトを含める。
8. P5Rを採用した後にだけ更新する正式HTML、doc/index.html、統合台帳、P6入力を列挙する。
9. 新規Markdownを、パス、リンク、状態、Secret、要件追跡、管理用hash非導入の観点で静的確認する。

## 出力

次のMarkdownを作成する。

plan/Phase5R_バックテスト製品完全化_再構成提案・実行計画書_v0.1_2026-08-16.md

必須章:

- まず結論
- 中学生でも分かる用語説明
- 現在地の事実とP5Rが必要な理由
- 3案比較
- 「複数Unitを管理」の明確な判定
- P5R対象、P6残置、P7以降残置
- UIから完成と判定する受入シナリオ
- P5Rの詳細RunbookとStep別の直接実行プロンプト
- P5R-H0 / H1 / H2
- Unknown / Stop / 非目的
- 採用後の公式文書更新一覧
- REQ / UC / Screen / Test / Evidence / Gateの追跡表
- 実ランタイムの受領証跡または正直なFallback記録
- このプロンプトを実行したStep 2結果

文章は日本語で書く。
重要なリスクと停止条件には、中学生でも分かる短い説明を付ける。
結論を曖昧にしない。
~~~

---

## 10. Step 2 — 上のプロンプトを実行した結果

### 10.1 実施した調査

Step 1の指示どおり、P4 / P5 / P6の正式資料、実装、UIモック、P5品質証跡を読み、次を確認した。

1. REQ-V2-0044〜0055は、単一RunだけでなくSweep、履歴、比較、非同期CSV、Holdout / Walk-forwardを含む。
2. P4のUIは固定匿名ダミーであり、P4の完了は固定ローカルの設計・品質境界である。
3. Application APIはBacktestの契約を持つが、capabilityはSUPPORTED_DESIGNと表示している。
4. LocalWorkerは意図的なCore adapter / artifactが無いと実行を有効化しない。
5. BacktestCoreAdapterの現在の結果投影は、最大ドローダウン、勝率、総残高を実計算結果として完成させていない。
6. P5には限定市場データのQualityと期間分割があるが、Walk-forwardは戦略未実行である。
7. Phase 6は、複数運用Unit、Portfolio、Risk、OMS、Forward / Shadow、再起動・照合・Killのために定義されている。

### 10.2 実ランタイム受領記録

ルート実行では、Coordinatorを実際に起動した。

| 項目 | 事実 |
|---|---|
| runtime_backend | multi_agent_v1 |
| dispatch_mode | root → coordinator |
| Orchestrator名 | AutoTradePhasePlanning_Orchestrator_v0_1 |
| Orchestrator JSON | C:\project\strategy_test\.codex\orchestrators\AutoTradePhasePlanning_Orchestrator_v0_1.json |
| Orchestrator固定model | gpt-5.6-terra |
| coordinator agent_id | 01a00802-0485-76c0-a7f4-0f0cfedc2348 |
| Coordinatorの書き込み範囲 | 読み取り専用。作業ツリーの変更なし |
| Coordinatorの子Agent起動 | 子Agentの実行環境ではspawn / waitが利用できず、A10 / A20 / A30 / A90 / A95は未起動 |
| 子Agentの状態 | agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACK |

Coordinatorは、P5Rを入れること、P6全体を移さないこと、Backtest専用の実験束だけをP5Rへ切り出すことを推奨した。
ただし、指定された5 Agentの独立レビューは未実行である。したがって、この提案は「Coordinatorの読み取りレビューとルートの統合自己レビューを受けた提案」であり、「全指定Agentによる独立レビュー済み」とは表現しない。

### 10.3 Step 2の最終判断

| 質問 | 回答 |
|---|---|
| P5Rを入れるか | **入れる** |
| P5の直後に薄く挿入するだけでよいか | **よくない**。実データ→実Core→実5指標→UI、Sweep、結果分析、Walk-forwardまで入れる必要がある |
| P6全体をP5Rに入れるか | **入れない**。P6の安全機能まで混ぜると、Backtest完成が遅れ、責務が崩れる |
| 複数Unit管理をP5Rに入れるか | **本来の運用Unit管理は入れない**。Backtest Experiment Set / Sweepだけを入れる |
| P5R完了後にP6は何をするか | 複数運用Unit、Portfolio、Risk、OMS、Forward / Shadow、Kill、照合、復旧を固定Simulationで完成させる |

---

## 11. 要件追跡の骨格

| P5R項目 | 主な要件 | 主な画面 | 主な検証 | 後続への境界 |
|---|---|---|---|---|
| 入力・preflight | REQ-V2-0044 | SCREEN-05〜08 | 型、単位、期間、Data品質、未来参照、範囲外拒否 | P6の運用Riskは扱わない |
| 単一Run | REQ-V2-0045 | SCREEN-08、09、17、19 | 正常、取消、停止、失敗、再実行、再開 | Forward / ShadowはP6 |
| 5指標・詳細 | REQ-V2-0046 | SCREEN-10、11 | 独立オラクル、実結果、根拠リンク | 利益性の採用はしない |
| Sweep定義 | REQ-V2-0047 | SCREEN-08、09 | 上限、丸め、重複、無効行 | 運用Unitの同時管理はP6 |
| Sweep資源確認 | REQ-V2-0048 | SCREEN-08、09、02 | 件数、推定、明示確認、開始拒否 | 20〜40運用Unitの構造負荷はP6 / P8 |
| 全結果・回復 | REQ-V2-0049 / 0050 | SCREEN-09〜12、17、19 | 部分失敗、取消、checkpoint、再開 | OMSの復旧はP6 |
| 履歴・比較 | REQ-V2-0051 / 0052 | SCREEN-10、12、19 | 同条件再Run、差分、比較不能、自動採用禁止 | Candidate / Live採否はP9以降 |
| CSV | REQ-V2-0053 | SCREEN-10、12、19 | 非同期、進捗、取消、失敗、完了 | 大規模実機性能はP8 |
| Holdout / Walk-forward | REQ-V2-0054 / 0055 | SCREEN-08、10、12、18、19 | 窓別実Run、未来参照拒否、再利用制限 | 実時間ForwardはP6 |

---

## 12. Open Unknown、停止条件、残リスク

### 12.1 P5から引き継ぐUnknown

| ID / 事実 | P5Rでの状態 | 停止または制限 |
|---|---|---|
| EXTERNAL-DATA-PROVIDER-TERMS | OPEN_NOT_PASS | 追加取得、再配布、Provider変更、外部実行を始めない |
| P5-08-HOST-ISOLATION | NOT_VERIFIED | P5Rのローカル実行を過去の外部取得隔離証拠に読み替えない |
| P5-11-CHILD-DISPATCH | NOT_VERIFIED | P5当時の独立レビュー済みと表示しない。P5R自身で別の受領記録を取る |
| P5-EXECUTION-COST | NOT_MEASURED | 実測手数料・滑り・内部実行費と表示しない。仮定値は仮定値として表示する |

### 12.2 P5Rで新たに明確化すべきこと

| 項目 | 決める場所 | なぜ必要か |
|---|---|---|
| 固定PCでの受入負荷 | P5R-H0 | 「大量」と言うだけでは、どの件数・時間・容量で合格か決まらないため |
| ローカル保存方式と保持期間 | P5R-H0 / P5R-02 | 過去RunとCSVを安全に参照し、勝手に消えないようにするため |
| UIの実行形態 | P5R-02 | モックだけでなく、ローカルUIがどのApplication APIを呼ぶかを決めるため |
| 仮定値の入力形式 | P5R-02 | fee / slippageを実測と誤解しないようにするため |
| Walk-forwardの窓ルール | P5R-H0 / P5R-02 | 窓を結果を見た後で都合よく変えないため |

### 12.3 分かりやすい停止ルール

| 起きたこと | 何を止めるか | 中学生向けの説明 |
|---|---|---|
| Data品質が悪い、未来のデータが混じる | そのRunを開始しない | 未来の答えを見ながらテストを受けるとずるになるため |
| 5指標の根拠が作れない | Completedと表示しない | 答えだけあって計算途中が説明できないなら、正しいか分からないため |
| checkpointが合わない | 自動再開しない | 途中から再開して別の実験になってしまうのを防ぐため |
| Sweepの一部が失敗した | 全成功と表示しない | 100問中10問未採点なのに100点と言ってはいけないため |
| 比較条件が違う | 同じ順位表に並べない | テストの教科や問題数が違う点数を、そのまま比べるのは不公平だから |
| Holdoutを調整に使い回す | 自動採用を止め、要確認にする | 最後の答え合わせを何度も練習に使うと、本当の実力が分からなくなるため |
| P6対象をP5Rに混ぜる | P5Rの設計・実装を止める | 目的が「実験室完成」から「本番ロボット作り」へすり替わるため |
| 外部I/OやSecretが混じる | 該当Stepを止める | P5RはローカルBacktestだけを安全に完成させるPhaseだから |

---

## 13. 参照した主な根拠

| 根拠 | この提案への意味 |
|---|---|
| [要件定義書：単一Backtest〜Walk-forward](../doc/requirements/01_自動トレードシステム要件定義書_v2.html#19-単一設定backtest) | REQ-V2-0044〜0055がP5Rの要件範囲を示す |
| [要件定義書：Phase 6](../doc/requirements/01_自動トレードシステム要件定義書_v2.html#5-phase-6-複数運用単位-portfolio-risk-oms-forward-shadow) | 複数運用Unit、Portfolio、Risk、OMS、Forward / ShadowがP6の本来の責務であることを示す |
| [Phase 4完了判定](../doc/phase4/05_完了/07_Phase4完了判定・Phase5計画引渡し.html) | P4は固定ローカルの製品土台であり、実市場のBacktest完成ではない |
| [Phase 5完了判定](../doc/phase5/06_完了/08_Phase5完了判定・Phase6計画引渡し.html) | P5の限定データ範囲とOpen Unknownを示す |
| [P6計画入力](phase5/Phase6計画入力一覧_2026-08-12.md) | P5から渡すData契約、対象外、P6開始前の注意を示す |
| [統合台帳](../doc/00_全Phase残課題Blocked統合台帳.html) | P5の現在状態、Human Gate、Open Unknownの正本 |
| [UI契約](../ui/mock/src/p4Contract.ts) | Backtest画面が固定ダミー・P4範囲であることを示す |
| [UIモック本体](../ui/mock/src/App.tsx) | 結果、Chart、比較が固定表示例であることを示す |
| [Application capability](../src/autotrade/application/api.py) | BacktestがSUPPORTED_DESIGNと表示される現在地を示す |
| [Worker](../src/autotrade/application/worker.py) | Core adapter / artifact未設定時に実行を有効化しないことを示す |
| [Core adapter](../src/autotrade/application/core_adapter.py) | 5指標の実投影をP5Rで完成させる必要を示す |
| [BacktestRunner](../src/autotrade/backtest/runner.py) | P5Rで再利用する型付きCore契約を示す |
| [P5品質証跡](../tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/quality-report.json) | 使える限定データ範囲と、収益性・Live適合が未評価であることを示す |
| [P5期間分割証跡](../tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/period-split.json) | Walk-forwardが境界のみで、戦略未実行であることを示す |
| [P5費用・Gap証跡](../tests/evidence/phase5/RUN-P5-09-BINANCE-001/quality/cost-gap.json) | fee / slippage / 内部費用が未測定であることを示す |

---

## 14. 作成時の静的確認と次の一手

### 14.1 本提案の静的確認方針

この新規計画文書は、次を確認してから完了扱いにする。

1. 保存先が plan/ 配下である。
2. 参照リンクが既存のローカル資料を指している。
3. P5Rが提案段階であり、現行の正式ロードマップを変更したと偽らない。
4. Broker、Paper、Live、Secret、実資金、外部I/Oを実行対象として含めない。
5. REQ-V2-0044〜0055、P6境界、P5のOpen Unknownを明記する。
6. 管理・差分・証跡・manifest・stale・retryのための管理用hashを新規に導入しない。

### 14.2 作成時の確認結果

| 確認 | 結果 |
|---|---|
| AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1相当の静的ポリシー確認 | ALLOW。廃止済みの管理目的の照合経路は検出されなかった |
| Markdownのローカルリンク | 15件を確認し、欠落0件 |
| Secret候補 | 0件 |
| 形式 | Markdown見出し行69件（Step 1の埋め込みプロンプト内を含む）。最終ステージング後に `git diff --cached --check` を実行する |

### 14.3 採用する際の次の一手

ユーザーがこの再構成を採用する場合、次の一文でP5R-H0の準備へ進められる。

> Phase 5Rの追加と、この提案書の対象範囲を承認します。P5R-H0の正式計画書を作成してください。

その承認後に初めて、正式Phase計画、正式HTML、統合台帳、P6入力を更新する。
承認前は、この文書を提案として保持し、現行P6の正式範囲を変更しない。

---

## 15. 作成後の設計レビュー所見 — Findings first

| ID | 重要度 | 所見 | この提案での対応 | P5Rを完了扱いにする前の条件 |
|---|---|---|---|---|
| P5R-F-001 | High | 現在のUIモックの固定対象はMCLなどであり、P5の実データ対象BTCUSDT / ETHUSDTと一致しない | P5R-02でData Adapter・UI入力・表示用SchemaをP5の限定対象へ詳細設計し、P5R-05で固定Seedを実API表示へ置き換える | P5範囲外の固定例が実Backtest結果として残らない |
| P5R-F-002 | High | 現在のBacktestCoreAdapterは最大ドローダウン、勝率、総残高、期間を実結果として完全に投影していない | P5R-03で独立オラクルのGoldenを先に作り、P5R-04で5指標を実計算へ接続する | 実データの5指標と取引・残高の根拠が一致する |
| P5R-F-003 | High | 「大量Sweepでどこまでを受入にするか」のPC条件・候補件数・時間・容量が現在は未決定 | P5R-H0で固定PC・標準負荷・境界負荷・測定方法を承認対象にする | 未測定の性能を「完成」とは呼ばない |
| P5R-F-004 | Medium | Provider条件、host isolation、実行費がOpenのままである | P5Rを既存ローカルデータだけの範囲に限定し、追加取得・再配布・外部実行を禁止する | P5のOpen UnknownをPass化せず、P5R-H2にも残す |
| P5R-F-005 | Medium | 今回のCoordinatorの子Agentは実行環境上未起動で、指定Agentの独立レビューは未実施である | Step 2の受領記録に正直に残し、P5R正式計画では実ランタイム起動・待機またはFallbackをStepごとに記録する | 未起動Agentを独立レビュー済みと表現しない |

**レビュー結論:** P5Rの追加案そのものにCriticalな矛盾はない。
ただし、P5R-F-001〜003は「P5Rを実装して完成と言う」前に必ず閉じるHighであり、P5R-F-004〜005はOpenのまま正しく引き継ぐ必要がある。
