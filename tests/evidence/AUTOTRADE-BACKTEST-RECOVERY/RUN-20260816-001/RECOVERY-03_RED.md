# RECOVERY-03 RED Evidence

- Phase ID: `AUTOTRADE-BACKTEST-RECOVERY`
- Step ID: `RECOVERY-03`
- 実行日: 2026-08-16
- 設計ID: `P5R-RECOVERY-DD-01`
- 対象: `tests/phase5R/test_backtest_history_recovery.py`

## コマンド

```text
py -3 -m pytest -q tests/phase5R/test_backtest_history_recovery.py
```

## 結果

- 終了コード: `1`
- 結果: `6 failed`
- 構文エラー: なし
- import／依存不足による収集失敗: なし
- 本体コード変更: なし

## 失敗の意味

失敗は、現在のサービスが起動時に履歴カタログを読み込んでいないこと、`recovery_report()`を公開していないこと、`BACKTEST_CATALOG_ROOT`を持たないこと、APIの`/api/backtest/recovery`が存在しないことによる。つまり、設計した再起動後復元機能が未実装であることを示す意図したREDであり、無関係な回帰や環境不足ではない。

| テスト | 設計上の要求 | 現状の失敗 |
|---|---|---|
| `test_new_service_restores_completed_run_detail_and_rows` | REQ-R01〜R03 / RECOVERY-T-01〜T-03 | 再生成したサービスで`RUN_NOT_FOUND` |
| `test_legacy_result_is_restored_with_explicit_legacy_mode` | REQ-R04 / RECOVERY-T-04 | legacy resultを読み戻さない |
| `test_incomplete_after_restart_is_recovery_required_not_success` | REQ-R05〜R06 / RECOVERY-T-05〜T-07 | カタログを読み戻さない |
| `test_corrupt_and_mismatched_history_are_reported_without_hiding_other_runs` | REQ-R05 / RECOVERY-T-05〜T-06 | `recovery_report`未実装 |
| `test_catalog_path_is_application_scoped_and_never_phase_named` | REQ-R03 | カタログパス定数未実装 |
| `test_recovery_report_is_available_from_local_http_api` | REQ-R07 | APIが404 |
このRED確認後に限り、RECOVERY-04の本体実装へ進む。
