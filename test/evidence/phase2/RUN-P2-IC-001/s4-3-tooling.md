# RUN-P2-IC-001 S4.3 品質ツール設定・証跡

## 判定

`BLOCKED`。`.venv` の Python 3.12.13 を確認し、ユーザーが取得を許可したため、PyPI の固定版 `ruff==0.16.1` と `mypy==2.3.0` を導入した。`pytest==9.1.1` と `pytest-cov==7.1.0` は既存導入版を固定設定へ記録した。

formatter、lint、type、固定 P2 pytest wrapper、coverage は全て終了コード 0 で完了した。一方、Runner は change_hash を再計算して一致を確認した後、`target_paths` 外の変更を検出してゲート実行を開始せず `BLOCKED` を返した。Human Gate も未承認であるため、Pass にはしない。

## 固定設定

- 開発用依存: `requirements-dev.txt`
- ツール設定: `pyproject.toml`
- 信頼済み scope: `scripts/quality_gate/trusted_scopes.json`
- Manifest: `run-manifest.json`
- 詳細な機械可読証跡: `verification.json`

## 実行結果

| Gate | コマンド | version | scope | 終了コード | 結果 |
|---|---|---|---|---:|---|
| formatter | `.venv\\Scripts\\python.exe -m ruff format --check src/autotrade/market_data tests/market_data` | ruff 0.16.1 | src / tests | 0 | PASS |
| lint | `.venv\\Scripts\\python.exe -m ruff check src/autotrade/market_data tests/market_data` | ruff 0.16.1 | src / tests | 0 | PASS |
| type | `.venv\\Scripts\\python.exe -m mypy src/autotrade/market_data` | mypy 2.3.0 | src | 0 | PASS |
| pytest | `.venv\\Scripts\\python.exe -m scripts.quality_gate.local_p2_pytest` | pytest 9.1.1 | tests/market_data | 0 | 9 passed |
| coverage | `.venv\\Scripts\\python.exe -m pytest tests/market_data --cov=autotrade.market_data --cov-report=term-missing --cov-report=json:test/evidence/phase2/RUN-P2-IC-001/coverage.json` | pytest-cov 7.1.0 | src / tests | 0 | 88.43% (threshold 80%) |

fixture SHA-256 は `sha256:94022229698e972353b8ec9537f455af5cb29d47253f5f2a1ed5d33b08b50169`、Runner が再計算した実差分 SHA-256 と Manifest の `change_hash` は `sha256:fd8033a64a8949570ce3231ead103e0a1f28f168b1f14a2a3f8b5bb1ee8a7419` で一致した。hash 算出では `test/evidence/**` を除外し、証跡の追記が自身の入力を変えないようにした。

## `.coverage` の扱い

`Resolve-Path .coverage` で repository root の単一ファイル `C:\project\strategy_test\\.coverage` であることを確認した後、`git rm --cached -- .coverage` を実行した。物理ファイルは保持し、`.gitignore` に `.coverage` を追加した。履歴の書き換えは行っていない。

## 安全境界

Runner と P2 test wrapper は外部 network、Databento、Broker、Secret、実取引へ接続しない。wrapper は固定 `tests/market_data` のみを起動し、Runner は host の outbound isolation marker が確認できない場合に BLOCKED とする。
