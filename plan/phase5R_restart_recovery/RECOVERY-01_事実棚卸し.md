# RECOVERY-01 事実棚卸し・設計境界

- Phase ID: `AUTOTRADE-BACKTEST-RECOVERY`
- Step ID: `RECOVERY-01`
- 実行日: 2026-08-16（Asia/Tokyo）
- 実行方式: ルートAgentによるFallbackチェックリスト。独立Agentはruntime thread limitのため未起動。
- 関連受領記録: [RECOVERY-01-runtime-dispatch.md](./RECOVERY-01-runtime-dispatch.md)

## 1. 結論

現行の画面履歴は、`BacktestProductService`のPythonプロセス内辞書から作られている。`result.json`はEドライブに残るが、API起動時に読み込む処理がない。したがって、ブラウザ更新だけならAPIが生きている間は履歴が残るが、APIプロセスまたはWindowsを再起動すると、画面のRun履歴は空になる。

今回の最小完成方針は、P5Rの既存HTTP APIへ直接接続できるEドライブ上のJSON履歴カタログを追加することである。P4の未接続SQLite `MetadataStore`は、別契約・別状態機械・別APIのため、この修正では接続しない。新しい保存場所は次のとおりとする。

```text
E:\strategy_test_data\autotrade\backtest\
├─ results\<run_id>\result.json       # 結果本体。既存形式を継承
├─ exports\<job_id>\result.csv        # CSV結果
└─ catalog\runs\<run_id>.json         # 履歴一覧・再表示に必要なRun情報
```

`catalog`は、学校の答案ファイルに貼る「名前・条件・点数・保存場所」の台帳に相当する。結果本体と台帳を分けるが、どちらか一方だけを信用して成功表示しない。

## 2. コード事実

| 事実 | 根拠 | 影響 |
|---|---|---|
| 起動時に`BacktestProductService`を1個作る | `src/autotrade/application/http_server.py:17` | 新しいPythonプロセスごとに空のサービスが作られる |
| Run一覧は`self._runs.values()`だけを読む | `src/autotrade/application/backtest_product.py:227-230` | ディスクのresult.jsonは一覧に入らない |
| Run詳細・rowsも`self._runs`だけを読む | `backtest_product.py:220-236` | 再起動後の旧Runは404になる |
| Run作成時に辞書へ登録し、threadを起動する | `backtest_product.py:206-218` | 登録がメモリだけで永続化されていない |
| 結果は`results/<run_id>/result.json`へ書く | `backtest_product.py:997-1002` | 結果本体は残る |
| result.jsonの現形式は`run_id`、`metrics`、`rows`、`provenance` | Eドライブの既存18 Runを代表確認 | spec、状態、開始時刻、終了時刻などが不足する |
| APIの履歴取得は`GET /api/backtest/runs/history` | `http_server.py:47-48` | サービスの復元処理を実装すれば既存UI APIを再利用できる |
| UIは履歴タブを押したときに`listRuns()`を呼ぶ | `ui/mock/src/P5RBacktestScreen.tsx:137-141,253` | API復元後、履歴タブへ移動すれば一覧を取得できる |
| UIの「結果を開く」はRun IDのrows APIを呼ぶ | `P5RBacktestScreen.tsx:176-178,288` | `get_rows`復元が必要 |
| P4 MetadataStoreはP4 API用である | `src/autotrade/application/persistence.py`、`api.py`、P4 tests | P5R HTTP APIへ直接接続するには別統合設計が必要 |

## 3. Eドライブの現状

- `E:\strategy_test_data\autotrade\backtest\results`は存在する。
- 2026-08-16の確認時点でRunディレクトリは18個あり、確認対象はすべて`result.json`を持っていた。
- `catalog`、`metadata`、`history`はまだ存在しない。
- 既存result.jsonは旧形式で、先頭は`run_id`、`metrics`、`rows`、`provenance`である。
- 既存結果を作業用fixtureとしてリポジトリへコピーしない。旧形式互換テストでは、小さな匿名JSONをテスト内で作る。

## 4. 復元契約の分類

| 入力状態 | 画面に返す状態 | 扱い |
|---|---|---|
| 新形式catalogとresult.jsonがそろい、内容が一致 | `SUCCEEDED`等の保存状態 | 通常の履歴・詳細・rows・比較に使う |
| 旧形式result.jsonだけがある | `SUCCEEDED`、`provenance.recovery_mode=LEGACY_RESULT_ONLY` | 既知値だけ復元。不明な条件は`UNKNOWN`等で明示 |
| catalogがあるがresult.jsonがない | `RECOVERY_REQUIRED` | 成功扱いせず、回復問題として扱う |
| result.jsonがJSONとして壊れている | `RECOVERY_REQUIRED`またはrecovery issue | 一覧から黙って消さず、問題を取得可能にする |
| catalogのrun_idとファイル名が不一致 | `RECOVERY_REQUIRED`またはrecovery issue | パス・ID混同を受け入れない |
| catalogがresults外の相対パスを指す | `RECOVERY_REQUIRED`またはrecovery issue | パス脱出を拒否する |
| 旧catalogがQUEUED/RUNNING | `RECOVERY_REQUIRED` | 終了したthreadを自動再開・成功扱いしない |
| 旧catalogがCANCELLEDでStrategyStateがない | `RECOVERY_REQUIRED` | 現状の同一プロセス専用再開を、再起動後へ拡張しない |
| catalogがFAILED | `FAILED` | 失敗理由を保持し、成功扱いしない |

## 5. 旧形式から安全に分かる範囲

現在のresult.jsonから、次は安全に取り出せる。

- Run ID: `run_id`
- 指標: `metrics`
- Ledger: `rows`
- Data由来: `provenance`
- 銘柄: rowsのsymbolが一意ならその値。複数または無い場合は`UNKNOWN`
- 開始・終了: metricsの`period_start_utc`、`period_end_utc`が正しいUTC文字列なら使用
- Strategy: provenanceの`core_validation.selected_system`が`SYS1`または`SYS2`なら、それぞれ`TURTLE_SYS1`または`TURTLE_SYS2`と表示
- Entry/Exit lookback: `core_validation`に存在する場合だけ使用
- Fee/Slippage: provenanceに値がある場合だけ使用
- 初期残高: 最初のBALANCE行のcashが妥当な文字列の場合だけ使用

次は旧形式から確定できないため、推測しない。

- 正確な作成時刻、開始時刻、終了時刻
- 元のclient request id
- 旧RunがSweep childだったかどうか
- 途中状態のStrategyState、完全な再開情報
- 保存時点でのcatalog状態

旧形式復元には`recovery_mode=LEGACY_RESULT_ONLY`を付け、ユーザーが新形式と同じ完全な履歴情報だと誤解しないようにする。

## 6. 必須テストと追跡

| テストID | 保証すること | 種別 |
|---|---|---|
| `RECOVERY-T-01` | 完了Run作成後にサービスを作り直すとRun一覧へ復元される | pytest / integration |
| `RECOVERY-T-02` | 復元Runのmetrics、provenance、rowsが元と一致する | pytest |
| `RECOVERY-T-03` | 復元RunのcompareとCSV生成が使える | pytest |
| `RECOVERY-T-04` | 旧形式result.jsonだけでも既知値を復元し、不明値を作らない | pytest |
| `RECOVERY-T-05` | 壊れたJSON、ID不一致、results外パス、result欠落を成功扱いしない | pytest |
| `RECOVERY-T-06` | QUEUED/RUNNINGを再起動後に自動成功・自動再開しない | pytest |
| `RECOVERY-T-07` | APIプロセス再起動後にhistory/detail/rowsが戻る | HTTP integration |
| `RECOVERY-T-08` | UIで再起動前のRunを履歴から開き、Ledgerが表示される | Playwright |
| `RECOVERY-T-09` | 新規catalogがEドライブ配下で、禁止名・Cドライブに依存しない | pytest |
| `RECOVERY-T-10` | 外部リクエストが0件である | Playwright |

## 7. A05/A10/A90/A95の責務チェック（Fallback適用）

### A05相当: Phase実行計画

- Stepを調査→設計→RED→実装→統合検証→文書→最終レビューに分けた。
- 設計承認とRED確認を実装より前に置いた。
- API再起動とUI操作を別の受入条件にした。

### A10相当: 要件・Unknown追跡

- P5Rの「履歴・比較」「CSV」「結果詳細」へ再起動復元を接続する。
- P4 SQLite統合、途中Run完全再開、大量Runの運用は今回のUnknownとして残す。
- P6以降のForward/Shadow/Paper/Liveは対象外のままにする。

### A90相当: 設計レビュー

- 結果本体だけで履歴の完全復元とみなさない。
- 旧形式の不足情報を推測で埋めない。
- 壊れたファイルを黙って無視しない。
- 実行中Runを自動再開しない。
- Eドライブ以外へ保存しない。

### A95相当: 管理用hash再導入判定

- 今回のカタログはRun ID、状態、spec、結果参照、schema versionを使うが、管理用hashは使わない。
- 既存のData identityやCore由来の保護情報は、今回の履歴管理用に新しいhashを生成しない。
- manifest、stale、fingerprint、hash retry、管理用checksumを完了条件に追加しない。
- これはA95 Agentの独立実行結果ではなく、Fallback時のルートチェックである。

## 8. Step 1判定

`RECOVERY-01`は、独立Agentのruntime実行についてはFallbackである。一方、必要なコード・保存ファイル・UI・既存設計の事実確認、保存場所、復元状態、テスト境界は確認できた。P5Rの現HTTP APIへ接続するEドライブJSONカタログの詳細設計へ進める。詳細設計で保存スキーマ、原子性、破損時のAPI応答、UIの回復表示を確定する。
