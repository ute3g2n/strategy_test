# CTX-03 GREEN検証証跡

- 計画: `CTXMAP-PLAN-001 v0.1`
- Step: `CTX-03`
- 実行日: `2026-08-14`
- H0: `APPROVED`（ユーザー承認文「承認する。続けて」）
- RED証跡: [`CTX-03_RED_evidence.md`](./CTX-03_RED_evidence.md)

## TDDの閉ループ

1. A110相当のテスト先行で `tests/context_index/test_context_index.py` を作成した。
2. 実装が存在しない状態で `ModuleNotFoundError: No module named 'scripts.context_index'` を確認し、RED証跡へ保存した。
3. CTXMAPの最小実装として `context/` と `scripts/context_index/` を追加した。
4. 受入条件を補うため、HTML抽出、状態ファイル、CLI、入力拒否、重複、範囲外、曖昧renameを追加テストした。
5. 実装後に以下のGREEN検証を実行した。

## 実行結果

|検証|コマンド|結果|
|---|---|---|
|単体テスト|`& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q`|`18 passed`|
|カバレッジ|`& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q --cov=scripts/context_index --cov-report=term-missing`|`90.12%`、fail-under `80%`を達成|
|ruff|`& .\\.venv\\Scripts\\python.exe -m ruff check scripts/context_index tests/context_index`|`All checks passed!`|
|mypy|`& .\\.venv\\Scripts\\python.exe -m mypy scripts/context_index tests/context_index --follow-imports=normal`|`Success: no issues found in 7 source files`|
|構文|`& .\\.venv\\Scripts\\python.exe -m compileall -q scripts/context_index tests/context_index`|`COMPILEALL_PASS`|
|JSON|`context/context_policy.json`、`context/artifact_manifest.schema.json`をPython標準JSON parserで検証|`JSON_PARSE_PASS`|
|差分空白|`git diff --check -- scripts/context_index tests/context_index context`|`PASS`|

## 受入条件との対応

|条件|確認内容|状態|
|---|---|---|
|新規Markdown/HTML|決定的なpath、title、heading、hash、行数、local link、trace IDを抽出|PASS|
|小変更|本文量20%以下で構造・trace・linkが不変の変更を `modified_minor` と判定|PASS|
|大幅変更|本文量比率超過、heading、trace ID、local link変更を `modified_major` と判定|PASS|
|rename|同一hashの単一移動を `renamed`、複数候補を `rename_ambiguous` と判定|PASS|
|削除・追加|`deleted` と `added` を決定的順序で返す|PASS|
|REQ/DEC/UNK相当|trace ID候補を抽出し、変更時にmajor扱い|PASS（REQ/DEC fixture）|
|schema不正|必須キー、ID、hash、型を検証|PASS|
|stale hash|現物hashまたはサイズ不一致を検出|PASS|
|未登録|現物に存在するmanaged文書がmanifestにない場合に失敗|PASS|
|Secret|Secretらしいpath・本文を拒否し、検出値をエラーへ出力しない|PASS|
|第三者領域|`third_party`等を探索対象から除外|PASS|
|Windows/POSIX path|backslashをslashへ正規化し、絶対・UNC・traversalを拒否|PASS|
|manifest-only query|検索結果へ本文を返さず、path traversalと不正limitを拒否|PASS|

## 品質境界と未実施Gate

- `scripts/context_index/` はrepo内の安全な相対path、UTF-8、最大サイズ、Secret denylistを前提にする。
- `query_context.py` はmanifest metadataだけを検索し、本文のJIT取得や外部通信は実装していない。
- CTX-03の実行対象Runは `scripts/quality_gate/trusted_scopes.json` に登録されていないため、WSL隔離の固定4-Gateは実行していない。ローカルunit、ruff、mypy、coverage、compileall、JSON検証をPASSとして記録し、固定4-Gate PASSとは主張しない。
- A130/A150のruntime受領は個別hand-off checklistまでであり、独立した閉ループレビューは成立していない。詳細は `CTX-03_dispatch_receipt.json` に記録した。
- 外部依存の追加、外部通信、既存アプリ本体・取引ロジック・既存evidenceの変更は行っていない。

## 次Stepへの引渡し

`CTX-04` では、この基盤を呼び出す `run_context_maintenance.py` とA07連携を追加し、新規文書・大幅変更・失敗時fail closedを統合テストする。CTX-03単体のGREENは、全量manifest coverageや常駐watch有効化の承認を意味しない。
