# 実装品質の実行証跡

実行計画は `plan/`、再実行可能なテスト・レビュー・Human Gate 証跡はここに保存します。

```text
test/evidence/{phase_id}/{run_id}/
├── run-manifest.json
├── verification.json
├── test/
├── debug/
├── reviews/
└── human-gate/approval.json
```

Run Manifest は JSON のみです。Secret、API キー、個人情報、外部サービス応答、標準出力・標準エラーは保存しません。`approval.json` は run_id と change_hash を含み、残件が空であることを Human Gate の成立条件とします。
