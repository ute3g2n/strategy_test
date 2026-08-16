# RECOVERY-05 ルートレビュー代替記録

独立Agent起動はthread上限でできなかったため、`SELF_REVIEW_FALLBACK`として記録する。対象は、対象パスの差分、pytest、UI build/unit/lint、API子プロセス再起動、Playwrightの同一Run ID・metrics・provenance・rows比較、外部リクエスト0件である。

## Findings first

- Critical: 発見なし。
- High: 発見なし。
- Medium: Holdoutの一度だけという状態は再起動後の永続化対象外。今回のRun履歴復元完了条件には含めず、Unknownとして残す。
- Low: 大量履歴のメモリ上限、Eドライブ障害時のバックアップ／世代管理、P4 SQLite統合は未決定。実装完了扱いにせず、計画書と統合台帳へ残す。

判定: Run履歴・結果・Ledgerの再起動後復元については証拠付きで受入候補。Unknownは別機能の完了を妨げない範囲で明示する。
