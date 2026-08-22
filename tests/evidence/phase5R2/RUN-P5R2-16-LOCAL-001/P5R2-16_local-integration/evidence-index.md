# P5R2-16 local integration evidence

- 判定: `P5R2-16_GREEN_CONFIRMED`
- 固定Run: `RUN-P5R2-16-LOCAL-001`
- 固定入口: `scripts/wsl_quality_gate/run_test.ps1`
- 固定4 Gate: formatter / lint / type / test = `PASS`
- 固定対象pytest: `108 passed`
- WSL host outbound isolation: `CONFIRMED` (`networking_mode=none`)
- 外部Provider、login、契約、API call、Data download、Secret、費用、物理削除、Playwright、P6開始: 実施していない

## 証拠ファイル

- [`verification.json`](../verification.json): 固定4 Gateの正式結果
- [`host-isolation.json`](../host-isolation.json): WSLネットワーク隔離結果
- [`automation/run-test-summary.json`](../automation/run-test-summary.json): 固定ラッパー結果
- [`restore.json`](../restore.json): `.wslconfig`復元結果
- [`P5R2-16_GREEN.json`](./P5R2-16_GREEN.json): 本Stepの統合判定
- [`P5R2-16_A95_policy.json`](./P5R2-16_A95_policy.json): A95静的ポリシーfallbackの判定。A95 runtime agent実行とは扱わない
- [`P5R2-16ログ`](../../../../../plan/phase5R2/ログ/P5R2-16_local統合・recovery_2026-08-22.md): 実行・レビュー・境界記録

`host-runner-debug.json`には最終PASSに至る前の失敗試行（承認伝播不足を含む）が履歴として残っている。最終判定は、最終execution ID `72bc6bcb0db448b381f57765d5f1757d`に一致する`verification.json`、`host-isolation.json`、`automation/run-test-summary.json`だけで行う。

## 確認範囲

- legacy `1m` の内部読取境界と利用者向け `15m` / `30m` / `1h` / `4h` / `1d` の選択境界を確認した。
- Job staging、promotion、Catalog current pointer、Run固定DataSet、merge / replace、dedupe / conflict、CSV出力保護を確認した。
- restart、Job途中停止、promotion途中停止、OperationGuard再起動、未完了Run、破損・不一致を `RECOVERY_REQUIRED` または利用不可へ閉じ込めることを確認した。
- 既存P5R履歴を消さず、legacyとcurrentを混在させないことを確認した。

DATA-G1、DELETE-G1、H2、P6はこのEvidenceで承認済みにならない。
