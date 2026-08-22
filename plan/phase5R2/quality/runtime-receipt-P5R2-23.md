# P5R2-23 runtime receipt

- Run: `RUN-P5R2-23-FINAL-LOCAL-001`
- 判定: `P5R2-23_LOCAL_GREEN`
- Coordinator／指定Agent: 計画記載どおり。ただしnested named dispatchは成立せず、`RUNTIME_DISPATCH_FALLBACK_REQUIRED`、`agent_id=N/A`、`independent=false`、`SELF_REVIEW_FALLBACK`を記録した。
- P5R2契約・Manual・external Runner対象pytest: `112 passed`
- UI build: PASS、Vitest: `14 passed`、lint: PASS（既存warningのみ）
- P5R2-19／21／22 Playwright: 各desktop／mobile `2 passed`。P5R2-22 axe serious／critical `0`、外部request `0`。
- HTML local reference: `882 references / 0 missing / 0 duplicate id`（対象文書6件）
- A95: `ALLOW`。管理hash、manifest、stale、fingerprint、hash retry、hash receiptは追加していない。
- Python追加契約は`black --check`、`compileall`、pytestで確認。Windows rootのruff／mypy CLIは未配置で、P5R2-13／14／18／21の固定WSL Gate PASS Evidenceを参照した。
- H2: `UNAPPROVED`
- P6: `NOT_STARTED`
