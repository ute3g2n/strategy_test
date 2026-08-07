# 実装品質の実行証跡

実行計画は `plan/`、再実行可能なテスト・レビュー・Human Gate 証跡はここに保存します。

```text
tests/evidence/{phase_id}/{run_id}/
├── run-manifest.json
├── verification.json
├── test/
├── debug/
├── reviews/
└── human-gate-user-declaration.md
```

Run Manifest は JSON のみです。Secret、API キー、個人情報、外部サービス応答、標準出力・標準エラーは保存しません。Human Gateは、対象Runに対するユーザーの「承認します」という明示的な意思表示を `human-gate-user-declaration.md` に記録し、機械Gate、レビュー、残件の確認がすべて通ることを成立条件とします。署名鍵や外部承認チャネルは使いません。
