# CTX-07 GREEN evidence

- Step: CTX-07 — commit前ゲート・監視経路・運用安全化
- 実行日: 2026-08-14
- 判定: ローカルGREEN候補。A07固定runtimeとtrusted scopeは未成立のため、H1候補のPASSではない。

## 実装範囲

- `scripts/context_index/check_context_gate.py`: 明示変更集合、文書保守、決定的コードmanifest更新、relation graph更新、validator、Secret／path／rename／delete拒否、sanitized receipt、allowlistを実装。
- `scripts/context_index/context_watch.py`: H1 receipt検査、単一lock、debounce、直列イベント、生成物自己ループ除外、pending／event log、Gate前段を実装。外部ネットワークと永続サービスは使わない。
- `auto-commit.sh`／`auto-commit.cmd`: Gate PASS後の明示pathだけをstageし、既存index dirty、Gate失敗、allowlist再検証失敗では停止する。`git add -A`は使用しない。
- `package.json`、`scripts/watch-start.js`、`scripts/watch-status.js`、`scripts/watch-stop.js`、`README.md`、`AGENTS.md`に起動条件、停止、PID、ログ、復旧を反映。

## テスト対象

- 新規文書のA07 responseによるrecord追加。
- A07 unavailable時のpending／manifest不変。
- source追加時のcode manifest／relation graph更新。
- Secret、rename／delete、生成物path、H1未承認拒否。
- auto-commitの明示allowlistと既存未追跡ファイル非stage。

## 制限

- 固定A07モデル `gpt-5.1` はruntimeで `Unknown model` となり、A07を独立実行済みとは扱っていない。
- Orchestrator、A110、A120、A130、A150はhandoff／checklist受領のみで、独立レビュー・実行済みとは扱っていない。
- CTX-07の固定4 Gate／trusted scopeは未登録のため、WSL隔離Gateは実行していない。

## ローカル検証結果

```text
pytest tests/context_index -q --cov=scripts/context_index --cov-report=term-missing
73 passed
coverage: 80.10%（fail-under 80%）
ruff check scripts/context_index tests/context_index: PASS
mypy scripts/context_index: PASS（15 source files）
python -m compileall -q scripts/context_index tests/context_index: PASS
document manifest validation: PASS（423 active artifacts, errors=0）
code manifest validation: PASS（254 artifacts, COMPLETE=217, PARTIAL=37, errors=0）
relation graph: PARTIAL（3,279 nodes, 6,939 edges）
```

`npm run watch-start` は `WATCH_START_REJECTED: H1_RECEIPT_MISSING` で終了し、未承認watcherは起動していない。A07固定runtime未成立のため、これは自動保守有効化の合格を意味しない。
