# P5R2-13 runtime receipt

## 判定

`P5R2-13_GREEN_CONFIRMED`。最終ソースをWSL隔離環境の固定4 Gateへ通し、formatter、lint、type、testが全てPASSした。対象pytestは49件PASS、既存application/backtest回帰は174件PASS（43件はP5R2対象除外）だった。

## 実行証跡

- Run ID: `RUN-P5R2-13-LOCAL-001`
- host wrapper execution ID: `bc58f63950d34bb3ba7b1a831197e0a7`
- verification: [verification.json](../../../tests/evidence/phase5R2/RUN-P5R2-13-LOCAL-001/verification.json)
- automation summary: [run-test-summary.json](../../../tests/evidence/phase5R2/RUN-P5R2-13-LOCAL-001/automation/run-test-summary.json)
- GREEN Evidence: [P5R2-13_GREEN.json](../../../tests/evidence/phase5R2/RUN-P5R2-13-LOCAL-001/P5R2-13_GREEN.json)
- A95 policy: [P5R2-13_A95_policy.json](../../../tests/evidence/phase5R2/RUN-P5R2-13-LOCAL-001/P5R2-13_A95_policy.json)

host outbound isolationは`CONFIRMED`（networkingMode=none、default routeなし、外向きNICなし）。既存protected fixtureはread-only参照で、入力前後のidentityが一致した。

## Runtime dispatchの事実

計画記載のProject Coordinator／A110〜A160／A95のnested dispatchは確立していない。したがって、指定部品は全て次の状態である。

`agent_id=N/A`、`spawn_status=NOT_DISPATCHED`、`wait_status=NOT_DISPATCHED`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`。

実際のread-only probeは次の2件で、指定Project Agent rosterとは別物として記録した。

| probe | agent_id | 結果 |
|---|---|---|
| Python review | `01a02a09-750f-7f30-8811-dde551feb67a` | Critical 0 / High 0 |
| Security review | `01a02a14-eede-7701-b001-930082d67884` | Critical 0 / High 0 / Medium 0 |

## A95

A95静的ポリシーは、新規の管理用hash、manifest fingerprint、stale、retry、receipt hashを追加していないためALLOWとした。既存ファイルの管理用hash語彙はbaseline候補として分類し、勝手に削除・再計算・比較はしていない。

## 禁止操作

外部Provider、login、API call、download、Secret、費用、物理削除、Playwright、npm、P6開始は行っていない。DATA-G1、DELETE-G1、H2は未承認のまま維持する。

## 回復履歴

初回はEvidence root未初期化、2回目はP5R2-13固定pytest template未登録で停止した。runnerのroot初期化とtemplate allowlistを修正し、最終実行でPASSを確認した。停止を成功に置き換えていない。
