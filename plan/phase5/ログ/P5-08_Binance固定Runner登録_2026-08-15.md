# P5-08 Binance固定Runner登録ログ

- Step: `P5-08`
- Phase: `PHASE5_MARKET_DATA_OPERATIONALIZATION_EVIDENCE_2026_08_12`
- Run: `RUN-P5-08-BINANCE-001`
- Date: `2026-08-15`
- Decision: `P5-08_RAW_AND_EXPANDED_CSV_ACQUIRED_OPERATOR_WAIVER`

## 実施内容

運用者の「承認します。登録作業はあなたがやって」を、`P5-DATA-G1-BINANCE-AMENDMENT-001` の承認として記録した。現行の固定範囲はBinance Data Vision公開アーカイブ、Spot、`BTCUSDT`／`ETHUSDT`、1m、2025-02-24T00:00:00Z以上から2026-08-01T00:00:00Z未満、UTC、`CRYPTO_24_7_UTC`である。

次の固定登録を作成した。

- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/request.json`
- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/runner-registration.json`
- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/allowlist.json`
- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/host-isolation.json`
- `tests/evidence/phase5/RUN-P5-08-BINANCE-001/operator-waiver-20260815.md`
- `scripts/phase5_external_data/run_binance_data_vision.py`

## 安全境界

- dry-runが既定。今回のexecuteは運用者waiverと明示コマンドにより、固定範囲へ限定した。
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
- `ready_for_external_io=true`
- `host_isolation_gate=OPERATOR_WAIVED`（事実は`NOT_VERIFIED`）
- `provider_terms_gate=OPERATOR_WAIVED`（事実は`UNKNOWN`）
- `operator_waiver_applied=true`
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

このため「開始前提のwaiver」「外部取得完了」「P5-08全体PASS」は分離する。Provider条件とhost isolationはUnknown／未検証のままであり、Normalized／Qualityを未実行のためP5-08全体PASSとはしていない。

## Runtime dispatch

Rootは`multi_agent_v1__spawn_agent`で`AutoTradeProject_Orchestrator_v0_1`（固定model `gpt-5.6-terra`）を実起動し、wait完了を取得した。Coordinator環境では子Agent起動ツールが利用できず、以下をfallbackとして記録した。

- `RUNTIME_DISPATCH_FALLBACK_REQUIRED`
- `LOCAL_FALLBACK_NO_SUBAGENTS`
- 全5 Agent：`agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`

独立Agent実行・独立レビュー済みとは記載しない。

証跡：[`root runtime receipt`](../../../tests/evidence/phase5/RUN-P5-08-BINANCE-001/dispatch/P5-08-root-runtime-receipt-20260815.json)、[`Coordinator receipt`](../../../tests/evidence/phase5/RUN-P5-08-BINANCE-001/dispatch/P5-08-execution-coordination-receipt-20260815.json)

## 実行結果（2026-08-15）

運用者waiverを適用したうえで、固定Runnerの`--mode execute`を実行した。

- [開始Evidence](../../../tests/evidence/phase5/RUN-P5-08-BINANCE-001/execution-start-20260815.json)
- [完了Evidence](../../../tests/evidence/phase5/RUN-P5-08-BINANCE-001/execution-finish-20260815.json)
- [取得サマリ](../../../tests/evidence/phase5/RUN-P5-08-BINANCE-001/execution-summary.json)
- 対象：`BTCUSDT`／`ETHUSDT` × 18月 = 36件
- 成果物：Raw ZIP 36件、`.CHECKSUM` 36件、展開CSV 36件、未完了`.part` 0件
- 検証：checksum不一致0、timestamp unit不一致0、重複timestamp 0、symbol／月範囲違反0
- API key／Secret読取：`false`。Provider data cost：`0 USD`
- `normalized_status=NOT_EXECUTED`、`quality_status=NOT_EXECUTED`

## 実行後の残作業

1. P5-09でRaw／展開CSVからNormalized、D1／H4／H1／M30／M15、Quality、`CRYPTO_24_7_UTC`、Cost／Gap、Holdout Evidenceを作成する。
2. Provider条件=`UNKNOWN`、host isolation=`NOT_VERIFIED`をPassへ変換せず、waiver適用事実とともに台帳へ保持する。
3. 子Agent未起動fallbackを独立レビュー済みと表記せず、P5-09以降のレビュー実行時に新しいdispatch receiptを保存する。
