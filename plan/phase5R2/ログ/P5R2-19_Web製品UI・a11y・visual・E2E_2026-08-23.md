# P5R2-19 Web製品UI・a11y・visual・E2E 実行ログ

- Step: `P5R2-19`
- Run: `RUN-P5R2-19-LOCAL-001`
- 判定: `LOCAL_UI_VERIFIED_WITH_RUNTIME_FALLBACK`
- 実行日: `2026-08-23`

## 実行範囲

P5R2-16のlocal統合GREEN、P5R2-H1、P5R2-18 externalのhost-level isolation未確認を入力に、実Application APIへ接続するUIをlocal loopbackだけで統合した。P5R2-18の外部Data受入完了は前提にせず、外部request 0で検証した。

実装した範囲は次のとおり。

- 戦略時間足を `15m / 30m / 1h / 4h / 1d` に限定し、`1m` はsource説明だけにした。
- Catalogに銘柄、時間足、期間、quality、usable、legacy、Job状態、provenanceを表示した。
- `DATA_INSUFFICIENT` のエラー、生成確認Dialog、銘柄・時間足・期間の引継ぎ、複数時間足生成、Catalogから任意に開ける生成画面を接続した。
- source DatasetのIDだけをブラウザから受け、OHLCV本体はサーバー側で解決する境界にした。
- SCREEN-09とSCREEN-10を同じRun API状態・取消理由へ接続し、in-flight UI二重操作を無効化した。
- DELETE-G1未承認中は結果表示削除をdisabledにし、`DELETE_GATE_REQUIRED`を表示した。物理削除は実行していない。
- 外部Downloadは`HOST_LEVEL_ISOLATION_NOT_VERIFIED`で停止し、Provider、Secret、費用、外部Data取得を行っていない。

## Runtime truthfulness

rootからCoordinator proxy `01a02b67-3f14-7493-98d6-9abc024c4948`を起動したが、nested named Agent dispatchが利用できず、Coordinator proxyは完了前にshutdownした。したがって、A172、A130、A171、A95の独立完了は主張しない。rootが実装・検証・A95静的判定を実施し、`independent=false`、`review_mode=SELF_REVIEW_FALLBACK`としてruntime receiptへ記録した。

## 検証結果

- Backend P5R2対象回帰: `63 passed`
- UI build: PASS
- UI lint: PASS（既存Fast Refresh warningのみ）
- UI Vitest: `13 passed`
- P5R2専用Playwright: desktop `1280x900`、mobile `390x844`ともPASS
- axe: P5R2専用3画面旅程でcritical／serious violation `0`
- keyboard／focus: strategy timeframe selectのfocus検証PASS
- 外部request: 許可された`127.0.0.1:4173`／`127.0.0.1:8765`以外 `0`
- P4-08履歴回帰: desktop／mobileの3テストずつPASS（旧P5R2画面は明示legacy-history entryから検証）

既存の全E2E一括実行には、P5R旧テストの長時間旅程・既存visual baselineなど、P5R2の受入範囲外の履歴テストが含まれ、全体greenとは判定していない。P5R2の合否は専用Evidenceで分離している。

## 禁止境界

DELETE-G1、H2、P6は未承認・未開始のまま保持する。既存Historical Data、Run、Audit、Evidence、Export済みCSVの削除、外部Provider接続、Secret、費用、外部Data取得は行っていない。

## 成果物

- [P5R2-19 verification](../../tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/P5R2-19_ui/verification.md)
- [P5R2-19 GREEN](../../tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/P5R2-19_GREEN.json)
- [P5R2-19 runtime receipt](../quality/runtime-receipt-P5R2-19.json)
- [P5R2-19 capture registry](../../tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/P5R2-19_ui/ui-capture-registry.md)
- [P5R2-19 A95 policy](../../tests/evidence/phase5R2/RUN-P5R2-19-LOCAL-001/P5R2-19_A95_policy.json)

次はP5R2-20のDELETE-G1 packet作成へ進む。承認前の物理削除は行わない。
