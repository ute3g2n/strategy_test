# P5R-03A trusted scope登録証跡

- H1: `APPROVED_BY_DELEGATED_AUTHORITY`
- 登録対象: `RUN-P5R-03-20260816-001`
- 登録先: `scripts/quality_gate/trusted_scopes.json`
- scope_mode: `target_only`
- 登録内容: target paths、excluded paths、fixture、固定4 Gate、UI build/unit/Playwright project、外部通信0件ポリシー
- 実行前状態: この登録より前にP5Rのtest subprocess/Playwrightを実行していない。
- 変更責任: root fallback（ComponentLifecycle coordinatorのagent-thread limitによる未起動を明記）
- 禁止: management hash、manifest fingerprint、stale、hash retry、外部Data、Broker、Secret、実注文、実資金
