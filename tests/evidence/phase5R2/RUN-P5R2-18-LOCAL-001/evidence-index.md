# RUN-P5R2-18-LOCAL-001 Evidence Index

## 判定

`PASS`。このRunはP5R2-18専用Runnerと品質Gateのlocal検証だけを対象とする。外部Providerへの接続、Data download、E-drive staging／promotionは対象外であり、実行していない。

## 固定4 Gate

- formatter: PASS
- lint: PASS
- type: PASS
- test: PASS（P5R2-18専用pytest入口、9件）
- WSL host outbound isolation: `CONFIRMED`、`networking_mode=none`
- protected fixture: 既存参照をread-only確認

## 主要証拠

- [`verification.json`](./verification.json): 固定4 Gateの結果
- [`host-isolation.json`](./host-isolation.json): WSL隔離状態
- [`wsl-verification-capture.json`](./wsl-verification-capture.json): wrapper execution ID付き取得結果
- [`automation/run-test-summary.json`](./automation/run-test-summary.json): fixed入口の完了状態
- [`P5R2-18_A95_policy.json`](./P5R2-18_A95_policy.json): A95 static fallback
- [`../RUN-P5R2-18-EXTERNAL-001/preflight/registration-preflight.json`](../RUN-P5R2-18-EXTERNAL-001/preflight/registration-preflight.json): 外部Run dry-run（`BLOCKED`）

## 境界

local WSLの隔離確認は、外部Provider Runのhost-level isolation確認ではない。External Runは別の`host-isolation.json`で`NOT_VERIFIED`のまま保持し、execute／download／promotionを停止している。管理用hash、manifest、fingerprint、stale、hash retry、receipt hashは追加していない。
