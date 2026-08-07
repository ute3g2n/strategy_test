# S4.4 独立 Python レビュー

- Run ID: `RUN-P2-IC-001`
- Design: `P2-D07`
- Requirements: `REQ-Q02`, `REQ-Q19`, `REQ-Q20`, `REQ-Q23`
- HEAD commit: `8d3f3d3dd41b6d5b33e6b870a3f5b4f1b10ffab4`
- 実差分 SHA-256: `sha256:fd8033a64a8949570ce3231ead103e0a1f28f168b1f14a2a3f8b5bb1ee8a7419`
- fixture SHA-256: `sha256:94022229698e972353b8ec9537f455af5cb29d47253f5f2a1ed5d33b08b50169`
- 参照 Manifest: `tests/evidence/phase2/RUN-P2-IC-001/run-manifest.json`
- 参照 registry: `scripts/quality_gate/trusted_scopes.json`
- TDD 証跡: `tests/evidence/phase2/RUN-P2-IC-001/tdd-quality-gate-extension-red.md`

## 実施順序と再現手順

1. `.venv\\Scripts\\python.exe -m ruff format --check src/autotrade/market_data tests/market_data` → 終了コード 0
2. `.venv\\Scripts\\python.exe -m ruff check src/autotrade/market_data tests/market_data` → 終了コード 0
3. `.venv\\Scripts\\python.exe -m mypy src/autotrade/market_data` → 終了コード 0
4. `.venv\\Scripts\\python.exe -m pytest tests/quality_gate/test_runner.py tests/market_data -q` → 39 passed
5. `git diff --check` → 終了コード 0
6. production scope の禁止依存検索（Databento/Broker/Secret/HTTP client）を実施。該当は docstring の安全宣言だけで、import/call はない。

TDD は RED（wrapper import 不在）を保存後、GREEN（quality-gate 30 passed、全体 42 passed、P2 wrapper 9 passed）を保存済みである。4 Gate の最終結果は [verification.json](../verification.json) にあり、formatter/lint/type/test/coverage は全て終了コード 0 と記録されている。

## Findings

| Finding ID | 重要度 | 状態 | 根拠 | 再現手順 | 修正要否 | 再レビュー結果 |
|---|---|---|---|---|---|---|
| S4.4-PY-001 | Critical/High なし（Info） | CLOSED | `ruff format --check`、`ruff check`、`mypy`、対象 pytest が全て成功。固定 fixture 以外の I/O はない。 | 上記 1–6 を順番に実行 | 不要 | S4.4 実行で PASS |
| S4.4-PY-002 | High | OPEN | Runner の実差分検査は `target_paths 外の変更を検出しました` を返している。これは Python 実装の局所品質とは別に、受入 scope を破る残件である。 | host isolation marker を確認した上で `LocalQualityGateRunner(...).run(manifest, write_evidence=False)` を実行 | 必須。scope 外差分を除去するか、承認済み baseline を更新してから hash を再計算 | 未解消。Run は BLOCKED のまま |
| S4.4-PY-003 | Medium | CLOSED | `GitChangeInspector` は Unicode untracked path を NUL 区切りで扱い、`tests/evidence/**` を hash から除外する。Manifest の hash と再計算値が一致する。 | `GitChangeInspector().change_hash(Path.cwd(), "HEAD")` と Manifest の `change_hash` を比較 | 不要 | S4.4 実行で PASS |

## 判定

Python コード上の Critical/High は 0 件。ただし S4.4-PY-002（scope 外差分）が未解消であり、設計外変更を含むため、このレビュー単独でも Human Gate へ進めない。判定は `BLOCKED`。

