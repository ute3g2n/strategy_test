# P5R-05〜11 UI品質Evidence

- Run ID: `RUN-P5R-05-20260816-001`
- 対象画面: `SCREEN-08` Backtest製品機能（実P5R Application API）

| 検査 | 結果 |
|---|---|
| `npm run build` | PASS（TypeScript build + Vite build） |
| `npm run test -- --run` | 10 passed |
| `npm run lint` | P5R変更箇所の警告なし。既存 `src/ui.tsx` のFast Refresh警告5件のみ |
| P4 UI回帰 `tests/p4-08.spec.ts --project=chromium-desktop` | 3 passed |
| P5R manual journey `tests/p5r-backtest.spec.ts` | 2 passed（desktop / mobile） |
| Desktop viewport | 1280 x 900 |
| Mobile viewport | 390 x 844 |
| 外部request | desktop 0 / mobile 0 |
| axe critical / serious | desktop 0 / mobile 0 |

P5Rの実画面は固定dummy結果を表示せず、型付きローカルApplication APIを呼び、返されたRun ID、状態、5指標、Ledger、停止理由、評価結果を表示する。APIはループバック限定で、P5R画面から外部Data・Broker・Secret・注文へ接続しない。
