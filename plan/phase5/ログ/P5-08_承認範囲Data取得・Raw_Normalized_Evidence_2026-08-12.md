# P5-08 承認範囲Data取得・Raw／Normalized Evidence

- Step ID: `P5-08`
- Phase ID: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan: `P5-PLAN-001`
- Run ID: `RUN-P5-08-BLOCKED-GATE-001`
- 状態: `P5-08_BLOCKED_PREEXECUTION_EVIDENCE_MISSING`
- 判定: `BLOCKED`

## Findings first

| ID | 重大度 | 状態 | 内容・処置 |
|---|---|---|---|
| P5-08-F-001 | Medium | STOP / OPEN | P5-DATA-G1の範囲は2026-08-13に承認済みだが、実アカウントentitlement、契約・ライセンス、budget control、Secret metadata、外部host isolation、外部Runの実行前Evidenceは未確認であり、P5-08を開始しない。事前費用見積りは開始条件としない。 |
| P5-08-F-002 | Medium | STOP / OPEN | `P5-EXTERNAL-WORKER-UNKNOWN`は未解消。固定Runner、request、target scope、Evidence root、local dry-runは作成したが、外部実行前のentitlement・budget・Secret metadata・host isolationが未確認のため、`-Execute`を起動しない。 |
| P5-08-F-003 | Medium | RECORDED | Coordinator spawnは`collab spawn failed: agent thread limit reached`で失敗。childは未起動としてreceiptに記録し、独立実行・独立レビューを主張しない。 |
| P5-08-F-004 | Medium | CLOSED | 外部I/O、Provider、Secret、費用、実Data取得、Raw／Normalized保存は0件。P5-DATA-G1承認後も、実行前Evidenceが揃うまでData取得を開始しない。 |

Critical=0、High=0。ただしこれはP5-08のPASSではなく、開始前のfail-closed判定である。

## 発火制御

- P5-07申請表を入力として読み取った。
- P5-DATA-G1の明示承認は `tests/evidence/phase5/RUN-P5-DATA-G1-APPROVED-001/human-gate-p5-data-g1.md` に存在する。P4-H2、P5-H0、P5-H1、P5-06 PASSをP5-DATA-G1へ代用していない。
- P5-08の外部取得、Provider endpoint、Secret参照、費用発生、Raw／Normalized生成、Data hash作成、実Runは実行していない。
- Broker、Paper、Live、実資金、実Risk、Cloud、Core、P4 DB、migration、repositoryは対象外であり、変更していない。

## 必須入力の判定

| 入力 | 判定 | 不足時の停止 |
|---|---|---|
| P5-DATA-G1承認記録 | 保存済み／適用済み | `APPROVED` |
| Run ID／target_paths／固定command | request、Run ID、target scope、Evidence root、固定Runner、local dry-runを作成済み。外部取得Runは未発行 | `MANIFEST_UNKNOWN` |
| Provider契約・権限・budget control・Secret境界 | 承認範囲は適用済み。実行前の契約・権限・budget control・Secret metadataは未確認。事前見積りは必須としない | `PROVIDER_GATE_REQUIRED` |
| host isolation | P5-06 local harnessの確認を外部取得へ一般化不可 | 外部Run単位で未確認なら`QUALITY_STOP` |
| Raw／Normalized／Manifest／provenance hash | 未生成 | `EVIDENCE_MISSING` |

## 後続判定

| Step | 状態 | 根拠 |
|---|---|---|
| P5-09 | `BLOCKED` | P5-08 Raw／Normalized Evidenceなし、Quality実証未実施 |
| P5-10 | `NOT_STARTED` | Quality／Calendar／Cost／Gap／Holdout実証なし。UnknownをPassにしない |
| P5-H2 | `HUMAN_GATE_REQUIRED` | P5-10完了候補が存在しない |
| P5-11 | `NOT_STARTED` | P5-H2未承認 |

## Evidence／receipt

- [P5-07申請表](../../../doc/phase5/05_実証/06_Phase5外部Data_Gate申請・範囲表.html)
- [P5-DATA-G1承認Evidence](../../../tests/evidence/phase5/RUN-P5-DATA-G1-APPROVED-001/human-gate-p5-data-g1.md)
- [P5-DATA-G1費用ルール変更Evidence](../../../tests/evidence/phase5/RUN-P5-DATA-G1-APPROVED-001/human-gate-p5-data-g1-amendment-2026-08-13.md)
- [P5-08公式仕様・アカウント確認](P5-08_公式仕様・アカウント確認_2026-08-13.md)
- [P5-08 Evidence root／Runner README](../../../tests/evidence/phase5/RUN-P5-08-DATABENTO-001/README.md)
- [P5-08 request](../../../tests/evidence/phase5/RUN-P5-08-DATABENTO-001/request.json)
- [P5-08 dry-run report](../../../tests/evidence/phase5/RUN-P5-08-DATABENTO-001/logs/dry-run-report.json)
- [P5-07ログ](P5-07_外部Data_Gate申請・範囲表_2026-08-12.md)
- [P5-08 dispatch receipt](../../../tests/evidence/phase5/RUN-P5-08-BLOCKED-GATE-001/dispatch-receipts.md)
- [P5-08 machine-readable receipt](../../../tests/evidence/phase5/RUN-P5-08-BLOCKED-GATE-001/dispatch-receipt.json)

上記P5-08 dispatch receiptは2026-08-12時点の承認前・開始拒否の履歴であり、現在のP5-DATA-G1承認を取り消すものではない。現在の承認状態は別途保存したHuman Gate Evidenceを正本として参照する。

P5-DATA-G1の範囲は明示承認済みである。承認範囲、固定Runner、command、target scope、Secret境界、契約・権限、budget control、Secret metadata、外部host isolation、Evidence rootが揃うまで、P5-08は再開しない。事前費用見積りは開始条件にしないが、実行後usage監査は必須とする。
