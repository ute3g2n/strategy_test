# RECOVERY-04 GREEN Evidence

- Phase ID: `AUTOTRADE-BACKTEST-RECOVERY`
- Step ID: `RECOVERY-04`
- 設計ID: `P5R-RECOVERY-DD-01`
- 実行日: 2026-08-16

## 対象変更

- `src/autotrade/application/history_catalog.py`
- `src/autotrade/application/storage_paths.py`
- `src/autotrade/application/backtest_product.py`
- `src/autotrade/application/http_server.py`
- `ui/mock/src/backtestApi.ts`
- `ui/mock/src/P5RBacktestScreen.tsx`

## 実行結果

| コマンド | 結果 |
|---|---|
| `py -3 -m pytest -q tests/phase5R/test_backtest_history_recovery.py` | PASS: 7 passed |
| `py -3 -m pytest -q tests/phase5R/test_backtest_product_red.py` | PASS: 8 passed |
| `npm run build`（`ui/mock`） | PASS |
| `py -3 -m compileall -q ...` | PASS |
新形式のcatalog/result保存、サービス再生成後の一覧・詳細・行・比較・CSV、旧形式の明示的legacy復元、破損・不一致・途中状態の復旧必須化、API recovery endpoint、UIの初回履歴取得を確認した。Holdoutの一度だけという状態は今回のRun履歴カタログの対象外であり、別Unknownとして残す。
