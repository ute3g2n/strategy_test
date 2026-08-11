# P4-09 Integrated Quality Run Manifest

- Step: `P4-09`
- Phase: `PHASE4_PRODUCT_APPLICATION_BACKTEST_2026_08_11`
- Run ID: `RUN-P4-04D-001`
- Execution date: `2026-08-12` (Asia/Tokyo)
- P4-H1: `APPROVED` — [human-gate-p4-h1.md](human-gate-p4-h1.md)
- P4-H2: `WAITING_FOR_USER_APPROVAL`; P4-10 is not executable
- P4-08 baseline commit: `e1ac9d0`
- Trusted-scope registry: `scripts/quality_gate/trusted_scopes.json` / `scopes.RUN-P4-04D-001`
- Scope mode: `target_only`
- Fixture: `tests/fixtures/phase3/run_p3_backtest_fixture_manifest_v1.json`
- Fixture SHA-256: `sha256:aeb03df1eef3ea836d176a8b0443c45b6bc7f6d01e455fd6026cabf16c536fa4`
- Final review status: `COMPLETED_P4-09_P4-H2_BLOCKED`

## Review scope

P4-09 is a read-only integrated review of the P4-06 Application implementation, P4-07 API／worker／result／evidence contracts, P4-08 fixed UI contract evidence, and the P4-04A〜D design set. It does not add application behavior, database schema, migration, HTTP transport, dependency, Core change, WSL run, external I/O, Secret, Broker／Paper／Live, or real Risk／Account／OMS behavior.

The registered target paths are `src/autotrade/application`, `tests/application`, `tests/phase4`, `tests/fixtures/phase4`, and `ui/mock`. During this Step they are inspected and quality evidence is rechecked; no source file in those paths is changed.

## Fixed evidence inputs

| Evidence | Review use | Expected result |
|---|---|---|
| P4-06/P4-07 Python target gates | Application contract and implementation quality | formatter／lint／mypy／pytest PASS |
| P4-06/P4-07/P4-08 hash manifests | Artifact integrity | all listed hashes PASS |
| P4-08 Playwright JSON | UI contract／state／a11y result | 6 expected, 0 unexpected, 0 skipped |
| P4-08 screenshots | visual runtime evidence | 21 desktop + 21 mobile |
| P4-04A API design | canonical API inventory | API-P4-001〜019 = 19/19 |
| P4-04B DB design | metadata persistence and ER coverage | required 15 logical tables / ER entities |
| P4-04C UI design | screen and state coverage | SCREEN-01〜21 = 21/21; 13×10 runtime state operations |
| P4-04D quality design | REQ／UC／Test／Evidence／Gate trace | no unclassified P4 API or screen |

## Required fail-closed boundaries

- `UNK-P4-04D-004`: host outbound isolation evidence is not available; WSL quality gate is not started by P4-09 and this remains a blocker to P4-H2 candidacy.
- `UNK-P4-UI-002`: font／OS rendering and formal pixel baseline are not fixed; screenshots are retained as evidence but are not promoted to a formal pixel PASS.
- Coordinator child dispatch is unavailable inside the Coordinator runtime; `p4-09-dispatch.md` records `LOCAL_FALLBACK_NO_SUBAGENTS`, `independent=false`, and no child Agent is claimed as completed.
- Any Core diff, external request, Secret value, unverified hash, missing API／DB／UI mapping, or unapproved Gate remains a stop condition.
