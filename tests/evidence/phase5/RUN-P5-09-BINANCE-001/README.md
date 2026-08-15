# RUN-P5-09-BINANCE-001

P5-08で取得したBinance Data Vision Spot Kline 1mのローカル品質実証Runである。

- 対象: `BTCUSDT`, `ETHUSDT`
- 期間: `2025-02-24T00:00:00Z` 以上、`2026-08-01T00:00:00Z` 未満
- Calendar: `CRYPTO_24_7_UTC`
- 入力: `RUN-P5-08-BINANCE-001/expanded/`
- 外部通信: 0
- API key / Secret: 読取0
- 結果: `QUALITY_EVIDENCE_COMPLETE_WITH_OPEN_UNKNOWN`

## 結果

両銘柄とも1m 753,120本、gap 0、重複0、OHLCV不整合0、補間0。D1／H4／H1／M30／M15をUTC境界で生成した。Train／Validation／Holdoutの境界重複もない。

## Unknown

Provider利用・保持・再配布条件はP5-08から`UNKNOWN`、外部取得Runのhost isolationは`NOT_VERIFIED`であり、P5-09はこれをPassへ変換しない。Runtime child Agent 7体は未起動で、独立レビュー済みとは扱わず、`SELF_REVIEW_FALLBACK`とする。

## 入口

- `manifest.json`
- `evidence-index.json`
- `quality/quality-report.json`
- `quality/calendar-application.json`
- `quality/cost-gap.json`
- `quality/period-split.json`
- `execution-finish-20260815.json`
- `stop-decision.json`
- `regeneration-procedure.md`
- `dispatch/P5-09-root-runtime-receipt-20260815.json`
- `dispatch/P5-09-child-runtime-receipt-20260815.json`

文書管理用のidentity digestは作成していない。P5-08のsource checksum検証結果だけを、データ完全性の証拠として参照する。
