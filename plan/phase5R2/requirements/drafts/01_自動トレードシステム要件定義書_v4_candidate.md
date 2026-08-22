# 自動トレードシステム要件定義書 v4 candidate — P5R2

- 文書ID: `RQV4-CANDIDATE-P5R2-001`
- 版: `v4-candidate.0.1`
- 作成日: `2026-08-22`
- 状態: `CANDIDATE / NOT_CURRENT / P5R2-HREQ_UNAPPROVED`
- 正式化条件: `P5R2-HREQ` の明示承認後に P5R2-06A で公開する。v3 は上書きも無効化もしない。

## 1. この候補の位置付け

この文書は、P5R の旧完了範囲を履歴として残したまま、P5R2 で追加・是正する Backtest 製品要件の候補である。P5R2-HREQ 未承認のため、現在の正本は引き続き `doc/requirements/01_自動トレードシステム要件定義書_v3.html` である。

P5R2 は P5R と P6 の間に置く。P6、Broker、Paper、Live、実注文、実資金は P5R2 の対象外であり、P5R2-H2 まで開始しない。

## 2. 継承と変更理由

| 旧ID・成果物 | v4 candidate での扱い | 変更理由 |
|---|---|---|
| `REQ-V2-0027` | 戦略時間足は P5R2-REQ-TF-001 で具体化 | 利用者が 15m / 30m / 1h / 4h / 1d を選べることを明示する。 |
| `REQ-V2-0028` | P5R2-REQ-TF-004〜006 で具体化 | UTC anchor、closed bar、期間終端の切下げ、限定補間を明示する。 |
| `REQ-V2-0035` | P5R2-REQ-TF-001〜003 で具体化 | Single Backtest の時間足選択と 1m source を混同しない。 |
| `REQ-V3-0113` | P5R2-REQ-ROADMAP-001 により補足 | P5R 完了の履歴を保持し、P5R2 を P6 前の必須是正 Phase とする。 |
| `REQ-V3-0114` | P5R2-REQ-HD-001〜006、RUN-001〜004 により補足 | 実Applicationの既存Backtest機能を、Data管理と安全な画面操作へ広げる。 |
| `REQ-V3-0117` / P5R-AC | P5R2-REQ-RUN-001〜004 により補足 | 保存済みRunを壊さず、取消・表示非表示・監査を分離する。 |
| P5Rの完了HTML・Manual v0.5 | `HISTORY / NOT_INVALIDATED` | 当時の限定Scopeの完了事実とEvidenceは保持する。P5R2承認前に手順書本文を変更しない。 |

## 3. P5R2 candidate Requirement

### 3.1 ロードマップと時間足

| ID | Shall | 受入候補 |
|---|---|---|
| `P5R2-REQ-ROADMAP-001` | システムは P5R の旧完了を履歴として保持し、P5R2 を P5R と P6 の間の要件是正 Phase として扱わなければならない。P6 は P5R2-H2 まで停止する。 | v3との差分、P5R旧完了、P5R2現在状態、P6停止条件がindex・台帳・P5R2成果物で一致する。 |
| `P5R2-REQ-TF-001` | Single Backtest は戦略時間足として `15m / 30m / 1h / 4h / 1d` のいずれか一つだけを選べなければならない。`1m`を戦略時間足として選ばせてはならない。 | 5種類だけが選択可能で、1 Runに選択時間足が一つ固定される。 |
| `P5R2-REQ-TF-002` | Historical source は `1m` とし、上位足はローカルで生成する。1m source と derived Data を同じ論理Dataとして混在させてはならない。 | CatalogとRun入力でsource/derivedの区別を確認できる。 |
| `P5R2-REQ-TF-003` | 既存の1m/M30保存Data・Run・結果は閲覧専用のlegacyとして表示し、新規30m選択、再実行、自動移行、実削除と混同してはならない。 | legacy属性と新規選択対象を別表示し、legacyを新規Run入力へ自動使用しない。 |
| `P5R2-REQ-TF-004` | 上位足はUTC 00:00 anchorで生成し、終了時刻が境界でない場合は直前の確定足まで切り下げる。指定終了と有効終了を利用者に表示し、partial barをRunへ渡してはならない。 | 指定終了、有効終了、UTC、閉じた足だけをRun入力として確認できる。 |
| `P5R2-REQ-TF-005` | 内部の連続1分欠損だけは未来値を使わない方式で補間し、警告とprovenanceを付けて `USABLE_WITH_WARNING` 候補にできる。始端・終端欠損、上限超過、時系列逆転は使用禁止とする。 | 警告と使用禁止を区別し、欠損条件・補間方式・provenanceを確認できる。 |
| `P5R2-REQ-TF-006` | Backtestの必要期間・時間足が不足する場合、開始を止め、理由と「生成する」確認を表示しなければならない。承諾時は当該銘柄の時間足生成画面へ遷移する。 | 不足時にRunが開始されず、銘柄を引き継いだ生成画面へ遷移できる。 |

### 3.2 Historical Data Download Job と DataSet Catalog

外部の1m Historical Dataを取得する `HistoricalDownloadJob` と、取得済み1m sourceから15m／30m／1h／4h／1dをローカル生成する `TimeframeGenerationJob` は、同じJob基盤を再利用する場合でも `job_type`、ID、状態、入力、出力を分けて管理する。前者はProvider境界と`P5R2-DATA-G1`、後者はlocal生成・品質検査・銘柄／期間引継ぎの境界に属する。どちらのJobも、完了しただけではDataSetを使用可能へ昇格させない。

| ID | Shall | 受入候補 |
|---|---|---|
| `P5R2-REQ-HD-001` | UIは、Binance Data Visionを候補Providerとする`HistoricalDownloadJob`の取得要求を作成できなければならない。ただし実host、利用条件、symbol、期間、通信、Secret、費用、実downloadは `P5R2-DATA-G1` 承認後だけに許可する。Binanceは候補Providerであり、HREQ承認や公式文書のread-only閲覧だけで採用・契約・通信許可が確定したとは扱わない。 | Gate前には実通信が起きず、取得要求の候補UI/API/監査要件だけが存在する。 |
| `P5R2-REQ-HD-002` | Download Job と DataSet を別ID・別状態で管理しなければならない。`PARTIAL / FAILED / CANCELLED` Jobをusable DataSetへ自動昇格してはならない。 | Job状態とDataSet usable状態が別表示で、失敗JobからRunを開始できない。 |
| `P5R2-REQ-HD-003` | UIは銘柄別に生成済みの時間足・期間・品質・usable状態・legacy属性を一覧表示し、銘柄、複数の生成対象時間足、期間を選べなければならない。既定期間は現在生成可能な全期間とする。 | 一覧と生成画面で選択値、既定期間、状態、期間カバレッジを確認できる。 |
| `P5R2-REQ-HD-004` | 同一論理Dataは Provider、market、symbol、Data時間足、正規化スキーマが全て同じ場合だけとする。Provider・marketが異なるData、1m sourceとderived Dataを自動混在・自動マージしてはならない。 | identity属性が全て保存・比較され、異なるidentityのマージを拒否する。 |
| `P5R2-REQ-HD-005` | 同一論理Dataの非重複期間を追加した結果は新しい不変DataSet versionとして保存し、旧versionを保持しなければならない。Runは選択したDataSet ID/versionを固定参照する。 | Catalogでcoverage・version・provenanceを確認でき、過去Runの参照先が変わらない。 |
| `P5R2-REQ-HD-006` | 同一timestampの完全一致バーは一つにdedupeし、両方の取得Jobをprovenanceに残す。値が異なる場合は自動上書き・自動マージをせず、競合解決まで新versionを `UNUSABLE` または保留とする。 | 値競合ではRunが開始されず、競合理由と対象期間を確認できる。 |
| `P5R2-REQ-HD-007` | 品質検査は警告だけの `USABLE_WITH_WARNING` と、始端・終端欠損、許容上限超過、値競合、時系列逆転、必須provenance欠落等の `UNUSABLE` を区別しなければならない。Download Jobの成功だけで使用可能にしてはならない。 | Preflightがusable区分と警告・停止理由を示し、UNUSABLEをRun入力から拒否する。 |

### 3.3 Backtest Run の取消・結果サマリー表示

| ID | Shall | 受入候補 |
|---|---|---|
| `P5R2-REQ-RUN-001` | `QUEUED / RUNNING`のRunだけを、実行一覧・進捗・結果サマリーで同じ判断により取消要求できなければならない。二重操作は同一要求として扱い、監査する。 | 3画面で同じ可否と理由が表示され、二重押下で状態を壊さない。 |
| `P5R2-REQ-RUN-002` | `SUCCEEDED / FAILED / CANCELLED / RECOVERY_REQUIRED / LEGACY_RESULT_ONLY / PARTIAL_FAILED`等のterminal状態への取消は、Run状態を変更しない受付・監査記録とし、表示非表示操作と混同してはならない。 | terminal取消後もRun状態が変わらず、理由と監査記録を確認できる。 |
| `P5R2-REQ-RUN-003` | 結果サマリー画面の「削除」は結果表示を非表示にする操作だけとする。Run、Run状態、結果本体、CSV、checkpoint、Historical Data、比較、Holdout、監査記録を削除・変更してはならない。 | 結果サマリーから非表示にしてもRun一覧と保存物が残り、再表示できる。 |
| `P5R2-REQ-RUN-004` | 結果表示状態はRun状態と別に保存し、非表示・再表示・重複操作・取消要求を監査しなければならない。実Data・実Run・保存結果の物理削除、Trash、purge、復元期限は `P5R2-DELETE-G1` で別途承認する。 | 表示状態だけが変わり、物理削除がGate前に実行できない。 |

### 3.4 監査・Manual・安全境界

| ID | Shall | 受入候補 |
|---|---|---|
| `P5R2-REQ-AUDIT-001` | Download開始・確認・取消・失敗・再試行、DataSet usable昇格、Run取消、結果非表示・再表示、delete要求・拒否・成功・失敗・cascadeを監査対象として定義しなければならない。最低項目は操作者、理由、対象ID、旧状態、新状態、依存物件数とする。 | 各変更操作で最低項目と結果を追跡できる。 |
| `P5R2-REQ-DOC-001` | `doc/phase5R/07_運用手順/01_バックテスト手順書.html` はP5R2-H2の前に、実装済みかつ検証済みの操作だけを反映して改訂しなければならない。時間足、Data取得・一覧、Download取消・再試行、Run取消、結果非表示・再表示、失敗・復旧、用語、画像、Evidence、改訂履歴を対象にする。 | Manual改訂要件表の各項目にTest・画像・Evidence・実装状態が追跡され、未実装を操作可能と書かない。 |
| `P5R2-REQ-GATE-001` | HREQ、H1、DATA-G1、DELETE-G1、H2の承認対象を分離し、未承認操作を実行可能にしてはならない。 | Gateごとの対象、再開条件、証拠先、停止範囲が統合台帳にある。 |

### 3.5 H0で確認した4領域・8件のatomic candidate crosswalk

H0で確認した8件は、人が承認する製品要求の単位として次のIDに固定する。右欄の詳細Requirementは、8件を実装・Acceptanceへ分解する下位追跡であり、推奨案や正式v4ではない。P5R2-HREQは、この8件とその下位追跡の整合を対象にする。

| 領域 | atomic candidate ID | 追跡する詳細Requirement | 現在状態 |
|---|---|---|---|
| 時間足 | `P5R2-CREQ-TF-001` | `P5R2-REQ-TF-001`、`P5R2-REQ-TF-003`、`P5R2-REQ-TF-004` | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |
| 時間足 | `P5R2-CREQ-TF-002` | `P5R2-REQ-TF-002`、`P5R2-REQ-TF-005`、`P5R2-REQ-TF-006` | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |
| 時間足 | `P5R2-CREQ-TF-003` | `P5R2-REQ-TF-003`、legacy・UTC・期間境界 | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |
| Historical Data | `P5R2-CREQ-HD-001` | `P5R2-REQ-HD-001`、`P5R2-REQ-HD-002`、`HistoricalDownloadJob`、`TimeframeGenerationJob` | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |
| Historical Data | `P5R2-CREQ-HD-002` | `P5R2-REQ-HD-003`〜`P5R2-REQ-HD-007` | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |
| Backtest Run操作 | `P5R2-CREQ-RUN-001` | `P5R2-REQ-RUN-001`、`P5R2-REQ-RUN-002` | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |
| Backtest Run操作 | `P5R2-CREQ-RUN-002` | `P5R2-REQ-RUN-003`、`P5R2-REQ-RUN-004` | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |
| 手順書 | `P5R2-CREQ-DOC-001` | `P5R2-REQ-DOC-001`、`P5R2-REQ-AUDIT-001`、`P5R2-REQ-GATE-001` | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |

## 4. 状態・操作の候補表

| 対象 | 状態 | 取消 | 結果非表示 | 実削除 |
|---|---|---|---|---|
| Download Job | QUEUED / RUNNING | 候補。Job取消のみでDataSetをusableにしない。 | N/A | DATA-G1/DELETE-G1前は不可 |
| Download Job | PARTIAL / FAILED / CANCELLED | 再試行候補。usable昇格不可。 | N/A | DATA-G1/DELETE-G1前は不可 |
| DataSet | USABLE / USABLE_WITH_WARNING | N/A | N/A | DELETE-G1前は不可 |
| DataSet | UNUSABLE / CONFLICT | Run開始不可。解決まで停止。 | N/A | DELETE-G1前は不可 |
| Backtest Run | QUEUED / RUNNING | 取消要求可。idempotent。 | 結果がまだなければ不可 | DELETE-G1前は不可 |
| Backtest Run | SUCCEEDED / FAILED / CANCELLED | 状態不変の取消受付・監査のみ。 | 結果表示があれば可。再表示可。 | DELETE-G1前は不可 |
| Backtest Run | RECOVERY_REQUIRED / LEGACY_RESULT_ONLY / PARTIAL_FAILED | 取消不可または状態不変受付。理由を表示。 | 保存済み結果がある場合だけ可。 | DELETE-G1前は不可 |

## 5. Unknown とLater Gate

| ID | 現在の扱い | 決定時期・停止範囲 |
|---|---|---|
| `P5R2-HREQ` | 未承認 | このcandidateを正式v4にするかを人が判断するまで、v3が正本、実装不可。 |
| `P5R2-H1` | 未承認 | API、永続化、UI、RED、実装、Test実行は不可。 |
| `P5R2-DATA-G1` | 未承認 | host、利用条件、symbol、期間、通信、Secret、費用、実downloadは不可。 |
| `P5R2-DELETE-G1` | 未承認 | 実Data・実Run・保存結果の物理削除、Trash、purge、復元運用は不可。 |
| `P5R2-UNK-TF-006` | `OPEN / LATER_GATE` | 「現在生成可能な全期間」の算出規則（元1mの最初・最後の有効UTC、欠損区間、UTC境界、`USABLE_WITH_WARNING`の包含、legacy包含）をH1の詳細設計で確定する。確定前はデフォルト期間を実装済み仕様と扱わない。 |
| `P5R2-UNK-HD-004` | `NEEDS_HUMAN_GATE` | Provider配布物の保護対象hashの目的・停止範囲が不明。管理用hashは導入しない。 |
| `P5R2-H2` | 未承認 | 完了判定とP6開始は不可。 |

## 6. 公式一次情報のread-only記録

- 確認日: 2026-08-22
- [Binance Developer Docs: General REST API Information](https://developers.binance.com/en/docs/products/spot/rest-api): 公開market data向けのendpoint、時刻・時系列の返却順、公開Data用base endpointの説明をread-onlyで確認した。
- [Binance Academy: How to Retrieve Binance Spot Market Data Efficiently](https://academy.binance.com/ka-GE/articles/how-to-retrieve-binance-spot-market-data-efficiently): 確認時点ではBinance本体へredirectされたため、候補Requirementの根拠には採用しない。URLとredirect事実だけを調査履歴として残す。

この調査は公開文書の閲覧だけであり、ログイン、契約、API call、Data downloadを含まない。Provider採用、利用条件、実host、費用、実通信の承認ではなく、Binanceは候補Providerのまま`P5R2-DATA-G1`で確定する。

## 7. P5R2-04 出口

このcandidateと P5R2-ART-03/04 は P5R2-05 の独立レビュー入力である。P5R2-HREQ の自動承認、正式v4公開、実装、Test実行、外部Data、Secret、費用、実削除、P6開始を含まない。
