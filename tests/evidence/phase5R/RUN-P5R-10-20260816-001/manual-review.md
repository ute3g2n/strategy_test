# P5R-10 手順書・スクリーンショット統合Evidence

- Run ID: `RUN-P5R-10-20260816-001`
- 正式手順書: `doc/phase5R/07_運用手順/01_バックテスト手順書.html`
- Playwright: `ui/mock/tests/p5r-backtest.spec.ts`
- Capture Run: `RUN-P5R-09-20260816-001`

## P5R-MANUAL-G1 判定

| 条件 | 結果 |
|---|---|
| H1代理承認と固定scope登録 | PASS。`RUN-P5R-00-20260816-001/h1-decision.json`、`RUN-P5R-03-20260816-001/registration-receipt.md` |
| 実Application APIの実結果 | PASS。各journeyが実Run / Job / Holdout / Walk-forward応答をassert |
| Desktop | 15 / 15 capture、1280 x 900 |
| Mobile | 15 / 15 capture、390 x 844 |
| assert後撮影 | 全30枚で `assertion_before_screenshot = Playwright DOM assertions passed` |
| 外部request | Desktop 0、Mobile 0 |
| axe critical / serious | Desktop 0、Mobile 0 |
| HTML画像・リンク | 画像15枚、詳細設計2件、capture registryとEvidenceリンクを静的確認 |

採用した正式画像は、Playwright EvidenceのDesktop 15枚を機械的に `doc/phase5R/07_運用手順/assets/backtest_manual/` へコピーしたものだけである。手作業で作成・加工した画像、P4固定dummy画像、外部Data画面は含めていない。
