# P5-08 Binance固定Runner登録ログ

- Step: `P5-08`
- Phase: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Run: `RUN-P5-08-BINANCE-001`
- Date: `2026-08-15`
- Decision: `P5-08_FIXED_REGISTRATION_COMPLETE_EXTERNAL_EXECUTION_NOT_STARTED`

## 実施内容

運用者の「承認します。登録作業はあなたがやって」を、`P5-DATA-G1-BINANCE-AMENDMENT-001` の承認として記録した。現行の固定範囲はBinance Data Vision公開アーカイブ、Spot、`BTCUSDT`／`ETHUSDT`、1m、2025-02-24T00:00:00Z以上から2026-08-01T00:00:00Z未満、UTC、`CRYPTO_24_7_UTC`である。

次の固定登録を作成した。

- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/request.json`
- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/runner-registration.json`
- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/allowlist.json`
- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/host-isolation.json`
- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/registration-receipt.json`
- `scripts/phase5_external_data/run_binance_data_vision.py`

## 安全境界

- dry-runが既定で、外部通信は0件。
- API key／Secretの値と環境変数は読まない。
- 許可先はHTTPSの `data.binance.vision:443` だけ。ProxyとRedirectは拒否する。
- Spot monthly Kline 1m ZIPと同一URLの`.CHECKSUM`だけを対象とする。
- Futures、Funding、Liquidation、Tick、Order book、REST API主経路、Broker、Paper、Live、Cloud、Core、P4 DBは対象外。
- `.CHECKSUM`照合はダウンロードしたSource Dataの完全性・再現性に直接必要な用途だけであり、文書管理用hash、Manifest hash、Evidence hash、receipt hashは作成していない。

## dry-run結果

固定Runnerのdry-runはローカルで実行し、次の状態を出力した。

- `external_io_performed=false`
- `data_acquired=false`
- `api_key_or_secret_read=false`
- `ready_for_external_io=false`
- `HOST_ISOLATION_NOT_VERIFIED`
- `PROVIDER_TERMS_UNKNOWN`
- `normalization_status=NOT_EXECUTED`
- `quality_status=NOT_EXECUTED`

## 実行前確認（2026-08-15）

登録後、私が外部通信なしで次の確認を実施した。

- Binance公式README／Spot API FAQ／Product Terms noticeを確認した。公開Data、API key不要、Klineのmicrosecond timestamp、`.CHECKSUM`、archive更新可能性は確認できた。
- ただし、READMEのMIT表記を市場Dataそのものの再配布許諾へ拡張できる明示根拠はなく、取得Dataの保持・再配布条件は`UNKNOWN`のままとした。
- Windows Firewall／network／WSL状態を読み取り専用で確認した。`codex_sandbox_offline_block_outbound` がAny protocol／Any port／Any programで非loopback outboundをBlockし、WSL distroはStoppedだった。
- この状態は「Binanceだけ許可する隔離」ではなく、P5-08に必要なprovider-only allowlistのpre／post実行証拠でもない。ネットワークprobe、Binance request、API key／Secret readは0件。

確認Evidence：

- [Provider利用条件確認](../../../tests/evidence/phase5/RUN-P5-08-BINANCE-001/provider-terms-review-20260815.md)
- [Host isolation確認](../../../tests/evidence/phase5/RUN-P5-08-BINANCE-001/host-isolation-check-20260815.json)

このため「登録完了」と「P5-08実行可能」「P5-08 PASS」は分離する。UnknownをPass化していない。

## Runtime dispatch

Rootは`multi_agent_v1__spawn_agent`で`AutoTradeProject_Orchestrator_v0_1`（固定model `gpt-5.6-terra`）を実起動し、wait完了を取得した。Coordinator環境では子Agent起動ツールが利用できず、以下をfallbackとして記録した。

- `RUNTIME_DISPATCH_FALLBACK_REQUIRED`
- `LOCAL_FALLBACK_NO_SUBAGENTS`
- 全5 Agent：`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`

独立Agent実行・独立レビュー済みとは記載しない。

証跡：`tests/evidence/phase5/RUN-P5-08-BINANCE-REGISTRATION-20260815-001/dispatch-receipt.json`

## P5-08の実行前に必要な残作業

1. Binanceの利用・保持・再配布条件を確認し、`provider_terms`をCONFIRMEDにする。
2. OS／host isolationを実行ID付きで取得し、`host-isolation.json`をVERIFIEDに更新する。
3. 明示的にexecuteを開始する。ただし、今回の登録作業では実行していない。
4. Raw ZIP、`.CHECKSUM`、展開CSVを取得後、別途Normalized／Quality／Calendar／Cost／Gap／Holdout Evidenceを作成する。
