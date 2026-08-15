# P5-08 運用者 Waiver 記録

- 対象: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12` / `P5-08` / `RUN-P5-08-BINANCE-001`
- 記録日時: `2026-08-15T17:32:01+09:00`
- 記録者: root coordinator
- 有効範囲: このRunの実行調整のみ

## 運用者指示

運用者は、P5-08の開始に関して次の二つの事前条件をこのRunから除外するよう明示した。

1. Provider利用条件の事前確認
2. 実行前後のhost-isolation通信証拠の取得

## 正確な扱い

- この記録はProviderの利用・保持・再配布条件を確認済み、許諾済み、又はPASSとするものではない。事実状態は `UNKNOWN` のままとする。
- この記録はhost isolationを検証済み、又はPASSとするものではない。事実状態は `NOT_VERIFIED` のままとする。
- waiverは上記二つを **P5-08開始判断の事前条件として用いない** ための運用者決定である。
- Binance外部I/O、Secret読取り、Broker、Paper、Live、実資金、実Risk、Cloudは、この調整記録だけでは実行しない。
- 実Data取得を開始する実行主体は、別途の明示的な `--mode execute` 操作と実行receiptを必要とする。本調整では外部I/Oを行わない。

## 参照

- 既存preflight: `tests/evidence/phase5/RUN-P5-08-BINANCE-001/preflight/registration-preflight.json`
- 既存Runner: `scripts/phase5_external_data/run_binance_data_vision.py`
- 今回のdispatch receipt: `tests/evidence/phase5/RUN-P5-08-BINANCE-001/dispatch/P5-08-execution-coordination-receipt-20260815.json`
