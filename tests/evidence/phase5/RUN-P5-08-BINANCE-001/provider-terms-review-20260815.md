# P5-08 Binance Provider利用条件確認

- Check ID: `P5-08-PROVIDER-TERMS-CHECK-20260815-001`
- Checked at: `2026-08-15T08:19:14Z`
- Scope: Binance Data Vision Spot monthly Kline 1m、`BTCUSDT`／`ETHUSDT`、内部バックテスト用途
- Result: `UNKNOWN / EXECUTION_BLOCKED`
- External I/O: `0`
- API key／Secret read: `false`

## 公式一次情報で確認できたこと

| 確認項目 | 結果 | 根拠 |
|---|---|---|
| 公開アーカイブの存在 | CONFIRMED | [Binance Public Data README](https://github.com/binance/binance-public-data/blob/master/README.md?plain=1) は `data.binance.vision` のdaily／monthly公開データを説明している。 |
| Spot Kline 1mの形式 | CONFIRMED | 同READMEはKlineの列とintervalを説明し、2025-01-01以降のSpot timestampがmicrosecondsであることを記載している。 |
| ZIP完全性確認 | CONFIRMED | 同READMEは同じ場所の `.CHECKSUM` とSHA-256確認方法を記載している。 |
| 公開市場DataのAPI key不要 | CONFIRMED | [Binance Market Data Only FAQ](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md?plain=1) は公開market-data endpointが認証不要であることを説明している。 |
| Data archiveの更新可能性 | CONFIRMED | 同READMEは、問題発見時にarchive fileが後日更新される可能性を記載している。 |
| 取得データの保持許諾 | UNKNOWN | 確認した公式README／API FAQは取得方法を説明するが、P5の保存期間・保持許諾を明示していない。 |
| 取得データの再配布許諾 | UNKNOWN | READMEの `MIT` 表記は公開Dataリポジトリの説明・スクリプトのライセンスと解釈できるが、archive内の市場Dataそのものへの再配布許諾とは確認できない。 |

BinanceのSpot API文書は、製品条件の詳細を[Binance Product Terms of Use](https://www.binance.com/en/terms)へ参照させている。また、Spot API文書自体の[Terms of Use notice](https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/PROD-TERMS-OF-USE.md)はProduct Termsを読むよう案内している。しかし、今回確認できた公開一次情報から、P5の保存・再配布条件を明示的に確定できる条項は取得できなかった。

## 判定

この確認により「公開DataをAPI keyなしで取得できる」「取得後に`.CHECKSUM`でSource Dataを検証できる」は確認できた。一方、プロジェクトの停止条件である利用・保持・再配布条件は、推測で `CONFIRMED` にしない。したがって `request.json` の `provider_terms.status` は `UNKNOWN` のまま、`--mode execute` は開始しない。

今回の固定範囲では第三者へのRaw／Normalized Dataの公開・再配布を行わない方針とする。ただし、これはBinanceの規約確認を代替するものではない。正式な利用許諾を確定するには、Binanceの適用地域・アカウント・利用目的に紐づくProduct TermsまたはBinanceからの明示回答が必要である。
