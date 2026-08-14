# CTX-06 GREEN検証証跡

- 計画: `CTXMAP-PLAN-001 v0.1`
- Step: `CTX-06`
- 実行日: `2026-08-14`
- RED証跡: [`CTX-06_RED_evidence.md`](./CTX-06_RED_evidence.md)
- Router入口: `scripts/context_index/context_router.py`
- MCP入口: `scripts/context_index/context_mcp_server.py`
- CLI入口: `scripts/context_index/context_cli.py`
- Fixture: `context/routing_fixtures.json`

## 実装した契約

- Routerは`verified=true`のsnapshotだけを受け付ける。64桁snapshot hashが渡された場合はmanifest payloadから再計算し、staleなら停止する。本文・コード本文・全文検索は初期入力にしない。
- Routerの出力キーは`primary_ids`、`supporting_ids`、`jit_ranges`、`rationale_by_id`、`missing_information`、`manifest_snapshot_hash`、`request_id`、`receipt`だけに固定した。
- primaryは最大3件、supportingは最大6件、JIT範囲は最大3件に制限し、文書は見出し、コードは登録symbol／行範囲として返す。
- `load_router_snapshot()`はartifact manifestとcode manifestをvalidatorで検証し、relation graphの構造を確認してからsnapshotを公開する。
- `search_context`はmanifestの安全なmetadataだけを検索し、`get_related`はrelation graphだけを返す。どちらも本文を読まない。
- `get_artifact`は登録artifact ID、managed document allowlist、canonical repo path、読取前後hash、UTF-8、サイズ、Secret denylist、prompt injection denylist、行／見出し範囲、応答上限を順に検証する。
- `get_code_slice`は登録code IDと`COMPLETE/PARTIAL` recordを対象にし、登録symbolまたはsymbol内line range以外を読まない。source hash、UTF-8、サイズ、Secret、prompt injectionも検証する。
- stdio JSONL以外のtransportは実装せず、HTTP listen／TCP／外部MCP／外部DB／network dependencyを追加していない。stdoutはJSONL応答だけに限定する。
- CLIはroute、search、get-artifact、get-code-slice、get-related、stdioの同期入口を持ち、例外時にtraceback・絶対path・本文を出力しない。
- document manifestは421件、code manifestは248件を登録し、relation graphは文書＋コード関係を再生成した。

## 実行結果

| 検証 | コマンド／対象 | 結果 |
|---|---|---|
| CTX-03〜06統合テスト | `& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q` | `56 passed` |
| カバレッジ | `& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q --cov=scripts/context_index --cov-report=term-missing` | `80.28%`、fail-under `80%`を達成 |
| ruff | `& .\\.venv\\Scripts\\python.exe -m ruff check scripts/context_index tests/context_index` | `All checks passed!` |
| mypy | `& .\\.venv\\Scripts\\python.exe -m mypy scripts/context_index` | `Success: no issues found in 13 source files` |
| 構文 | `& .\\.venv\\Scripts\\python.exe -m compileall -q scripts/context_index tests/context_index` | `PASS` |
| JSON | policy、manifest、state、graph、fixture、receipt | `JSON_OK` |
| document validator | `validate_manifest(context/artifact_manifest.json)` | `valid=True / active=421 / errors=0` |
| code validator | `validate_code_manifest(context/code_manifest.json)` | `valid=True / status=PARTIAL / COMPLETE=214 / PARTIAL=34 / errors=0` |
| relation graph | `build_relation_graph` CLI | `status=PARTIAL / nodes=3202 / edges=6824` |
| routing fixture | `context/routing_fixtures.json` | `10 cases / allowed primary set一致` |
| stdio smoke | `context_mcp_server --stdio` | `JSONL response / no HTTP listener` |

## セキュリティ・境界テスト

- `../../outside`、repo外manifest path、Windows絶対pathを拒否した。
- 未登録artifact／code／relation ID、未登録symbol、範囲0、範囲逆転、巨大応答を拒否した。
- documentのstale hash、invalid UTF-8、Secret-like contentを本文なしで拒否した。
- prompt injection文書を`PROMPT_INJECTION_SUSPECTED`として本文返却前に拒否した。
- search結果には`content`を含めず、Router結果にも本文を含めないことを確認した。
- malformed JSONと未知toolのstdio requestは、`REQUEST_INVALID`／`TOOL_NOT_FOUND`だけを返した。
- fixtureおよび実manifestに既知のSecret sentinel値がないことを確認した。

## 実行境界と未完了状態

- ローカルpytest、coverage、ruff、mypy、compileall、JSON、両manifest validatorはGREENである。
- 実code manifestは保守的解析とsecret-like source metadata omissionを含むため`PARTIAL`であり、完全ASTを主張しない。
- A08/A07の固定model `gpt-5.1`は現runtimeで受理されず、`agent_id=N/A`、`RUNTIME_DISPATCH_FALLBACK_REQUIRED`として記録した。代替modelをA08/A07の成功へ黙って置換していない。
- OrchestratorおよびA110/A120/A130/A150はhandoff/checklistを返したが、独立レビュー閉ループは成立していない。独立PASSは主張しない。
- `scripts/quality_gate/trusted_scopes.json`にCTX-06 Runは未登録のため、WSL隔離固定4-Gate PASSは実行・主張していない。
- H1承認前の常駐watcher、保存時自動A07呼出し、commit／push自動化、外部I/Oは有効化していない。

## 次Stepへの引渡し

`CTX-07`では、CTX-06のvalidator、hash、A07 pending、source構造変更、未追跡ユーザー変更をcommit前にfail-closedで確認するgateを実装する。
