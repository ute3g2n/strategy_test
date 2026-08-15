# RUN-P5-08-BINANCE-001

Binance Data VisionのSpot Kline 1mを、P5-08の固定Runnerで取得した実行証跡です。

## 実行結果

- 状態：`RAW_AND_EXPANDED_CSV_ACQUIRED`
- 対象：`BTCUSDT`、`ETHUSDT`
- 期間：2025-02-24T00:00:00Z以上、2026-08-01T00:00:00Z未満
- 対象月：2025-02〜2026-07、各18月
- 取得件数：36件（2 symbol × 18月）
- 成果物：Raw ZIP 36件、`.CHECKSUM` 36件、展開CSV 36件、未完了`.part` 0件
- 合計サイズ：319,477,441 bytes
- checksum不一致：0件
- timestamp unit不一致：0件
- 重複timestamp：0件
- symbol／月範囲違反：0件
- API key／Secret読取：`false`
- Provider data cost：`0 USD`
- Normalized：`NOT_EXECUTED`
- Quality：`NOT_EXECUTED`

## 運用者waiver

このRunでは、運用者の明示決定により次の2項目を開始前提から除外しました。

1. Provider利用条件の事前確認
2. 実行前後のhost-isolation通信証拠

これは事実の再分類ではありません。Provider termsは`UNKNOWN`、host isolationは`NOT_VERIFIED`のままです。waiverはこのRunの開始判定にだけ適用し、P5-09以降の品質・利用条件・レビューの合否を自動的に満たすものではありません。

参照：[`operator-waiver-20260815.md`](operator-waiver-20260815.md)

## 主な証跡

- [`request.json`](request.json)
- [`runner-registration.json`](runner-registration.json)
- [`allowlist.json`](allowlist.json)
- [`host-isolation.json`](host-isolation.json)
- [`execution-start-20260815.json`](execution-start-20260815.json)
- [`execution-finish-20260815.json`](execution-finish-20260815.json)
- [`execution-summary.json`](execution-summary.json)
- [`preflight/registration-preflight.json`](preflight/registration-preflight.json)
- [`root runtime receipt`](dispatch/P5-08-root-runtime-receipt-20260815.json)
- [`Coordinator receipt`](dispatch/P5-08-execution-coordination-receipt-20260815.json)

## 対象外

Binance Futures、Funding、Liquidation、Tick、Order book、REST API主経路、Broker、Paper、Live、実資金、実Risk値、Cloud、Core、P4 DB、API key／Secret値は対象外です。

## 次のGate

P5-09でNormalized、D1／H4／H1／M30／M15、`CRYPTO_24_7_UTC`、Quality、Cost／Gap、Holdoutを検証します。このREADMEと取得サマリだけではP5-08全体PASS、P5-H2、Live利用を宣言しません。
