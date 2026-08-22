# P5R2-08 要件入力・coverage

状態: `READ_ONLY_INPUT / P5R2-HREQ_APPROVED / P5R2-H1_APPROVED_BY_DELEGATED_AUTHORITY`。これは入力整理成果物の現在同期状態であり、P5R2-08作成時点のH1未承認という履歴はログへ保持する。根拠は `AT-REQ-004 v4.0`、`P5R2-PLAN-002 v0.2`、P5R/P5R2のHTML・既存ソース・UI・Test・Manualである。P5Rの完了は履歴であり、P5R2の未実装要件を完了扱いにしない。

## 4領域・8 atomic Requirement

|領域|atomic Requirement|下位Requirement|既存入口（read-only根拠）|設計入力・後続Step|Manual / Gate|
|---|---|---|---|---|---|
|時間足|`P5R2-CREQ-TF-001`|TF-001, TF-004|`backtest_product.py` と `backtestApi.ts` は現在1m固定|戦略足の選択・UTC/closed barをP5R2-09で設計、P5R2-13で実装候補|Manual改訂はP5R2-22。H1前は変更不可|
|時間足|`P5R2-CREQ-TF-002`|TF-002, TF-005, TF-006|`timeframe_aggregator.py`、`market_data/quality.py`、`preflight.py`|source/derived、補間、生成遷移、qualityをP5R2-09で設計し、P5R2-13／14／22でlocal確認|`P5R2-UNK-TF-004/006` はH1判断済み、H2 review|
|時間足|`P5R2-CREQ-TF-003`|TF-003, TF-004|`history_catalog.py`、`backtest_product.py` は既存Run復元を保持|legacy表示と指定/有効期間の分離をP5R2-09で設計|Manual P5R2-22、H1|
|Historical Data|`P5R2-CREQ-HD-001`|HD-001, HD-002|`job_service.py`、`persistence.py`、`market_data/acquisition_protocol.py`|Download/Generation Jobを別契約としてP5R2-09、local実装はP5R2-14|DATA-G1前は候補・local fake providerだけ。外部I/O禁止|
|Historical Data|`P5R2-CREQ-HD-002`|HD-003〜HD-007|`catalog_resolver.py`、`quality.py`、`persistence.py`|Catalog/identity/coverage/promotion/recoveryをP5R2-09で設計|`P5R2-UNK-TF-004/006`、DATA-G1、H1|
|Backtest Run操作|`P5R2-CREQ-RUN-001`|RUN-001, RUN-002|`BacktestProductService.cancel_run`、`RunStatusCard`、`MetadataStore.cancel_job`|3画面共通cancel判定とOperationGuardをP5R2-09、P5R2-15で実装候補|H1。terminal取消は状態不変・監査|
|Backtest Run操作|`P5R2-CREQ-RUN-002`|RUN-003, RUN-004|`result_view.py`、`storage_paths.py`、CSV Job処理|ResultArtifact/CSV registry/許可root/TOCTOUをP5R2-09で設計|DELETE-G1前に実削除なし。CSV、Data、Run、Audit、Evidenceを保護|
|手順書|`P5R2-CREQ-DOC-001`|AUDIT-001, DOC-001, GATE-001|`doc/phase5R/07_運用手順/01_バックテスト手順書.html`|実装済み・検証済み操作だけをP5R2-22で改訂|H2前に現行P5R Manualを未実装仕様へ更新しない|

## P5R旧完了とP5R2現行の分離

|区分|扱い|
|---|---|
|P5R旧完了|P5R-H2、1m local read-only Backtest、既存Run復元、CSV Job、既存Manual v0.5、既存Evidenceは履歴として保持する。|
|P5R2現行|時間足是正、source/derived Data、Data Catalog/Job、merge/replace、3画面取消、terminal ResultArtifact削除、監査、Manual追従を新規要件として扱う。|
|混同禁止|P5RのTest/Evidence/ManualはP5R2 Acceptanceの証明ではない。P5R2-H1前にソース、Test subprocess、Playwright、外部I/O、Secret、費用、実削除を行わない。|

## Unknown と停止境界

|ID|決定期限・owner|停止範囲|Evidence先|
|---|---|---|---|
|`P5R2-UNK-TF-004`|H1判断済み、P5R2-13 local evidence、H2 review。owner: P5R2詳細設計責任者＋root承認者|候補外Dataのusable昇格・Run入力を禁止|`doc/requirements/01_自動トレードシステム要件定義書_v4.html`、P5R2-13 GREEN、P5R2-22 Manual evidence、P5R2-H1 packet|
|`P5R2-UNK-TF-006`|H1判断済み、P5R2-13／14／22 local evidence、H2 review。owner: P5R2詳細設計責任者＋root承認者|sourceなし・品質未承認の既定期間表示・送信を禁止|同v4、P5R2-13／14 GREEN、P5R2-22 Manual evidence、P5R2-H1 packet|
|`P5R2-UNK-QG-001`|RESOLVED_LOCAL / EXTERNAL_SEPARATE。P5R2-12／18 local evidenceで確認済み|External Runのhost-level isolation未確認をlocal Gateへ読み替えない|`scripts/wsl_quality_gate/run_test.ps1`、`scripts/quality_gate/trusted_scopes.json`、P5R2-12／18 quality成果物|
|`P5R2-UNK-QG-002`|RESOLVED_LOCAL_READONLY。P5R2-12／18で既存protected fixtureをread-only確認済み|identity置換、管理用hash新設、未確認fixtureのPass扱いを禁止|trusted scopes、P5R2-H1 packet、P5R2-12／18 Evidence|

UnknownはPassではない。期限までに決まらない場合は、該当する実装・Test・Gateを止める。
