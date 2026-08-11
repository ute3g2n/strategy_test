# 自動トレードシステム要件定義書v2 断片F03：Backtest・検証結果（章19〜22）

| 項目 | 内容 |
|---|---|
| Document set ID | `AT-REQ-V2-SET-001` |
| Fragment | `F03` |
| Step | `RQV2-07` |
| 状態 | `DRAFT_BODY`（章19〜22の要求本文candidate） |
| 作成日 | 2026-08-11 |
| 編集所有権 | F03のみ。章19〜22を正本とし、F02のData／Strategy／Unitを参照する。 |
| 正本入力 | `RQU-20`章19〜22、RQV2-01〜06成果物、固定Core基準線、RQU-17A／18A |
| 画面リンク | `SCREEN-08`〜`SCREEN-12`、既存UC／State／E2E追跡 |
| 安全境界 | 外部取得、Broker、Secret、Paper注文、Live注文、Core本体変更は行わない。 |

> 単一設定Backtestとパラメータ網羅検証は別の実行形態である。固定Coreのsynthetic／fixture契約は実市場の長期性能・利益性・Paper／Live承認を意味しない。

## 19. 単一設定Backtest

### 19.1 入力と事前検査

単一Backtestは、銘柄、期間、時間足、Strategy Variant、Strategy／Config Version、Data Manifest、初期資金、Risk入力、手数料、滑り、Gap、Roll、Calendar、Long／Short、Holdout／Walk-forward条件を一つのRun入力として扱う。UI、JSON、YAMLは同じ型付きモデルへ変換し、入力値・単位・版・差分を開始前に表示する。Riskは全Modeで入力有無を確認するが、Q-247の現行例外に従い、Risk値の範囲・項目間整合性を本断片で自動検査しない。

事前検査は、必須不足、余分項目、型違い、通常パラメータの範囲、期間、Data Quality、未来参照、Calendar、Config Version、Manifest、重複Runの扱いを明示する。入力エラーは全件表示し、該当入力へ戻れる。検査不合格のRunはQueueへ入れず、開始しない。

### 19.2 実行・進捗・取消・失敗

開始前に、銘柄・期間・時間足・設定・Data状態・Risk入力・Manifestを一画面で確認する。開始後は`Validating`、`Queued`、`Running`、`Pausing`、`Paused`、`Cancelling`、`Cancelled`、`Completed`、`Failed`、`Stopped`、`Recovery Required`を表示する。進捗、経過、現在Bar、次の判断時刻、処理済み件数、停止理由、ログ・EvidenceをRunへ紐付ける。

取消と停止は別にする。Queue待機中の取消は実行前に取り消し、実行中の取消は安全なcheckpointで止めて中途結果を参考用として保存する。入力不正、Manifest不一致、未来参照、Data Quality不良は再試行せず失敗とする。再試行可能な一時失敗はF02の10／30／60秒・最大3回規則へ従う。

### 19.3 計算・結果・Evidence

処理順、確定足、Signal時刻、仮想約定、費用、滑り、Gap、Roll、Position更新、損益計算、反対Signalの順序をManifestとResultへ保存する。最低限、総損益、最大の落ち込み、取引回数、勝率、総残高を表示する。Chartは価格、Entry、追加、Stop、Exit、Signal、Position、損益を同一時間軸で参照でき、取引・Signal・設定・Data・ログ・Evidenceへリンクする。

### REQ-V2-0044 単一Backtestの入力を一意に固定する

- Shall: システムは、単一Backtest開始前に銘柄、期間、時間足、Strategy／Config Version、Data Manifest、初期資金、Risk入力、費用、滑り、Gap、Roll、Calendarを一意のRun入力として確定しなければならない。
- Source: RQU-20 §19.1〜19.2、RQV2-06、Q-31、Q-149、Q-262〜Q-263
- Reason: 実行条件の欠落・後変更・再現不能を防ぐため。
- Assumptions: Riskは入力有無だけを確認するQ-247例外を適用する。
- Inputs: UI／JSON／YAML設定、Data、Strategy、Config、Manifest、Risk。
- Processing: 型・範囲・版・Quality・期間・未来参照・Calendarを検査する。
- Outputs: 検査結果、固定Run入力、開始可否、エラー位置。
- Exceptions: 必須欠落、余分、型違い、版不一致、Data不良は開始拒否する。
- Stop: Manifestまたは主要条件が不明なままQueueへ投入する場合。
- Recovery: 入力を修正し、全件の事前検査を再実行する。
- Persistence: 入力、差分、Manifest、hash、検査結果、操作を保存する。
- Acceptance: UI／JSON／YAMLの同じ内容が同じ型付きRun入力になり、開始前に全値を確認できること。
- Implementation status: `IMPLEMENTED_VERIFIED`（固定Replay入力範囲）／UI統合は`NOT_IMPLEMENTED`
- Target phase: Phase 4以降のBacktest UI／Run実装
- Traceability: Q-31、Q-114、Q-149、Q-261、Q-262、UC-V2-024、UC-V2-025、SCREEN-08

### REQ-V2-0045 単一Backtestの開始・進捗・停止を記録する

- Shall: システムは、単一Backtestの開始前確認、Queue、進捗、取消、停止、失敗、再実行、完了、EvidenceをRun状態と画面状態へ反映しなければならない。
- Source: RQU-20 §19.3、Q-34、Q-35、Q-104、RQV2-06 Run／Job／Queue
- Reason: 実行中の状態と結果を利用者が確認し、安全に取消・復旧するため。
- Assumptions: 外部副作用のないBacktestでも、長時間処理・資源制御・保存失敗を扱う。
- Inputs: Run、Job、Queue、進捗、停止・取消操作、Resource State。
- Processing: 状態遷移、checkpoint、部分結果、エラー、再試行可否を管理する。
- Outputs: 進捗、現在状態、停止Reason、次操作、Evidenceリンク。
- Exceptions: 保存失敗、資源不足、処理Error、取消競合は状態を分けて記録する。
- Stop: 状態が不明、checkpointが破損、取消後に処理継続を確認できない場合。
- Recovery: 既知のcheckpointから再開または新Runとして再実行する。
- Persistence: Run／Job状態、時刻、進捗、checkpoint、ログ、Evidenceを保存する。
- Acceptance: 正常・取消・停止・失敗・再実行を画面と機械記録で区別できること。
- Implementation status: `IMPLEMENTED_VERIFIED`（固定Run契約）／UI・長時間Workerは`NOT_IMPLEMENTED`
- Target phase: Phase 4以降のExecution／UI／Ops
- Traceability: Q-34、Q-35、Q-104、Q-109、UC-V2-026〜029、SCREEN-09、SCREEN-17

### REQ-V2-0046 単一Backtestの5指標と根拠を表示する

- Shall: システムは、単一Backtestの結果として総損益、最大の落ち込み、取引回数、勝率、総残高を定義済みの単位・期間・丸めで表示し、Chart・取引・Signal・設定・Data・Evidenceへ戻れるようにしなければならない。
- Source: RQU-20 §19.4、Q-38、Q-73、Q-74、Q-82、RQV2-05／06
- Reason: 主要指標だけを見て計算条件や取引明細を誤解しないため。
- Assumptions: 収益性の保証・自動採用は行わない。
- Inputs: Fill、Cost、Position、Price、設定、期間、Data Manifest。
- Processing: 指標を同じRun入力と処理順で計算し、欠損・未完了を表示する。
- Outputs: 5指標、Chart、取引明細、Signal説明、停止・未完了状態。
- Exceptions: 中途結果、失敗Run、欠損期間は完了結果と区別する。
- Stop: 主要入力・処理順・単位が不明な結果を完了として表示する場合。
- Recovery: Manifest・ログ・計算版を照合し、再計算または未完了表示へ戻す。
- Persistence: 指標、単位、丸め、期間、Result Version、hash、Evidenceを保存する。
- Acceptance: 固定fixtureで5指標と許容差を再現し、結果から根拠へ遷移できること。
- Implementation status: `IMPLEMENTED_VERIFIED`（固定synthetic／fixture範囲）
- Target phase: Phase 4以降のResult UI／Replay Gate
- Traceability: Q-38、Q-73、Q-74、UC-V2-030、UC-V2-034、UC-V2-035、SCREEN-10、SCREEN-11

## 20. パラメータ網羅検証

### 20.1 入力範囲と組合せ展開

網羅検証は、複数のパラメータ候補を全組合せへ展開して一つずつ実行する。パラメータごとに固定値、下限、上限、変更単位、型、小数桁、丸め、重複値排除、適用条件を入力する。上限は必ず含め、最後のstep幅が変わる場合も生成値と件数を表示する。条件付きパラメータが無効な組合せは、黙って除外せず、非実行理由を残す。

### 20.2 開始前確認とQueue

開始前に、全組合せ数、実行可能件数、無効件数、見込み時間、見込み容量、Resource State、Queue優先度を表示し、運用者が明示確認するまで開始しない。固定の論理上限は設けないが、実PCの負荷に応じて警告・待機・開始拒否・停止する。網羅検証のJobは単一Backtestと別のRun／Job／Result構造を持つ。

### 20.3 部分失敗・取消・再開

一組合せ処理ごとにcheckpointを保存する。個別失敗を記録して次へ進める条件と、全体を止める条件を分ける。取消・停止・異常終了後は、完了、失敗、取消、未実行、要確認を表へ残し、checkpointとManifestが一致する場合だけ再開する。失敗組合せだけの再試行は、新しいJobまたはRunとして記録する。

### REQ-V2-0047 網羅検証の範囲・型・上限包含を固定する

- Shall: システムは、各パラメータの固定値・下限・上限・変更単位・型・丸め・適用条件を検査し、生成値へ上限を必ず含め、無効組合せを理由付きで残さなければならない。
- Source: RQU-20 §20.1〜20.2、Q-103、Q-105〜Q-108、Q-260
- Reason: 組合せ数・実行範囲・小数丸めの曖昧さで検証結果を再現できなくなることを防ぐため。
- Assumptions: 固定の論理上限は置かず、Resource Stateで開始可否を制御する。
- Inputs: Parameter Schema、固定値、範囲、step、型、条件、丸め規則。
- Processing: 値生成、重複排除、上限包含、条件評価、組合せ数算出を行う。
- Outputs: 値一覧、組合せ一覧、無効理由、件数、見込み時間・容量。
- Exceptions: 下限>上限、step不正、型不一致、丸め衝突、条件矛盾は開始拒否する。
- Stop: 組合せ定義が不明、上限が欠落、無効組合せを隠す場合。
- Recovery: Schemaを修正し、全組合せを再展開して確認する。
- Persistence: Schema版、生成値、丸め、組合せhash、無効理由、確認を保存する。
- Acceptance: 上限包含、最後のstep幅、重複値除去、無効行表示を固定ケースで確認すること。
- Implementation status: `NOT_IMPLEMENTED`
- Target phase: Phase 4以降のSweep／Validation
- Traceability: Q-103、Q-105〜Q-108、Q-260、UC-V2-024、UC-V2-025、UC-V2-033、SCREEN-08、SCREEN-09

### REQ-V2-0048 網羅検証の開始前に件数と負荷を確認する

- Shall: システムは、網羅検証の開始前に全組合せ数、実行可能・無効件数、予想時間、予想容量、Resource State、Queue状態を表示し、運用者の明示確認なしに開始してはならない。
- Source: RQU-20 §20.2、Q-102〜Q-104、Q-157、Q-244、Q-282
- Reason: 大量処理を無意識に開始せず、実時間運用を圧迫しないため。
- Assumptions: 予想値は推定であり、完了時間を保証しない。
- Inputs: 組合せ一覧、過去Run、Resource、優先度、実時間Unit。
- Processing: 件数・見込みを算出し、警告、Queue、開始可否を決める。
- Outputs: 確認Dialog、開始／待機／拒否状態、予想値。
- Exceptions: 見込み算出不能、Resource取得不能、実時間処理の優先度不明は開始不可。
- Stop: 確認前開始、実時間優先違反、容量不足を検出した場合。
- Recovery: Queueへ待機、条件縮小、Resource回復、運用者確認後に再評価する。
- Persistence: 件数、見込み、Resource、警告、確認、Queue判定を保存する。
- Acceptance: 件数・無効行・予想値・確認・開始拒否の全経路が表示されること。
- Implementation status: `NOT_IMPLEMENTED`
- Target phase: Phase 4以降のSweep／Ops性能Gate
- Traceability: Q-102、Q-103、Q-104、Q-157、Q-244、Q-282、UC-V2-027、SCREEN-09、SCREEN-02

### REQ-V2-0049 網羅結果を全組合せ単位で保存する

- Shall: システムは、網羅検証の全組合せについて、総損益、最大の落ち込み、取引回数、勝率、総残高、状態、設定値、Run／Job／Manifest／Evidenceを一行単位で保存しなければならない。
- Source: RQU-20 §20.4、Q-38、Q-40、Q-42、Q-73、Q-80
- Reason: 完了・無効・失敗・取消の行を含む全結果を比較・監査できるようにするため。
- Assumptions: 最良値をシステムが自動採用しない。
- Inputs: 組合せ、単一Run結果、Status、Metrics、Manifest、Error。
- Processing: 組合せ行を作り、結果・未実行・失敗・取消を状態付きで集約する。
- Outputs: 全件表、Chart、Filter、Sort、Detail、CSV Job。
- Exceptions: 部分結果、計算不能、途中停止は完了結果と別状態にする。
- Stop: 失敗・無効行を削除して全件完了と表示する場合。
- Recovery: Job・checkpoint・ログから欠落行を再構築する。
- Persistence: 全行、状態、指標、設定、Run、操作、出力hashを保存する。
- Acceptance: 5指標を全件表示し、状態・設定・詳細・Evidenceへ遷移できること。
- Implementation status: `IMPLEMENTED_VERIFIED`（固定結果契約）／大量表・CSVは`NOT_IMPLEMENTED`
- Target phase: Phase 4以降のSweep／Result UI
- Traceability: Q-38、Q-40、Q-73、Q-80、UC-V2-030〜034、UC-V2-061、SCREEN-10〜12

### REQ-V2-0050 網羅検証の取消・失敗・再開を区別する

- Shall: システムは、網羅検証の個別失敗、全体停止、取消、未実行、要確認、checkpointからの再開を別状態で保存し、個別失敗を次の組合せへ進める条件と全体停止条件を明示しなければならない。
- Source: RQU-20 §20.3、Q-109、Q-112、Q-114、Q-221、Q-222
- Reason: 部分失敗を成功・未実行・自動再試行と誤解しないため。
- Assumptions: 再試行不可ErrorはF02／F03のFailure Catalogへ接続する。
- Inputs: Job、組合せ、Error、停止／取消、checkpoint、Resource。
- Processing: 個別・全体状態、次処理可否、再開位置、再試行上限を判定する。
- Outputs: 状態表、途中結果、理由、再開ボタン、再試行Job。
- Exceptions: checkpoint破損、Manifest不一致、組合せ順不明は再開不可とする。
- Stop: 失敗行を削除、再開位置を推測、全体完了と誤表示する場合。
- Recovery: 安全なcheckpointまたは新Runから明示的に再実行する。
- Persistence: 組合せ状態、Error、checkpoint、再試行、操作、Evidenceを保存する。
- Acceptance: 個別失敗継続、全体停止、取消、再開、失敗行再試行を別テストで確認すること。
- Implementation status: `NOT_IMPLEMENTED`
- Target phase: Phase 4以降のSweep Worker／Ops
- Traceability: Q-109、Q-112、Q-114、Q-221、Q-222、UC-V2-028、UC-V2-029、UC-V2-035

## 21. Backtest結果、分析、比較、報告

### 21.1 単一Runと全件表

単一Runは主要数値を上部、Chartと判断線を中央、取引・Signal・Position明細を下部に表示する。網羅検証は全組合せを行形式で表示し、並べ替え、絞込み、ページングまたは仮想化、詳細遷移、CSV全件出力を持つ。UI上の「最新結果」は選択中の表示ポインタであり、過去Run・設定版・操作記録・結果ファイルを削除しない。

### 21.2 比較と自動採用禁止

Run比較は、期間、Data Manifest、Strategy／Config Version、Timeframe、Instrument、費用、滑り、Calendar、Modeを横並びにし、比較可能・比較不能を表示する。運用者が採否メモを入力できるが、システムは「最良設定」を自動採用しない。採否はResultの数値と別のHuman／運用判断記録とする。

### REQ-V2-0051 同条件Runの最新表示と内部履歴を分離する

- Shall: システムは、同一条件の再Runを警告・停止せずに許可し、通常表示では最新結果を示しながら、過去の設定版、Run、ログ、Result、操作記録、Evidenceを内部保持しなければならない。
- Source: RQU-20 §21.3〜21.4、Q-115、Q-147、Q-250、RQV2-06 REQ-V2-0043
- Reason: 再現性の比較と画面の見やすさを両立し、上書きで監査履歴を失わないため。
- Assumptions: 画面からの非表示・論理削除・物理削除はF05で定義する。
- Inputs: Run条件、Manifest、Result Version、既存履歴、表示選択。
- Processing: 新Runを別IDで保存し、最新ポインタだけを更新する。
- Outputs: 最新Result、履歴一覧、比較・詳細リンク、重複なし警告。
- Exceptions: 条件差分がある場合は同条件でなく、差分を表示する。
- Stop: 最新表示の更新で履歴を物理削除・変更する場合。
- Recovery: 内部履歴から最新ポインタと画面表示を再構築する。
- Persistence: Run／Result Version、Manifest、ポインタ、hash、操作を保存する。
- Acceptance: 同一条件2回以上のRunを全履歴と最新表示の双方で確認できること。
- Implementation status: `NOT_IMPLEMENTED`
- Target phase: Phase 4以降のResult／Persistence／UI
- Traceability: Q-115、Q-147、Q-250、UC-V2-032、UC-V2-034、UC-V2-061、SCREEN-10、SCREEN-12

### REQ-V2-0052 比較可能条件を明示する

- Shall: システムは、Run比較時にData、期間、Timeframe、Instrument、Strategy／Config Version、費用、Calendar、Modeが同一か差分かを表示し、比較不能なRunを同じ順位表へ混在させてはならない。
- Source: RQU-20 §21.3、Q-40、Q-80、Q-115、RQU-18A Q-250
- Reason: 異なる入力・期間・Dataを数値だけで比較して採否を誤ることを防ぐため。
- Assumptions: 比較不能でも履歴参照・差分確認は可能とする。
- Inputs: Run Manifest、Result、Filter、比較対象。
- Processing: 共通条件を照合し、差分と比較可否を算出する。
- Outputs: 比較表、差分、比較可能／不能ラベル、採否メモ欄。
- Exceptions: Manifest欠落、版不明、期間重複不明は比較不能とする。
- Stop: 比較不能Runを同一条件として最良選択へ流用する場合。
- Recovery: Manifestを補完または比較対象を分けて再表示する。
- Persistence: 比較条件、差分、採否メモ、操作、Evidenceを保存する。
- Acceptance: 同一条件・異条件・期間重複・Data版違いの比較表示を確認できること。
- Implementation status: `NOT_IMPLEMENTED`
- Target phase: Phase 4以降のResult／Analysis UI
- Traceability: Q-40、Q-80、Q-115、UC-V2-031、UC-V2-032、UC-V2-035、SCREEN-10〜12

### REQ-V2-0053 大量表と全件CSVを非同期化する

- Shall: システムは、網羅結果の大量表を並べ替え・絞込み・詳細遷移できる形で表示し、全件CSV出力を非同期Jobとして進捗・取消・失敗・ファイルhash付きで処理しなければならない。
- Source: RQU-20 §20.4、§21.2〜21.4、Q-44、Q-73、Q-147、Q-152、Q-238
- Reason: 長時間出力や大量行でUIを停止させず、出力結果を監査可能にするため。
- Assumptions: 表部品と具体性能はRQV2-09／後続技術Gateで選定する。
- Inputs: Result rows、Filter、Sort、Export request、列定義、時刻・小数・欠損規則。
- Processing: 表示用ページング／仮想化、CSV Job、進捗、取消、hash生成を行う。
- Outputs: 表、詳細、CSV、Job状態、ファイルhash。
- Exceptions: 行欠落、出力失敗、取消、文字コード・単位変換エラーは完了としない。
- Stop: 全件出力が無記録で同期実行され、UI・Queueを占有する場合。
- Recovery: Job checkpointまたは新しいExport Jobで再生成する。
- Persistence: Filter、Sort、列定義、入力Result、出力、hash、操作を保存する。
- Acceptance: 大量結果を絞込み・詳細表示し、全件CSVを非同期で完了・失敗・取消まで追跡できること。
- Implementation status: `NOT_IMPLEMENTED`
- Target phase: Phase 4以降のResult／UI／Worker
- Traceability: Q-44、Q-73、Q-147、Q-152、Q-238、UC-V2-031、UC-V2-034、UC-V2-065、SCREEN-10〜12

## 22. 検証期間分割、Holdout、Walk-forward

### 22.1 期間と役割

学習・調整期間、Holdout期間、Walk-forward窓、Forward期間を別属性とする。期間は手動指定または規則指定で生成し、開始・終了・境界・タイムゾーン・重複・隙間・最低データ量を保存する。Holdoutは設定調整に使わず、Walk-forwardは窓ごとに学習・評価・移動を記録する。

### 22.2 バイアスと再利用禁止

未来データ参照、期間境界の混入、Survivorship bias、同じHoldoutを繰り返し調整へ使うこと、結果を見てから期間を都合よく変更することを禁止する。期間不足、Data Quality不良、Calendar不一致は該当窓を未完了・停止として残す。比較結果は運用者が閲覧し、システムが最良設定や将来収益を自動採用しない。

### REQ-V2-0054 Holdout／Walk-forwardの期間境界を保存する

- Shall: システムは、学習・調整・Holdout・Walk-forwardの各期間、窓、境界、タイムゾーン、入力Data／Manifest、設定Versionを保存し、期間の重複・隙間・未来参照を検査しなければならない。
- Source: RQU-20 §22、Q-117、Q-115、Q-262、RQV2-06 Data／Timeframe契約
- Reason: 期間分割を後から都合よく変更せず、比較可能性と再現性を確保するため。
- Assumptions: 最低期間・窓数など具体値は後続Gateで決める。
- Inputs: 期間指定、窓規則、Data、Calendar、Config／Strategy Version。
- Processing: 期間生成、境界検査、重複・隙間・未来参照、窓別Runを作成する。
- Outputs: 期間表、窓別Result、警告、未完了・停止状態、Evidence。
- Exceptions: 期間不足、重複、隙間、未来値、Data不良は窓を完了としない。
- Stop: Holdoutを調整へ再利用、期間境界不明、未来参照を検出した場合。
- Recovery: 期間・Data・Configを固定し、該当窓を再作成または除外理由付きで残す。
- Persistence: 期間、窓、役割、Data／Calendar／Config版、Result、操作、Evidenceを保存する。
- Acceptance: 固定期間のHoldout／Walk-forwardで未来参照拒否と窓別追跡を確認すること。
- Implementation status: `IMPLEMENTED_VERIFIED`（固定synthetic範囲）／長期実データは`LATER_GATE`
- Target phase: Phase 4以降のValidation／Data Gate
- Traceability: Q-117、Q-115、Q-262、UC-V2-033、UC-V2-035、`RQU-UNK-18-01`

### REQ-V2-0055 Holdout結果の再利用を制限する

- Shall: システムは、Holdoutまたは評価窓の結果を設定調整・自動最良選択へ直接再利用せず、再利用要求がある場合は理由・対象・運用者判断・新しいRunを記録しなければならない。
- Source: RQU-20 §22、RQU-20 Findings F-013、Golden／Test Strategy Skill
- Reason: 後知恵による過学習・バイアスを抑え、評価結果の意味を保つため。
- Assumptions: 本要求は投資成果や収益性を保証するものではない。
- Inputs: Holdout Result、設定変更、比較、採否メモ、運用者操作。
- Processing: 評価用途と調整用途を分離し、再利用を警告・Gateへ送る。
- Outputs: 再利用禁止／要確認表示、差分、採否記録、新Run。
- Exceptions: 記録欠落、同一期間再利用、設定差分不明は新規採用不可とする。
- Stop: システムがHoldout最良値を自動採用する場合。
- Recovery: 新しい調整期間・Config Version・Manifestを作成し、別Runへ戻す。
- Persistence: Holdout利用履歴、設定差分、採否、Gate、Result、Evidenceを保存する。
- Acceptance: Holdout結果を見た後の設定変更が自動適用されず、明示記録が必要なこと。
- Implementation status: `NOT_IMPLEMENTED`
- Target phase: Phase 4以降のValidation／Human Gate
- Traceability: Q-117、Q-237〜Q-240、UC-V2-033、UC-V2-032、GATE-V2-HOLDOUT

### 22.3 Core再利用と未実証範囲

| 能力 | Core状態 | 証拠範囲 | 未実証・後続 |
|---|---|---|---|
| Replay、Fill、Cost、Roll、Gap、Calendar、Holdout | `IMPLEMENTED_VERIFIED` | 固定synthetic・fixture、契約、snapshot／restore、look-ahead拒否 | 市場別実測Cost／Slippage、正式Calendar、長期Holdout |
| Turtle Strategy、Signal、Golden | `IMPLEMENTED_VERIFIED` | 固定入力・期待値・回帰Guard | 未検証パラメータ、利益性、Live注文 |
| Engine adapter／LEAN PoC | `IMPLEMENTED_VERIFIED`（PoC） | offline候補比較・Core parity・固定Run | 最終Engine採用、Paper・Live接続 |
| UI、Job Queue、大量組合せ、長期データ | `NOT_IMPLEMENTED`／`LATER_GATE` | 要件・既存モック・固定証拠を入力にする | 実装、負荷、長期・外部実証 |

### 22.4 F03レビュー記録

| 観点 | 確認結果 |
|---|---|
| 単一／網羅分離 | 別章・別REQ・別受入条件として記載 |
| 入力／事前検査 | UI／JSON／YAML、Manifest、Risk例外、期間、Qualityを記載 |
| 網羅範囲 | 下限・上限・step・型・上限包含・無効組合せ・件数・Queueを記載 |
| 5指標 | 総損益、最大の落ち込み、取引回数、勝率、総残高を単一・全件へ定義 |
| 同条件Run | 最新表示と内部履歴を分離し、重複停止しない方針を記載 |
| Holdout | 期間境界、未来参照、再利用禁止、窓別証拠を記載 |
| Screen／UC | SCREEN-08〜12、UC-V2-024〜035へ接続 |
| Core状態 | 固定synthetic／PoC範囲とUI・大量・長期・外部未実証を分離 |
| 外部I/O・実装 | 変更・実行0件 |

### 22.5 Findings first

| Finding ID | 重大度 | 指摘 | 対応 |
|---|---|---|---|
| `RQV2-07-F-001` | High | 単一Backtestと網羅検証の入力・結果・再開を混ぜると、全件結果の欠落と受入漏れが起きる。 | 別REQ・別Run／Job・別表・別受入条件へ分離した。 |
| `RQV2-07-F-002` | High | 上限包含、丸め、無効組合せ、部分失敗が曖昧だと結果件数を再現できない。 | Schema、生成規則、無効理由、全件保存、checkpointを固定した。 |
| `RQV2-07-F-003` | High | Holdout結果を見た後の設定再利用が後知恵・バイアスになる。 | 自動採用を禁止し、期間・Config・運用者判断・新Runを分離した。 |
| `RQV2-07-F-004` | Medium | 固定CoreのReplay／PoC証拠を大量表・長期Data・UI Workerへ一般化できない。 | Core状態表で固定範囲と未実証範囲を分けた。 |

**RQV2-07判定: `COMPLETE_WITH_SEPARATE_BACKTEST_SWEEP_AND_HOLDOUT_CONTRACT`。** 単一Backtestと網羅検証、5指標、同条件Run、Holdout／Walk-forward、停止・再開・Evidenceを記載した。RQV2-08はF04（章23〜30）だけを編集対象として開始する。

### 22.6 変更履歴

| 日付 | 版 | 内容 |
|---|---|---|
| 2026-08-11 | v0.1 | RQV2-07で章19〜22を本文candidate化。単一・網羅Backtest、5指標、比較、同条件Run、Holdout／Walk-forward、固定Core範囲と未実証範囲を記載した。 |
