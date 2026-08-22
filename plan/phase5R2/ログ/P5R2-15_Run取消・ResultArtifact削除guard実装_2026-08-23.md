# P5R2-15 Run取消・ResultArtifact削除guard実装ログ

## 範囲

- 対象要件：`P5R2-CREQ-RUN-001`、`P5R2-CREQ-RUN-002`
- H1：local実装・固定品質Gateの範囲で承認済み
- DATA-G1：未承認。Provider、login、API call、Data download、Secret、費用は行わない
- DELETE-G1：未承認。実Data、Run、Evidence、監査、CSV、Result Artifactのunlink・tombstone・cascadeは行わない
- P5R2-16：restart、migration、永続Operation監査は後続へ残す
- P5R2-19：実UI、Playwright、a11y、visualは後続へ残す

## TDDと実装

1. `tests/application/test_p5r2_run_operation_red_contract.py` と `tests/phase5R/test_p5r2_result_artifact_red_contract.py` を実装前に実行し、6件のREDを確認した。証跡は `tests/evidence/phase5R2/RUN-P5R2-15-LOCAL-001/P5R2-15_RED.json`。
2. `OperationGuard`を追加し、module contract、RunService、BacktestProductServiceのlocal HTTP経路で共有できるcancel入口を定義した。
3. `QUEUED→CANCELLED`、`RUNNING→STOP_REQUESTED`を状態機械に合わせ、terminal／RECOVERY_REQUIRED／PARTIAL_FAILED／LEGACY_RESULT_ONLYは状態不変＋Auditとした。
4. server-owned Run stateとoperation revisionをBacktestProductServiceからguardへ渡し、呼出元の偽装state／revisionを取消判定へ使わないようにした。同一プロセス内の二重押下、再送、別tab、競合を拒否する。
5. `LocalResultArtifacts.delete_result_artifact`はlogical Artifact IDだけを受け、保護対象・active Run・path安全異常を拒否する。terminal ResultでもDELETE-G1前は常に`DELETE_GATE_REQUIRED`であり、物理I/Oを実行しない。

## 検証

- RED契約：6件失敗（実装前）
- P5R2-15契約＋追加guard：13件PASS（中間GREEN）
- BacktestProductService cancel integration：1件PASS
- 既存P4 Result保存／non-hash回帰：22件PASS
- `ruff check`：PASS
- `mypy src/autotrade/application`：PASS
- 固定品質入口：`scripts.quality_gate.local_p5r2_p15_pytest`
- 固定WSL Gate：未実行（次の実行記録で更新）

## レビューと判定

Luna Max reviewerの指摘を反映し、RUNNINGの遷移、server-owned state、実HTTP取消経路を修正した。Result Artifactの種別・依存・canonical pathの永続解決と、Operation監査のrestart永続化はP5R2-16／DELETE-G1前提の後続範囲である。固定WSL Gateとread-onlyレビューが完了するまで`GREEN_CONFIRMED`へ遷移させない。

## 実行ランタイム

指定Project Coordinator／Agent rosterの完全な独立dispatch結果はruntime receiptへ事実どおり記録する。実際に起動したreviewerだけを独立レビューとして扱い、未起動Agentを実行済みとは記録しない。管理hash、manifest fingerprint、stale判定、hash retryは作成しない。
