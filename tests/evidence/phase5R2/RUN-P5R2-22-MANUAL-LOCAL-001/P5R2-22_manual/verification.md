# P5R2-22 Manual verification

## Scope

`01_バックテスト手順書.html`のP5R2現行章、旧P5R履歴境界、実Application API画面の画像・Capture Registry・リンクを確認した。P5R2-22はlocal-onlyで、Provider、Secret、費用、外部Data Download、実削除、P6を実行していない。

## Assertions

- SCREEN-08の戦略時間足は`15m / 30m / 1h / 4h / 1d`。`1m`はsource説明だけ。
- Data Catalog、`DATA_INSUFFICIENT`確認dialog、銘柄引継ぎ生成画面、source coverage全期間の初期値、複数時間足、`STAGED` Jobをassertした。
- SCREEN-09／SCREEN-10を実Application APIから読み、状態・進捗・取消可否・結果表示保護を確認した。
- desktop／mobileともaxe critical／seriousは0、外部Requestは0。
- Manualのlocal `href`／`src`は198件確認し、欠落0、duplicate id 0。

## Evidence

- desktop: `ui/chromium-desktop/p5r2-manual-capture.json`
- mobile: `ui/chromium-mobile/p5r2-manual-capture.json`
- P5R2-19 condition: `tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/ui/`
- P5R2-21 deletion: `tests/evidence/phase5R2/RUN-P5R2-21-DELETE-LOCAL-001/P5R2-21_delete/ui/`

## Status boundary

これはP5R2-22のlocal green候補であり、H2承認ではない。P5R2完了宣言、P6-H0、P6実装、外部Data取得、Provider接続、Secret、費用は未開始である。
