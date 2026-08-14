# CTX-05 RED証跡

- 計画: `CTXMAP-PLAN-001 v0.1`
- Step: `CTX-05`
- 実行日: `2026-08-14`
- 対象: `tests/context_index/test_code_manifest.py`
- コマンド: `& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index/test_code_manifest.py -q`
- 終了コード: `1`
- 判定: `RED`

## 失敗内容

実装前のテスト収集時に、次の未実装エラーを確認した。

```text
ModuleNotFoundError: No module named 'scripts.context_index.build_code_manifest'
```

relation graphとcode deltaのモジュールも同じく未実装である。`skip`、`xfail`、閾値緩和、対象削除は行っていない。

## 固定した受入条件

- Pythonは標準AST由来のfunction/class/method/nested/import/decorator/line rangeを抽出する。
- syntax error、未対応構文、TypeScript/JavaScript、PowerShell、shellは完全性を偽らず `PARTIAL` と限界理由を保持する。
- JSON設定は安全なtop-level metadataと参照先だけを残し、Secret key/value/raw本文を出力しない。
- relation graphは明示関係、循環、未解決target、document link、trace IDを有限かつ決定的に表現する。
- 同一入力のmanifest・graphはcanonical順序と固定時刻で再現する。
- renameは単一同一hashだけidentityを維持し、曖昧候補を自動選択しない。
- コメントのみの変更とfunction/import等の構造変更を区別する。
- stale source hash、抽出欠損、Secret、範囲外pathはPASSへ変換しない。

実装後は同じテスト集合をGREEN検証へ再実行する。
