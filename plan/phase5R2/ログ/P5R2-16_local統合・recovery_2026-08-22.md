# P5R2-16 local統合・migration・restart／recovery 実行ログ

- Step: `P5R2-16`
- Run: `RUN-P5R2-16-LOCAL-001`
- 実行日: 2026-08-23
- 判定: `P5R2-16_GREEN_CONFIRMED`
- 次Step: `P5R2-17`

## 1. 実施範囲

P5R2-13〜15で実装した時間足境界、Historical Data Job／Catalog、Run取消／ResultArtifact guardを、永続化、restart、migration、promotion途中停止、統合recoveryの観点で接続確認した。対象はローカル固定fixtureとlocal fake provider相当のテスト入力だけである。

- 利用者向け時間足: `15m`、`30m`、`1h`、`4h`、`1d`
- legacy内部読取: `1m`。利用者選択肢には表示しない
- 無効な表記: `M30`。利用者向け `30m` と混同しない
- recovery状態: `RECOVERY_REQUIRED` として新規利用・usable表示から隔離
- legacy履歴: 既存P5R履歴を消去・上書きせず、currentと別境界で保持

## 2. 実装・検証結果

| 確認項目 | 結果 | 証拠 |
|---|---|---|
| Job registryのdurable write、再読込、CAS | PASS | `src/autotrade/application/job_service.py`、`tests/phase5R/test_p5r2_local_integration_red.py` |
| staging token、source Job再検証、preview束縛 | PASS | `src/autotrade/application/history_catalog.py`、同テスト |
| promotionのPREPARED／COMMITTEDとcurrent pointer | PASS | `src/autotrade/application/history_catalog.py`、同テスト |
| promotion途中失敗後のcurrent利用不可・recovery隔離 | PASS | 同テストのpromotion interruptionケース |
| Runのdataset参照固定と履歴復元時のCatalog recovery集約 | PASS | `src/autotrade/application/backtest_product.py`、`tests/phase5R/test_backtest_history_recovery.py` |
| OperationGuardのrestart復元、audit衝突拒否、cancel保存失敗rollback | PASS | `src/autotrade/application/run_service.py`、`tests/application/test_p5r2_run_operation_guard.py` |
| CSV出力のroot境界、exclusive tempfile、atomic replace | PASS | `src/autotrade/application/csv_job.py`、`src/autotrade/application/backtest_product.py` |
| Historical Dataのsymlink／reparse／TOCTOU拒否 | PASS | `src/autotrade/application/backtest_product.py`、`tests/phase5R/test_p5r2_local_integration_red.py` |
| 固定4 Gate | PASS | [`verification.json`](../../../tests/evidence/phase5R2/RUN-P5R2-16-LOCAL-001/verification.json) |

Windowsの固定対象pytestは `108 passed in 5.62s`。WSLの同一固定入口でもformatter、lint、type、testの4 GateがPASSし、test Gateは108件を通過した。

## 3. WSL品質Gateの経緯

初回の失敗は隠さず記録した。途中で、固定Gateの承認伝播不足、診断証跡の不足、WSL上のWindowsドライブ前提テストを検出した。各修正後にWindows側を正本としてcommitし、WSL側は `git pull --ff-only` で同期した。最終実行では、委譲済みP5R2 Human Gate権限を明示して公式固定入口を実行し、`state=PASS`、`wrapper_exit_code=0` を確認した。

最終Evidenceのhost isolationは `CONFIRMED`、`networking_mode=none`、外向きrouteなしである。固定Gateの承認はlocal品質範囲だけに適用し、外部Providerや実Data取得の承認とは解釈していない。

## 4. レビューと修正

read-onlyレビューで検出されたHigh相当の論点は、次の修正で閉じた。

- Catalog recovery状態をBacktestProductServiceの復元結果へ集約した。
- STAGEDかつacceptedなJob以外をsourceにできないようにした。
- Job registryをファイルロックと再読込付きCASへ変更した。
- cancel永続化失敗時にメモリ状態をrollbackし、recovery-requiredを返すようにした。
- OperationGuard復元のschema、revision、audit、token、collisionを検証した。
- staging IDのactive再利用を拒否し、完了済みtokenだけの置換を許可した。
- Decimalを含むsource datasetを永続化可能な値へ正規化した。
- CSV、Historical Data、Job、Evidenceのpath境界、symlink／reparse、TOCTOUをfail-closedにした。

実際にread-onlyレビューを行ったagentは、Euclid `01a02af7-bd7c-72c1-b15e-d3835c883e93`、Pascal `01a02af7-e28e-7f91-9607-e54d3fc1f964`、Nietzsche `01a02af7-d10b-7900-9b45-52891533f549`である。指定roster全員の独立dispatchではない。A95 runtime dispatchは成立していないため、A95は静的ポリシー確認のfallbackとして記録し、実行済みとは扱わない。管理用hash、manifest、fingerprint、stale、hash retry、hash receiptは追加していない。

## 5. 境界・未解消事項

このStepで、次の操作は行っていない。

- 外部hostへの接続、login、契約、API call、Data download
- Secretの読取・保存、費用発生
- 実Historical Data、Run、Audit、Evidence、CSVの削除
- Playwright、P6開始

P5R2-DATA-G1、P5R2-DELETE-G1、P5R2-H2は未承認のまま統合台帳に残す。P5R2-17はDATA-G1 packet作成だけを行い、外部I/Oへ進まない。

## 6. 証拠

- [`P5R2-16 GREEN`](../../../tests/evidence/phase5R2/RUN-P5R2-16-LOCAL-001/P5R2-16_local-integration/P5R2-16_GREEN.json)
- [`固定4 Gate`](../../../tests/evidence/phase5R2/RUN-P5R2-16-LOCAL-001/verification.json)
- [`host isolation`](../../../tests/evidence/phase5R2/RUN-P5R2-16-LOCAL-001/host-isolation.json)
- [`runtime receipt`](../quality/runtime-receipt-P5R2-16.json)

## 7. 移行判定

`P5R2-16_GREEN_CONFIRMED`としてP5R2-17 DATA-G1 packet作成へ移行する。これはDATA-G1承認、DELETE-G1承認、H2承認、P5R2完了、P6開始を意味しない。
