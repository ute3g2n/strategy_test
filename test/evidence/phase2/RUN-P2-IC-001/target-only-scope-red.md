# BLK-RUN-001 対象限定スコープ RED 証跡

- 実行日: 2026-08-06
- テスト: `tests/quality_gate/test_runner.py::test_p2_target_only_scope_ignores_unrelated_worktree_changes`
- 期待: `settings/` と `doc/` の変更を無視し、固定4 Gate の後に `HUMAN_GATE_REQUIRED` となる。
- 実際: `BLOCKED`
- 意味: 変更前の Runner は、試験対象以外の差分も対象範囲違反として扱っている。これは BLK-RUN-001 の再現であり、実装前の RED である。
