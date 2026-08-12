# P5-09 Quality／Calendar／Cost／Gap／期間分割／Holdout実証

- Step ID: `P5-09`
- Phase ID: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan: `P5-PLAN-001`
- Run ID: `RUN-P5-09-BLOCKED-UPSTREAM-001`
- 状態: `P5-09_BLOCKED_P5_DATA_G1_AND_P5_08`
- 判定: `BLOCKED`

## Findings first

| ID | 重大度 | 状態 | 内容・処置 |
|---|---|---|---|
| P5-09-F-001 | Medium | STOP / OPEN | P5-DATA-G1が未承認。実測Data、Calendar、Cost、Gap、期間分割、Holdoutを実行・推定しない。 |
| P5-09-F-002 | Medium | STOP / OPEN | P5-08がBLOCKEDでRaw／Normalized／Manifest／provenance Evidenceがない。Quality実証を開始しない。 |
| P5-09-F-003 | Medium | RECORDED | Coordinator spawnは`collab spawn failed: agent thread limit reached`で失敗。childは未起動としてreceiptへ記録した。 |
| P5-09-F-004 | Medium | CLOSED | 外部I/O、Provider、Secret、費用、実Data、Quality実証、Holdout操作は0件。UnknownをPassにしていない。 |

Critical=0、High=0。ただしこれはP5-09のPASSではなく、上流Gate未成立による停止判定である。

## 発火制御

- P5-DATA-G1=APPROVED、P5-08完了、trusted scope、host isolation、Run Manifest、Data／Calendar hashの全条件を満たしていない。
- P5-04のQuality／Cost／Holdout設計は入力設計として保持するが、実測値・実Data Evidenceへ一般化しない。
- Cost／Slippage／GapはASSUMPTIONのまま。MEASUREDへ置換していない。
- Broker、Paper、Live、実資金、実Risk、Cloud、Core、P4 DB、migration、repositoryは対象外で、変更・実行していない。

## 実証対象の未実行表

| 対象 | 必須入力 | 判定 | 停止コード |
|---|---|---|---|
| Quality／欠損／重複／単調性 | Raw／Normalized、contract hash、quality schema | 未実行 | `EVIDENCE_MISSING` |
| Calendar／DST／Roll／timezone | CalendarVersion、RollRule、Data hash | 未実行 | `CALENDAR_UNKNOWN` |
| Cost／Slippage／Gap | MEASURED provenance、単位、期間、hash | 未実行 | `COST_PROVENANCE_INVALID` |
| train／validation／holdout／walk-forward | as-of、split hash、期間・市場範囲 | 未実行 | `SPLIT_INTEGRITY_STOP` |
| look-ahead／survivorship | approved Data、時間境界、監査Evidence | 未実行 | `FUTURE_DATA_STOP` |

## 後続判定

| Step | 状態 | 根拠 |
|---|---|---|
| P5-10 | `NOT_STARTED` | P5-08／09の実証Evidenceなし。UnknownをPassにしない |
| P5-H2 | `HUMAN_GATE_REQUIRED` | P5-10完了候補が存在しない |
| P5-11 | `NOT_STARTED` | P5-H2未承認 |

## Evidence／receipt

- [P5-08判定ログ](P5-08_承認範囲Data取得・Raw_Normalized_Evidence_2026-08-12.md)
- [P5-09 dispatch receipt](../../../tests/evidence/phase5/RUN-P5-09-BLOCKED-UPSTREAM-001/dispatch-receipts.md)
- [P5-09 machine-readable receipt](../../../tests/evidence/phase5/RUN-P5-09-BLOCKED-UPSTREAM-001/dispatch-receipt.json)

P5-DATA-G1承認、P5-08の承認範囲内Data Evidence、全hash、Calendar、Manifest、host isolationが揃うまで、P5-09を再開しない。
