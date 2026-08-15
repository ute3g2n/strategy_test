# RUN-P5-08-BINANCE-001

Binance Data Vision の Spot Kline 1m を使うP5-08の固定登録ルートです。

現在状態は `REGISTERED_NOT_EXECUTED` です。今回の登録では、外部通信、実Data取得、API key／Secret読取、Normalized生成、Quality判定を行っていません。

## 固定対象

- `BTCUSDT`、`ETHUSDT`
- Spot、月次ZIP、1m
- `2025-02-24T00:00:00Z` 以上、`2026-08-01T00:00:00Z` 未満
- UTC / `CRYPTO_24_7_UTC`
- `https://data.binance.vision/data/spot/monthly/klines/{symbol}/1m/{symbol}-1m-{YYYY-MM}.zip`
- 同じURLの `.CHECKSUM`

## 登録ファイル

- `request.json`: 固定要求、期間、symbol、対象path、停止条件
- `runner-registration.json`: 固定Runnerと固定command
- `allowlist.json`: `data.binance.vision:443` のHTTPS許可先
- `host-isolation.json`: 現時点は `NOT_VERIFIED`
- `host-isolation-check-20260815.json`: 読み取り専用のWindows確認結果。全外向きBlockであり、Binance-only allowlistの証拠ではないため `NOT_VERIFIED`
- `provider-terms-review-20260815.md`: Binance公式情報の確認結果。公開取得/API key不要/checksumは確認したが、Data保持・再配布許諾は `UNKNOWN`
- `preflight/registration-preflight.json`: local dry-run結果

## 実行前に残るGate

Provider利用・保持・再配布条件の確認と、OS／host isolationの実証が終わるまで `--mode execute` は停止します。Normalized／Qualityは取得後の別Gateであり、このRunnerの登録だけでPASSにしません。

## 固定dry-run

```powershell
python scripts/phase5_external_data/run_binance_data_vision.py --mode dry-run --request tests/evidence/phase5/RUN-P5-08-BINANCE-001/request.json --registration tests/evidence/phase5/RUN-P5-08-BINANCE-001/runner-registration.json --allowlist tests/evidence/phase5/RUN-P5-08-BINANCE-001/allowlist.json --host-isolation tests/evidence/phase5/RUN-P5-08-BINANCE-001/host-isolation.json --output tests/evidence/phase5/RUN-P5-08-BINANCE-001/preflight/registration-preflight.json
```

`--mode execute` は今回の登録作業では実行していません。
