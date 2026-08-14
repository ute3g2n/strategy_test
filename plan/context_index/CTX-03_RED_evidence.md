# CTX-03 RED証跡

- 実行日時: 2026-08-14
- 対象: `tests/context_index/test_context_index.py`
- コマンド: `& .\\.venv\\Scripts\\python.exe -m pytest tests/context_index -q`
- 終了コード: `1`
- 結果: RED

## 失敗署名

テスト収集時に次の未実装エラーが発生した。

`ModuleNotFoundError: No module named 'scripts.context_index'`

これはCTX-03の実装対象（`scripts/context_index/`）がまだ存在しないことによる、意図した未実装REDである。既存実装の構文エラー、依存取得失敗、対象テストのskip、xfail、閾値緩和による失敗ではない。

## テストと受入条件の対応

テストは新規Markdown／HTML、軽微変更、大幅変更、見出し変更、REQ/DEC変更、rename、削除、schema不正、未登録、stale hash、Secret拒否、third_party除外、Windows／POSIX path、決定的出力、manifest-only queryを対象にしている。

この証跡はGREENを意味しない。最小実装後に同一pytestを再実行し、失敗が解消されたことを別のGREEN証跡へ記録する。
