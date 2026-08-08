# P2-12-03 試行履歴と正本

| 実行ID / 時刻 | 結果 | 扱い |
|---|---|---|
| `e8ec794ea5b049c4aa49fdde94d4c190` / 17:59Z | 保護入力が未配置でBLOCKED | Windows入力利用の明示許可より前の履歴。最終状態の根拠にしない。 |
| `8db62aa2e25d4461adaebf95b87ad1ef` / 18:19Z | 実DBN読取り後、UNKでBLOCKED | 管理者権限でリポジトリのdecoderを動かす問題がレビューで見つかったため、受入根拠にしない。 |
| `cfab929d6d12473b9d7633691e4eeb69` / 18:25Z | 通常権限で実DBNを4件読取り後、UNKでBLOCKED | **P2-12-03の正本**。入力hash前後一致、networkingMode=none、外向き通信経路なしを確認。 |

正本の自動実行結果は `automation/run-test-summary.json` の `BLOCKED` と、`wsl-verification-capture.json` の同一実行IDである。`host-runner.json` の `FAILED` は、WSL runnerが安全にBLOCKEDを返したことをPowerShell側が例外として記録した技術上の表現であり、品質GateのFAILEDではない。

やさしい説明: 途中で2回止まりました。1回目は箱が無かったため、2回目は箱の読み方が危なかったためです。危ない読み方を直してから、3回目に安全なやり方で読み直しました。いま見るべき結果は3回目だけです。
