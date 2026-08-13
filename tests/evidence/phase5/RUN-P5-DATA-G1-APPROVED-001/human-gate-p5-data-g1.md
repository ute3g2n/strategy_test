# P5-DATA-G1 Human Gate承認記録

- Phase: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan: `P5-PLAN-001 / plan/Phase5_実行計画書_v0.1_2026-08-12.md`
- Gate: `P5-DATA-G1`
- Run ID: `RUN-P5-DATA-G1-APPROVED-001`
- Status: `APPROVED`
- Execution status: `NOT_STARTED`
- Received: `2026-08-13`（Asia/Tokyo）
- User statement: 「P5-DATA-G1 は推奨構成の値をそのまま適用して下さい。」

> このファイルは推奨値適用を承認した時点の原記録（historical snapshot）である。費用事前見積り必須ルールの現行扱いは、後続の [`P5-DATA-G1-AMEND-COST-PREFLIGHT-001`](human-gate-p5-data-g1-amendment-2026-08-13.md) が優先する。原記録の内容は履歴として保持し、現行状態は変更Evidence・request・Runner・台帳を参照する。

## 承認の意味

上記のユーザー指示を、P5-07Aで整理した推奨構成をP5-DATA-G1の申請範囲へ適用する明示承認として記録する。承認対象は市場Data Providerの限定範囲だけであり、P5-08の実行完了、P5-09の品質実証、P5-H2、Broker、Paper、Live、実資金、実Risk、Cloud、Core変更を意味しない。

## 適用する承認範囲

| 項目 | 適用値 |
|---|---|
| Provider／契約 | Databento Historical API、Usage-based Historical only、Liveなし、外部再配布なし |
| Dataset | `GLBX.MDP3` |
| 対象 | `MCL`、`M6A`、`MZC`、`MZS`、`MZW`。Provider入力は各`[ROOT].FUT`、`stype_in=parent`、`stype_out=instrument_id` |
| 契約形態 | outright futuresのみ。spread、option、swap、spotは除外 |
| 期間 | `start=2025-02-24T00:00:00Z`、`end=2026-08-01T00:00:00Z`（排他的）、`as_of=2026-07-31T23:59:59Z` |
| 時間足 | `D1`／`H4`／`H1`／`M30`／`M15`。元データは`ohlcv-1m`、保存UTC、営業日・DSTは`America/Chicago` |
| Schema | 全期間`definition`、`ohlcv-1m`、`statistics`。TBBOは`2026-07-01T00:00:00Z`〜`2026-08-01T00:00:00Z`のパイロット |
| Raw／Normalized | DBN + zstd、`.dbn.zst`、日単位分割、SHA-256、Raw個別契約、Normalizedは`P5-NORMALIZED-BAR-v1.0.0` |
| Roll | 派生continuousは前日出来高front month、価格back-adjustなし。Roll時の価格差はGapへ分離 |
| Endpoint／通信 | `https://hist.databento.com/v0/`のみ、HTTPS/TLS、`hist.databento.com:443`のみallowlist、同時接続1、最大1 request/秒 |
| Retry／停止 | 429は`Retry-After`に従い最大2回。401／402／403／404／422、206 partial、available以外、scope・hash・Calendar・費用・Secret・通信逸脱はfail-closed停止 |
| 費用 | 1 Run上限25 USD、Historicalチーム月額上限50 USD、80%警告、100%停止。実行前見積りが必須 |
| Secret | 参照名`DATABENTO_API_KEY`のみ。値は記録・表示・CLI投入しない。用途はHistorical限定、期限上限`2026-08-31`、Run後rotate／revoke |
| Evidence | `tests/evidence/phase5/RUN-P5-08-DATABENTO-001/`。Raw／Normalized／Quality／Manifestを同一Runへ束ねる |
| 保持／再配布 | Raw／NormalizedはP5-H2後180日上限案、Manifest／Quality／Provenance／hash／StopDecisionは3年案、外部再配布・公開・Cloudバックアップなし |
| Runner | `P5-EXT-DATABENTO-HIST-001`、version`0.1.0`、固定command案はP5-07A記載のもの |

## 承認範囲からの除外

- `stocks`、FXスポット、cryptoの実Data取得。
- 標準契約をMicro契約の実績へ一般化する長期proxy。
- Live配信、Broker接続、注文、Paper、Live、実資金、実Risk、Account／OMS、Cloud。
- 別Provider、別endpoint、対象追加、Secret用途変更、未登録Runnerの推測起動。

## 適用後も残る停止条件

- `P5-EXTERNAL-WORKER-UNKNOWN`はOPENのまま。Runner実体、依存lock、固定command、target scope、外部host isolation、再現手順が未登録である。
- 実アカウントのentitlement、契約・ライセンス、事前費用見積り、Secret metadata、外部Runの通信監査は未確認である。
- したがってP5-08は外部I/O、Secret参照、費用発生、実Data取得を開始しない。P5-08の再開には、上記証拠と承認範囲の一致が必要である。
- この記録はP5-DATA-G1の範囲承認であり、P5-08／P5-09／P5-H2のPASSではない。

## 副作用確認

- 外部I/O: `false`
- Provider access: `false`
- Secret access: `false`
- Cost incurred: `false`
- Data acquired: `false`
- Core／P4 DB／migration／Broker／Paper／Live変更: `false`

## 参照

- [P5-07申請表](../../../../doc/phase5/05_実証/06_Phase5外部Data_Gate申請・範囲表.html)
- [P5-07A推奨値・公式根拠HTML](../../../../doc/phase5/05_実証/07_P5-DATA-G1推奨入力値・やさしい説明.html)
- [P5-07A公式根拠ログ](../../../../plan/phase5/ログ/P5-07A_P5-DATA-G1推奨入力値・公式根拠_2026-08-12.md)
- [P5-08再開条件ログ](../../../../plan/phase5/ログ/P5-08_承認範囲Data取得・Raw_Normalized_Evidence_2026-08-12.md)
