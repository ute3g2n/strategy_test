# AUTOTRADE-APP-STARTUP-PLAN-001 Step 1 Traceability

| 事実・要求 | 確認元 | 次Stepへの反映 |
|---|---|---|
| UIはVite previewで配信する | `ui/mock/package.json` | `npm run build`後に`npm run preview` |
| APIはloopbackの8765で待ち受ける | `scripts/phase5r/backtest_api_server.py`、`src/autotrade/application/http_server.py` | `127.0.0.1:8765`固定 |
| UIの既定APIは8765 | `ui/mock/src/backtestApi.ts` | UI/APIのポートを一致させる |
| UI/APIのE2Eは別プロセスを使う | `ui/mock/playwright.config.ts` | 起動Smokeでも2プロセスを確認 |
| 既存の起動batはアプリ用ではない | ルート`*.bat`/`*.cmd`棚卸し | 新規`start_autotrade.bat`を作る |
| カレントディレクトリ依存を避ける | Windows batの入口要件 | `%~dp0`からルートを解決 |
| 無関係なプロセスを終了しない | プロジェクト安全境界 | 競合時Fail-closed、停止時も対象確認 |
| 外部接続を追加しない | API安全境界・Backtest対象 | bind先を127.0.0.1に固定 |
| 手順書に初心者向け起動説明が必要 | バックテスト操作手順書の現状 | 起動・成功・失敗・停止を追補 |
| 独立Agent起動 | Runtime Receipt | thread limitにより未受理。自己レビューと明記 |

## 未解決・継承

- `P5R-UNK-001`は変更しない。
- 本作業はアプリ起動の利便性を整えるもので、Backtestの結果妥当性や本番運用の承認を意味しない。
