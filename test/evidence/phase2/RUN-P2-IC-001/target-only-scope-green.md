# BLK-RUN-001 対象限定スコープ GREEN 証跡

- 実行日: 2026-08-06
- テスト: `tests/quality_gate/test_runner.py::test_p2_target_only_scope_ignores_unrelated_worktree_changes`
- 結果: `1 passed`
- 確認内容: `settings/` と `doc/` の差分を無視し、registryの三つのtarget_pathsをInspectorへ渡し、固定4 Gateの後に `HUMAN_GATE_REQUIRED` となった。
- 追加確認: `tests/quality_gate` は `35 passed`。Manifestの `scope_mode` 改変は実行前に `ManifestValidationError` となった。
