# RECOVERY-01 要件・設計・成果物追跡

| 追跡ID | 事実・要求 | 根拠 | 次Stepの成果物 | 状態 |
|---|---|---|---|---|
| `REQ/P5R-AC-09-R` | 再起動後もRun履歴を一覧で開ける | P5R要件の履歴・比較、現行APIのメモリ依存 | RECOVERY-02、RECOVERY-04、RECOVERY-05 | OPEN→設計中 |
| `REQ/P5R-AC-06-R` | 再起動後も結果詳細とLedgerを開ける | `result.json`にrowsがあるがAPI復元なし | RECOVERY-02、RECOVERY-04、RECOVERY-05 | OPEN→設計中 |
| `REQ/P5R-AC-10-R` | 復元Runを比較できる | compareが`_runs`だけを参照 | RECOVERY-03、RECOVERY-04 | OPEN→RED予定 |
| `REQ/P5R-AC-11-R` | 復元RunからCSVを再生成できる | CSV APIが`_runs`と`_csv_jobs`だけを参照 | RECOVERY-03、RECOVERY-04 | OPEN→RED予定 |
| `REQ/P5R-RECOVERY-01` | 完了Runのcatalog/result整合性を検査する | 新規追加要件 | RECOVERY-02、RECOVERY-04 | OPEN |
| `REQ/P5R-RECOVERY-02` | 旧形式result.jsonを既知値だけ復元する | Eドライブの既存result.json形式 | RECOVERY-02、RECOVERY-03、RECOVERY-04 | OPEN |
| `REQ/P5R-RECOVERY-03` | 途中Runを自動成功・自動再開しない | StrategyStateが現状メモリのみ | RECOVERY-02、RECOVERY-04 | OPEN |
| `REQ/P5R-RECOVERY-04` | C/temp/phase5rへ新規保存しない | storage_paths契約・ユーザー指示 | RECOVERY-03、RECOVERY-04、RECOVERY-05 | OPEN |
| `DEC/P5R-RECOVERY-01` | P5R現APIにはEドライブJSONカタログを接続する | 最小差分・既存P4 SQLiteとの契約分離 | RECOVERY-02 | PROPOSED |
| `DEC/P5R-RECOVERY-02` | 1Run 1catalog JSON、結果本体はresult.json | atomic write、旧形式互換、分離責務 | RECOVERY-02 | PROPOSED |
| `DEC/P5R-RECOVERY-03` | 新しい管理用hashを追加しない | A95 policy | 全Step | FIXED |
| `UNK/P5R-RECOVERY-001` | P4 MetadataStoreの将来統合 | 別契約・未接続 | 完了判定・後続Phase | OPEN |
| `UNK/P5R-RECOVERY-002` | 実機Windows再起動の手動受入 | 自動API再起動との差 | RECOVERY-05/06/07 | OPEN |
| `UNK/P5R-RECOVERY-003` | StrategyState完全永続化と再起動後resume | 現状同一プロセス専用 | 完了判定・後続Phase | OPEN |
| `ART/P5R-RECOVERY-01` | 事実棚卸し | 本ファイル | RECOVERY-02 | COMPLETE |
| `ART/P5R-RECOVERY-02` | Runtime fallback receipt | RECOVERY-01-runtime-dispatch.md | 全Step | COMPLETE_WITH_FALLBACK |
