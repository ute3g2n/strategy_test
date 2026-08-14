# CTX-05 GREEN検証証跡

- 計画: `CTXMAP-PLAN-001 v0.1`
- Step: `CTX-05`
- 実行日: `2026-08-14`
- RED証跡: [`CTX-05_RED_evidence.md`](./CTX-05_RED_evidence.md)
- 実装入口: `scripts/context_index/build_code_manifest.py`
- 関係グラフ入口: `scripts/context_index/build_relation_graph.py`
- 差分検出入口: `scripts/context_index/detect_code_delta.py`

## 実装した契約

- Pythonは標準ライブラリの`ast`だけで、function、async function、class、method、nested定義、decorator、import/from import、alias、relative import、公開候補、行範囲を抽出する。
- TypeScript／JavaScriptは追加依存を導入せず、export/import、require、function、class、arrow functionを保守的に抽出する。動的importは解決せず、`PARTIAL`と診断を返す。
- PowerShellとshellはfunction、dot-source／sourceを保守的に抽出し、文法の完全性を主張しない。
- JSON等のmanaged configは安全なtop-level key、相対参照path、秘密らしきkey/valueの件数だけを保存し、秘密名・値・本文を保存しない。
- ソースの秘密らしき文字列は構造抽出の入力として読み取るが、出力へ保持せず、該当recordを`PARTIAL`にして`SECRET_LIKE_CONTENT_OMITTED`を記録する。秘密path、サイズ超過、UTF-8不正、読取失敗は`BLOCKED`とする。
- `code_id`は既存recordを優先し、単一hashのrenameだけを旧IDへ接続する。同一hashの複数候補は`RENAME_AMBIGUOUS`として黙って選ばない。
- relation graphはcode file、symbol、document、trace IDのnodeと、contains/imports/links_to/references_trace_idのedgeを持つ。local referenceの未解決はnodeを捏造せず、`resolution=unresolved`と`PARTIAL`で残す。外部packageは`external`として扱う。
- code deltaはsource hashだけでなく、行番号を除いたsymbol/import/export/config構造を比較し、コメントだけの変更を`modified_non_structural`、構造変更を`modified_structural`に分類する。
- `source_exclude_paths`で`tests/evidence`、`plan/context_index`、生成済みmanifest等を通常のcode artifactから除外し、CTX-00の境界分類を維持する。

## 実行結果

| 検証 | コマンド／対象 | 結果 |
|---|---|---|
| CTX-03/04/05統合テスト | `& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q` | `44 passed` |
| カバレッジ | `& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q --cov=scripts/context_index --cov-report=term-missing` | `80.04%`、fail-under `80%`を達成 |
| ruff | `& .\\.venv\\Scripts\\python.exe -m ruff check scripts/context_index tests/context_index` | `All checks passed!` |
| mypy | `& .\\.venv\\Scripts\\python.exe -m mypy scripts/context_index` | `Success: no issues found in 10 source files` |
| 構文 | `& .\\.venv\\Scripts\\python.exe -m compileall -q scripts/context_index` | `PASS` |
| JSON | `context/context_policy.json`、新規schema 2件をPython標準JSON parserで検証 | `JSON_OK` |
| 実manifest生成 | `build_code_manifest` CLI | `243 artifacts / status=PARTIAL` |
| 実関係グラフ生成 | `build_relation_graph` CLI | `1628 nodes / 2282 edges / status=PARTIAL` |
| 実manifest整合 | `validate_code_manifest` | `valid=True / status=PARTIAL / errors=0` |
| Secret出力確認 | code/relation manifestを既知fixture値・鍵名で検索 | `検出なし` |

## テストしたシナリオ

- Pythonのnested定義、class method、alias import、relative import、decorator、行範囲。
- Python syntax error時の`PARTIAL`とsource excerpt非保持。
- TypeScript export/import、arrow function、dynamic import未解決。
- PowerShell function／dot-source、shell function／source。
- JSONのsecret-like key/value非保持とsafe metadata。
- 同一入力の決定性、source hash stale、exclude directory、manifest validation。
- rename時のcode ID維持、同一hash複数pathの`RENAME_AMBIGUOUS`。
- 循環import、missing local target、document local link、trace ID edge。
- コメントのみの変更とsymbol追加の構造変更分類。

## 実行境界と未完了状態

- CTX-05はローカルのunit／integration／coverage／ruff／mypy／compileall／JSON検証までGREENである。
- 実manifestはJavaScript等の保守的解析と、秘密らしきsource文字列を含むrecordのため`PARTIAL`である。`validate_code_manifest`は全243件のhash・coverageを検証し、errorは0件だった。`PARTIAL`を完全解析済みとは主張しない。
- 実runtime receipt上、指定OrchestratorとA110/A120/A130/A150はhandoffまたはchecklist完了であり、独立review閉ループは成立していない。A07はCTX-04同様、本Stepの必須Agentではない。
- `scripts/quality_gate/trusted_scopes.json`にCTX-05 Runは登録されていないため、WSL隔離の固定4-Gate PASSは主張しない。
- 外部依存、外部通信、常駐watcher、MCP登録、Git stage／commit／pushはCTX-05の範囲外である。

## 次Stepへの引渡し

`CTX-06`では、今回の`code_manifest.json`と後続のdocument manifestを先行入力にして、A08ルーターとローカルstdio MCPのJIT取得境界を実装する。本文・コード本文をルーターの初期入力にしない契約を維持する。
