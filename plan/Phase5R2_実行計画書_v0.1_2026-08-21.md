# Phase 5R2 実行計画書

- 計画ID: `P5R2-PLAN-001`
- 版: `v0.1`
- 作成日: `2026-08-21`
- 状態: `REQUIREMENTS_HEARING_NOT_STARTED / P6_ON_HOLD_FOR_P5R2`
- 対象: P6開始前のBacktest製品是正。今回の計画作成では実装、外部Data接続、Secret投入、費用発生、既存Data・結果の削除を行わない。

## 1. 結論と開始条件

P5Rは `COMPLETE_WITH_OPEN_UNKNOWN` の履歴として残す。ただし、Single Backtestの利用者向け時間足が `1m` 固定になっており、利用者意図（`15m / 1h / 4h / 1d`）と一致しない。また、UIからのHistorical Data取得・在庫管理、およびRun一覧・結果画面での取消／削除は未完成である。これらをP6へ持ち込まず、P5R2として要件を聞き直し、要件基線を承認してから後続実装計画を再生成する。

`1m` は市場Dataの内部ソース間隔であり、利用者が戦略実行時間足として選ぶ候補ではない。現時点の初期案は、画面で選べる戦略時間足を `15m / 1h / 4h / 1d` に限定し、`1m` からの完成Bar集約を内部実装として保持することである。これはまだ確定要件ではない。旧要件の `M30` は矛盾として必ず回答を得る。

P6は `P5R2-H2` 完了とP6への改訂引渡しまで開始しない。P5R2の計画、ヒアリング、要件文書の候補作成だけは `P5R2-H0` 承認後に実施できる。外部Dataを実際にダウンロードする操作、Providerの認証、料金発生、実装、データ・結果の破壊的削除は別Human Gateを要する。

## 2. 現状事実・根因

| 事実ID | 確認済み事実 | 根因・影響 |
|---|---|---|
| `P5R2-FACT-TF-01` | `ui/mock/src/P5RBacktestScreen.tsx` は時間足を読み取り専用の `1m` と表示する。`ui/mock/src/backtestApi.ts` の `BacktestSpec.timeframe` も `'1m'` に限定する。 | UIと型の双方で候補が消えている。|
| `P5R2-FACT-TF-02` | `backtest_product.py` は `SPOT / 1m` 以外を事前検査で停止し、Strategy設定も `M1` だけを有効化する。 | 画面だけ選択式にしても、API・実行・由来・比較が一致しない。|
| `P5R2-FACT-TF-03` | `backtest/runner.py` には `M1` から `M15/M30/H1/H4/D1` を集約し、完成していない窓を `PARTIAL_BAR_REJECTED` とする仕組みがある。 | P5RはP5の限定Data範囲を、利用者向け時間足へ誤って流用した可能性が高い。M30の扱い、時刻境界、欠損時の停止を確定する必要がある。|
| `P5R2-FACT-HD-01` | P5Rの画面と手順書は既存のローカルread-only Dataのみを前提とし、外部Dataを取得する画面ではないと明記する。 | 新機能はData Catalog、取得Job、品質判定、Provider境界を新規に要件化する必要がある。|
| `P5R2-FACT-RUN-01` | APIには実行中Runの `cancel` があるが、履歴表は「結果を開く」のみで、履歴からの取消・削除API／UIがない。 | 実行一覧・進捗・結果サマリーの操作可能状態を状態遷移とともに定義し直す必要がある。|
| `P5R2-FACT-MAN-01` | `doc/phase5R/07_運用手順/01_バックテスト手順書.html` は `P5R-MAN-01 v0.5`。`1m` 固定、既存Dataのみ、取得不可の説明であり、P5R2後の画面と矛盾する。 | 実装・UI受入と同じ基線で手順書、スクリーンショット、用語集、リンク、初心者向け異常時説明を更新・検証する。|

## 3. P5R2の要件ID・Unknown・Human Gate

### 3.1 追加要件ID案

| ID群 | 対象 | 最低受入の方向 |
|---|---|---|
| `REQ-V4-P5R2-TF-01..08` | 時間足 | `M15/H1/H4/D1` だけを利用者が選択可能にし、`M1` を内部ソースとして明示する。集約、UTC境界、完成Bar、欠損、Run同一性、Sweep、履歴・比較を追跡する。|
| `REQ-V4-P5R2-HD-01..14` | Historical Data | Provider・対象・認可・費用・取得Job・進捗・取消・再試行・品質・Catalog・重複・更新・削除・provenance・依存Runを定義する。|
| `REQ-V4-P5R2-RUN-01..10` | Run取消／削除 | `QUEUED/RUNNING/terminal/RECOVERY_REQUIRED` ごとの操作可否、確認、soft/hard delete、監査、結果・CSV・checkpoint・比較・Evidenceへの影響を定義する。|
| `REQ-V4-P5R2-MAN-01..06` | 手順書 | 機能一覧、時間足選択、Data取得・一覧、取消／削除、失敗時対応、禁止事項、実画面画像・アクセシビリティ・リンクを受入にする。|

### 3.2 初期Unknown

| ID | 未確定事項 | 解消しない場合の扱い |
|---|---|---|
| `P5R2-UNK-TF-01` | 旧 `M30` を完全廃止するか、互換閲覧のみ残すか。 | 利用者選択候補へ含めず、要求者回答まで実装設計を停止する。|
| `P5R2-UNK-TF-02` | 1 Runあたりの戦略時間足、UTC日次境界、開始・終了時刻の丸め、欠損／途中足の拒否・表示方針。 | 結果再現性を保証できないため実装を停止する。|
| `P5R2-UNK-HD-01` | 初回Provider・市場・銘柄・期間・利用規約・保持／再配布可否・認証・料金。 | 画面設計は可能でも実ダウンロードを禁止する。|
| `P5R2-UNK-HD-02` | データ削除の保持期間、依存Runがある場合の扱い、利用者ロール。 | 破壊的削除を実装・有効化しない。|
| `P5R2-UNK-RUN-01` | terminal Runの削除範囲（結果、CSV、checkpoint、比較参照、Evidence、監査記録）と復元可能性。 | hard deleteを禁止し、要件確定まで操作を追加しない。|
| `P5R2-UNK-MAN-01` | 手順書の改訂版切替時点、対象読者、必要な画像・動画・印刷版。 | 旧手順書を現行として保持し、未実装機能を操作可能とは記載しない。|

### 3.3 Human Gate

| Gate | 承認対象 | 承認前に禁止すること | 次の成果物 |
|---|---|---|---|
| `P5R2-H0` | P5R2の範囲、ヒアリング開始、P6保留、要件候補作成。 | 実装、外部接続、Secret、費用、削除。 | ヒアリング記録・要件候補。|
| `P5R2-HREQ` | 時間足・Provider境界・Data/Run削除意味・手順書改訂要件を含む要件基線。 | 後続実装計画の確定、実装、外部Data取得。 | v0.2の後続実行計画。|
| `P5R2-HDATA` | 実ダウンロードのProvider、対象、規約、認証、費用上限、通信境界、保存先。 | 実Provider接続、Secret投入、料金が発生する操作。 | 取得実装／実行用の限定Gate。|
| `P5R2-HDEL` | Data/Run削除の対象、保持、復元、監査、依存関係の扱い。 | hard delete、依存結果・Evidence消去。 | 削除機能の実装／有効化。|
| `P5R2-H1` | 詳細設計、REDテスト、品質Gate対象、UI/API/Data操作の安全境界。 | GREEN化・完了宣言。 | 実装・統合試験。|
| `P5R2-H2` | 全受入、手順書、Open Unknown、P6への改訂引渡し。 | P6実装・実行、Paper/Live。 | P6-H0計画の更新。|

## 4. ヒアリング質問バンク

各回答は、回答値、承認者、日時、根拠、影響する要件ID、影響する後続成果物を表で保存する。未回答を推測で埋めない。

| 質問ID | 質問・選択肢 | 推奨初期案 | 回答が変える成果物 |
|---|---|---|---|
| `Q-TF-01` | 利用者選択候補を `15m/1h/4h/1d` の4つに確定するか。`1m` は内部ソース表示のみとするか。 | はい。 | UI/API型、Preflight、実行契約、結果由来、手順書。|
| `Q-TF-02` | 旧 `M30` は (a)完全廃止、(b)既存履歴の表示のみ、(c)候補として残す、のどれか。 | (b)。 | 互換変換、既存Run、メニュー、テスト、要件v4。|
| `Q-TF-03` | Single Runは戦略時間足を1つ選ぶか、複数時間足を同時に使う戦略を含めるか。 | 1 Run = 1戦略時間足。 | Strategy Plugin契約、UI、Run同一性、比較。|
| `Q-TF-04` | 時刻境界はUTC固定、日足はUTC 00:00開始、途中足・欠損は停止して理由表示でよいか。 | はい。 | 集約器、Preflight、品質、手順書、Golden test。|
| `Q-HD-01` | 初回Providerと対象市場・銘柄は何か。既存Binance Spot BTCUSDT/ETHUSDTに限定するか。 | 既存範囲から開始。 | 公式調査、Provider Adapter、Catalog、Data Gate、画面文言。|
| `Q-HD-02` | 取得は公開・認証なしだけを許すか、API keyを使うProviderも対象にするか。 | 公開・認証なしを初期範囲。 | Secret境界、設定、監査、HData。|
| `Q-HD-03` | 利用者が選べる期間、上限、見積り／確認、同時Job数、取消・再試行・再開の要件は何か。 | 上限・見積り・明示確認・1 Job・取消と安全な再試行。 | Job状態機械、UI、API、負荷試験。|
| `Q-HD-04` | Catalogに表示する項目（Provider、対象、source間隔、派生時間足、期間、行数、容量、品質、更新時刻、由来、依存Run）と、更新／重複／削除の規則は何か。 | 全項目を表示、重複は新規作成せず差分更新を提案。 | Data model、一覧UI、削除設計、手順書。|
| `Q-RUN-01` | 取消を許す状態は `QUEUED/RUNNING` のみでよいか。完了・失敗・取消済みは削除候補にするか。 | 取消は非terminalのみ。 | API状態遷移、ボタン有効化、E2E。|
| `Q-RUN-02` | 削除は (a)利用者から隠すsoft delete、(b)復元可能なゴミ箱、(c)即時hard delete、のどれか。 | (b)を検討し、期限後hard deleteは別承認。 | 永続化、監査、復元UI、HDEL。|
| `Q-RUN-03` | 削除時に結果・CSV・checkpoint・比較参照・Data provenance・Evidenceをどう残すか。依存Runは削除不可とするか。 | Runの監査最小記録とEvidenceを保持、依存関係は削除を停止。 | Catalog整合、ストレージ、復旧、手順書。|
| `Q-MAN-01` | 手順書は既存HTMLを改訂するか、新版を作り旧版を履歴化するか。 | 新版を作り旧版を履歴化。 | doc/index、リンク、スクリーンショット、完了判定。|

## 5. 成果物・DAG

```text
P5R2-00 (H0) → P5R2-01 現状・追跡 → P5R2-02 第1回ヒアリング
                                      → P5R2-03 第2回／矛盾解消
                                      → P5R2-04 要件候補・手順書差分
                                      → P5R2-05 独立レビュー／A95
                                      → P5R2-06 要件改訂・HREQ承認
                                      → P5R2-07 後続計画の再生成（ここで初めて全実装StepのPromptを追加）
                                      → P5R2-H1 → 実装 … → P5R2-H2 → P6改訂引渡し
```

今回作る／更新するものは、計画書、P5R2の未承認Gateを登録する統合台帳、`doc/index.html` の計画導線である。`P5R2-04` 以降の実行で、要件定義書v4候補、`doc/phase5R2/` の正式HTML、手順書改訂版、実装設計、テスト・Evidenceを作る。計画作成段階ではそれらを作成・改変しない。

## 6. 各Stepの直接実行プロンプト

以下の各Promptは単独で貼り付けて実行できる。共通して、`AutoTradePhasePlanning_Orchestrator_v0_1` を coordinator とし、A05/A10/A80/A90/A95を定義JSONのmodel（A80/A95は `reasoning_effort=low`）で個別実起動・全件waitする。起動不能なら `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、未起動Agent、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK` を記録し、独立レビュー済みとは表示しない。管理hash、checksum、fingerprint、stale、hash retry、manifest整合を完了条件にしない。直接の安全／再現性で必要なDataの保護対象hashだけは、目的と不一致時の停止範囲を記す。各Stepで外部接続、Secret、料金発生、削除、実装を行わない。

### P5R2-00 — H0判定と着手境界

```text
あなたはP5R2-00のルート担当です。P5R2の実装を始めず、P5R2-H0の承認資料を作成してください。
目的: P6を保留し、Single Backtest時間足、Historical Data取得・管理、Run取消／削除、01_バックテスト手順書改訂をP5R2の要件ヒアリング対象として確定する。
必読: README.md, settings/language.md, settings/ai_component_rules.md, plan/Phase5R2_実行計画書_v0.1_2026-08-21.md, 統合台帳, P5R完了判定。
実施: (1)既存P5Rの完了事実と今回の是正範囲を分ける、(2)P5R2-H0の承認対象・禁止事項・再開条件・証拠先を作る、(3)統合台帳に未承認Gateを登録する案を作る、(4)P6開始禁止を明記する。
禁止: 実装、外部通信、Provider接続、Secret、費用、Data/Run削除、P5R完了状態の改ざん。
受入: 承認者が「ヒアリングは許可するが実装・外部I/O・削除は許可していない」と一読で分かる。A95静的判定、path/schema/link/Secret/state/要件追跡の非hash確認を添える。
出力: H0判定案、更新対象、Unknown、dispatch receipt、Findings first。ファイル編集はH0承認後のルート担当だけが行う。
```

### P5R2-01 — 現状監査・要件追跡

```text
あなたはP5R2-01のルート担当です。実装をせず、時間足・Historical Data・取消/削除・手順書の現状を証拠付きで監査してください。
必読: P5R計画、P5R完了判定、要件v2/v3、統合台帳、doc/index.html、01_バックテスト手順書、P5RBacktestScreen.tsx、backtestApi.ts、backtest_product.py、runner.py。
実施: (1)UI型/API/実行器/保存/手順書を機能単位で対応表にする、(2)1m固定の根因とM15/H1/H4/D1集約の既存能力を分離する、(3)取消と削除を状態・画面・API・保存物別に棚卸しする、(4)Data取得とCatalogの既存・欠落を棚卸しする、(5)REQ→UC→画面/API/Data object→Test→Evidence→Gateの追跡表を作る。
禁止: コード変更、外部Data接続、既存のhash/manifest運用復活、未確認の仕様を事実として書く。
受入: 各主張にpathと行・節の根拠があり、P5Rの完了成果とP5R2の欠落が混ざらない。中学生向けの短い危険説明を各Critical/Highへ添える。
出力: 現状事実表、根因、影響範囲、要件ID草案、Unknown、ヒアリング入力、dispatch receipt、A95判定。
```

### P5R2-02 — 第1回ヒアリング

```text
あなたはP5R2-02の要件聞き取り担当です。前Stepの事実表を入力に、利用者へ回答しやすい第1回ヒアリングを実施・記録してください。実装しません。
必須質問: Q-TF-01..04、Q-HD-01..04、Q-RUN-01..03、Q-MAN-01。各質問に選択肢、推奨初期案、選択した場合に変わる要件・画面・API・テスト・手順書・Gateを添える。
実施: (1)確定回答、保留回答、前提、根拠を分離、(2)M30と1mの役割を必ず確認、(3)Provider/規約/認証/費用/通信は未承認のまま記録、(4)削除を取消と混同しない、(5)手順書の版切替と画像更新方針を確認する。
禁止: 回答の推測、外部接続、秘密情報の要求・保存、削除・実装。
受入: 未回答には影響と停止条件があり、回答だけで次の設計が変わる箇所を追跡できる。
出力: 質問票、回答台帳、保留事項、矛盾候補、次回質問、dispatch receipt、Findings first。
```

### P5R2-03 — 第2回ヒアリング・矛盾解消

```text
あなたはP5R2-03の要件整合担当です。第1回回答と現状監査を入力に、矛盾・安全境界・受入条件を解消する第2回ヒアリングを実施してください。実装しません。
必須確認: 時間足ごとのUTC境界・部分足・欠損・比較同一性、download Job状態と取消/再試行、Catalogのusable判定と重複更新、Data/Run削除のsoft/hard/復元/依存/Evidence保持、手順書の操作順と異常時説明。
実施: (1)回答が矛盾したら具体例で再質問、(2)各状態遷移に許可・拒否・理由・利用者表示を定義、(3)外部I/Oと削除をHData/HDelへ切り分け、(4)受入シナリオと否定ケースを草案化する。
禁止: 未承認事項の既定化、料金・認証・削除の実行、P6開始。
受入: 実装判断を左右するUnknownが列挙され、残るものはHREQの前に回答が必要か、後続Gateでよいかが明示される。
出力: 矛盾解消表、状態遷移表、受入候補、Unknown判定、dispatch receipt、A95判定。
```

### P5R2-04 — 要件候補・手順書差分設計

```text
あなたはP5R2-04の要件編集担当です。承認済み回答だけを使い、要件定義書v4候補とP5R2要件追跡、01_バックテスト手順書の改訂仕様を作成してください。まだ正式版の公開・実装はしません。
必須内容: REQ-V4-P5R2-TF/HD/RUN/MAN、利用者時間足と内部1mの区別、M30の処置、Data Catalog/Job/品質/由来、Run取消/削除状態機械、Gate、Unknown、UI/API/Data/Test/Evidence追跡、P6への影響。
手順書差分: 機能一覧、画面地図、時間足選択、Data取得前確認・取得中・取消/再試行・一覧、Run一覧/結果での取消・削除確認、復元/依存時の停止、禁止事項、用語、全リンク、desktop/mobile画像撮影リスト、アクセシビリティと初心者向け説明。
禁止: 未承認のProvider仕様を断定、旧手順書を先に現行扱いへ切替、実装・外部I/O・削除。
受入: 文書変更の前後差、各要件の受入/否定テスト、手順書の画面対応が追跡可能。A95は管理hashを作らない。
出力: 要件候補差分、追跡表、手順書改訂仕様、更新対象一覧、dispatch receipt、Findings first。
```

### P5R2-05 — 独立レビュー・A95静的判定

```text
あなたはP5R2-05のレビュー担当です。P5R2-04の候補をFindings firstでレビューし、修正案を返してください。実装・文書公開・外部I/O・削除は行いません。
レビュー軸: (1)1m内部ソースと利用者時間足の混同、(2)M30旧要件の残留、(3)途中足/欠損/時刻境界/未来参照、(4)Provider/認証/費用/規約/通信、(5)取得・取消・再試行の競合、(6)Data/Run削除によるEvidence・依存破壊、(7)状態表示・確認UI・アクセシビリティ、(8)手順書と実画面の乖離、(9)P6境界、(10)管理hash再導入。
各FindingにSeverity、根拠、利用者向けやさしい説明、修正案、再確認条件を付ける。Critical/HighはHREQへ進めない。
A95判定: 管理hash/checksum/fingerprint/stale/hash retry/manifest整合を完了条件にした案はBLOCKED。直接のData同一性保護は目的・対象・不一致時停止範囲がある場合のみALLOW。用途不明はNEEDS_HUMAN_GATE。
出力: Findings first、採否表、再レビュー条件、A95判定、dispatch receipt。
```

### P5R2-06 — 要件改訂・HREQ承認

```text
あなたはP5R2-06の統合担当です。HREQ前の最終要件パケットを作成してください。未解消Critical/Highがあれば止め、要件を勝手に確定しません。
入力: ヒアリング全記録、要件候補、レビュー採否、A95判定、統合台帳。
実施: (1)採用済み修正のみを要件定義書v4候補とP5R2正式追跡へ統合、(2)旧v3/P5Rを履歴としてリンク、(3)P5R2-HREQの承認対象・未承認事項・再開条件を明記、(4)統合台帳のP5R2-H0/HREQ/HData/HDel/H1/H2と最新状態を整合、(5)手順書改訂をP5R2の必須受入に固定、(6)HREQ承認後にのみP5R2-07を起動できるようにする。
禁止: HREQを代理承認、実装・Provider接続・Secret・費用・削除、P6開始。
受入: 要件ID、受入条件、否定ケース、Gate、Unknown、手順書受入、P6保留が矛盾なく読める。path/schema/link/Secret/state/要件追跡を非hash確認し、A95結果を添える。
出力: HREQ承認依頼、承認用差分、残Unknown、採否表、dispatch receipt、review_mode。
```

### P5R2-07 — HREQ後の後続計画再生成メタプロンプト

```text
あなたはP5R2-07の計画改訂担当です。P5R2-HREQで人間が承認した要件基線だけを入力に、P5R2実行計画をv0.2として新規作成し、P5R2-H2およびP6改訂引渡しまでの未実施Stepすべてに、単独で実行できる詳細Promptを追加してください。このStep自体では実装しません。

必読: HREQ承認記録、要件定義書v4、P5R2 v0.1、要件追跡、Unknown/Blocked統合台帳、既存P5R設計・手順書、対象コード、P5R2-05レビュー/A95判定。未承認回答・推測・旧P5Rの1m固定を入力に混ぜない。

生成要件:
1. 完了済みP5R2-00..06を履歴として保持し、未実施部分だけをv0.2へ追加する。各StepにID、目的、依存、入力、出力、対象path、担当Orchestrator/Agent/Skill、Human Gate、禁止事項、受入、テスト、Evidence、直接実行Promptを置く。
2. 少なくとも、詳細設計、詳細設計レビュー、REDテスト、品質Gate scope登録、API/Domain/Storage実装、実Application API接続UI、UIアクセシビリティ/視覚検証、Data Provider公式一次情報調査、HData前後の実ダウンロード、Run/Data削除の安全実装、マイグレーション/互換、統合/E2E、手順書改訂・実画面撮影、独立コード/セキュリティレビュー、H2完了判定、P6計画入力更新を順序づける。
3. 時間足はM15/H1/H4/D1、1m内部ソース、M30の承認済み処置、UTC境界、欠損・途中足・未来参照、Run同一性・比較・Sweepを全Stepへ反映する。
4. Historical DataはProvider/利用規約/認証/費用/通信をHDataの前に停止させる。Data Catalog、download job、進捗、取消、再試行、品質、重複/更新、provenance、依存Run、容量/保持を設計・受入に含める。外部通信の実行PromptはHData承認記録と固定対象範囲がなければSTOPする。
5. 取消／削除は状態機械、確認UI、soft/hard delete、復元、監査、checkpoint/CSV/比較/Evidence/Data依存、path traversal防止を含める。HDel承認なしに破壊的削除を実行しない。
6. `doc/phase5R/07_運用手順/01_バックテスト手順書.html` の改訂を独立Stepにする。機能一覧、操作リンク、初心者向け説明、失敗時対応、用語、画面画像、desktop/mobile、Playwright、axe、リンク検査、旧版履歴・新版本導線を受入にする。未実装画面を手順書で可能と書かない。
7. 実Application API UIには AutoTradeProject_ImplementationQuality_Orchestrator_v0_1、AutoTrade_A172_WebProductUiEngineer_v0_1、autotrade_skill_web_product_ui_implementation_v0_1 を指定する。固定ダミーUIの責務と混ぜない。Python実装は python implementation/test/debug/code review Skill群を明示する。詳細設計は ImplementationDesign Orchestrator/A82/A91を用いる。
8. 各Promptに、定義JSON固定model、全指定Agent個別起動・wait、receipt、起動不能時の `RUNTIME_DISPATCH_FALLBACK_REQUIRED` / `agent_id=N/A` / `independent=false` / `SELF_REVIEW_FALLBACK` を明記する。管理hash/checksum/fingerprint/stale/hash retry/manifest整合を完了条件にしない。保護対象Dataの同一性確認だけは目的と不一致時の停止範囲を明記する。
9. H1、HData、HDel、H2の承認資料・禁止事項・再開条件・統合台帳更新を各Gate直前Stepへ置く。P6はP5R2-H2後にのみ計画入力を更新し、実装開始は別P6-H0とする。

出力: `plan/Phase5R2_実行計画書_v0.2_<date>.md`、差分要約、DAG、全未実施StepのPrompt、Gate/Unknown台帳更新案、受入マトリクス、A95静的判定、runtime receipt。Critical/Highまたは未承認Gateがあれば、該当StepをBLOCKEDとして停止する。
```

## 7. 01_バックテスト手順書の受入条件

`REQ-V4-P5R2-MAN-*` の正式化時には、少なくとも以下を満たす。

1. `1m` が内部ソースDataであり、利用者向け戦略時間足ではないことを、画面表示・手順・用語で同じ意味にする。
2. `15m/1h/4h/1d` の選択、選択できない条件、UTC境界、途中足・欠損時の停止理由を操作順とともに説明する。
3. Historical Dataの取得前確認、対象選択、進捗、取消、再試行、品質完了、Catalog一覧、更新・重複・削除制限、依存Runを説明する。HData未承認時は「取得できない」と明記する。
4. 実行一覧・進捗・結果サマリーからの取消／削除について、状態別の可否、確認画面、復元・監査・依存時の拒否を説明する。HDel未承認なら破壊的削除を案内しない。
5. 機能一覧、目次、各操作リンク、失敗時対応、用語、禁止事項、P6以降との境界、旧版／新版導線を更新する。
6. 実Application APIを通るdesktop/mobileの画面で、Playwright操作・スクリーンショット、axe、リンク、HTML静的確認を行い、画像と文章の画面状態を一致させる。

## 8. Findings first とA95静的判定

### Critical / High候補

1. `HIGH-TF-01`: 画面の候補だけを増やし、API・実行・由来・比較を1m固定のままにすると、表示と結果が別の条件になる。**やさしい説明:** 15分を選んだつもりで1分の計算が走ると、結果を信じられない。APIから結果の記録まで同じ時間足で確認する。
2. `HIGH-HD-01`: UIダウンロードをProvider規約・認証・費用・通信承認なしに有効化すると、許可されていない通信や料金・保持違反を起こし得る。**やさしい説明:** ダウンロードボタンは、知らないうちに外へ通信する入口になる。先に「どこから何を、いくらで取るか」を承認する。
3. `HIGH-DEL-01`: 結果やDataを削除してEvidence・比較・依存Runまで消すと、後から結果の根拠を確認できない。**やさしい説明:** 成績表だけ消しても、元の問題や答案まで消えると確かめ直せない。まず復元可能な削除と依存確認を決める。
4. `HIGH-MAN-01`: 画面実装より先に手順書を更新すると、利用者に存在しない操作を案内する。**やさしい説明:** 説明書どおりに押してもボタンがなければ迷う。実画面で確認してから公開する。

### A95判定

`ALLOW_WITH_BOUNDARY`。本計画は管理hash、checksum、fingerprint、stale、hash retry、manifest整合を計画・完了条件にしない。Data取得後のraw/normalized/derived Dataの同一性保護は、利用者に見せるDataの由来・品質・Run再現性を守る直接目的に限る。不一致時は当該Dataを `usable` にせず、依存Backtest開始を停止する。用途不明なhash追加は `NEEDS_HUMAN_GATE`、管理用hash復活は `BLOCKED` とする。

## 9. ランタイム受領証跡（計画作成時）

この実行環境では `multi_agent_v1__spawn_agent` / `multi_agent_v1__wait_agent` が公開されず、指定Agentの実起動はできなかった。従って `RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`coordinator_agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK` と記録する。これは独立Agentレビューを実施済みという意味ではない。

| 役割 | agent_id | model | reasoning_effort | 割当 | 起動／wait結果 |
|---|---|---|---|---|---|
| coordinator: `AutoTradePhasePlanning_Orchestrator_v0_1` | `N/A` | `gpt-5.6-terra` | 定義JSONどおり | 全体統合・receipt | 未起動／wait不可 |
| `AutoTrade_A05_PhaseExecutionPlanner_v0_1` | `N/A` | `gpt-5.6-luna` | 定義JSONどおり | Step/DAG/Gate/直接Prompt | 未起動／wait不可 |
| `AutoTrade_A10_RequirementsCurator_v0_1` | `N/A` | `gpt-5.6-luna` | 定義JSONどおり | ヒアリング・要件ID・矛盾解消 | 未起動／wait不可 |
| `AutoTrade_A80_DocumentIntegrator_v0_1` | `N/A` | `gpt-5.6-luna` | `low` | 成果物・導線・手順書・台帳 | 未起動／wait不可 |
| `AutoTrade_A90_DesignReviewer_v0_1` | `N/A` | `gpt-5.6-luna` | 定義JSONどおり | Findings first・安全レビュー | 未起動／wait不可 |
| `AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1` | `N/A` | `gpt-5.6-luna` | `low` | 管理hash再導入の静的判定 | 未起動／wait不可 |

未起動Agentの各責務はルート担当が分離して自己レビューした。後続Stepではランタイムが利用可能なら、各Promptの契約どおり個別起動・全件wait・receiptを必須とする。
