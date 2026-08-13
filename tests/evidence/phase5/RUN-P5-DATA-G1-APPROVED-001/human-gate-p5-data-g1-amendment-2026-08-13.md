# P5-DATA-G1 承認範囲変更記録（費用見積り必須ルールの廃止）

- Phase: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan: `P5-PLAN-001`
- Gate: `P5-DATA-G1`
- Amendment ID: `P5-DATA-G1-AMEND-COST-PREFLIGHT-001`
- Status: `APPROVED`
- Applied: `2026-08-13`（Asia/Tokyo）
- User instruction: 「費用見積もりが必要なルールを廃止します」

## 変更内容

P5-DATA-G1の適用範囲から、`get_billable_size`／`get_cost`を外部Data取得前に必ず実行しなければならない、という開始条件を削除する。

この変更は「実行前の見積りを必須にしない」という変更であり、費用管理そのものを削除する変更ではない。次の制御は維持する。

- 1 Runの上限は25 USD。
- Historicalチーム月額上限は50 USD。
- 80%で警告、100%で停止。
- Provider／チーム側のbudget controlを設定する。
- 実行後のusage／billing監査を必須とする。
- 実行後に費用がUnknownなら、P5-08をPASSにしない。
- 上限変更、Provider変更、別Endpoint、対象拡大、Live利用は本変更の対象外。

## 変更後の開始条件

P5-08は、P5-DATA-G1承認、契約・entitlement、Secret metadata、固定Runner、`request.json`、外部host isolation、target scope、Evidence rootが揃えば開始できる。実行前費用見積りが存在しなくても開始条件違反とはしないが、budget controlが未確認の場合は開始しない。

## 副作用確認

- 外部I/O: `false`
- Provider access: `false`
- Secret value access: `false`
- Cost incurred: `false`
- Data acquired: `false`

## 参照

- [元のP5-DATA-G1承認Evidence](human-gate-p5-data-g1.md)
- [P5-08 request](../RUN-P5-08-DATABENTO-001/request.json)
- [P5-08 cost policy](../RUN-P5-08-DATABENTO-001/budget-control.json)
