# CTX-04 RED証跡

- 計画: `CTXMAP-PLAN-001 v0.1`
- Step: `CTX-04`
- 実行日: `2026-08-14`
- 対象: `tests/context_index/test_context_maintenance.py`
- コマンド: `& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index/test_context_maintenance.py -q`
- 終了コード: `1`
- 判定: `RED`

## 失敗内容

実装前のため、テスト収集時に次の未実装エラーが発生した。

```text
ModuleNotFoundError: No module named 'scripts.context_index.run_context_maintenance'
```

これはCTX-04の保守統合入口がまだ存在しないことを示す意図的なREDである。`skip`、`xfail`、閾値緩和、テスト削除による回避は行っていない。

## 固定した受入条件

- 新規Markdown／HTMLはA07 `record_add` とvalidator PASSなしに通さない。
- 大幅変更はA07 `record_update` または `metadata_unchanged` を要求する。
- 小変更は意味メタデータを不要に書き換えず、hashとstateを更新する。
- A07未起動、timeout、非0、壊れたstrict JSON、confidence不足はfail closedにする。
- Secret、絶対path、UNC、traversal、巨大入力をreceiptへ漏らさない。
- retryは上限付き、同一requestの再実行は冪等、異なるhashの再利用は拒否する。
- renameとdeleteはartifact historyを壊さず、誤った新規追加へ変換しない。

実装後はこの同一テスト集合をGREEN検証へ再実行する。
