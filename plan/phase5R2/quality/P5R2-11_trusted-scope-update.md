# P5R2-11 trusted scope更新ログ

## 更新日

2026-08-22

## 更新対象

- `scripts/quality_gate/trusted_scopes.json`
- `scripts/wsl_quality_gate/run_test.ps1`
- `scripts/wsl_quality_gate/run_isolated_p2.ps1`
- `scripts/wsl_quality_gate/run_isolated_p2.sh`

## 更新内容

1. `RUN-P5R2-11-LOCAL-001`を`phase5R2`、`P5R2-11`、`target_only`で登録した。
2. H1 packetの許可pathだけをtargetへ登録し、`.env`系、文書・計画、外部依存、Secret、既存Evidenceをexcludedへ登録した。
3. Evidence rootを`tests/evidence/phase5R2/RUN-P5R2-11-LOCAL-001/`として登録した。これは後続runnerの書込み先であり、P5R2-11では作成していない。
4. 既存`RUN-P5R-03-20260816-001.fixture`のpath/name/versionと、既存recordに登録済みのprotected checksumをread-only参照として登録した。新しいchecksum・hashの再計算はしていない。失敗時はBLOCKEDとし、retryしない。
5. 固定4 Gateをformatter→lint→type→testの順で登録した。UI build/unit/PlaywrightはP5R2-19の別Stepとした。
6. 初期登録時はP5R2-UNK-QG-001/002を`unknowns`に残し、scope登録済みでもEvidence未生成・P5R2-12前確認待ちとした。
7. 初期登録時は`execution_allowed=false`を明記し、P5R2-11からの誤実行をfail-closedにした。

## Namespace互換

旧`phase[0-9]+`制約を、既存の`phase2`／`phase3`／`phase5`／`phase5R`と新しい`phase5R2`を受ける形へ最小変更した。PowerShell wrapperのEvidence phase小文字化を止め、既存`phase5R`の大文字pathを保持する。

## 未実行

`run_test.ps1`、`run_isolated_p2.ps1`、`run_isolated_p2.sh`、WSL、pytest、test subprocess、Playwright、npm、外部network、Secret、実Data、物理削除は実行していない。

## 停止条件

P5R2-12でhost outbound isolation、既存protected identityとの接続、Evidence root、固定Gate templateが確認できない場合は`QUALITY_GATE_BLOCKED`とする。UnknownをPassへ変更しない。

## P5R2-12 preflight後の状態更新（2026-08-22）

P5R2-12の固定入口preflightで、WSL2 `networkingMode=none`、default routeなし、外向きNICなしをEvidence化した。既存protected fixtureのpath/name/versionと記録済みprotected checksumも一致した。`phase5R2` namespaceとP5R2専用固定pytest入口（application／backtest／market_data／phase5R）を確認した。

この確認を根拠に、P5R2-UNK-QG-001/002をtrusted scope／Run Manifestの実行ブロックUnknownから除外し、`execution_allowed=true`、`registration_status=EXECUTION_ENABLED_HOST_ISOLATION_AND_FIXTURE_CONFIRMED`へ更新した。P5R2-12のREDテスト、固定4 GateのPass、P5R2完了、DATA-G1、DELETE-G1、H2、P6開始を意味しない。

## P5R2-12 RED実行後の現在状態（2026-08-22）

後続P5R2-12で同じRun IDの固定入口を実行した。formatter／lint／typeはPASS、testは8件のatomic Requirementに対応する未実装契約を検出して期待REDとなった。これはQuality Gate全体のPASSではなく、P5R2-13でGREEN実装へ進むためのRED確認である。DATA-G1、DELETE-G1、H2、P6開始条件は変わらない。

Evidence: `tests/evidence/phase5R2/RUN-P5R2-11-LOCAL-001/P5R2-12_RED.json`
