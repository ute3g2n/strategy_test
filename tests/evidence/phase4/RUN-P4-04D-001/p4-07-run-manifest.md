# P4-07 Run Manifest

- Step: `P4-07`
- Phase: `PHASE4_PRODUCT_APPLICATION_BACKTEST_2026_08_11`
- Run ID: `RUN-P4-04D-001`
- Execution date: `2026-08-12` (Asia/Tokyo)
- Baseline: `2ce571e` (P4-06 implementation was committed as `10dd8ba` before this Step)
- Approval: `P4-H1=APPROVED` in [human-gate-p4-h1.md](human-gate-p4-h1.md)
- Trusted scope: `scripts/quality_gate/trusted_scopes.json` / `RUN-P4-04D-001`

## Target and exclusion

The target-only scope is `src/autotrade/application`, `tests/application`,
`tests/phase4`, and `tests/fixtures/phase4`. Core source and existing Core
fixtures are read-only inputs. The following were not changed or started:

- `src/autotrade/backtest`, `src/autotrade/market_data`, `src/autotrade/strategy`
- `ui/mock`, HTTP server, dependency manifests, WSL, external I/O, Broker/Paper/Live,
  Secret, real Risk/Account/OMS, Cloud, and an external database
- P4-08 UI and P4-09 integration quality

The registered read-only fixture is
`tests/fixtures/phase3/run_p3_backtest_fixture_manifest_v1.json` with the
registered SHA-256
`sha256:aeb03df1eef3ea836d176a8b0443c45b6bc7f6d01e455fd6026cabf16c536fa4`.

## Fixed execution contract

The Application boundary calls a supplied typed Core adapter once per Job.
Result bodies remain under the separate local result-file boundary; the
metadata database stores references and hashes only. Result publication uses
temporary files and a final directory rename, and result/evidence references
are committed with the terminal Job transition. CSV output is relative-only,
atomic, and never overwrites an existing target.

Single Backtest, Sweep members, Result/Evidence, CSV Job, checkpoint resume,
Holdout blocked assessment, idempotency, expected revision, lease/fencing,
marker/hash mismatch, and rollback are exercised with fixed local dummy data.
The typed `BacktestCoreAdapter` reuses the frozen `BacktestRunner`; no Core
source or Core ResultStore source is modified.

## Runtime dispatch record

The requested Coordinator was started first, but its runtime could not expose
`multi_agent_v1__spawn_agent` or `multi_agent_v1__wait_agent`. The Step uses
`DISPATCH_MODE=LOCAL_FALLBACK_NO_SUBAGENTS`, `independent=false`, and
`review_mode=SELF_REVIEW_FALLBACK`. No unstarted Agent is represented as an
independent result. Details are in [p4-07-dispatch.md](p4-07-dispatch.md).
