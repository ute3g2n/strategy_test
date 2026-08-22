# P5R2-DELETE-G1 Human Gate 判断

- step_id: `P5R2-DELETE-G1`
- 判断日: `2026-08-23`
- 判断者: root Codex
- 権限根拠: 利用者がP5R2-25完了までのP5R2 Human Gate承認権限をroot Codexへ移譲した記録
- packet: [`08_P5R2-DELETE-G1承認packet.html`](../../../doc/phase5R2/08_DELETE-G1/08_P5R2-DELETE-G1承認packet.html)
- 判断: `APPROVED_BOUNDED_P5R2_21_FIXTURE_ONLY`
- runtime receipt: [`runtime-receipt-P5R2-DELETE-G1.json`](../quality/runtime-receipt-P5R2-DELETE-G1.json)
- Human Gate Evidence: [`human-gate-p5r2-delete-g1.md`](../../../tests/evidence/phase5R2/RUN-P5R2-DELETE-G1-PACKET-001/human-gate-p5r2-delete-g1.md)

## 判断

P5R2-DELETE-G1を、承認packetに記載したbounded範囲で承認する。P5R2-21の実装と、新規一時fixtureだけを使う物理削除受入へ進める。

## 承認した対象

- 利用者が明示したterminal状態のBacktest結果ResultArtifactだけ。
- `logical_result_artifact_id`からサーバーが解決する固定ResultArtifact root内の対象だけ。
- APIは呼出元指定のpathを受け付けず、symlink／Windows reparse point、traversal、root外、ID不一致、TOCTOU、active／recovery中、CSV Export中、保持選択中をfail-closedで拒否する。
- 同一operation tokenは冪等に処理し、別tokenの同時要求はserver lockで直列化する。
- 成功後は`RESULT_DELETED`とAudit／tombstoneを残し、復元APIは作らない。
- 実物理削除の受入対象は、新規作成する一時fixtureだけとする。

## 承認していない対象

- Historical Data、Catalog、source／derived Data
- Run本体、Run manifest、cancel／progress履歴
- Export済みCSV、CSV Job、利用者が保存したCSV
- Audit、tombstone、Evidence、screenshot、quality receipt
- 既存の実Data、実Run、既存Evidence、既存fixture
- 一括削除、保持期間purge、Trash、restore API
- Provider login、API call、外部Data download、Secret、費用
- P5R2-H2、P5R2完了宣言、P6開始

## 確認結果

| 確認 | 結果 |
|---|---|
| P5R2-15 local guard／RED／GREEN | terminal Result以外の保護、path指定拒否、active／unsafe拒否、DELETE-G1前の物理I/OなしをEvidenceで確認した。 |
| P5R2-19 UI | 3画面でDELETE-G1未承認表示、二重押下防止のUI境界、CSV／Data／Run／Audit／Evidence保護説明を確認した。 |
| 対象範囲 | terminal ResultArtifactだけ、P5R2-21は新規一時fixtureだけに限定した。 |
| 外部I/O | 0。local実装・local testだけを許可する。 |
| 既存データへの物理操作 | 0。実行していない。 |
| Critical／High | root責務のFindings-first確認で0。named Agentの独立完了とは扱わない。 |
| A95 | 管理用hash経路を追加しない静的判定はALLOW。保護対象identityの新規hashやmanifestは作らない。 |

## runtime dispatchの真実性

指定Coordinator／Agentのnested dispatchはこのGateでは成立しなかったため、runtime receiptには`RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`を記録した。root Codexの確認を独立Agentレビューと偽らない。Gate判断は、packet、既存Evidence、権限移譲記録、上記の限定条件に基づくrootのbounded判断である。

## P5R2-21開始条件

P5R2-21では、まず新規一時fixtureを作り、削除対象と保護対象の存在を確認してから、物理削除を1回だけ行う。既存の`tests/evidence`、通常のEドライブData、既存Run、既存CSV、既存Auditを削除対象にしない。失敗、対象差替え、path検査不能、Audit保存失敗が起きた場合はDELETE_FAILED／BLOCKEDで停止する。

## やさしい説明

結果画面の結果ファイルだけを消す機能の実装を許可しました。ただし、材料のData、実行記録、CSV、監査記録、品質の証拠は絶対に消しません。最初の実験では、新しく作った練習用ファイルだけを消します。
