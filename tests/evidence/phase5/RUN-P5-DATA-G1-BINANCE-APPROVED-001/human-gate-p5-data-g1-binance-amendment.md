# P5-DATA-G1 Binance amendment 承認記録

- Status: `APPROVED`
- Gate ID: `P5-DATA-G1-BINANCE-AMENDMENT-001`
- Phase: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Recorded at: `2026-08-15T14:24:04+09:00`
- Approval source: 運用者の明示メッセージ「承認します。登録作業はあなたがやって」

## 承認範囲

この承認は、Binance Data Vision の公開アーカイブを使う現行P5-08範囲の登録作業を対象とする。

- Provider: `https://data.binance.vision/`
- Asset class: crypto
- Market segment: Spot
- Symbols: `BTCUSDT`, `ETHUSDT`
- Base interval: `1m`
- Period: `2025-02-24T00:00:00Z` 以上、`2026-08-01T00:00:00Z` 未満
- Time basis: UTC / `CRYPTO_24_7_UTC`
- Archive: Spot monthly Kline ZIP と同一URLの `.CHECKSUM`
- Evidence root: `tests/evidence/phase5/RUN-P5-08-BINANCE-001/`
- Run ID: `RUN-P5-08-BINANCE-001`
- Provider data cost: `0 USD`; internal storage、通信、実行usage監査は別管理
- 公開アーカイブ取得ではAPI key、Secret、entitlement、既存環境変数を使用・読取しない

## 承認除外

Binance Futures、Funding、Liquidation、Tick、Order book、REST API主経路、Broker、Paper、Live、実注文、実資金、実Risk、Cloud、Core変更、symbol追加、Provider変更、API key／Secret用途は承認しない。

## 状態の注意

この記録はP5-DATA-G1の対象範囲と登録作業の承認であり、実Data取得、host isolationの確認、Provider利用条件の確認、Normalized／Quality PASSを意味しない。未確認事項はUnknownのまま保持し、固定Runnerのdry-runで停止理由を明示する。
