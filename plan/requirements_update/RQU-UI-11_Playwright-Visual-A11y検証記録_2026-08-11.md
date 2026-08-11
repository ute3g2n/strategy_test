# RQU-UI-11 Playwright E2E・Visual・アクセシビリティ検証記録

## 1. 実行情報

| 項目 | 内容 |
|---|---|
| Step ID | `RQU-UI-11` |
| Phase ID | `REQUIREMENTS_UI_UPDATE_2026_08_11` |
| Orchestrator | `AutoTradeProject_UiMock_Orchestrator_v0_1` |
| 対象 | React UIモック、オフライン静的HTML UIモック候補 |
| 固定Seed | `20260811` |
| Evidence Run | `tests/evidence/requirements_ui/RQU-UI-11-20260811-1325/` |
| 最終状態 | `COMPLETED_WITH_OPEN_FINDINGS`（RQU-UI-13でF-007/F-008を解消） |
| 外部取得 | なし。Broker、市場データ、Secret、通知、外部APIには接続していない |

## 2. Findings first

| Finding ID | 重大度 | 内容 | 対応 | 状態 |
|---|---|---|---|---|
| `RQU-UI-11-F-001` | High | 初回実行で、複数のstatus要素・状態バッジに対するPlaywright指定が厳密すぎた | 対象領域を限定し、状態バッジは先頭要素を指定するように修正 | 解消 |
| `RQU-UI-11-F-002` | High | 初回実行でReact側に色コントラストと横スクロール領域のキーボード操作違反が検出された | muted色を調整し、`.table-scroll`へtabIndex/aria-labelを付与 | 解消 |
| `RQU-UI-11-F-003` | High | 初回実行でスマートフォン幅の静的HTMLに、非表示scrimと表スクロール領域の問題が検出された | `[hidden]`の表示規則と`.table-wrap`のtabIndex/aria-labelを追加 | 解消 |
| `RQU-UI-11-F-004` | Medium | UIは固定ダミーとローカル実行だけであり、実Broker・実市場データ・実通知の接続可否は未実証 | RQU-UI-12以降および後続Gateで実証対象として保持 | Open（Unknown） |
| `RQU-UI-11-F-005` | Medium | 正式要件・正式UIへの昇格はRQU-UI-H3承認前のため未実施 | candidateのまま保持し、H3で差分と証跡を提示 | Open（Gate待ち） |

Unknownを`Pass`へ変更したものはない。外部接続を行わないことは、接続成功の証明ではなく、この検証の安全境界として扱う。

## 3. 実行内容

`ui/mock/tests/rqu-ui-11.spec.ts`に、次の8種類の検証をPC幅・スマートフォン幅で実装した。

1. Backtest条件入力、網羅検証、結果、Forward/Shadow、Paper/Live、Human Gate、停止・復旧、警告対応の主要操作経路。
2. `NORMAL`、`LOADING`、`EMPTY`、`REQUIRED`、`WARNING`、`STOPPED`、`FAILED`、`RECOVERY`、`HUMAN-GATE`、`UNAPPROVED`の10状態と影響・次操作。
3. キーボード操作、Base UI Dialog、Escapeによる閉じる操作、フォーカス復帰。
4. React版21画面の到達性。
5. React版21画面のaxe critical/serious検査。
6. 静的HTML版21画面の到達性、外部リクエスト検査、画像証跡。
7. 静的HTML版21画面のaxe critical/serious検査。
8. RQU-UI-13の安全操作（確認Dialog、Live自動承認、網羅検証入力、重複判定、Strategy理由、H1/M30）検査。

Playwright CLIを使う場合の探索と、`@playwright/test`による再現可能な正式検証を混同しないよう、正式証跡は`@playwright/test`に固定した。今回の証跡は固定コマンドと固定Seedで再実行できる。

## 4. 実行コマンドと結果

| コマンド | 結果 |
|---|---|
| `npm run build` | PASS |
| `npm run lint` | PASS_WITH_WARNINGS（既存のFast Refresh警告5件、エラー0） |
| `npm run test:e2e:rqu-ui-11 -- --update-snapshots` | PASS（18/18）。RQU-UI-13修正後のbaseline生成に使用 |
| `npm run test:e2e:rqu-ui-11` | PASS（18/18、skip 0、unexpected 0） |
| `git diff --check` | PASS |

最終`results.json`の期待値は18、unexpectedは0、flakyは0である。PC/スマートフォン各9テストを実行し、React/静的HTMLの全21画面をそれぞれ到達確認した。Reactの21画面×10状態は各viewportで210/210セル、静的HTMLは遷移完了後に全21画面と重要7画面をVisual比較した。

## 5. 証跡

| 種別 | 証跡 |
|---|---|
| Playwright結果 | `tests/evidence/requirements_ui/RQU-UI-11-20260811-1325/results.json` |
| HTMLレポート | `tests/evidence/requirements_ui/RQU-UI-11-20260811-1325/playwright-report/` |
| Reactルート | `react-route-summary-chromium-desktop.json`、`react-route-summary-chromium-mobile.json` |
| 静的HTMLルート | `static-route-summary-chromium-desktop.json`、`static-route-summary-chromium-mobile.json` |
| 外部境界 | 静的HTMLの`externalRequests: []`、ブラウザイベント全件の`externalRequests: []` |
| axe | `a11y-react-chromium-desktop.json`、`a11y-react-chromium-mobile.json`、`a11y-static-chromium-desktop.json`、`a11y-static-chromium-mobile.json`。各21画面、critical/serious 0件 |
| 画像 | `screenshots/`配下のPC/スマートフォンReact・静的HTML画像、およびPlaywright snapshot。遷移完了待ちと重要7画面の比較をRQU-UI-13で再実行。画像はGit管理外 |
| 失敗時証跡 | trace/video/screenshotをretain-on-failureで保存する設定。最終実行では失敗なし |

## 6. 追跡と受入確認

- 画面識別子は`SCREEN-01`〜`SCREEN-21`、状態識別子は`NORMAL`等10件、操作記録は`RQU-UI-11`へ追跡した。
- 画面・要求・ユースケースの対応は、`RQU-UI_要件UIテスト追跡マトリクス_2026-08-11.md`のRQU-UI-11追跡行を正本とする。
- 受入項目は、同日付の`RQU-UI_UIモック受入確認表_2026-08-11.md`のRQU-UI-11項目へ記録した。
- 主要Critical/Highの自動検証は最終実行でPassした。ただし、実運用接続、Q-243の実証、正式化は後続Gateで確認する。

## 7. 次工程

RQU-UI-11の自動検証は完了したため、RQU-UI-12の専門領域・Design・Red Teamレビューへ進む。レビューでは、実接続を行ったと誤認させる表現、Human Gateの安全境界、初期候補5銘柄、5時間足、同時運用単位、Unknownの扱い、Q-243の確認と後続実証の分解を優先して監査する。RQU-UI-H3未承認のため、正式要件HTML、`doc/index.html`、正式UI状態への変更は行わない。

RQU-UI-12の画像レビューで検出したDrawer閉じる遷移中の撮影競合は、RQU-UI-13で遷移完了待ちと静的重要7画面の個別比較を追加して解消した。静的HTMLは表示・導線専用、操作可能性はReact版で確認する範囲差も候補文書へ明記した。

## 8. 変更履歴

| 版 | 日付 | 内容 |
|---|---|---|
| `v0.1` | 2026-08-11 | RQU-UI-11の初回失敗（指定・コントラスト・モバイルスクロール）を検出し修正、baselineを生成 |
| `v0.2` | 2026-08-11 | PC/スマートフォン14テスト、21画面ルート、4 axe結果、外部リクエスト0件を再実行で確認。Open Unknownを保持 |
| `v0.3` | 2026-08-11 | RQU-UI-13でLive自動承認・危険操作・網羅検証入力・重複判定・時間足を追加検証。React 21×10状態、静的重要7画面Visual、Drawer遷移待ちを確認し、18/18へ更新。画像はGit管理外。 |
