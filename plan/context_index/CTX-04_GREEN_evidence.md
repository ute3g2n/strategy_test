# CTX-04 GREEN検証証跡

- 計画: `CTXMAP-PLAN-001 v0.1`
- Step: `CTX-04`
- 実行日: `2026-08-14`
- RED証跡: [`CTX-04_RED_evidence.md`](./CTX-04_RED_evidence.md)
- 実装入口: `scripts/context_index/run_context_maintenance.py`

## 実装した保守契約

- `maintain_document()` は1回につき1つの相対pathだけを受け取り、policyのmanaged documentか、UTF-8か、サイズ上限内か、Secret denylistに抵触しないかを確認する。
- 新規文書はA07のstrict JSON `record_add` とvalidator PASSが両方なければmanifestを変更せずBLOCKEDにする。
- 大幅変更はA07の `record_update` または `metadata_unchanged` を要求し、既存 `artifact_id` と `source_hash` を検証する。
- 小変更はA07を起動せず、意味メタデータを保持したままhash・サイズ・行数・更新時刻とstateを決定的に更新する。
- A07 runtime未起動、timeout、非0、壊れたJSON、追加キー、hash不一致、confidence不足、validator失敗はfail closedにする。
- A07へ渡すpayloadは1ファイル、構造差分、既存メタデータ、安全な最大18,000文字excerpt、request/hashだけに限定する。
- receiptはA07のraw出力を保存せず、相対path、hash、action、理由、runtime状態、試行回数だけをsanitized保存する。Secret、本文、絶対ユーザーパス、stderrは保存しない。
- `process_delta()` は単一renameとdeleteだけを受け、artifact historyを維持し、曖昧な推測をしない。
- CLIはmanifest/receiptを同一repository内へatomic writeし、失敗時にmanifest出力を作らない。Git stage/commit/push、常駐監視、外部I/Oは行わない。

## 実行結果

|検証|コマンド|結果|
|---|---|---|
|CTX-03/04統合テスト|`& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q`|`34 passed`|
|カバレッジ|`& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q --cov=scripts/context_index --cov-report=term-missing`|`87.01%`、fail-under `80%`を達成|
|ruff|`& .\\.venv\\Scripts\\python.exe -m ruff check scripts/context_index tests/context_index`|`All checks passed!`|
|mypy|`& .\\.venv\\Scripts\\python.exe -m mypy scripts/context_index tests/context_index --follow-imports=normal`|`Success: no issues found in 9 source files`|
|構文|`& .\\.venv\\Scripts\\python.exe -m compileall -q scripts/context_index tests/context_index`|`COMPILEALL_PASS`|
|schema JSON|`context/*.json`をPython標準JSON parserで検証|`CONTEXT_SCHEMA_JSON_PASS`|
|差分空白|`git diff --check -- scripts/context_index tests/context_index context plan/context_index/CTX-04_RED_evidence.md`|`PASS`|

## テストしたシナリオ

- 新規Markdown／HTML: A07 `record_add`、payload上限、validator PASS。
- 見出し・本文・trace IDを含む大幅変更: `record_update` と `metadata_unchanged`。
- 小変更: A07不要理由、hash更新、summary/purpose維持。
- A07不在、timeout、retry成功、retry上限超過、壊れたstrict JSON、追加キー、confidence不足、hash不一致。
- Secret本文、除外ディレクトリ、path traversal、receiptへの本文・絶対path漏えい。
- 同一requestの冪等再実行、異なるhashのreplay conflict。
- 単一rename、delete、state hash更新、CLIのblocked receiptとatomic manifest出力。

## 実行境界と未完了状態

- A07定義の固定model `gpt-5.1` は現runtimeで利用できず、実A07 dispatchは `agent_id=N/A` としてBLOCKED扱いにした。代替modelをA07成功へ黙って置換していない。
- fake dispatcherによるA07成功系は、strict schema、hash、confidence、validator、sanitized receiptの統合fixtureとして検証した。実runtimeによる意味更新のPASSとは区別する。
- CTX-04 Run IDは `scripts/quality_gate/trusted_scopes.json` に未登録のため、WSL隔離の固定4-Gateは実行していない。local unit/coverage/ruff/mypy/compileall/JSONをPASSとし、固定4-Gate PASSは主張しない。
- runtime handoffはOrchestrator 2件とA120/A110/A130/A150が完了したが、子dispatch閉ループおよび独立A150レビューは成立していない。A07は未起動である。詳細は `CTX-04_dispatch_receipt.json` を参照する。
- 常駐watcher、保存時自動A07呼出し、auto-commit変更、MCP、外部ネットワークはCTX-04の範囲外であり、CTXMAP-H1前には有効化しない。

## 次Stepへの引渡し

`CTX-05` では managed source のcode manifestとrelation graphを追加する。CTX-04の文書保守入口は、コード構造変更の再解析・Router・MCP・commit前ゲートの完了を意味しない。
