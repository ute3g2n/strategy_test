# RECOVERY-07 最終レビュー・引渡し記録

- 実行日: 2026-08-16（Asia/Tokyo）
- 対象: Windows/API再起動後のBacktest完了Run履歴復元
- 判定: `COMPLETE_WITH_OPEN_SCOPE`
- 独立Agentレビュー: 未実施（thread limitによるRuntime fallback）

## 1. 最終判定

完了したBacktest Runについて、Eドライブの結果本体と履歴カタログを起動時に読み直し、API履歴・詳細・Ledger・比較・CSV・UI表示へ戻せる状態を実装した。途中、破損、結果参照不一致、結果欠落は成功扱いにせず、`RECOVERY_REQUIRED` または問題一覧として扱う。旧形式の結果だけが残る場合は、推測できない条件を `UNKNOWN` として表示する。

実機Windowsの再起動ボタンを押す手動受入は未実施である。今回の実証は、管理下のAPI子プロセスを停止して同じポートで起動し直すPlaywright試験であり、実機Windows再起動は運用開始前のHuman Gateとして残す。

## 2. 変更範囲の確認

| 分類 | 対象 | 確認結果 |
|---|---|---|
| 永続化 | `src/autotrade/application/history_catalog.py`、`storage_paths.py` | Eドライブ配下、結果本体とcatalog、原子的書込み、パス境界を確認 |
| API・サービス | `backtest_product.py`、`http_server.py` | 起動時restore、RecoveryReport、履歴・詳細・rows・compare・CSVを確認 |
| UI | `backtestApi.ts`、`P5RBacktestScreen.tsx` | 起動時の履歴取得、復元注意表示、結果を開く操作を確認 |
| テスト | `tests/phase5R/test_backtest_history_recovery.py`、Playwright | RED→GREEN、API再起動後の同一Run復元を確認 |
| 文書 | 要件、詳細設計、手順書、完了判定、Index、統合台帳 | P5R-AC-17／REQ-V3-0128とOpen scopeを同期 |

## 3. 検証結果

| 検証 | 結果 |
|---|---|
| `py -3 -m pytest -q tests/phase5R/test_backtest_history_recovery.py` | 7 passed |
| `py -3 -m pytest -q tests/phase5R` | 33 passed |
| `py -3 -m pytest -q tests/application tests/backtest` | 171 passed |
| `npm run build` | PASS |
| `npm run test` | 10 passed |
| `npm run lint` | exit 0。既存warning 5件のみ |
| `npx playwright test --config playwright.backtest-recovery.config.ts` | 1 passed |
| 外部通信 | 0件 |
| A95静的ポリシー確認 | 対象全件 `ALLOW`。管理用の新しい識別値を完了条件に追加していない |

証拠は `tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/` に保存した。Playwright画像は `backtest-history-after-api-restart.png` である。

## 4. Open scopeと引渡し先

- 実機Windows再起動の手動受入: 運用開始前Human Gate。
- 計算途中Runのチェックポイント保存・自動resume: 後続の再開機能設計。
- 過去CSV Jobの状態、Holdoutの一度だけ状態: 永続化統合設計。
- 大量履歴の上限・保持期限・バックアップ: 通常運用前の運用設計。
- P4 SQLite MetadataStoreとの統合: 別の永続化統合設計。

上記は完了扱いにせず、`doc/00_全Phase残課題Blocked統合台帳.html` と完了判定へ残した。

## 5. Runtime dispatchの事実

`multi_agent_v1__spawn_agent` はRECOVERY-01〜07で実際に試行したが、毎回 `collab spawn failed: agent thread limit reached` となった。対象Agentの独立実行・独立レビューとは扱わず、各receiptに `agent_id=N/A`、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK` を記録した。`wait_agent` は起動対象がないため実行していない。

## 6. 引渡し条件

- [x] 変更対象と対象外を確認した。
- [x] Python、UI、Playwright、HTMLリンク、外部通信を検証した。
- [x] Recovery issueを成功扱いしないことを確認した。
- [x] A95の静的ポリシー確認結果を記録した。
- [x] 未実施の実機Windows再起動をOpen scopeとして明記した。
- [x] 自己評価を `tests/evidence/AUTOTRADE-BACKTEST-RECOVERY/RUN-20260816-001/agent-self-evaluation.md` に保存した。
- [x] Git commit `a6c42cb`（`main`）を作成し、`origin/main`へpushした。
