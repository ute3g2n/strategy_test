# P3-11 A150 Python / 証跡レビュー

- reviewer: `AutoTrade_A150_PythonCodeReviewer_v0_1`
- verdict: `RETURN_FOR_REMEDIATION`
- critical: 0
- high: 2
- medium: 2

## Findings

- `P3-IR-001`: CalendarPortが6ケースの業務意味論を実行せず、BacktestRunnerへ接続されていない。
- `P3-IR-002`: source-runのcanonical verification、WSL capture、automation summary、restoreの状態を相互検証していない。
- `P3-IR-003`: `_m30`のfallback source IDsと既定`BAR_1M`が、欠落した入力provenanceを通す。
- `P3-IR-004`: `_review_results`は実レビューのFinding内容を検査せずAPPROVEを生成する。

対象範囲の通常機械GateはPASSだが、上記は品質Gateの合否ではなく、契約・監査証跡の不備である。修正後にA150再レビューが必要。
