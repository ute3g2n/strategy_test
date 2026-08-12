# P5-08 承認範囲Data取得・Raw／Normalized Evidence

- Step ID: `P5-08`
- Phase ID: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan: `P5-PLAN-001`
- Run ID: `RUN-P5-08-BLOCKED-GATE-001`
- 状態: `P5-08_BLOCKED_P5_DATA_G1_NOT_APPROVED`
- 判定: `HUMAN_GATE_REQUIRED`

## Findings first

| ID | 重大度 | 状態 | 内容・処置 |
|---|---|---|---|
| P5-08-F-001 | Medium | STOP / OPEN | P5-DATA-G1が未承認。P5-07申請表の対象、Provider、契約、費用、Secret、通信、保存、Runnerは承認済み実行範囲ではないため、P5-08を開始しない。 |
| P5-08-F-002 | Medium | STOP / OPEN | `P5-EXTERNAL-WORKER-UNKNOWN`が未解消。実在・固定・承認済みRunner、command、target scope、Evidence rootがないため、Runnerを推測・起動しない。 |
| P5-08-F-003 | Medium | RECORDED | Coordinator spawnは`collab spawn failed: agent thread limit reached`で失敗。childは未起動としてreceiptに記録し、独立実行・独立レビューを主張しない。 |
| P5-08-F-004 | Medium | CLOSED | 外部I/O、Provider、Secret、費用、実Data取得、Raw／Normalized保存は0件。P5-DATA-G1未承認のままEvidenceを作らない。 |

Critical=0、High=0。ただしこれはP5-08のPASSではなく、開始前のfail-closed判定である。

## 発火制御

- P5-07申請表を入力として読み取った。
- P5-DATA-G1の明示承認は存在しない。P4-H2、P5-H0、P5-H1、P5-06 PASSをP5-DATA-G1へ代用していない。
- P5-08の外部取得、Provider endpoint、Secret参照、費用発生、Raw／Normalized生成、Data hash作成、実Runは実行していない。
- Broker、Paper、Live、実資金、実Risk、Cloud、Core、P4 DB、migration、repositoryは対象外であり、変更していない。

## 必須入力の判定

| 入力 | 判定 | 不足時の停止 |
|---|---|---|
| P5-DATA-G1承認記録 | 欠落／未承認 | `HUMAN_GATE_REQUIRED` |
| Run ID／target_paths／固定command | 外部取得Run未発行 | `MANIFEST_UNKNOWN` |
| Provider契約・権限・費用・Secret境界 | 未承認 | `PROVIDER_GATE_REQUIRED` |
| host isolation | P5-06 local harnessの確認を外部取得へ一般化不可 | 外部Run単位で未確認なら`QUALITY_STOP` |
| Raw／Normalized／Manifest／provenance hash | 未生成 | `EVIDENCE_MISSING` |

## 後続判定

| Step | 状態 | 根拠 |
|---|---|---|
| P5-09 | `BLOCKED` | P5-08 Raw／Normalized Evidenceなし、P5-DATA-G1未承認 |
| P5-10 | `NOT_STARTED` | Quality／Calendar／Cost／Gap／Holdout実証なし。UnknownをPassにしない |
| P5-H2 | `HUMAN_GATE_REQUIRED` | P5-10完了候補が存在しない |
| P5-11 | `NOT_STARTED` | P5-H2未承認 |

## Evidence／receipt

- [P5-07申請表](../../../doc/phase5/05_実証/06_Phase5外部Data_Gate申請・範囲表.html)
- [P5-07ログ](P5-07_外部Data_Gate申請・範囲表_2026-08-12.md)
- [P5-08 dispatch receipt](../../../tests/evidence/phase5/RUN-P5-08-BLOCKED-GATE-001/dispatch-receipts.md)
- [P5-08 machine-readable receipt](../../../tests/evidence/phase5/RUN-P5-08-BLOCKED-GATE-001/dispatch-receipt.json)

P5-DATA-G1が明示承認され、承認範囲、固定Runner、command、target scope、Secret境界、host isolation、Evidence rootが揃うまで、P5-08は再開しない。
