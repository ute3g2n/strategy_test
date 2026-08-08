# P2-09 Windows側品質Gate

| Gate | 結果 |
|---|---|
| formatter | PASS |
| lint | PASS |
| mypy | PASS |
| pytest | PASS（55 passed） |
| coverage | PASS（80.00%） |

WSL: `run_test.ps1` を `RUN-P2-RPL-001` として実行。`networking_mode=none`、host isolation `CONFIRMED`、formatter/lint/type/test の固定4 Gateはすべて PASS。Run全体は H2-3 の外部承認チャネルが未実施のため `HUMAN_GATE_REQUIRED`（wrapper exit 20）であり、これは4 Gateの失敗ではない。

WSL証跡: `wsl-verification-capture.json`、`automation/run-test-summary.json`、`automation/run-test-evidence.log`。最新実行の `execution_id=81c9a9a166174a588524f5839a36f2ae`。Data GateのUNKNOWN判定は品質GateのPASSとは別の業務判定であり、Phase 3 handoffを許可しない。
