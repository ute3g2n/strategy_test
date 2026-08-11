# P4-06 Run Manifest

| Field | Value |
|---|---|
| Run ID | `RUN-P4-04D-001` |
| Step | `P4-06` |
| Status | `PASS_WITH_UNKNOWN` |
| Human Gate | `P4-H1=APPROVED` |
| Registry check | `scripts/quality_gate/trusted_scopes.json` → `scopes.RUN-P4-04D-001` registered and approval-aligned |
| Baseline | `2ce571e` |
| Fixture | `tests/fixtures/phase3/run_p3_backtest_fixture_manifest_v1.json` |
| Fixture hash | `sha256:aeb03df1eef3ea836d176a8b0443c45b6bc7f6d01e455fd6026cabf16c536fa4` |
| Core diff | `0` |
| External I/O / Secret / WSL | `0` / `0` / not started（host isolation Unknownのため実行しない） |

The initial registry check used an invalid `runs` key and produced a false BLOCKED record. The authoritative file uses `scopes`; the corrected lookup passed before the implementation retry. The implementation contains only local Product/Application metadata code and tests. Database objects are created only in test `:memory:`/temporary contexts; no repository database or external migration was run.

## Target scope

- `src/autotrade/application`
- `tests/application`
- `tests/phase4`
- `tests/fixtures/phase4`

The read-only input fixture remains `tests/fixtures/phase3/run_p3_backtest_fixture_manifest_v1.json` with the registered SHA-256. Core source, existing UI mock, external I/O, Secret, HTTP server, dependencies, WSL, and real-risk/order paths were not changed or started.
