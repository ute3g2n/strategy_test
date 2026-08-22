# 自動トレードシステム要件定義書 v4 candidate — P5R2

- 文書ID: `RQV4-CANDIDATE-P5R2-001`
- 版: `v4-candidate.0.1`
- 作成日: `2026-08-22`
- 状態: `CANDIDATE / SUPERSEDED_BY_AT-REQ-004 / P5R2-HREQ_APPROVED / NOT_CURRENT`
- 正式化履歴: `P5R2-HREQ` の明示承認を2026-08-22に受領し、P5R2-06Aで `doc/requirements/01_自動トレードシステム要件定義書_v4.html` を正式公開した。v3は上書きも無効化もせず、candidateは承認前の入力履歴として保持する。

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
| `P5R2-REQ-HD-005` | 同一論理Dataの非重複期間は、利用者が開始したDownload／merge操作で現在のDataへ追加できなければならない。マージ後に過去Runの結果が変わることを許容し、旧Dataで実行したRun／結果は利用者の確認後に削除して、新しいDataで再実行できるようにする。システムは、過去Runが変わり得ることだけを理由にmergeを禁止してはならない。 | Catalogで現在のcoverage、merge対象、影響を受けるRun／結果、再実行対象を確認できる。利用者確認なしに過去Run／結果を削除しない。 |
| `P5R2-REQ-HD-006` | 同一timestampの完全一致バーは一つにdedupeする。値が異なる場合は、利用者が明示的に「新しいDataで置換して影響Run／結果を削除する」操作を選べるようにし、選択しない場合は `CONFLICT` として停止する。値の競合を理由に、利用者が選択した置換・merge操作自体を禁止してはならない。 | 競合対象、置換対象、削除対象Run／結果、再実行対象を確認でき、確認後に現在Dataを更新できる。 |
| `P5R2-REQ-HD-007` | 品質検査は警告だけの `USABLE_WITH_WARNING` と、始端・終端欠損、許容上限超過、値競合、時系列逆転、必須provenance欠落等の `UNUSABLE` を区別しなければならない。Download Jobの成功だけで使用可能にしてはならない。 | Preflightがusable区分と警告・停止理由を示し、UNUSABLEをRun入力から拒否する。 |

### 3.3 Backtest Run の取消・結果サマリー表示

| ID | Shall | 受入候補 |
|---|---|---|
| `P5R2-REQ-RUN-001` | `QUEUED / RUNNING`のRunだけを、実行一覧・進捗・結果サマリーで同じ判断により取消要求できなければならない。フロントエンドは処理中の二重押下を禁止し、サーバーは対象Runの現在状態と操作tokenを確認して、再送・別画面・別タブによる二重状態変更を拒否しなければならない。 | 3画面で同じ可否と理由が表示され、UI二重押下、通信再送、別画面操作で状態を壊さない。複雑な汎用冪等性基盤は作らず、Run操作に必要な最小token・状態検査を行う。 |
| `P5R2-REQ-RUN-002` | `SUCCEEDED / FAILED / CANCELLED / RECOVERY_REQUIRED / LEGACY_RESULT_ONLY / PARTIAL_FAILED`等のterminal状態への取消は、Run状態を変更しない受付・監査記録とし、表示非表示操作と混同してはならない。 | terminal取消後もRun状態が変わらず、理由と監査記録を確認できる。 |
| `P5R2-REQ-RUN-003` | 結果サマリー画面の「削除」は、利用者が表示不要と判断したterminal Runのアプリ管理結果Artifactを物理削除できなければならない。利用者が表示・保持したい結果は削除せず、意図的にExportしたCSVは削除対象外とする。Runの実行状態、Historical Data、監査記録、Export済みCSVを削除してはならない。 | 削除前に対象Artifact・対象Run・CSV Export状態を確認でき、削除後は結果を画面に表示しない。Export済みCSVが残り、復元操作は提供しない。 |
| `P5R2-REQ-RUN-004` | 結果Artifactの削除状態をRunのterminal状態と分離して保存し、削除要求・拒否・成功・失敗・CSV保護を監査しなければならない。物理削除は論理IDと許可rootで対象Artifactだけに限定し、path traversal・symlink・任意path・Export済みCSV・監査記録を削除してはならない。 | terminal Runだけが削除対象となり、削除後は `RESULT_DELETED` として表示制御できる。復元は行わず、監査記録とCSVは残る。 |

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
| 時間足 | `P5R2-CREQ-TF-001` | `P5R2-REQ-TF-001`、`P5R2-REQ-TF-004` | USER_CONFIRMED / CANDIDATE_PENDING_HREQ |
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
| Backtest Run | SUCCEEDED / FAILED / CANCELLED | 状態不変の取消受付・監査のみ。 | 保持したい結果は表示継続。不要結果はCSV保護確認後にArtifact削除可。 | DELETE-G1前は不可 |
| Backtest Run | RECOVERY_REQUIRED / LEGACY_RESULT_ONLY / PARTIAL_FAILED | 取消不可または状態不変受付。理由を表示。 | 保存済み結果があり、削除対象として明示された場合だけ可。 | DELETE-G1前は不可 |

## 5. Unknown とLater Gate

| ID | 現在の扱い | 決定時期・停止範囲 |
|---|---|---|
| `P5R2-HREQ` | 未承認 | このcandidateを正式v4にするかを人が判断するまで、v3が正本、実装不可。 |
| `P5R2-H1` | 未承認 | API、永続化、UI、RED、実装、Test実行は不可。 |
| `P5R2-DATA-G1` | 未承認 | host、利用条件、symbol、期間、通信、Secret、費用、実downloadは不可。 |
| `P5R2-DELETE-G1` | 未承認 | 今回候補のresult Artifact物理削除を、対象Artifact、許可root、CSV保護、監査、依存関係、失敗時停止の範囲で承認する。Historical Data本体・Export済みCSV・監査記録の削除は対象外。Gate前の実削除は不可。 |
| `P5R2-UNK-TF-004` | `CANDIDATE_SPECIFIED / LATER_GATE` | 欠損1本の補間方式、OHLCV、未来値禁止、provenance、`USABLE_WITH_WARNING`／`UNUSABLE`境界は§8.4 F-001で候補仕様として固定した。H1ではこの候補をAPI・Persistence・Test・Manualへ写像するが、別方式を選択してはならない。 |
| `P5R2-UNK-TF-006` | `OPEN / LATER_GATE` | 「現在生成可能な全期間」の算出規則（元1mの最初・最後の有効UTC、欠損区間、UTC境界、`USABLE_WITH_WARNING`の包含、legacy包含）をH1の詳細設計で確定する。確定前はデフォルト期間を実装済み仕様と扱わない。 |
| `P5R2-UNK-HD-004` | `USER_APPROVED_LIMITED / NO_HASH_FLOW` | ユーザー承認を受領した。ただし管理用hash経路は導入せず、将来の保護対象hashは目的・対象・比較時点・不一致時fail-closed範囲・再取得条件が明文化されるまで実行しない。 |
| `P5R2-H2` | 未承認 | 完了判定とP6開始は不可。 |

## 6. 公式一次情報のread-only記録

- 確認日: 2026-08-22
- [Binance Developer Docs: General REST API Information](https://developers.binance.com/en/docs/products/spot/rest-api): 公開market data向けのendpoint、時刻・時系列の返却順、公開Data用base endpointの説明をread-onlyで確認した。
- [Binance Academy: How to Retrieve Binance Spot Market Data Efficiently](https://academy.binance.com/ka-GE/articles/how-to-retrieve-binance-spot-market-data-efficiently): 確認時点ではBinance本体へredirectされたため、候補Requirementの根拠には採用しない。URLとredirect事実だけを調査履歴として残す。

この調査は公開文書の閲覧だけであり、ログイン、契約、API call、Data downloadを含まない。Provider採用、利用条件、実host、費用、実通信の承認ではなく、Binanceは候補Providerのまま`P5R2-DATA-G1`で確定する。

## 7. P5R2-04 出口

このcandidateと P5R2-ART-03/04 は P5R2-05 の独立レビュー入力である。P5R2-HREQ の自動承認、正式v4公開、実装、Test実行、外部Data、Secret、費用、実削除、P6開始を含まない。

## 8. P5R2-06 review finding統合候補（HREQ未承認）

P5R2-05のFindingを候補Requirementへ反映するための補足である。ここでの `ADOPT` は候補文書への採用を意味するだけで、正式v4公開、実装、Test PASS、Gate承認を意味しない。`PARTIAL` と `NEEDS_HUMAN_GATE` は未解消のまま保持する。

| Finding | 採否 | candidateへの反映・停止境界 |
|---|---|---|
| `P5R2-05-F-001` 欠損補間 | `ADOPT / USER_CONFIRMED` | 内部の連続欠損1本だけを直前Closeで補間し、OHLCは同値、Volumeは0、warningとprovenanceを付与して `USABLE_WITH_WARNING` 候補にする。始端・終端、2本以上、時系列逆転、上限超過は `UNUSABLE`。 |
| `P5R2-05-F-002` 期間マージ | `ADOPT / USER_REVISED` | 正規化後の期間は半開区間 `[start, end)`、同一UTC timestampの完全一致だけをdedupeする。利用者が確認したmerge／replaceは、過去Run結果が変わり得ることを理由に禁止しない。影響Run／結果の確認・削除は明示操作とし、旧versionの永久保持は必須にしない。 |
| `P5R2-05-F-003` Run依存表 | `ADOPT / USER_REVISED` | 3画面×全Run状態×取消／保持／result Artifact物理削除×保存物×依存×監査の共有マトリクスを追加する。保持結果は残し、Export済みCSV、Historical Data、監査記録は保護する。 |
| `P5R2-05-F-004` 二重操作 | `ADOPT / MINIMAL_GUARD` | フロントのin-flight disableを基本にし、サーバーは対象状態と操作tokenだけを検査する。同一tokenの再送は同じ結果を返し、状態が変わった後の別tokenは二重状態変更を行わない。汎用冪等性基盤は作らない。 |
| `P5R2-05-F-005` Provider境界 | `NEEDS_HUMAN_GATE` | host、redirect、proxy、Secret、費用、容量、利用条件、実downloadは `P5R2-DATA-G1` まで禁止し、Gate packetへ移管する。 |
| `P5R2-05-F-006` Job復旧 | `ADOPT / USER_CONFIRMED` | staging→検査→atomic promotionを単位化し、失敗時はcurrent Catalogを変更せずrollback、孤児Dataは未掲載で隔離、再起動時は `RECOVERY_REQUIRED`、途中DataはRun入力にしない。 |
| `P5R2-05-F-007` 削除path | `ADOPT / USER_REVISED → DELETE-G1` | terminal結果の不要Artifactだけを、論理IDと許可rootから解決して物理削除する。path traversal、symlink／reparse point、任意path、Export済みCSV、監査記録を拒否・保護し、削除後は `RESULT_DELETED` として記録する。復元は提供しない。実削除はGate前に行わない。 |
| `P5R2-05-F-008` HREQ再開条件 | `ADOPT` | `REVIEW_RUNTIME_BLOCKED` は再開条件ではなく停止状態として、計画・台帳・packetを統一する。 |
| `P5R2-05-F-009` TF-003重複 | `ADOPT` | `P5R2-REQ-TF-003` は `P5R2-CREQ-TF-003` のlegacy／UTC／期間境界責務へ限定し、TF-001から除外する。 |
| `P5R2-05-F-010` 全期間 | `PARTIAL / LATER_GATE` | `P5R2-UNK-TF-006`を維持し、source有効範囲・欠損・UTC・warning・legacy包含をH1で確定。確定前は既定期間を実装済みと扱わない。 |
| `P5R2-05-F-011` 生成画面遷移 | `ADOPT` | 銘柄・時間足・期間の引継ぎ、戻る、取消、再試行、入力変更時の再確認を候補ACへ追加する。 |
| `P5R2-05-F-012` 監査 | `PARTIAL` | 操作者、理由、対象ID、旧／新状態、依存数に加えrequest／correlation ID、権限、時刻、失敗理由を候補化。保持期間・改ざん防止は後続設計で確定する。 |
| `P5R2-05-F-013` Manual | `ADOPT` | 実画面assert→axe→desktop/mobile画像→Evidence→Manual差分確認をH2必須Acceptanceへ追加する。 |
| `P5R2-05-F-014` 8件追跡 | `PARTIAL` | 各atomic行に質問ID、回答原文、正規化結果、状態、採否、後続Evidenceを直接付ける。 |
| `P5R2-05-F-015` 保護対象hash | `PARTIAL / USER_APPROVED_LIMITED` | ユーザー承認を受領し、管理用hash経路を作らない境界を記録。実際の保護対象hashを採用する場合の目的・対象・比較時点・停止範囲・再取得条件は別途明文化するまで保留。 |

### 8.1 HREQ前のfail-closed状態補足

- 補間閾値、全期間算出規則、Provider実行条件、物理削除条件、保護対象hash用途が未確定の間は、対象Data／操作を使用可能・実行可能へ昇格しない。
- 結果サマリーの「削除」は、保持したい結果を残したうえで、利用者が明示したterminal結果Artifactだけを物理削除する候補である。Run状態、Historical Data、Export済みCSV、checkpoint、比較、Holdout、Evidence、監査記録は削除対象にしない。DELETE-G1／H1前は実削除を行わない。
- `CANDIDATE / NOT_CURRENT / P5R2-HREQ_UNAPPROVED`、v3現行正本、P5R旧完了履歴、P6停止を維持する。

## 8.2 P5R2-06 A90再レビュー結果（HREQ未承認）

2026-08-22に、P5R2-06統合後の候補を `AutoTrade_A90_DesignReviewer_v0_1` がread-onlyで再レビューした。A90は、F-008（`REVIEW_RUNTIME_BLOCKED`を再開条件にしない）とF-009（TF-003 crosswalk重複解消）をClosed、F-015をHuman Gate継続と評価した一方、次の6件をHighとして残した。したがって、candidateの採否統合は完了したが、P5R2-06のExit条件（Critical／High=0、HREQ-blocking Unknown=0）は未成立である。

| A90 Finding | 重大度 | 未閉鎖の契約 | 閉鎖に必要な追補 |
|---|---|---|---|
| `A90-P5R2-06-F-001` | High | 補間上限・欠損率・方式・provenance schema・`USABLE_WITH_WARNING`昇格条件 | Requirement、Acceptance、状態表、Persistence、Negative Test、Manualを同一条件で固定する。 |
| `A90-P5R2-06-F-002` | High | timestamp正規化、merge transaction、API応答、Persistence不変制約 | `[start,end)`、完全一致判定、競合停止、新version、旧version固定参照をAPI／Persistence／Testで閉じる。 |
| `A90-P5R2-06-F-003` | High | 3画面×全Run状態×取消／非表示／再表示／実削除×保存物×依存×監査の共有マトリクス | 画面別可否、保存物保護、拒否理由、AuditEvent、Negative Testを一つの表へ統合する。 |
| `A90-P5R2-06-F-004` | High | idempotency keyの範囲、重複応答、競合優先順位、CAS／排他、retry、監査一意性 | 操作別request ID契約、同時操作、再送・再起動後応答、監査一意制約をAPI／Persistence／Testで固定する。 |
| `A90-P5R2-06-F-006` | High | staging／検査／atomic昇格、rollback、orphan、再起動、`RECOVERY_REQUIRED` | Job／DataSet／versionの所有関係、昇格トランザクション、孤児隔離、fail-closed、partial failure Testを定義する。 |
| `A90-P5R2-06-F-007` | High | 実体path再解決、symlink／対象外path拒否、tombstone／復旧 | DELETE-G1で対象・root・依存・保持・復元を承認し、traversal／symlink／別ID／Evidence保護のNegative Testを追加する。 |

Mediumとして、Provider境界のGate移管（F-005）、生成可能全期間（F-010）、生成画面の失敗時入力保持（F-011）、AuditEvent schema・保持・参照制御（F-012）、Manual fidelity（F-013）、8行の直接Evidence参照（F-014）も未閉鎖である。`P5R2-UNK-HD-004`はユーザー承認を受領したが、管理用hash、manifest、checksum receipt、fingerprint、stale、hash retryは導入していない。保護対象hashの実採用は比較契約と停止範囲が別途明文化されるまで保留する。

**現在の状態：** `CANDIDATE / NOT_CURRENT / P5R2-06_REVIEWED_ADVISORY / P5R2-HREQ_UNAPPROVED`。A90でCritical／High=0を確認済みだが、HREQ承認、v4正式公開、H1、実装、Test subprocess、Playwright、外部Data取得、実削除、P6開始を行わない。A90の前回レビューと改訂内容は `plan/phase5R2/ログ/P5R2-06_レビュー統合・HREQ承認packet_2026-08-22.md` とruntime receiptへ追跡する。

## 8.3 ユーザー最新回答によるHigh候補の改訂（2026-08-22）

P5R2-05／P5R2-06の旧候補にあった「immutable versionを保持し、過去Runの参照先を変えない」「結果削除は表示非表示だけ」という方針は、ユーザーの最新回答により現行候補から更新する。旧回答はART-02の履歴として保持し、最新回答を現行候補へ反映する。

| Finding | 最新方針 | 現行候補への反映 |
|---|---|---|
| F-001 | 推奨案を採用 | 内部欠損1本、直前Close固定、Volume 0、警告・provenance、始端／終端・上限超過はUNUSABLEをRequirement／ACへ明記する。 |
| F-002 | 過去Run結果の変更を許容 | 利用者が開始したmerge／replaceを禁止しない。影響Run／結果を確認後に削除し、新Dataで再実行できる。旧versionの永久保持を必須にしない。timestamp値競合時は、置換を明示選択しない限り停止する。 |
| F-003 | 表示保持と不要結果削除を分離 | 保持したい結果は削除しない。不要なアプリ管理result Artifactは削除候補とし、Export済みCSV、Historical Data、監査記録は保護する。 |
| F-004 | フロント二重押下禁止を採用 | UIのin-flight disableに加え、サーバーは操作tokenと現在状態だけを検査する最小ガードを置く。汎用冪等性基盤は作らない。 |
| F-006 | 推奨案を採用 | staging→検査→atomic promotion、rollback、孤児Data、RECOVERY_REQUIRED、途中versionのRun使用禁止を明記する。 |
| F-007 | 物理削除を実装対象へ変更 | terminal結果の不要Artifactだけを物理削除する。論理ID・許可root・symlink／traversal拒否、Export済みCSV・監査記録保護、復元なしを必須とする。実削除はDELETE-G1／H1承認後。 |

F-002の「merge」とF-007の「削除」は、システムが無断で実行することを意味しない。利用者がDownload／merge／replace／deleteを開始し、対象・影響・CSV保護を確認した後に実行する候補である。A90再レビューでこの改訂後の候補を再確認するまで、HREQ・実装・実削除は停止する。

## 8.4 High 6件の改訂後契約（A90再レビュー入力）

この節は、ユーザー最新回答をRequirement、Acceptance候補、API／Persistence候補、Negative Test候補、Manual候補へ同じ意味で展開するための入力である。ここで示すAPI・Persistence・Test名は設計・実装済みを意味しない。HREQとH1の承認前は候補のまま保持する。

### F-001 欠損補間

- **Requirement／Acceptance:** UTCに正規化した1m列で、内部の連続欠損がちょうど1本の場合だけ、欠損直前の確定Closeを補間後のOpen／High／Low／Closeへ設定し、Volumeを0とする。欠損の前後を含むfuture barは補間値の決定に使わない。補間したtimestamp、方式 `PREVIOUS_CLOSED_BAR`、参照した直前Close、対象DataSet、生成Job、警告理由をprovenanceへ保存し、状態を `USABLE_WITH_WARNING` 候補として表示する。始端欠損、終端欠損、連続2本以上、時系列逆転、timestamp重複、provenance欠落は `UNUSABLE` とし、Run入力から拒否する。
- **Persistence／API候補:** `quality_status`、`warning_code`、`missing_timestamp`、`interpolation_method`、`source_dataset_id`、`source_job_id`、`source_close_timestamp` をDataSet品質・provenanceの一部として扱う。Preflightは `USABLE_WITH_WARNING`／`UNUSABLE` と理由を返す。
- **Negative Test／Manual候補:** 1本の内部欠損は警告付きで通る、2本・始端・終端・逆転・未来値参照は停止することを確認し、手順書には警告と使用禁止の違いを記載する。

### F-002 期間merge／replace

- **Requirement／Acceptance:** 同一identity（Provider、market、symbol、1m、正規化schema）の入力だけをUTCの半開区間 `[start, end)` で扱う。完全一致timestamp・OHLCVは1本にdedupeする。非重複区間はcurrent Dataへ追加でき、既存coverage内の値が異なるtimestampは `CONFLICT` として対象・旧値・新値をpreviewする。利用者が明示的にreplaceを選択した場合は新値を採用でき、過去Run結果が変わり得ることを理由にmerge／replaceを拒否しない。利用者確認なしに影響Run／結果を削除せず、確認後に選択された旧結果だけを削除候補として、新Dataでの再実行へ引き継ぐ。
- **Persistence／API候補:** `merge_preview` はcurrent coverage、追加区間、dedupe件数、conflict件数、影響Run／result Artifact、Export済みCSV件数を返す。`merge_apply` はpreviewのoperation tokenを検証してstagingをcurrent Catalogへ一度のpromotion単位で反映し、成功時にcurrent coverageと影響対象を更新する。旧versionを永久保持する制約は置かないが、auditには旧／新coverage、選択したreplace、影響数、操作者、理由を残す。
- **Negative Test／Manual候補:** identity違いの自動merge、確認なしの削除、conflictの暗黙上書き、部分promotion、Export済みCSVの削除を拒否する。手順書にはpreview→影響確認→merge／replace→必要な旧結果削除→再実行の順序を記載する。

### F-003 3画面の共有状態・保存物マトリクス

以下の3画面は同じRun状態判定を表示する。`取消` はQUEUED／RUNNINGだけ有効、`保持` は利用者が残す結果をそのまま表示、`削除` はterminal結果Artifactが存在し利用者が明示した場合だけ有効とする。`RESULT_DELETED` はRunのterminal状態とは別の結果Artifact状態であり、復元操作は提供しない。

| 画面 | Run状態 | 取消 | 保持・表示 | result Artifact削除 | 保護対象／監査 |
|---|---|---|---|---|---|
| 実行一覧 | QUEUED | 有効。操作中は二重押下不可。 | 結果なし。 | 無効。 | Run状態、Data、監査を保護。cancel要求を監査。 |
| 進捗 | QUEUED | 有効。実行一覧と同じ判定。 | 結果なし。 | 無効。 | Run状態、Data、監査を保護。 |
| 結果サマリー | QUEUED | 有効。結果がなければ削除不可。 | 結果なし。 | 無効。 | Run状態、Data、監査を保護。 |
| 実行一覧 | RUNNING | 有効。操作中は二重押下不可。 | 途中結果があっても保持。 | 無効。 | Run、途中Data、監査を保護。cancel要求を監査。 |
| 進捗 | RUNNING | 有効。実行一覧と同じ判定。 | 途中結果を表示しても削除不可。 | 無効。 | Run、途中Data、監査を保護。 |
| 結果サマリー | RUNNING | 有効。結果があっても削除不可。 | 途中結果を表示しても保持。 | 無効。 | Run、途中Data、監査を保護。 |
| 実行一覧 | SUCCEEDED | 無効。理由を表示。 | 残す結果は表示継続。 | terminal Artifactを明示選択した場合だけ有効。 | Run、Historical Data、Export済みCSV、監査を保護。 |
| 進捗 | SUCCEEDED | 無効。理由を表示。 | 残す結果は表示継続。 | 実行一覧と同じ判定。 | 同上。 |
| 結果サマリー | SUCCEEDED | 無効。理由を表示。 | 残す結果は表示継続。 | 対象Artifact、CSV Export状態、影響数を確認後に有効。 | 同上。削除要求・成否を監査。 |
| 実行一覧 | FAILED | 無効。理由を表示。 | 結果Artifactがあれば残す。 | 不要Artifactを明示した場合だけ有効。 | Run、Data、CSV、監査を保護。 |
| 進捗 | FAILED | 無効。理由を表示。 | 結果Artifactがあれば残す。 | 実行一覧と同じ判定。 | 同上。 |
| 結果サマリー | FAILED | 無効。理由を表示。 | 残す結果は表示継続。 | 対象Artifactを確認後に有効。 | 同上。削除を監査。 |
| 実行一覧 | CANCELLED | 無効。理由を表示。 | 結果Artifactがあれば残す。 | 不要Artifactを明示した場合だけ有効。 | Run、Data、CSV、監査を保護。 |
| 進捗 | CANCELLED | 無効。理由を表示。 | 結果Artifactがあれば残す。 | 実行一覧と同じ判定。 | 同上。 |
| 結果サマリー | CANCELLED | 無効。理由を表示。 | 残す結果は表示継続。 | 対象Artifactを確認後に有効。 | 同上。削除を監査。 |
| 実行一覧 | RECOVERY_REQUIRED | 無効。復旧待ち理由を表示。 | 保存済み結果は残す。 | 明示したterminal Artifactだけ有効。 | Run、staging、Data、CSV、監査を保護。 |
| 進捗 | RECOVERY_REQUIRED | 無効。復旧待ち理由を表示。 | 保存済み結果は残す。 | 実行一覧と同じ判定。 | 同上。 |
| 結果サマリー | RECOVERY_REQUIRED | 無効。復旧待ち理由を表示。 | 保存済み結果は残す。 | 対象Artifactを確認後に有効。 | 同上。削除を監査。 |
| 実行一覧 | LEGACY_RESULT_ONLY | 無効。legacy理由を表示。 | legacy結果は残す。 | 新規Result Artifactの削除対象として明示された場合だけ有効。 | legacy Data、CSV、監査を保護。 |
| 進捗 | LEGACY_RESULT_ONLY | 無効。legacy理由を表示。 | legacy結果は残す。 | 実行一覧と同じ判定。 | 同上。 |
| 結果サマリー | LEGACY_RESULT_ONLY | 無効。legacy理由を表示。 | legacy結果は残す。 | 対象Artifactを確認後に有効。 | 同上。削除を監査。 |
| 実行一覧 | PARTIAL_FAILED | 無効。部分失敗理由を表示。 | 残す結果は保持。 | 不要Artifactを明示した場合だけ有効。 | Run、Data、CSV、監査を保護。 |
| 進捗 | PARTIAL_FAILED | 無効。部分失敗理由を表示。 | 残す結果は保持。 | 実行一覧と同じ判定。 | 同上。 |
| 結果サマリー | PARTIAL_FAILED | 無効。部分失敗理由を表示。 | 残す結果は表示継続。 | 対象Artifactを確認後に有効。 | 同上。削除を監査。 |

### F-004 二重押下・再送・競合

- **UI契約:** cancel／deleteボタンはクリック直後からレスポンスまたは明示的失敗までin-flight disableとし、同じ操作を画面側から2回送信しない。別画面・別タブには同じ現在状態と理由を表示する。
- **最小サーバー契約:** 操作は対象ID・操作種別・operation tokenで受け、対象Run／Artifactを現在状態で再確認する。同一tokenのtimeout後再送は保存済み結果または現在状態を返して副作用を二重に行わない。別tokenが先行操作後に届いた場合は現在状態を返し、二度目の状態変更を拒否する。対象行のcompare-and-setまたは同等の短い排他を使い、汎用冪等性基盤は導入しない。
- **Audit／Test候補:** `ACCEPTED`、`DUPLICATE_IGNORED`、`STATE_REJECTED`、`PROTECTED_REJECTED`を対象ID・token・操作者・時刻・旧／新状態と共に記録し、二重クリック、通信再送、別タブ、同時要求、timeout後再送、再起動後の状態不整合を検証する。

### F-006 Jobのstaging・検査・atomic promotion・復旧

- **処理契約:** Download／生成要求ごとにstaging領域とJob IDを割り当て、入力identity、期間、schema、品質、provenanceを検査する。検査完了前のstaging DataはCatalogにもRun入力にも出さない。銘柄・複数時間足・期間を一つの生成要求として受けた場合、要求内の全出力とCatalog参照を一つのpromotion単位で昇格し、一部だけをusableにしない。
- **失敗・再起動契約:** 検査失敗、promotion中断、プロセス停止、保存先不一致ではcurrent Catalogを変更せず、stagingを未掲載で隔離し、Jobを `FAILED` または `RECOVERY_REQUIRED` とする。再起動後に所有Job・staging・Catalog参照を照合できないDataは `ORPHAN_STAGING` としてRun入力から拒否し、自動でcurrentへ昇格しない。promotion成功後だけDataSetを `USABLE`／`USABLE_WITH_WARNING` とする。
- **Persistence／Test／Manual候補:** JobとDataSetの所有関係、promotion単位、current pointer更新、rollback、孤児隔離、partial failure、再起動復旧、途中Data拒否を記録・検証し、手順書には失敗時の再試行と `RECOVERY_REQUIRED` の扱いを記載する。

### F-007 物理削除のpath安全

- **対象契約:** 削除要求はpathを受け取らず、利用者が選んだ論理 `result_artifact_id` のみを受け付ける。ServerはArtifact台帳から対象Run・terminal状態・許可root・Artifact種別を解決し、Export済みCSV、Historical Data、監査、Evidence、Run本体を削除集合から除外する。
- **安全契約:** 解決後のcanonical pathが許可root配下でない、`..`を含む、絶対任意pathである、symlink／Windows reparse pointである、台帳のArtifact IDと実体が一致しない場合は拒否する。削除開始前に対象、依存物件数、CSV Export状態を表示し、成功時はArtifact台帳を `RESULT_DELETED` と監査へ記録する。失敗時は `DELETE_FAILED` とし、Run状態、CSV、監査を保持して後続削除を続行しない。復元用の操作は提供しない。
- **Negative Test／Gate:** traversal、symlink／reparse、別Run ID、任意path、active Run、CSV、監査、外部Evidenceの削除を拒否し、物理削除の実行は `P5R2-DELETE-G1` とH1の承認後に限定する。手順書には「削除後は復元できない」「必要なら先にCSVをExportする」を明記する。

### 改訂後High契約の共通保存・状態・追跡表

以下は、旧Round 4回答にあった不変version／表示非表示のみの記述を現行候補へ持ち込まないための現在正本である。旧記述は質問回答・レビュー履歴として残すが、HREQ packet、ART-03、ART-04、Manual候補が実装時に参照するのはこの表と本節である。

| 対象 | 現在の状態・保存項目 | 許可される次状態／操作 | 必ず拒否すること | 直接追跡する候補 |
|---|---|---|---|---|
| 補間DataSet | `source_dataset_id`、`source_job_id`、`missing_timestamp`、`source_close_timestamp`、`PREVIOUS_CLOSED_BAR`、OHLCV、warning、provenance、quality status | 1本内部欠損だけ `USABLE_WITH_WARNING` 候補へ | 始端／終端、2本以上、未来値、逆転、provenance欠落 | F-001 / TF-005 / AC-TF-002 / negative test / Manual |
| Historical merge | current identity、半開coverage、merge preview token、追加／dedupe／conflict件数、影響Run／Artifact | 利用者確認後にmerge、またはreplace選択後にatomic promotion | identity違い、自動conflict上書き、確認なしの結果削除、partial promotion | F-002 / HD-004〜007 / AC-HD-002 / Manual |
| ResultArtifact | `PRESENT`、`DELETE_PENDING`、`RESULT_DELETED`、`DELETE_FAILED`、Run ID、Artifact ID、Export状態、dependency count | terminalかつ明示選択時だけdelete。削除後は表示対象外 | active Run、保持選択、CSV、Historical Data、Audit、Evidence、任意path、復元 | F-003/F-007 / RUN-003/004 / AC-RUN-002 |
| OperationGuard | target ID、operation kind、operation token、CAS version、outcome、created_atを保存し、`(target_id, operation_kind, token)`を一意にする。tokenはtarget／auditの存続中に再利用させない。 | 同一tokenは保存済みoutcome、別tokenは現在状態を再評価 | token重複による副作用、状態不一致、再起動後の二重変更 | F-004 / RUN-001 / API・Persistence・negative test |
| Generation promotion | Job ID、staging group、DataSet ID、promotion ID、current pointer、所有関係を保存 | `VALIDATING`→`PROMOTABLE`→一括`PROMOTED`。失敗はrollback／`RECOVERY_REQUIRED` | staging／partial／orphanのRun利用、current pointerの部分更新 | F-006 / HD-001/002 / AC-HD-001/002 |

### 現行Run／Artifact操作の共有マトリクス

`hide`／`show`はP5R2の現行操作として採用しない。ResultArtifactの表示対象外化は、物理削除後の `RESULT_DELETED` 表示制御であり、別の可逆hide／restore APIを作らない。Export状態は `NONE`、`EXPORTING`、`EXPORTED`、`EXPORT_FAILED` とし、`EXPORTING` 中は削除を拒否する。`NONE`／`EXPORT_FAILED` はCSVがないことを警告して明示確認があれば削除候補にできる。

| Artifact state | CSV export state | 3画面での表示 | delete可否 | 保護・依存・監査 |
|---|---|---|---|---|
| `PRESENT` | `NONE`／`EXPORT_FAILED` | 保持選択なら表示継続。不要選択なら削除確認を表示。 | terminalの明示選択と再確認後だけ可。 | CSVなし警告、Run／Data／Audit／Evidenceは保護、`DELETE_REQUESTED`を監査。 |
| `PRESENT` | `EXPORTING` | Export処理中を表示。 | 不可。Export完了または失敗後に再評価。 | CSV書込みとresult削除を同時に行わない。拒否を監査。 |
| `PRESENT` | `EXPORTED` | 保持選択なら表示継続。不要選択ならCSV件数を表示。 | result Artifactだけ可。Export済みCSVは常に不可。 | CSV registry／実CSV、Run、Historical Data、Audit、Evidenceを保護。 |
| `DELETE_PENDING` | any | 削除中を表示し、他画面の削除を無効化。 | 不可。OperationGuardの結果を返す。 | 二重削除を拒否し、状態とAuditを保持。 |
| `RESULT_DELETED` | `NONE`／`EXPORT_FAILED`／`EXPORTED` | 3画面で「結果Artifact削除済み」。 | 不可。restore／再表示操作は提供しない。 | Run terminal状態、CSV、Historical Data、Audit、Evidenceを保持。 |
| `DELETE_FAILED` | any | 削除失敗理由と再試行可否を表示。 | 新しい明示要求でのみ再評価。自動cascadeしない。 | 失敗時に残存Artifactと保護対象を保ち、Auditへ記録。 |

### F-004／F-006／F-007の実行境界補足

- **OperationGuard:** Serverは`OperationGuard`を永続化し、同一`target_id + operation_kind + operation_token`を一意制約で拒否する。同一tokenのtimeout後再送は保存済みoutcome（`ACCEPTED`、`DUPLICATE_IGNORED`、`STATE_REJECTED`、`PROTECTED_REJECTED`）を返す。プロセス再起動後もこの行と対象のCAS versionを読み、同じ判定をする。tokenのTTL再利用はしない。target／Auditが保持される限りtoken outcomeを削除しない。これを汎用冪等性基盤とはせず、Run／ResultArtifact操作専用の最小保存とする。
- **Generation state machine:** `QUEUED → RUNNING → VALIDATING → PROMOTABLE → PROMOTING → PROMOTED`を正常系とし、検査失敗は`FAILED`、プロセス停止・所有関係不明・promotion中断は`RECOVERY_REQUIRED`、stagingだけ残った出力は`ORPHAN_STAGING`とする。`PROMOTING`ではcurrent pointerを一度のtransactionで更新し、失敗時は更新前pointerへrollbackする。複数時間足の一つでも失敗した場合、要求全体をcurrentへ昇格せず、部分出力をRun入力から拒否する。
- **Physical delete algorithm:** API入力は論理IDだけとし、rootはServer設定の固定許可rootから解決する。Artifact台帳のID・Run・種別・rootを検証し、open直前とunlink直前にcanonical path、root配下、symlink／Windows reparse pointでないことを再検査する。検査とunlinkの間に対象が差し替わった場合はfail-closedで`DELETE_FAILED`とし、残りのcascadeを続けない。削除済み行はID・Run・監査参照を残した`tombstone`として`RESULT_DELETED`にし、復元APIは持たない。
