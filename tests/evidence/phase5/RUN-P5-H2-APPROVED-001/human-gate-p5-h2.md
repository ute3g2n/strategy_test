# P5-H2 Human Gate approval

- Gate ID: `P5-H2`
- Phase ID: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Plan: `P5-PLAN-001`
- Evidence Run ID: `RUN-P5-H2-APPROVED-001`
- Recorded at: `2026-08-15`（Asia/Tokyo）
- Decision: `APPROVED_WITH_OPEN_UNKNOWN_AND_STOP_CONDITIONS`
- Gate status: `APPROVED`

## Approval statement

運用者から「承認します。続けて」を受領した。これは直前のP5-11停止理由であるP5-H2に対する承認として記録する。

## Approved scope

- Provider: Binance Data Vision historical archive
- Market: Crypto Spot
- Symbols: `BTCUSDT`、`ETHUSDT`
- Base timeframe: Spot Kline `1m`
- Timezone / calendar: UTC / `CRYPTO_24_7_UTC`
- Derived timeframes: D1、H4、H1、M30、M15
- Evidence: P5-08 Raw／checksum／展開CSV、P5-09 Normalized／Quality／Calendar／Cost／Gap／Holdout、P5-10統合レビュー、REQ／UC／Test追跡、P6引渡し候補

## Residual Unknowns and stop conditions

次の事項は承認によって解消せず、`OPEN`／`NOT_VERIFIED`／`NOT_MEASURED`のままP6へ引き渡す。UnknownをPASSへ変更しない。

- Providerの利用・保持・再配布条件: `UNKNOWN`
- P5-08外部取得Runのhost isolation: `NOT_VERIFIED`
- 指定child Agentの独立実行・独立レビュー: `NOT_VERIFIED`
- fee、slippage、内部execution cost: `NOT_MEASURED`

上記に反する場合、またはEvidence欠落、範囲逸脱、UnknownのPASS化、Secret／外部I/O混入がある場合はFail-closedで停止する。

## Explicit exclusions

他のsymbol、Futures、Funding、Liquidation、利益性の採用、実Risk、Broker、Paper、Live、実資金、Cloud、未承認Secret、追加Data取得、Provider変更、Core、P4 DB変更は承認しない。

## Next step

P5-11を、上記の承認範囲・残存Unknown・停止条件を明記した完了判定／P6引渡し文書作成の範囲で再実行する。外部I/Oや注文経路は開始しない。
