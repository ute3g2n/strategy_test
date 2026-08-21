# Phase 5R2 実行計画書 — 時間足・Historical Data管理・Backtest取消／削除の要件是正

> Artifact ID: `P5R2-PLAN-001`
> Version: `v0.1`
> 作成日: `2026-08-21`
> 状態: `PLAN_CREATED / P5R2-H0_APPROVED / P5R2-01_COMPLETE / P5R2-02_ROUND1_COMPLETE / P5R2-03_ROUND2_WAITING_USER / P6_PAUSED`
> 現在の対象: 要件ヒアリング、要件候補の改訂、要件承認、承認後の実行計画再編まで
> 現在の非対象: P5R2本実装、外部Data取得、Secret投入、費用発生、実Data削除、P6開始

## 1. 結論

P6へ進む前に、P5R2を独立Phaseとして新設する。P5R2は、P5Rの完了履歴を削除せず、利用者が実際に必要とするBacktest製品要件とのずれを是正するPhaseである。

この`v0.1`は、次の範囲だけを確定した実行計画である。

1. 現行仕様・実装・手順書の差分を事実として固定する。
2. 追加要件を利用者へ段階的にヒアリングする。
3. 回答を要件ID、Acceptance、異常系、UI操作、API、永続化、安全境界へ変換する。
4. 要件定義書v3を上書きせず、v4 candidateを作成・レビュー・改訂する。
5. `P5R2-HREQ`承認後にv4を現在の正本として公開する。
6. 確定要件を入力に本計画を`v0.2`へ再編し、実装詳細設計からP5R2完了・P6再引渡しまでの直接実行Promptを追加する。

したがって、この計画書には要件確定前の実装方法を確定事項として書かない。後続工程の骨格は示すが、実装Stepの最終分割、担当Agent、対象ファイル、Quality Gate、Test、Run ID、Acceptanceは`P5R2-07`で確定要件から再生成する。

## 2. 今回すでに確定している要求

次の事項は、今回のユーザー指示と直前の会話で明示されているため、同じ質問を選択式で聞き直さない。

| Requirement ID | 確定要求 | 状態 |
|---|---|---|
| `P5R2-REQ-TF-001` | Single Backtestで利用者が選べる戦略時間足は`15m / 30m / 1h / 4h / 1d`の5種類とする。 | `CONFIRMED_BY_USER` |
| `P5R2-REQ-TF-002` | `1m`はHistorical Dataの最小ソース時間足であり、利用者向け戦略時間足として単独固定しない。 | `CONFIRMED_BY_USER` |
| `P5R2-REQ-TF-003` | `30m / M30`はP5R2の利用者選択対象に含める。既存1m／M30の保存済み履歴・Core互換・再利用の扱いは別途決める。 | `CONFIRMED_WITH_LEGACY_DECISION_OPEN` |
| `P5R2-REQ-HD-001` | アプリUIからHistorical Dataをダウンロードできる。 | `CONFIRMED_BY_USER` |
| `P5R2-REQ-HD-002` | 現在Backtestで使用可能なHistorical DataをUI上の一覧で管理できる。 | `CONFIRMED_BY_USER` |
| `P5R2-REQ-RUN-001` | Backtest実行一覧・進捗から、状態に応じて取消または削除を行える。 | `CONFIRMED_BY_USER` |
| `P5R2-REQ-RUN-002` | Backtest結果サマリーから、状態に応じて取消または削除を行える。 | `CONFIRMED_BY_USER` |
| `P5R2-REQ-DOC-001` | `doc/phase5R/07_運用手順/01_バックテスト手順書.html`を、P5R2の時間足、Data取得・管理、取消／削除へ追従改訂する。 | `CONFIRMED_BY_USER` |

## 3. 現在地と根因

| 観点 | 現在の事実 | P5R2で解決すること |
|---|---|---|
| P5R状態 | P5Rは`COMPLETE_WITH_OPEN_UNKNOWN`として完了し、P6引渡しまで記録済みである。 | P5Rの当時の限定Scopeを履歴として保持し、P5R2を現在の優先Phaseにする。 |
| 時間足UI | `ui/mock/src/P5RBacktestScreen.tsx`は時間足をread-onlyの`1m`で表示する。 | 5種類の戦略時間足を選択可能にし、利用可能Data・Strategy・期間と整合するPreflightへ変える。 |
| UI型 | `ui/mock/src/backtestApi.ts`の`BacktestSpec.timeframe`は`'1m'`だけである。 | UI、API、永続化、比較条件、表示形式の型を5種類の戦略時間足へ統一する。 |
| Application | `backtest_product.py`は`timeframe != 1m`を拒否し、StrategyConfigも`M1`だけを有効化する。 | 1m sourceから確定した選択時間足を生成し、選択時間足だけでStrategy判断する契約を確定する。 |
| Core | `runner.py`は`M15 / M30 / H1 / H4 / D1`の集約能力を持つ。 | Coreの再利用範囲、M30 legacy、M1必須内部契約、閉じた足だけを渡す境界を設計する。 |
| Historical Data | 通常実行は`E:\strategy_test_data\autotrade\historical\spot\klines\1m\`をread-onlyで参照する。P5のBinance取得Runnerは固定Run向けで、アプリAPI／UIとは未接続である。 | provider境界、Data Job、Catalog、品質、使用可能判定、取消・再試行、外部I/O Gateを製品要件化する。 |
| Run取消 | Application APIにはRun取消があるが、UIは現在開いている`activeRun`からしか呼べない。 | 実行一覧・進捗・結果サマリーの各表示から、対象Run IDを明示して取消できるようにする。 |
| Run削除 | Run削除API、UI、保存カタログ削除契約がない。 | 状態別削除可否、論理／物理削除、依存物、監査、復旧、確認操作を確定する。 |
| 手順書 | 現行手順書は`Spot / 1m / UTC`と、実Runカードの取消を前提にし、Data取得・Data一覧・Run削除を扱わない。 | 実装済み画面と一致する機能一覧、操作、成功条件、失敗・復旧、画像、追跡へ改訂する。 |

根因は、P5で品質確認した`1m`のsource fixture scopeを、P5Rの利用者向け戦略時間足scopeへそのまま流用したことにある。P5R2では、`source timeframe`、`derived timeframe`、`strategy timeframe`、`display timeframe`を別属性として扱う。

## 4. P5R2の目的・非目的

### 4.1 目的

- 利用者が`15m / 30m / 1h / 4h / 1d`からBacktest時間足を明示選択できる。
- 1m sourceからの集約、足境界、欠損、未確定足、時刻、Data provenanceを再現可能にする。
- UIから承認済み範囲のHistorical Data取得Jobを作成し、進捗、取消、失敗、再試行を扱える。
- Backtestで使用可能なData Setを一覧化し、品質・期間・銘柄・市場・source／derived時間足・状態を確認できる。
- Runの状態に応じ、実行一覧・進捗・結果サマリーから取消／削除を安全に操作できる。
- 要件、API、UI、永続化、Test、証跡、`01_バックテスト手順書`を同じIDで追跡する。

### 4.2 非目的

- P5R2-H0承認前の要件作業開始（承認前の停止条件として履歴保持）。
- P5R2-HREQ前の要件正式化、詳細設計、実装、RED／GREEN。
- P5R2-DATA-G1前のprovider接続、ファイル取得、Secret参照、費用発生。
- UIからの任意URL指定、任意host接続、任意パス保存。
- Broker、注文、Paper、Live、実資金、P6のRisk／OMS実装。
- Test Evidence、正式監査記録、要件履歴のUI削除。
- 管理目的の文書hash、manifest、fingerprint、stale判定、hash retryの再導入。

## 5. Human Gate、外部I/O Gate、停止条件

| Gate ID | 承認対象 | 未承認で許可すること | 未承認で禁止すること | 現在状態 |
|---|---|---|---|---|
| `P5R2-H0` | P5R2の追加Scope、要件ヒアリング、v4 candidate作成、公式一次情報のread-only調査範囲 | ユーザー明示承認済み。P5R2-01のlocal read-only調査・ART-01作成、P5R2-02の要件ヒアリング、`CANDIDATE / NOT_CURRENT` v4 candidate作成、公式公開文書のread-only調査範囲判断 | HREQ前の正式v4公開、H1前の実装・test subprocess・Playwright、DATA-G1前の外部Data取得・Secret・費用、DELETE-G1前の実削除、P6開始 | `APPROVED (2026-08-21)` |
| `P5R2-HREQ` | ヒアリング回答、要求ID、Acceptance、v4 candidate、Manual改訂要件、残Unknown | Gate packet・candidate・レビュー結果の閲覧 | v4正式公開、詳細設計、後続実装計画確定 | `UNAPPROVED` |
| `P5R2-H1` | `P5R2-07`で作る詳細設計、RED、対象path、Quality Gate、実装範囲 | 設計・Test候補の作成 | 実装・本試験・外部Data取得 | `PLANNED_UNAPPROVED` |
| `P5R2-DATA-G1` | provider、host、market、symbol、期間、source interval、認証、利用条件、費用上限、保存先、通信境界 | local fixtureによるUI/API/Test | 外部hostへの接続、実ファイル取得、Secret参照、費用発生 | `PLANNED_UNAPPROVED` |
| `P5R2-DELETE-G1` | Data／Run削除の対象、状態、依存、Trash、保持、復元、audit、実Dataを使う削除受入範囲 | 一時fixture上のdelete設計・RED／local試験 | 既存実Data、既存Run、Test Evidence、監査記録の削除 | `PLANNED_UNAPPROVED` |
| `P5R2-H2` | 全Acceptance、Data境界、取消／削除、Manual、Open Unknown、P6再引渡し | 完了候補と差分の閲覧 | P5R2完了宣言、P6開始 | `PLANNED_UNAPPROVED` |

P6は、ユーザーがP5R2をP6前に置くと指定したため、`P5R2-H2`まで開始しない。旧P5R-H2をP5R2のGateへ読み替えない。

## 6. 初期Unknown台帳

| Unknown ID | 決めること | 解消Step | 未解消時の停止範囲 |
|---|---|---|---|
| `P5R2-UNK-TF-001` | 1 Run 1時間足か、5種類の時間足同時参照を許可するか。 | P5R2-02〜03 | Strategy入力・比較条件・UI型を確定しない。 |
| `P5R2-UNK-TF-002` | 集約をRun時に行うか、derived cacheを事前生成するか。UI生成画面の「現在生成可能な全期間」、生成Jobの状態・再試行・同時実行、DataSet／usableの登録条件も決める。 | P5R2-02〜03 | Data Catalog・provenance・性能Acceptance・生成Job契約を確定しない。 |
| `P5R2-UNK-TF-003` | UTC anchor、終了時刻の包含、partial／missing bar。既存1m／M30保存物はQ-TF-06=Aで閲覧専用に確定済み。 | P5R2-03 | 時刻境界・partial／missing・現行30mとの比較契約を確定しない。 |
| `P5R2-UNK-TF-004` | Q-TF-05のユーザー回答「5. C」と、現行ART-02の「補間する方向性」が矛盾している。欠損1mを上位足へ補間する方式、最大欠損量、始端・終端欠損、品質表示、usable化、未来側データの利用禁止、再現性。 | P5R2-03〜04／HREQ | Q-R2-02で意味を再確認するまで、補間Dataを自動で使用可能にせず、Requirementを確定しない。 |
| `P5R2-UNK-HD-001` | 製品要件上の初期provider、market、symbol、source interval、期間指定方式、routine downloadの承認単位。 | P5R2-02〜04／HREQ | local fake providerを含むDownload／Catalog要件を確定しない。 |
| `P5R2-UNK-HD-002` | Data一覧の単位、必須列、使用可能判定、更新・重複・取消・再試行。任意symbolのcatalog／allowlist、market、未対応時の拒否も決める。 | P5R2-02〜03 | Catalog API／UI／永続化／入力境界を確定しない。 |
| `P5R2-UNK-HD-003` | Historical Dataの削除可否、参照Runとの依存、Trash／保持期間。 | P5R2-02〜03 | Data削除機能をScopeに入れない。 |
| `P5R2-UNK-HD-004` | provider sourceの直接整合確認に保護対象hashを使うか。使う場合の対象、比較時点、不一致時停止、再取得条件。 | P5R2-02〜04／HREQ | 用途不明のhashを追加せず、Dataを使用可能へ昇格させない。 |
| `P5R2-UNK-RUN-001` | Run状態別の取消／削除可否とボタン表示。 | P5R2-02〜03 | Run操作Acceptanceを確定しない。 |
| `P5R2-UNK-RUN-002` | soft delete／hard delete、結果・CSV・checkpoint・比較・Sweep・auditの扱い。 | P5R2-02〜03 | delete API／保存契約を確定しない。 |
| `P5R2-UNK-DOC-001` | 新規手順ID、画像数、旧1m説明の履歴表示、Data削除を手順に含めるか。 | P5R2-03〜04 | Manualの最終章立て・撮影台帳を確定しない。 |

HREQ前に閉じるUnknownと、後続Gateで実行直前に決める事項を混ぜない。

| Later Gate ID | HREQ時点で固定すること | Later Gateまで残してよいこと | 停止範囲 |
|---|---|---|---|
| `P5R2-DATA-G1` | Provider Adapter境界、許可Scopeの型、確認UI、DownloadJob／DataSet状態、品質・使用可能判定、Secret／費用のfail-closed要件 | 実provider利用条件の確認Evidence、実credentialの有無、対象Runの具体期間、費用上限、host／allowlist、実取得Run ID | 未承認中はlocal fake providerだけ。外部接続0、Secret参照0、費用0。 |
| `P5R2-DELETE-G1` | 状態別delete契約、Trash／復元、dependency、audit、Evidence非削除、確認UI | 実Data／実Runを使う受入対象、保持期間の運用値、purgeの実施可否 | 未承認中は一時fixtureだけ。既存実Data／Runを削除しない。 |

## 7. ヒアリング方式

### 7.1 原則

- 一度に質問を詰め込まず、Round 1は最大10問、Round 2以降は未解消の重要事項を最大8問ずつ提示する。
- 各質問は、`質問ID / 決めたいこと / 選択肢 / 推奨初期案 / 推奨理由 / 影響する要件・画面・API・Test`を含める。
- ユーザーの自由記述を選択肢へ無理に丸めず、原文と正規化した決定を両方保存する。
- `回答済み`、`仮決定`、`未回答`、`矛盾あり`、`後続Gate`を区別する。
- 回答が既存要件v2/v3と競合する場合、既存文書を黙って上書きせず、変更理由と旧要件の履歴扱いを明記する。
- 推奨案は決定ではない。ユーザー回答なしに`APPROVED`、`CONFIRMED`、`PASS`へ変えない。

### 7.2 質問バンク

| ID | 質問 | 推奨初期案 | 回答が変える後続範囲 |
|---|---|---|---|
| `Q-TF-01` | 1回のSingle Backtestでは5種類の戦略時間足から1つだけを選ぶか、主時間足＋参照時間足を同時指定するか。 | P5R2では1 Run 1選択時間足。マルチ時間足Strategyは別要件として残す。 | BacktestSpec、StrategyConfig、UI入力、比較可能条件、Golden Test |
| `Q-TF-02` | 1m sourceから15m／30m／1h／4h／1dをRun時集約するか、品質確認済みderived Dataを作ってCatalog登録するか。 | immutableな1m source＋品質確認済みderived cache。RunはCatalog上の使用可能Dataだけを読む。 | Data model、容量、性能、provenance、再生成、Catalog UI |
| `Q-TF-03` | Crypto Spotの足境界をUTC 00:00 anchorに固定してよいか。 | M15/H1/H4/D1をUTC 00:00起点、右端Close確定後だけStrategyへ渡す。 | 集約、期間入力、境界Test、手順書 |
| `Q-TF-04` | 指定終了時刻が足境界でない場合、入力拒否か、直前の確定足まで切り下げるか。 | Preflightで拒否し、利用可能な境界を表示する。暗黙切下げはしない。 | Validation、error code、UI支援、Acceptance |
| `Q-TF-05` | 1本でも1mが欠けたderived barをどう扱うか。 | 補間せず`PARTIAL_BAR_REJECTED`で対象Runを開始／継続しない。 | Quality、停止、Recovery、negative test |
| `Q-TF-06` | 新規Runでは30mを選択可能としたうえで、既存の1m／M30 Run・Data・結果を現行契約とどう関係づけるか。 | `A`確定：既存保存物は閲覧専用。新規30m選択は可能、既存保存物の再実行・現行比較・自動移行・削除はしない。 | 履歴表示、Manual注記、削除Gate |
| `Q-HD-01` | 最初のUIダウンロードproviderを何にするか。 | 既存実績のあるBinance Data Visionに限定し、Adapterで拡張可能にする。 | Provider Adapter、公式調査、DATA-G1、UI文言 |
| `Q-HD-02` | 初期対象をBTCUSDT／ETHUSDT Spotだけにするか、任意symbol選択を許可するか。 | 初期はBTCUSDT／ETHUSDT Spot。provider catalog拡張は後続。 | Scope、入力Validation、費用・容量、E2E |
| `Q-HD-03` | providerが15m／30m等も提供している場合でも、P5R2の製品sourceは確定済みの1mだけに固定し、直接取得した上位足を使用しない方針でよいか。 | sourceは1mだけ取得し、5種類の戦略時間足を同一規則で派生する。既回答の1m sourceを変更する質問ではなく、上位足の混在禁止を確認する。 | Download request、保存tree、provenance、品質 |
| `Q-HD-04` | routine downloadの承認単位をどうするか。 | provider／host／symbol／上限をDATA-G1で一度承認し、範囲内は毎回UI確認、範囲外は新Gate。 | Authorization、confirmation、audit、停止条件 |
| `Q-HD-05` | 日付指定は任意日時、UTC日、月単位のどれにするか。 | UIはUTC日付範囲、provider月次archiveへ内部変換し、余分な範囲は使用可能Dataへ昇格させない。 | Request、download分割、storage、quality |
| `Q-HD-06` | 同一Dataが存在するとき、拒否、上書き、差分更新のどれにするか。 | 同一source identityはskip、差分は新version、既存をin-place上書きしない。 | Idempotency、versioning、Catalog、Recovery |
| `Q-HD-07` | Download Jobに必要な操作は何か。 | QUEUED/RUNNINGの取消、FAILED/CANCELLEDの明示再試行、成功済みの再試行禁止。 | Job state、API、UI、checkpoint、Test |
| `Q-HD-08` | Dataを`使用可能`にする条件は何か。 | source整合、schema、時刻順、重複、欠損、範囲、derived生成、品質報告がPASSした後だけ。 | Catalog state、Preflight、Quality Gate |
| `Q-HD-09` | Data一覧で必ず見たい列は何か。 | provider、market、symbol、source interval、利用可能時間足、UTC期間、状態、欠損、行数、容量、更新日、version、使用中Run数。 | UI table、API response、a11y、Manual |
| `Q-HD-10` | Historical Data自体の削除もP5R2に含めるか。 | まず無効化／Trash移動だけ。参照RunがあるDataの物理削除は禁止。 | Data delete API、dependency、retention、Manual |
| `Q-HD-11` | provider配布元のsource archive整合確認に、provider提示値との保護対象hash比較を使うか。 | providerが公式比較値を配布する場合だけ採用し、不一致Dataは使用不可。再取得は新しい明示Jobとして行う。 | DATA-G1、Data quality、usable判定、再取得、A95判定 |
| `Q-HD-12` | Downloadの試行履歴と、Backtestで使えるDataを同じレコードにするか。 | `DownloadJob`と`DataSet`を別ID・別状態にし、PARTIAL／FAILED／CANCELLEDの成果物をDataSetの使用可能状態へ昇格させない。 | API、Persistence、Catalog、retry、削除競合 |
| `Q-RUN-01` | QUEUED/RUNNING Runの取消ボタンを一覧・進捗・サマリーの全てに出すか。 | 全てに同じ状態判定で表示し、対象Run IDと状態を確認して取消する。 | UI component、API idempotency、E2E |
| `Q-RUN-02` | Terminal Runの取消ボタンを隠すか、disabledで理由を示すか。 | disabled表示＋「完了済みのため取消不可」。操作可能性を見失わせない。 | UI状態、a11y、Manual |
| `Q-RUN-03` | Run削除を許可する状態はどれか。 | SUCCEEDED/FAILED/CANCELLEDのみ。QUEUED/RUNNINGは取消完了後に削除可能。 | State machine、409 error、UI |
| `Q-RUN-04` | 削除は即時完全削除か、Trashへ移す論理削除か。 | 結果・Catalog・CSV・checkpointをRun単位でTrashへ移し、一定期間後のpurgeは別操作／別方針。 | Storage、restore、retention、Manual |
| `Q-RUN-05` | 削除時に何を残すか。 | Test Evidenceは削除しない。最小audit tombstoneとしてRun ID、削除時刻、削除理由、元状態、依存物件数を残す。 | Audit、privacy、storage、Acceptance |
| `Q-RUN-06` | Sweep親子の削除単位をどうするか。 | 親削除時は子一覧と影響を表示し、明示cascade確認。子単独削除は比較・親集計への影響を表示。 | Sweep model、confirmation、dependency test |
| `Q-RUN-07` | 比較中、CSV Job中、Holdout参照中のRun削除をどうするか。 | 実行中依存Jobがあれば拒否。完了依存物は削除対象一覧へ含め、確認後に一貫して処理。 | Concurrency、transaction、error recovery |
| `Q-RUN-08` | 一括取消／一括削除をP5R2へ含めるか。 | 初期は1件ずつ。誤操作範囲を小さくし、bulkは後続要件。 | UI complexity、a11y、Safety Test |
| `Q-RUN-09` | 取消／削除可否表へ、通常のRun状態以外に何を含めるか。 | `RECOVERY_REQUIRED`、`LEGACY_RESULT_ONLY`、Sweep親／子、`PARTIAL_FAILED`、CSV生成中、比較中、Holdout参照中を全て含める。 | 状態マトリクス、dependency、409理由、Manual |
| `Q-AUDIT-01` | どの操作を監査記録へ残すか。 | Download開始／確認／取消／失敗／再試行、Data usable昇格、Run取消、delete要求／拒否／成功／失敗／cascadeを、操作者、理由、対象ID、旧／新状態、依存物件数とともに残す。 | Audit event、Persistence、Security、Manual |
| `Q-DOC-01` | 手順書の主読者を現行どおり初心者中心にするか。 | 現行ルールを維持し、Data品質・取消・削除の結果を画面で確認できる説明にする。 | 文体、章構成、用語、画像 |
| `Q-DOC-02` | 削除復旧／Trash操作を同じ手順書へ含めるか。 | 実装Scopeに入った操作だけを掲載し、未実装purgeを「できる」と書かない。 | BT-F／BT-MAN ID、Manual E2E、Safety境界 |

## 8. 成果物配置

### 8.1 今回の計画作成で作るもの

| 成果物 | 場所 | 状態 |
|---|---|---|
| P5R2実行計画v0.1 | `plan/Phase5R2_実行計画書_v0.1_2026-08-21.md` | 今回作成 |
| P5R2計画作成ログ | `plan/phase5R2/ログ/P5R2-PLAN_実行ログ_2026-08-21.md` | 今回作成 |
| P5R2 runtime receipt | `plan/phase5R2/ログ/P5R2-PLAN_runtime-dispatch_2026-08-21.md` | 今回作成 |
| `P5R2-ART-00` H0 packet | `plan/phase5R2/ログ/P5R2-00_H0開始確認_2026-08-21.md` | P5R2-00で作成・H0未承認 |
| P5R2-00 runtime receipt | `plan/phase5R2/ログ/runtime-receipt-P5R2-00.json` / `.md` | P5R2-00で作成 |
| 未承認Gate・Unknown | `doc/00_全Phase残課題Blocked統合台帳.html` | 今回同期 |
| 現在の入口表示 | `doc/index.html` | 今回同期 |

### 8.2 P5R2-01〜06Aで作る予定のもの

| Artifact ID | 予定場所 | 内容 |
|---|---|---|
| `P5R2-ART-01` | `doc/phase5R2/01_要件追跡/01_P5R2現状差分・根因・要求追跡.html` | P5R2-01で作成・統合レビュー完了。source／derived／strategy／displayの分離、Data管理未接続、Run操作欠落、初期trace、Unknownを記録し、P5R2-02へ引き渡した。 |
| `P5R2-ART-02` | `doc/phase5R2/01_要件追跡/02_P5R2ヒアリング回答・決定台帳.html` | Round 1の10回答、Q-TF-06=A、Q-R2-01〜08のRound 2質問packet、A90 High指摘、A95判定、変更影響。Q-TF-05の矛盾、補間・任意symbol・Provider範囲・Run cancel/delete・Manualの詳細は未確定。 |
| `P5R2-ART-03` | `doc/phase5R2/01_要件追跡/03_P5R2要件・AC・UI・API・Test追跡マトリクス.html` | RequirementからTest／Manualまでの追跡 |
| `P5R2-ART-04` | `doc/phase5R2/01_要件追跡/04_01_バックテスト手順書改訂要件.html` | 手順書の章・機能ID・操作ID・画像・失敗／復旧の改訂仕様 |
| `P5R2-REQ-V4-CANDIDATE` | `plan/phase5R2/requirements/drafts/01_自動トレードシステム要件定義書_v4_candidate.html` | HREQ前の候補。現在正本とは表示しない |
| `AT-REQ-004` | `doc/requirements/01_自動トレードシステム要件定義書_v4.html` | HREQ後の正式要件正本。v3は履歴保持 |
| `P5R2-PLAN-002` | `plan/Phase5R2_実行計画書_v0.2_<HREQ承認日>.md` | 確定要件から再編した最終Stepまでの全Prompt |

実装完了時には既存の`doc/phase5R/07_運用手順/01_バックテスト手順書.html`を改訂する。別名の正本を増やさず、文書内のversionと改訂履歴を更新し、P5R時点の画像・説明は履歴として必要な範囲だけ残す。

## 9. DAGと実行順

```text
P5R2-PLAN（このv0.1）
  ↓ 人が計画を確認
P5R2-00（H0 packet）
  ↓ P5R2-H0 明示承認
P5R2-01（現状差分・根因・追跡）
  ↓
P5R2-02（ヒアリング Round 1）
  ↓
P5R2-03（矛盾・Gap閉鎖 Round 2+）
  ↓ blocking Unknown = 0
P5R2-04（v4 candidate・AC・Manual改訂要件）
  ↓
P5R2-05（独立要件レビュー・Red Team・A95）
  ↓ Critical / High = 0
P5R2-06（改訂統合・HREQ packet）
  ↓ P5R2-HREQ 明示承認
P5R2-06A（v4正式公開・index／統合台帳同期）
  ↓
P5R2-07（計画v0.2再編＋最終StepまでのPrompt追加）
  ↓ P5R2-H1以降はv0.2だけを現在の実行入口にする
詳細設計 → RED → 実装 → DATA-G1 → 統合試験 → Manual改訂 → 最終レビュー → P5R2-H2 → P6再引渡し
```

並列実行は、同じ要件ID・同じHTML・同じ計画書を編集しない読取レビューだけに限定する。ヒアリング回答の正規化、Requirement ID採番、v4統合、計画v0.2統合は直列で行う。

## 10. 全Step共通実行契約

以下を各固有Promptの先頭へ連結し、1つのPromptとして実行する。固有Promptだけを単独実行しない。

```text
あなたはC:\project\strategy_testのP5R2を実行する。phase_id=P5R2、step_idは固有Prompt記載値を使う。

開始前にREADME.md、settings/language.md、settings/ai_component_rules.md、AGENTS.md、doc/00_全Phase残課題Blocked統合台帳.html、doc/index.html、plan/Phase5R2_実行計画書_v0.1_2026-08-21.mdを読む。固有Promptが指定するSkillのSKILL.mdは主Agentが全文を読み、参照先の必要資料も読む。

変更前にmulti_agent_v1__spawn_agent／wait_agentの利用可否を確認する。利用可能なら、固有Promptで指定したOrchestratorを定義JSONの固定modelでCoordinatorとして実spawnし、Coordinatorに指定Agent全件を各Agent JSONの固定modelと、JSONに定義がある場合だけreasoning_effortを指定して個別spawnさせ、全件waitさせる。完全名を列挙しただけ、JSONを読んだだけ、Skillを読んだだけ、rootが自己レビューしただけの状態を、起動済み・独立レビュー済みと書かない。

runtime receiptには、phase_id、step_id、runtime_backend、dispatch_mode、coordinator_agent_id、Orchestrator名／JSON path／model、各Agent名／JSON path／model／reasoning_effort／assigned_task／agent_id／受付status／完了status／output reference、wait結果、independent、review_modeを記録する。receiptはplan/phase5R2/ログ/runtime-receipt-<step_id>.jsonと同名の可読Markdownへ保存する。起動不能、固定model不受理、子Agent未起動、wait不能、子出力未取得のいずれかがあれば、RUNTIME_DISPATCH_FALLBACK_REQUIRED、未起動Agent、理由、agent_id=N/A、independent=false、review_mode=SELF_REVIEW_FALLBACKを記録し、独立実行済みとは書かない。

この計画内の完全名とJSON pathは次のとおり。固有PromptにA05等の短縮表示が残る場合も、実行時は必ずここに示す完全名、path、modelで展開する。
- A05 = AutoTrade_A05_PhaseExecutionPlanner_v0_1 / .codex/agents/AutoTrade_A05_PhaseExecutionPlanner_v0_1.json / gpt-5.6-luna
- A10 = AutoTrade_A10_RequirementsCurator_v0_1 / .codex/agents/AutoTrade_A10_RequirementsCurator_v0_1.json / gpt-5.6-luna
- A80 = AutoTrade_A80_DocumentIntegrator_v0_1 / .codex/agents/AutoTrade_A80_DocumentIntegrator_v0_1.json / gpt-5.6-luna / reasoning_effort=low
- A81 = AutoTrade_A81_DesignDocSetWriter_v0_1 / .codex/agents/AutoTrade_A81_DesignDocSetWriter_v0_1.json / gpt-5.6-luna
- A90 = AutoTrade_A90_DesignReviewer_v0_1 / .codex/agents/AutoTrade_A90_DesignReviewer_v0_1.json / gpt-5.6-luna
- A95 = AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1 / .codex/agents/AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1.json / gpt-5.6-luna / reasoning_effort=low
- PhasePlanning Coordinator = AutoTradePhasePlanning_Orchestrator_v0_1 / .codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json / gpt-5.6-terra
- DesignDocSet Coordinator = AutoTradeProject_DesignDocSet_Orchestrator_v0_1 / .codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json / gpt-5.6-terra
- ComponentLifecycle Coordinator = AutoTradeComponentLifecycle_Orchestrator_v0_1 / .codex/orchestrators/AutoTradeComponentLifecycle_Orchestrator_v0_1.json / JSON記載model

Skillの短縮表示も、.codex/skills/<完全名>/SKILL.mdの全文を読む。source_reader=autotrade_skill_source_reader_v0_1、traceability=autotrade_skill_traceability_v0_1、phase_execution_planning=autotrade_skill_phase_execution_planning_v0_1、orchestration=autotrade_skill_orchestration_v0_1、html_doc_writer=autotrade_skill_html_doc_writer_v0_1、design_doc_set_writer=autotrade_skill_design_doc_set_writer_v0_1、design_review=autotrade_skill_design_review_v0_1、red_team_review=autotrade_skill_red_team_review_v0_1、revision_integration=autotrade_skill_revision_integration_v0_1、protected_hash_policy_guard=autotrade_skill_protected_hash_policy_guard_v0_1を意味する。

P5R2-05／06の専門レビューでは、少なくともA90とA95の実agent出力を必要とする。Coordinatorから子Agentを起動できない場合、rootが同じ完全名・modelで個別起動しwaitしたreceiptをfallbackとしてよい。root自己レビューだけしかできない場合はindependent=falseを記録するだけでなく、P5R2-HREQ packetをレビュー完了扱いにせずREVIEW_RUNTIME_BLOCKEDで停止する。

対象Human Gateを統合台帳で確認する。未承認なら、Gate packet、read-only調査、候補文書の作成として明示許可された作業だけを行い、実装、外部接続、Secret参照、費用発生、Data／Runの実削除、test subprocess、Playwright、完了宣言、P6開始を行わない。ユーザーの明示承認文を別Gateへ読み替えない。

Windows側C:\project\strategy_testを正本とする。既存ユーザー変更を上書きしない。編集はapply_patchを使う。新規／大幅変更文書はpath、UTF-8、schema、link、Secret、状態、要件追跡を非hashで確認し、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1の静的判定へ渡す。管理用hash、checksum、fingerprint、stale、hash retry、manifest整合を判定・実行・停止・再試行・完了条件にしない。P5R2-HREQで用途が確定するまで新しい保護対象hashも採用しない。採用する場合は、provider source archiveの直接整合やcheckpoint改竄検知など安全性・Data再現性へ直結する目的だけに限定し、対象、比較契約、比較時点、不一致時のfail-closed範囲、再取得／再試行条件を要件へ明記する。A95は語句分類と静的判定だけを行い、hash値、manifest、checksum receipt、fingerprint、stale状態を生成しない。

Human Gate、Blocked、Unknown、現在状態を変更した場合は、doc/00_全Phase残課題Blocked統合台帳.html全体を検索し、関連行・現在状態・履歴リンクの矛盾を同時に直す。正式HTMLを追加した場合はdoc/index.htmlから到達可能にする。旧文書と旧判断は削除せずHISTORY／SUPERSEDEDとして残す。

Step完了前にgit status --shortと差分を確認し、今回のStepの変更だけをstageする。関連する静的検査を行い、Secret・鍵・個人情報がないことを確認して意味のある単位でcommitし、現在branchの追跡先へpushする。禁止、認証失敗、追跡先なし、意図しない変更がある場合は変更を保持し、理由をログと最終報告に残す。
```

## 11. 要件修正までの超詳細・直接実行Prompt

### P5R2-00 — H0 packetを作り、要件作業の開始可否を確認する

```text
step_id=P5R2-00。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（各model=gpt-5.6-luna、A80/A95はreasoning_effort=low）。Skillはautotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

目的は、P5R2-H0で人が判断すべき範囲を1 packetへ集約すること。P5R2-H0を自動承認しない。

次を行う。
1. この計画のユーザー要求4領域、atomicな確定Requirement 8件、Unknown／Later Gate、質問バンク、DAG、予定成果物、P6停止条件を再確認する。4領域と8件を混同しない。
2. P5Rの旧完了範囲と、P5R2で再度扱う製品要件を分ける。旧P5R-H2を無効化せず、P5R2へ流用もしない。
3. H0承認対象を、要件ヒアリング、local read-only調査、v4 candidate、公式一次情報のread-only調査の可否に限定する。
4. H0非承認中に禁止するものとして、ソース実装、test subprocess、Playwright、外部Data取得、Secret、費用、実削除、P6開始を明記する。
5. provider公式調査をH0に含める場合も、公開文書の閲覧だけであり、ログイン、契約、API call、Data downloadを含めないと明記する。
6. 統合台帳のP5R2-H0行に、対象、期限、再開条件、証拠先を揃える。未承認表示を維持する。
7. 運用者向けに、専門用語を使わない1ページ相当のH0説明を作る。

成果物はplan/phase5R2/ログ/P5R2-00_H0開始確認_<date>.md、runtime receipt、必要な統合台帳更新。Acceptanceは、H0の承認対象／非対象、Unknown、P6停止、外部I/O境界が矛盾なく読めること。

最後に人へ「P5R2-H0を承認します。要件ヒアリングを開始してください。」という明示文の判断を求める。承認がない場合はP5R2-01へ進まず、P5R2-H0_UNAPPROVEDで停止する。
```

### P5R2-01 — 現状差分、根因、Requirement traceを正式化する

```text
step_id=P5R2-01。開始条件はP5R2-H0の明示承認。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（JSON path／model／reasoning_effortは共通実行契約の完全名表どおり）。Skillはautotrade_skill_phase_execution_planning_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

目的は、ヒアリング前に「既にユーザーが決めたこと」「コードで確認できる事実」「まだ聞く必要があること」を混ぜずに固定すること。ソースやManualを変更しない。

必読対象:
- doc/requirements/01_自動トレードシステム要件定義書_v2.html §14
- doc/requirements/01_自動トレードシステム要件定義書_v3.htmlのP5R AC／REQ／Gate
- plan/Phase5R_実行計画書_v0.1_2026-08-16.md
- doc/phase5R/02_実装詳細設計/01_P5R実装詳細設計書.html
- doc/phase5R/06_完了/01_P5R完了判定・P6引渡し.html
- doc/phase5R/07_運用手順/00_バックテスト操作手順書作成ルール.html
- doc/phase5R/07_運用手順/01_バックテスト手順書.html
- ui/mock/src/P5RBacktestScreen.tsx、ui/mock/src/backtestApi.ts
- src/autotrade/application/backtest_product.py、http_server.py、history_catalog.py、storage_paths.py
- src/autotrade/backtest/runner.py
- scripts/phase5_external_data/run_binance_data_vision.py、run_binance_quality.py
- 関連する既存Test

次を行う。
1. source timeframe、derived timeframe、strategy timeframe、display timeframeを別欄にした現状表を作る。
2. `15m/30m/1h/4h/1d`、`1m source only`、`30m新規選択`をCONFIRMEDとして記録する。既存1m／M30保存物の扱いはOPENのまま残す。
3. v2の`REQ-V2-0027`、`REQ-V2-0028`、`REQ-V2-0035`、v3の`REQ-V3-0113`、`REQ-V3-0114`、`REQ-V3-0117`、P5R-ACと、今回の5種類時間足／Data／取消／削除要求の競合を明示する。`旧Requirement ID / 新P5R2 Requirement ID / 競合内容 / 変更理由 / 既存M30・1mの履歴扱い / Acceptance`の表を作り、M30選択を除外した初期解釈を訂正した履歴と、保存済みデータのlegacy方針を分ける。
4. 取消APIは存在するがactiveRunだけに接続されていること、履歴行と結果サマリーには対象Run操作がないこと、delete契約が存在しないことを分ける。
5. P5の外部取得Runnerは固定Run用であり、そのまま任意UI Jobへ公開できない安全境界を記録する。
6. 現行Manualの1m記述、取消導線、機能一覧、画像、Evidence追跡の改訂箇所を列挙する。
7. `P5R2-REQ-*`、`P5R2-UNK-*`、既存REQ-V2/V3、画面、API、保存、Test、Manualの初期traceを作る。
8. 推測で行番号を固定せず、実ファイル上のpathと現在のsymbol／見出しを証拠にする。

正式成果物P5R2-ART-01を作り、doc/index.htmlへP5R2の「要件調査中」導線を追加する。実装状態を改善済みと書かない。Critical/Highの事実誤認があれば閉鎖するまでP5R2-02へ進まない。
```

### P5R2-02 — 要件ヒアリング Round 1を実施する

```text
step_id=P5R2-02。開始条件はP5R2-H0承認とP5R2-ART-01の事実レビュー完了。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（JSON path／model／reasoning_effortは共通実行契約の完全名表どおり）。Skillはautotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

目的は、ユーザーが既に決めた要求を聞き直さず、後続設計を分岐させる重要事項だけを回答可能な形で聞くこと。このStepは対話Stepであり、回答を推測して一回で完了しない。

最初に、確定済みの次の理解を短く提示する。
- 利用者選択時間足は15m/30m/1h/4h/1dの5種類。
- 1mは内部sourceであり、利用者の戦略時間足ではない。
- UI Data download／使用可能Data一覧が必要。
- Run一覧・進捗・結果サマリーで取消／削除が必要。
- 01_バックテスト手順書を追従改訂する。

Round 1は最大10問とし、Q-TF-01〜06、Q-HD-01〜04を優先する。ただし既に会話または正式文書で回答済みなら質問せず、回答根拠を示して記録する。各質問に2〜3個の相互排他的な選択肢、推奨案、理由、回答で変わる成果物を付ける。自由記述も許容する。

回答受領後に次を記録する。
1. user_answer_verbatim: ユーザー原文。
2. normalized_decision: 実装可能な一文。
3. status: CONFIRMED / PROVISIONAL / OPEN / CONFLICT。
4. affected_ids: Requirement、AC、UI、API、Persistence、Test、Manual。
5. follow_up_needed: 追加質問と理由。
6. safety_effect: 外部I/O、Secret、費用、削除、監査への影響。

正式成果物P5R2-ART-02へ追記する。ただしRound 1だけでHREQ候補にしない。回答がない項目はOPENのままにし、回答済みと偽らない。最後にRound 2へ渡す未決事項を重要度順に最大8件へ絞る。
```

### P5R2-03 — Round 2以降で矛盾、異常系、削除境界を閉じる

```text
step_id=P5R2-03。開始条件はP5R2-02の回答記録があること。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（JSON path／model／reasoning_effortは共通実行契約の完全名表どおり）。Skillはautotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_phase_execution_planning_v0_1、autotrade_skill_orchestration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

目的は、Round 1回答から発生した分岐と、正常系だけでは決められない異常系を閉じ、要件candidateを書ける状態にすること。

次を行う。
1. 回答間、v2/v3、P5R2確定要求、既存Core／Storageの競合を表にする。
2. Q-HD-05〜12、Q-RUN-01〜09、Q-AUDIT-01、Q-DOC-01〜02から未解消項目だけを最大8問ずつ質問する。
3. 時間足について、1 Runの選択単位、UTC anchor、period境界、partial/missing、legacy 1m/M30、比較可能性を具体例で確認する。
4. Historical Dataについて、DownloadJob IDとDataSet IDを分離し、request、見積、確認、QUEUED/RUNNING/SUCCEEDED/FAILED/CANCELLED、PARTIAL成果物、retry、新version、quality、usable、disabled、Trashを状態遷移表へする。PARTIAL／FAILED／CANCELLEDの成果物を使用可能Dataへ昇格させない。
5. Runについて、各状態×各画面×取消／削除の可否表を作る。SUCCEEDED／FAILED／CANCELLEDだけでなく、RECOVERY_REQUIRED、LEGACY_RESULT_ONLY、Sweep親／子、PARTIAL_FAILED、CSV生成中、比較中、Holdout参照中、競合更新、二重押下、API再起動中、削除途中失敗を含める。
6. 削除対象をresult、catalog、rows、CSV、checkpoint、compare selection、holdout、sweep、audit tombstone、test evidenceに分ける。対象不明のままcascadeを許可しない。
7. Manualについて、新機能一覧、操作手順、成功条件、失敗・復旧、用語、desktop/mobile画像、Test／Registry追跡の必要数を候補化する。
8. Download開始／確認／取消／失敗／再試行、Data usable昇格、Run取消、delete要求／拒否／成功／失敗／cascadeの監査対象を決め、操作者、理由、対象ID、旧状態、新状態、依存物件数を最低項目として確認する。
9. 各決定からGiven/When/Then形式のAcceptanceと、拒否すべきnegative caseを作り、ユーザーへ最終確認する。

対話はHREQ前に閉じるblocking Unknownが0になるまで必要なRoundを繰り返す。1 Roundは最大8問。回答を得られない重要事項は、推奨案で勝手に閉じずP5R2_REQUIREMENTS_BLOCKEDとして停止する。実credential、実費用上限、実対象期間などDATA-G1／DELETE-G1で決めてもlocal要件の安全性を損なわない事項だけは、owner、期限、停止範囲、解消Evidenceを付けてLater Gate表へ送る。

Exit条件:
- TF/HD/RUN/DOC/AUDITのHREQ-blocking Unknownが0。DATA-G1／DELETE-G1へ送った実行時事項はLater Gate表で明示されている。
- 状態遷移、削除境界、外部I/O、Manual改訂範囲が回答済み。
- user answerと正規化決定に未説明の差がない。
- v2/v3から変える要件に変更理由がある。
```

### P5R2-04 — 要件v4 candidate、追跡表、Manual改訂要件を作る

```text
step_id=P5R2-04。開始条件はP5R2-03 Exit条件の成立。P5R2-HREQはまだ未承認。

CoordinatorはAutoTradeProject_DesignDocSet_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A81_DesignDocSetWriter_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（各gpt-5.6-luna、A80/A95 low）。Skillはautotrade_skill_design_doc_set_writer_v0_1、source_reader、traceability、html_doc_writer、design_review、red_team_review、revision_integration、protected_hash_policy_guardを使う。

目的は、承認済みと偽らないv4 candidateと、実装判断を残さない粒度のP5R2要求を作ること。ソース、Test、Manual本体は変更しない。

次を行う。
1. v3を上書きせず、plan/phase5R2/requirements/drafts/にv4 candidateを作る。
2. ロードマップをP5R→P5R2→P6へ変更し、P5R旧完了、P5R2現在状態、P6停止条件を記載する。
3. 時間足を15m/30m/1h/4h/1dへ統一し、1m sourceと既存保存物のlegacy扱いを別属性・履歴として説明する。`REQ-V2-0027/0028/0035`、`REQ-V3-0113/0114/0117`、P5R-AC、新P5R2 Requirementの対応表を収容する。
4. Historical Data Download JobとData Set Catalogを別ID・別状態として、quality／usable状態、provider Adapter、外部I/O／Secret／費用GateをShall、Reason、Input、Processing、Output、Exception、Stop、Recovery、Persistence、Acceptanceへ分解する。PARTIAL／FAILED／CANCELLEDのJob成果物をusable DataSetへ昇格させない。
5. Run取消／削除を状態、画面、API、idempotency、競合、dependency、Trash、audit、Recoveryへ分解する。RECOVERY_REQUIRED、LEGACY_RESULT_ONLY、Sweep親／子、PARTIAL_FAILED、CSV、比較、Holdout依存を含む完全状態表を要求する。
6. Download開始／確認／取消／失敗／再試行、Data usable昇格、Run取消、delete要求／拒否／成功／失敗／cascadeの監査Requirementを作り、操作者、理由、対象ID、旧／新状態、依存物件数を最低項目にする。
7. P5R2-ART-03を作り、REQ→AC→UI→API→Persistence→Test→Evidence→Manualを追跡する。Test名は候補であり未実装と表示する。
8. P5R2-ART-04を作り、01_バックテスト手順書の改訂対象を、機能一覧、画面見取り図、時間足選択、Data取得、Data一覧、Download取消／再試行、Run取消／削除、失敗・復旧、用語、画像、Evidence、改訂履歴に分ける。
9. Manual本体に存在する`Spot / 1m / UTC`、BT-MAN-07、履歴・比較、保存先、安全境界の変更箇所をtraceする。実装前に画面名や画像を確定したと偽らない。
10. providerが確定しH0で公式read-only調査が承認されている場合だけ、autotrade_skill_official_research_v0_1を使い、公式一次情報のURLと確認日を記録する。Data取得、login、API callはしない。未承認なら実接続条件をDATA-G1へ残す。
11. 統合台帳へHREQ未承認、H1未承認、DATA-G1未承認、DELETE-G1未承認、H2未承認、残Unknownを同期する。candidateを現在正本と表示しない。

Acceptance:
- 確定したユーザー回答が全てRequirement／ACへ変換される。
- 推奨案とユーザー決定を混同しない。
- 取消と削除、RunとData、sourceとstrategy timeframeを混同しない。
- HREQで閉じる設計要件と、DATA-G1／DELETE-G1で決める実行時事項を混同しない。
- DownloadJobとDataSetのID／状態／昇格条件、全変更操作のauditが要件化される。
- Manual改訂が「最後に文言だけ直す」扱いではなく、Test／画像／状態／失敗系を含む。
- 管理hash経路を再導入しない。
```

### P5R2-05 — 要件candidateを独立レビューし、Critical／Highを閉じる

```text
step_id=P5R2-05。開始条件はP5R2-04成果物が揃っていること。

CoordinatorはAutoTradeProject_DesignDocSet_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A81_DesignDocSetWriter_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（JSON path／model／reasoning_effortは共通実行契約の完全名表どおり）。Skillはautotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_source_reader_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。A90はFindings first、A95は静的policy判定を独立出力する。AgentはこのStepではcandidateを直接編集せず、review findingを返す。

レビュー観点:
1. User request coverage: 5種類の時間足、Data download／一覧、2画面の取消／削除、Manual改訂が欠けていないか。
2. Semantic split: 1m source／4 strategy timeframe、取消／削除、logical／physical delete、Data Job／Backtest Runが分離されているか。
3. State safety: 状態別操作、idempotency、二重操作、競合、部分失敗、再起動、復旧がfail-closedか。
4. Deletion safety: 実行中削除、依存物孤児化、path traversal、任意パス、Evidence消去、監査消去を許していないか。
5. External boundary: provider host、redirect、proxy、Secret、entitlement、費用、容量、通信、Data利用条件がGate前に実行可能になっていないか。
6. Time correctness: UTC anchor、closed bar、partial bar、欠損、future data、period boundary、compare identityが曖昧でないか。
7. Manual fidelity: UI実装前に未実装機能を「できる」と書く計画になっていないか。desktop/mobile、axe、assert先行画像、追跡があるか。
8. Traceability: user answer→REQ→AC→UI/API/DB→Test→Manualが切れていないか。
9. Phase boundary: P6、Broker、Paper、Live、実資金へ越境していないか。
10. A95: 管理hash、document checksum、receipt fingerprint、manifest stale、retry hashを完了条件にしていないか。直接保護対象hashは目的と停止範囲が限定されているか。

各FindingはID、severity、該当path／section、問題、事故シナリオ、必要修正、閉鎖Evidenceを持つ。Critical／Highが1件でもOPENならP5R2-06のHREQ packetを完成扱いにしない。Medium／Lowも採否と理由を残す。review結果とruntime receiptをplan/phase5R2/ログ/へ保存する。

A90とA95の実agent出力が取得できない場合、rootの自己レビューは参考Findingとして残してよいが、独立レビュー完了とはしない。`REVIEW_RUNTIME_BLOCKED / independent=false`としてP5R2-06のHREQ packet完成を停止する。
```

### P5R2-06 — レビューを統合し、HREQ承認packetを作る

```text
step_id=P5R2-06。開始条件はP5R2-05 reviewの受領。

CoordinatorはAutoTradeProject_DesignDocSet_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A81_DesignDocSetWriter_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（JSON path／model／reasoning_effortは共通実行契約の完全名表どおり）。Skillはautotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_red_team_review_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

目的は、review findingをcandidateへ反映し、ユーザーが承認可否を判断できるHREQ packetを作ること。HREQを自動承認せず、v4を正式公開しない。

次を行う。
1. FindingごとにADOPT / PARTIAL / REJECTを決め、理由と変更箇所を記録する。Critical／HighのREJECTは原則停止し、人の判断が必要ならHuman Gateへ送る。
2. v4 candidate、P5R2-ART-02/03/04、Unknown、Gate、ロードマップ、Manual改訂要件を同じ現在状態へ揃える。
3. A90を再起動して再レビューし、Critical／High=0を確認する。A90/A95の実agent出力がなく自己レビューだけの場合はindependent=falseを維持し、HREQ承認依頼へ進まずREVIEW_RUNTIME_BLOCKEDで停止する。
4. A95で静的再判定し、ALLOW / NEEDS_HUMAN_GATE / BLOCKEDを記録する。hash値は作らない。
5. HREQ packetに、確定要求、旧v3からの差分、ユーザー回答、削除境界、外部I/O境界、残Unknown、後続計画が変わる点、Manual改訂表、非対象を入れる。
6. v4 candidateはCANDIDATE / NOT_CURRENTの表示を維持する。
7. 統合台帳のP5R2-HREQをUNAPPROVEDのまま更新し、承認対象pathと再開条件を記載する。

Exit条件:
- Critical／High=0。
- HREQ-blocking Unknown=0。DATA-G1／DELETE-G1に送った実行時事項は、owner、期限、停止範囲、再開Evidence付きで残る。
- user answerと要件差分が1対1で追える。
- Manual改訂要件がP5R2-H2の必須Acceptanceに含まれる。

最後に「P5R2-HREQを承認します。要件v4を正式化し、P5R2-07で後続実行計画を再作成してください。」という明示文の判断を求める。曖昧な「続けて」を承認へ読み替えない。
```

### P5R2-06A — HREQ承認済み要件をv4として正式公開する

```text
step_id=P5R2-06A。開始条件はユーザーのP5R2-HREQ明示承認。未承認なら何も正式公開せず停止する。

CoordinatorはAutoTradeProject_DesignDocSet_Orchestrator_v0_1（.codex/orchestrators/AutoTradeProject_DesignDocSet_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A81_DesignDocSetWriter_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（JSON path／model／reasoning_effortは共通実行契約の完全名表どおり）。Skillはautotrade_skill_design_doc_set_writer_v0_1、autotrade_skill_traceability_v0_1、autotrade_skill_html_doc_writer_v0_1、autotrade_skill_revision_integration_v0_1、autotrade_skill_design_review_v0_1、autotrade_skill_protected_hash_policy_guard_v0_1を使う。

次を行う。
1. 承認されたcandidateと承認時の差分が一致することを非hashのpath／version／section／状態で確認する。
2. doc/requirements/01_自動トレードシステム要件定義書_v4.htmlとして公開し、v3をHISTORY / SUPERSEDED_BY_V4として保持する。v3を削除・上書きしない。v3からv4、v4からv3の相互リンク、Requirement差分表、P5R-H2のP6引渡しを履歴へ変更した理由、P5R2-06Aの変更履歴を必須にする。
3. P5R2-ART-01〜04を正式HTMLとして完成し、doc/index.htmlに要件v4とP5R2要件成果物の導線を追加する。v4 candidateはHREQ packet／正式P5R2成果物から`CANDIDATE / NOT_CURRENT`として辿れるようにし、doc/indexの現在正本欄へcandidateを置かない。
4. 統合台帳全体を検索し、P5R2-HREQ承認、v4現在正本、P6停止、P5R旧完了履歴、P5R2-H1/DATA-G1/H2未承認を整合させる。
5. Manual本体はまだ変更しない。P5R2-ART-04を改訂の正本入力としてリンクする。
6. HTMLのtitle、lang、見出し、表caption、相対リンク、ローカルasset、UTF-8、Secret、状態、Requirement ID重複を検査する。
7. A95静的判定を通し、管理hash経路がないことを確認する。

Exit条件は、v4と追加したP5R2正式HTMLが全てindexから到達可能で、v3↔v4の履歴・差分導線があり、台帳・v4・P5R2計画に現在状態の矛盾がなく、実装は未開始のままであること。
```

## 12. 要件確定後に後続計画を再編し、最終StepまでのPromptを追加する超詳細Prompt

### P5R2-07 — 実行計画v0.2を再作成する

```text
step_id=P5R2-07。これは計画改訂Stepであり、実装Stepではない。開始条件はP5R2-HREQ承認、P5R2-06A完了、要件v4の正式公開。条件未達なら実装計画を確定せず停止する。

CoordinatorはAutoTradePhasePlanning_Orchestrator_v0_1（.codex/orchestrators/AutoTradePhasePlanning_Orchestrator_v0_1.json、model=gpt-5.6-terra）。AgentはAutoTrade_A05_PhaseExecutionPlanner_v0_1、AutoTrade_A10_RequirementsCurator_v0_1、AutoTrade_A80_DocumentIntegrator_v0_1、AutoTrade_A90_DesignReviewer_v0_1、AutoTrade_A95_ProtectedHashPolicyGuardian_v0_1（各model=gpt-5.6-luna、A80/A95 reasoning_effort=low）。必要部品の再利用判断では、既存Orchestrator／Agent／Skill JSONを読むが、このStepでAI部品を作成・変更しない。変更が必要なら、実在するAutoTradeComponentLifecycle_Orchestrator_v0_1（.codex/orchestrators/AutoTradeComponentLifecycle_Orchestrator_v0_1.json）を使う別実行Stepを計画内に追加する。JSON実体を確認できなければ部品名を推測せず停止する。

必須Skill:
- autotrade_skill_phase_execution_planning_v0_1
- autotrade_skill_source_reader_v0_1
- autotrade_skill_traceability_v0_1
- autotrade_skill_orchestration_v0_1
- autotrade_skill_design_review_v0_1
- autotrade_skill_red_team_review_v0_1
- autotrade_skill_revision_integration_v0_1
- autotrade_skill_protected_hash_policy_guard_v0_1

必読入力:
1. 正式要件v4とP5R2-ART-01〜04。
2. P5R2-HREQ承認記録、回答台帳、review finding、採否表、残Unknown。
3. このv0.1計画と実行済みP5R2-00〜06Aログ。完了Stepを未実行へ戻さない。
4. P5Rの詳細設計、実装、Test、Manual作成ルール、完了・recovery成果物。
5. 現行UI/API/Application/Core/Storage/P5 external runner/Test全体。
6. trusted scope、quality gate、WSL実行入口、Evidence配置ルール。
7. 使用候補のOrchestrator／Agent／Skill JSON。modelとreasoning_effortはJSONを正本とする。

作業:
1. 確定Requirementごとに、変更対象module、API、永続化、UI、state、Test、Manual、Evidence、Gateを割り当てる。
2. 既存部品で再利用可能なものと、責務不足でComponentLifecycleが必要なものを分ける。名前があるだけで適合と判断しない。
3. 実装前の詳細設計Stepを、時間足、Historical Data Job／Catalog、Run取消／削除、共通Persistence／Migration／Securityへ分ける。実装者が判断を残さない型、endpoint、schema、sequence、exception、transaction、recovery、test tableを必須にする。
4. RED-first Stepを置き、state matrix、boundary、idempotency、concurrency、partial failure、restart、path traversal、external egress、Secret、cost、dependency、legacy migration、Manual E2Eを先に失敗させる。
5. P5R2-H1を、詳細設計、RED、target_paths、固定command、fixture、Run ID、Evidence root、host outbound isolation、外部I/O非実行範囲の承認Gateとして置く。
6. 実装Stepは少なくとも次の能力単位を検討し、確定要件に応じて統合／分割する。
   a. timeframe contract／aggregation／preflight／comparison／legacy表示。
   b. Historical Data request／download job／provider adapter／catalog／quality／usable state／retry。
   c. Run list・progress・summaryの対象Run取消、delete／Trash／dependency／audit。
   d. UI integration、responsive、keyboard、focus、axe、error recovery。
   e. 既存01_バックテスト手順書の改訂、実画面assert先行スクリーンショット、Registry、機能→手順→Test→Evidence追跡。
7. 外部接続を実装するlocal dummy／fake provider試験と、実providerへ接続するP5R2-DATA-G1を別Step・別Run ID・別Evidenceにする。DATA-G1前はnetwork 0、Secret 0、費用0を維持する。
8. Data／Run削除試験は一時fixtureだけで行い、既存実Data、既存Run、tests/evidenceを削除しない。P5R2-DELETE-G1を独立Stepとして置き、対象、依存、Trash、保持、復元、audit、実Dataを使う受入範囲を明示承認するまで破壊的操作を行わない。
9. `01_バックテスト手順書`改訂を独立Stepとして後回しにせず、UI E2E／visual／a11yと結合する。本文だけで操作できること、実装されていない機能を書かないこと、旧1m説明を現在仕様として残さないことをAcceptanceにする。
10. 最終統合レビュー、Security review、Python／UI code review、Manual fidelity review、Critical／High閉鎖、P5R2-H2 packet、P6再引渡しを順番に置く。
11. 各Stepについて、目的、開始条件、Human Gate、担当Orchestrator／Agent／Skill完全名、JSON path、固定model、runtime dispatch、対象path、非対象path、実行command、成果物、Acceptance、negative test、停止条件、rollback／recovery、次Step入力を含む「そのまま実行できるPrompt」を全文作る。
12. 実際に存在するtool、script、test command、pathだけを使用する。未作成のものは作成Stepを先に置く。未確認commandを固定Quality Gateと呼ばない。
13. すべてのPromptに、Gate未承認時の停止、fallback receipt、管理hash禁止、Git処理、統合台帳／index同期を含める。
14. DAG、並列可否、Human Gate表、Unknown解消表、Requirement coverage、Manual coverage、P6引渡し条件を作る。
15. v0.1を上書きせず、plan/Phase5R2_実行計画書_v0.2_<date>.mdを新規作成する。v0.1は要件確定前の履歴、v0.2は現在の実行入口と明記する。
16. doc/index.htmlと統合台帳の計画リンク・現在状態をv0.2へ更新する。ただしP5R2-H1、DATA-G1、H2を承認済みにしない。

計画v0.2の直接実行性Acceptance:
- 未実施の全Stepについて、開始条件、Gate、共通契約と連結済みの完全なPrompt、対象path、非対象path、実在command、成果物、Acceptance、negative test、停止条件、rollback／recovery、次Step入力が1件も欠けていない。
- 「検討する」「必要に応じて分割する」という骨格だけをPrompt完成と数えない。
- 最終StepであるP5R2-H2承認後の完了判定・P6再引渡しまで、途中欠番なく全文Promptがある。
- 各PromptのAgent／Skillは完全名、JSON path、固定modelを持ち、runtime receiptとfallback時の停止範囲がある。

計画v0.2の最低Step骨格:
- 詳細設計入力・AI部品再利用判定
- 必要ならAI部品ComponentLifecycle
- 実装詳細設計と専門レビュー／改訂／再レビュー
- RED・Golden・failure injection・quality scope設計
- P5R2-H1
- quality scope登録
- RED作成
- timeframe実装
- Historical Data Job／Catalog実装
- Run取消／削除実装
- local統合・回帰・migration／recovery
- P5R2-DATA-G1 packet
- 承認時だけ実provider受入
- P5R2-DELETE-G1 packet
- UI E2E／visual／a11y
- 01_バックテスト手順書改訂と実画像
- 統合レビュー、Security／Code review、改訂、再試験
- P5R2-H2 packet
- H2承認後の完了判定とP6再引渡し

レビュー:
- A90がFindings firstで計画のCritical／Highを出す。
- A95が管理hash再導入を静的監査する。
- A05がDAG、Gate、各Promptの直接実行性を再検査する。
- A10がRequirement coverageと回答反映を再検査する。
- A80が正式成果物、Manual、doc/index、統合台帳、履歴導線を再検査する。
- Findingを改訂し再レビューする。Critical／High=0になるまでv0.2を現在入口にしない。

このStepではソース実装、Test実行、Playwright、外部接続、Data／Run削除を行わない。成果物は計画v0.2、計画差分、runtime receipt、review記録、更新済みindex／統合台帳だけである。
```

## 13. P5R2-07で詳細化する暫定後続骨格

| 暫定区分 | 目的 | 現時点で固定しないもの |
|---|---|---|
| Design | 時間足、Data Job/Catalog、Run取消／削除、Storage／Migrationを実装可能な粒度へする。 | endpoint名、schema、file path、migration方式 |
| RED / Quality | 正常・異常・競合・復旧・Security・UI・Manualの失敗を先に固定する。 | Test件数、Run ID、target scope、command |
| H1 | 設計とlocal実装範囲を人が承認する。 | 承認対象は確定要件と設計から生成 |
| Implementation | Core再利用を守りつつAPI／UI／Persistenceを実装する。 | Step分割、担当Agent、追加AI部品 |
| DATA-G1 | provider外部接続の範囲を別承認する。 | provider、symbol、期間、費用、Secretはヒアリング結果に従う |
| UI / Manual | 全操作を実画面で検証し、既存Manualを改訂する。 | 画面名、BT-MAN番号、画像数 |
| Final | Critical／Highを閉鎖し、H2後にP6へ再引渡しする。 | 完了日、Evidence Run、残Unknown |

## 14. `01_バックテスト手順書`改訂計画

### 14.1 改訂対象

正式な改訂対象は`doc/phase5R/07_運用手順/01_バックテスト手順書.html`であり、改訂前の正本版は文書meta・改訂履歴・doc/index.htmlが一致する`v0.5`である。P5R2要件だけを別手順書へ分断せず、既存の起動、保存、Single Run、Sweep、履歴、比較、CSV、Holdout、Walk-forward、再起動復旧と統合する。

必要に応じて、`00_バックテスト操作手順書作成ルール.html`も、Data Download Job、Data Catalog、削除確認、Trash／復旧、危険操作の画像規則を追加する。ただしルール変更が不要なら、変更しない理由をP5R2-ART-04へ残す。

### 14.2 必須改訂項目

| 区分 | 必須内容 | 完了証拠 |
|---|---|---|
| Scope | `Spot / 1m / UTC`を利用者選択Scopeとして残さず、5種類の戦略時間足と1m sourceの違いを説明する。 | UI文言との照合、静的検索 |
| 条件入力 | 15m／30m／1h／4h／1dの選択、期間境界、Data利用可否、Preflight停止理由。 | desktop/mobile Playwright |
| Data取得 | provider、symbol、期間、見積／確認、開始、進捗、取消、失敗、再試行、品質確認。 | Job状態別E2E |
| Data一覧 | 使用可能／品質未確認／失敗／無効／削除待ち等の状態と、Backtestで使える条件。 | Catalog table E2E、a11y |
| Run取消 | 一覧・進捗・結果サマリーから対象Runを取消し、CANCELLED／checkpoint／再開可否を確認する。 | 画面別E2E、対象Run ID assert |
| Run削除 | 状態別可否、確認dialog、依存物、Trash／復旧、削除後の一覧・詳細・比較・CSV挙動。 | negative／recovery E2E |
| 失敗・復旧 | 外部通信失敗、Data欠損、partial bar、二重操作、削除競合、API再起動を平易に説明する。 | failure injection結果 |
| 安全境界 | Data downloadは注文ではない、削除対象、Evidence非削除、Broker／Paper／Live非対象を明記する。 | Manual review |
| 画像 | 本文assert成功後の実画面、desktop/mobile、alt、caption、Registry、Evidence link。 | capture registry、重大axe 0 |
| 追跡 | BT-F→BT-MAN→REQ/AC→Playwright test→画像→Evidenceを双方向に辿れる。 | link／anchor／coverage検査 |
| 履歴 | 文書version、改訂日、P5R2変更理由、旧1m説明の履歴扱い。 | 改訂履歴表 |

旧1m記述は現在の操作章から除き、P5R時点の履歴として明示した変更履歴から参照可能にする。現行仕様のstrategy timeframe定義は一箇所を正本にし、source 1mとの違いをそこから各操作へリンクする。

### 14.3 Manualの停止条件

- UIやAPIに存在しない操作を「できる」と書く。
- 取消と削除を同じ意味で説明する。
- 1mを選択可能な戦略時間足として残す。
- Dataの品質未確認状態を使用可能と説明する。
- 実行中Runの物理削除やTest Evidence削除を手順化する。
- assert前の画像、古い画面、外部CDN asset、リンク切れを採用する。
- Manual本文だけでは成功・失敗・復旧を判断できない。

## 15. このv0.1計画のAcceptance

| ID | Acceptance |
|---|---|
| `P5R2-PLAN-AC-01` | ユーザーが明示した4領域をatomicな確定Requirement 8件として記録し、Manual改訂も含む。 |
| `P5R2-PLAN-AC-02` | 15m/30m/1h/4h/1dと1m source、既存1m／M30保存物の扱いの違いが明確である。 |
| `P5R2-PLAN-AC-03` | ヒアリング質問が選択肢、推奨案、影響範囲を持ち、既回答を聞き直さない。 |
| `P5R2-PLAN-AC-04` | 要件修正までのP5R2-00〜06Aに直接実行Prompt、Gate、成果物、停止条件がある。 |
| `P5R2-PLAN-AC-05` | P5R2-07に、確定要件から計画を再編し最終StepまでのPromptを作る自己完結したPromptがある。 |
| `P5R2-PLAN-AC-06` | 01_バックテスト手順書の改訂対象、受入、画像、追跡、停止条件が独立して定義されている。 |
| `P5R2-PLAN-AC-07` | 外部I/O、Secret、費用、実削除、P6開始が未承認のまま実行されない。 |
| `P5R2-PLAN-AC-08` | 管理hash経路を再導入せず、保護対象hashだけを目的限定で扱う。 |
| `P5R2-PLAN-AC-09` | P5R旧完了履歴を保持し、現在のP5R2計画とP6停止条件を統合台帳・indexへ同期する。 |
| `P5R2-PLAN-AC-10` | v2/v3の具体Requirement IDとP5R2要件の競合・変更理由・legacy・Acceptanceを表で追跡するPromptがある。 |
| `P5R2-PLAN-AC-11` | HREQ前に閉じるUnknownとDATA-G1／DELETE-G1で決める実行時事項を分離する。 |
| `P5R2-PLAN-AC-12` | P5R2-07が、最終Stepまでの各Prompt全文と直接実行性の欠落0をAcceptanceにする。 |

## 16. 次のHuman action

この計画の作成時点ではP5R2-H0承認ではなかったが、ユーザーが次の文を明示したため、P5R2-H0を承認済みとして記録する。P5R2-01を実行し、ART-01レビュー後にP5R2-02の要件ヒアリングへ進んだ。Round 1の全10問は記録済みで、Q-TF-06はユーザー回答Aにより確定した。残るHigh指摘と追加UnknownはP5R2-03で閉じる。

```text
P5R2-H0を承認します。要件ヒアリングを開始してください。
```


## 17. P5R2-03実行結果・Round 2質問packet（2026-08-21）

P5R2-03は、root-direct fallbackによるread-only設計・要件・red-teamレビューと、Round 2質問packet作成まで完了した。ユーザー回答が未取得のため、状態は `P5R2-03_ROUND2_WAITING_USER` とする。P5R2-04、P5R2-HREQ、実装、test subprocess、Playwright、外部Data取得、Secret、費用、実削除、P6には進まない。

### 17.1 Runtime受領

- Coordinator `AutoTradePhasePlanning_Orchestrator_v0_1` は `01a0228c-cc91-7cd3-bd04-95b2f3a738de` で起動・完了したが、Coordinator内部のnested child spawn／waitは利用できなかった。
- nested child 5件は `not_started / agent_id=N/A / independent=false / review_mode=SELF_REVIEW_FALLBACK` として扱う。未起動を独立完了とは扱わない。
- root-direct fallbackではA05、A10、A80、A90、A95を固定model `gpt-5.6-luna` で個別spawn／waitし、read-only結果を受領した。詳細は `plan/phase5R2/ログ/runtime-receipt-P5R2-03.md/json` を参照する。
- A95は `NEEDS_HUMAN_GATE`。`P5R2-UNK-HD-004`を維持し、管理用hash、manifest、fingerprint、stale、checksum、hash retryは追加しない。

### 17.2 Findings first

1. **High：Q-TF-05に記録矛盾がある。** ユーザー回答「5. C」と、ART-02の「欠損1mを含む上位足は補間する方向性」が一致しない。Q-TF-05は `CONFLICT` とし、Q-R2-02で再確認する。
2. **High：TF-04の表示・確認契約が未確定。** 指定終了時刻、有効終了時刻、確認操作、UTC表示、開始より前・有効期間ゼロ、Run保存項目が未確定である。
3. **High：TF-05の品質・usable契約が未確定。** 欠損範囲、始端・終端、補間の表示、future参照禁止、provenance、再現性、使用不可条件が未確定である。
4. **High：HD-02/HD-04の入力・Provider境界が未確定。** 任意symbolの意味、Catalog外拒否、market、host、期間、容量、費用、範囲外停止が未確定である。
5. **High：DownloadJob/DataSetの状態分離とRun取消・削除のfail-closed契約が未確定。** 状態競合、依存、復旧、Trash、監査、二重操作、途中失敗を確定していない。
6. **Medium：01_バックテスト手順書は要件確定前に変更しない。** 現行v0.5は履歴として保持し、実装済み操作だけをP5R2-04以降で改訂する。

### 17.3 Round 2質問（推奨案は未回答・未確定）

各問は `OPEN`。回答は `Q-R2-01=A` のように回答する。自由記述も可とする。

#### Q-R2-01：指定終了時刻と有効終了時刻の表示・確認

- A：指定終了時刻と切下げ後の有効終了時刻を並べて表示し、実行前に確認ダイアログを出す。推奨。
- B：両方を表示するが、確認操作は不要。
- C：時間足境界でない終了時刻は入力エラーとして拒否する。
- 影響：`P5R2-REQ-TF-001`、Preflight、Single Backtest、API、Test、Manual。

#### Q-R2-02：Q-TF-05の欠損1mと補間

- A：補間せず、欠損を含む上位足は生成失敗（`PARTIAL_BAR_REJECTED`）とする。
- B：連続した限定欠損だけ補間し、品質警告付きで使用可能にできる。
- C：補間は一覧・調査表示だけに使い、補間を含むDataSetは常に `PARTIAL / unusable` とする。推奨。
- 影響：`P5R2-UNK-TF-004`、`P5R2-REQ-TF-002`、Quality、usable、provenance、look-ahead防止、再現性、Test、Manual。

#### Q-R2-03：任意symbolの入力境界

- A：Provider Catalogから対応済みSpot symbolだけを選択し、自由入力は不可とする。推奨。
- B：Catalog選択に加え、形式検証済みの自由入力を許可する。
- C：任意文字列を受け付ける。
- 影響：`P5R2-REQ-HD-001/002`、`P5R2-UNK-HD-002`、Catalog、入力検証、監査、DATA-G1。

#### Q-R2-04：DownloadJobとDataSetの状態契約

- A：DownloadJobとDataSetを別ID・別状態で管理する。Jobの `PARTIAL / FAILED / CANCELLED` はDataSetを `USABLE` に昇格させず、再試行は新Jobとする。推奨。
- B：JobとDataSetを同一レコード・同一状態で管理する。
- C：Job成功時点で品質確認なしにDataSetを使用可能にする。
- 影響：`P5R2-REQ-HD-001/002`、API、Persistence、Catalog、生成、品質、provenance、取消、再試行、Test。

#### Q-R2-05：同一DataとData Catalogの更新

- A：同一source identityはskipし、修正版は新versionとして登録し、既存Dataをin-place上書きしない。推奨。
- B：常に既存Dataを上書き更新する。
- C：重複を許可し、利用者が個別に選ぶ。
- 影響：Data一覧、usable、Run再現性、version、重複防止、復旧、Manual、Test。

#### Q-R2-06：Run取消の状態・画面・競合

- A：`QUEUED / RUNNING`だけ取消可能とし、実行一覧・進捗・結果サマリーの3画面で同じ判定を使う。二重押下は同一操作として扱い、terminal、`RECOVERY_REQUIRED`、`LEGACY_RESULT_ONLY` は理由付きで取消不可とする。推奨。
- B：進捗画面だけ取消可能とする。
- C：terminal状態にも取消ボタンを表示し、取消可能とする。
- 影響：`P5R2-REQ-RUN-001/002`、実行一覧、進捗、結果サマリー、API、状態遷移、Sweep、復旧、監査、Test、Manual。

#### Q-R2-07：Run削除の対象・依存・復旧

- A：`SUCCEEDED / FAILED / CANCELLED`だけ削除要求可とする。mutableなresult、rows、CSV、checkpoint、比較選択はTrash対象、catalogはtombstoneを残す。Sweep親子、比較、CSV Job、Holdout参照など依存中は拒否し、初期Scopeでcascade不可とする。`LEGACY_RESULT_ONLY` は閲覧専用とする。推奨。
- B：依存一覧を表示し、利用者が明示選択した対象だけcascade可能とする。
- C：result、catalog、関連物を即時完全削除する。
- 影響：result、catalog、rows、CSV、checkpoint、compare、Holdout、Sweep、復旧、`P5R2-DELETE-G1`、Test、Manual。

#### Q-R2-08：監査と01_バックテスト手順書改訂範囲

- A：Download開始・確認・取消・失敗・再試行、DataSet usable昇格、Run取消、削除要求・拒否・成功・失敗を監査する。操作者、理由、対象ID、旧状態、新状態、依存物件数を記録し、手順書には実装済みの操作だけを成功・失敗・復旧・Trash・legacy閲覧専用とともに掲載する。推奨。
- B：成功した取消・削除だけを監査し、手順書は別文書として扱う。
- C：監査と手順書の範囲は実装後に決める。
- 影響：Audit persistence、Security、`P5R2-UNK-DOC-001`、`doc/phase5R/07_運用手順/01_バックテスト手順書.html`、Manual、画像、Test追跡。

### 17.4 質問ID・Unknown・成果物の対応

| 質問 | 主な元ID | 主な影響 |
|---|---|---|
| Q-R2-01 | Q-TF-04、`P5R2-UNK-TF-003` | `P5R2-REQ-TF-001`、Preflight、Manual、Test |
| Q-R2-02 | Q-TF-05、`P5R2-UNK-TF-004` | `P5R2-REQ-TF-002`、Quality、usable、provenance、Test |
| Q-R2-03 | Q-HD-02、`P5R2-UNK-HD-002` | `P5R2-REQ-HD-001/002`、Catalog、入力境界、DATA-G1 |
| Q-R2-04 | Q-TF-02、Q-HD-01/03、`P5R2-UNK-TF-002` | DownloadJob、DataSet、状態、再試行、品質 |
| Q-R2-05 | Q-TF-02、Q-HD-02、`P5R2-UNK-HD-002` | Data Catalog、version、再現性、更新 |
| Q-R2-06 | `P5R2-UNK-RUN-001` | Run一覧、進捗、結果サマリー、取消、監査 |
| Q-R2-07 | `P5R2-UNK-RUN-002`、`P5R2-UNK-HD-003` | 削除対象、依存、Trash、復旧、DELETE-G1 |
| Q-R2-08 | `P5R2-UNK-DOC-001`、Q-AUDIT-01 | 監査、手順書、Manual、Test追跡 |

### 17.5 Later Gateと停止境界

- `P5R2-DATA-G1`：実Provider host、実symbol範囲、期間・容量・費用上限、通信、Secret、実download。
- `P5R2-DELETE-G1`：実Data／実Runの削除対象、保持期間、purge可否、復元運用。test evidenceとaudit tombstoneは削除対象にしない。
- `P5R2-UNK-HD-004`：Provider配布物の整合確認に保護対象hashを使う要否。用途・直接因果・失敗時停止範囲が未確定のため `NEEDS_HUMAN_GATE`。

Round 2の回答が揃うまで、P5R2-03は `P5R2-03_ROUND2_WAITING_USER` とする。P5R2-04、P5R2-HREQ、H1、DATA-G1、DELETE-G1、H2、実装、test subprocess、Playwright、外部I/O、Secret、費用、実削除、P6へ進まない。
