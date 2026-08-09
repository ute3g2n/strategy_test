# RUN-P3-GOLD-001 ローカル品質記録

- formatter: PASS
- lint: PASS
- type (`scripts/quality_gate`): PASS
- fixture / runner GREEN: 46 passed（品質gate自身 36件、fixture契約 10件）
- P3固定pytest: EXPECTED_RED（78 failed, 10 passed）。未実装のStrategy/Backtest契約を普通の失敗として固定した結果であり、品質GateのPASSではない。

外部通信、Broker、Secret、実engine、実データ取得は使っていない。
