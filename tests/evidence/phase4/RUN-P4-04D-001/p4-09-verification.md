# P4-09 Integrated Verification Evidence

## Findings first

| Finding | Severity | Status | Verification result |
|---|---|---|---|
| `FIND-P4-09-001` | Medium / process | RECORDED | Coordinator was started, but its child `spawn/wait` backend was unavailable. No independent Agent completion is claimed. |
| `FIND-P4-09-002` | Medium / evidence integrity | CLOSED | P4-06 hash for the shared Human Gate became stale after P4-08 scope normalization. The hash was updated to the current approved record and all P4-06〜08 manifests now pass. |
| `UNK-P4-04D-004` | Gate blocker / Unknown | OPEN | Host outbound isolation is not evidenced. WSL quality gate was not started. |
| `UNK-P4-UI-002` | Medium / Unknown | OPEN | Font／OS rendering and formal pixel baseline are not fixed. |

## Coverage verification

| Contract family | Expected | Result | Evidence |
|---|---:|---|---|
| Canonical API inventory | 19 (`API-P4-001`〜`API-P4-019`) | PASS — 19/19 present in P4-04A, P4-04B, P4-04C and P4-04D | P4 design set |
| Metadata persistence logical tables | 15 | PASS — `run`, `run_condition`, `run_state_transition`, `job`, `queue_item`, `checkpoint`, `result_reference`, `evidence_reference`, `sweep_parent`, `sweep_member`, `csv_job`, `idempotency_record`, `audit_event`, `holdout_assessment`, `schema_migration` | P4-04B |
| ER entities | 15 | PASS — all required entities are present in the Mermaid `erDiagram` | P4-04B |
| UI screens | 21 | PASS — `SCREEN-01`〜`SCREEN-21` present in design and `p4ScreenContracts` | P4-04C/P4-08 |
| Runtime state operations | 13 target/boundary screens × 10 states × 2 viewports | PASS — 260 operations recorded by P4-08 | P4-08 results and screenshots |
| Boundary-only screens | 8 | PASS — fixed `UNAPPROVED`／`P4_OUT_OF_SCOPE`; no functional controls | P4-08 results |
| API-to-screen binding | 19 canonical IDs | PASS — every canonical API is present in at least one screen binding; P4-X01〜X05 remain unsupported boundaries | P4-04C/P4-08 |

## API-to-persistence-to-evidence review

| API group | IDs | Review result |
|---|---|---|
| Capability／Preflight／Run／Sweep | `001`〜`004` | read-only preflight is separated from write transactions; Run/Sweep idempotency, revision and rollback are defined |
| Run／Job／Queue | `005`〜`012` | read projections do not commit; Job/Queue state, lease/fencing, cancel, resume and retry are fail-closed |
| Result／CSV／Evidence／Holdout | `013`〜`019` | committed-result-only reads, atomic CSV publication, hash-verified Evidence and non-promoting Holdout assessment are defined |

The P4-04A inventory and P4-04B coverage were cross-read. Each canonical API has either an explicit metadata read/write table or a read-only／N/A reason. Core ResultStore result bodies remain outside metadata persistence; file and Evidence references carry relative references and hashes only. UI binds contract metadata and does not access the DB directly.

## Machine evidence recheck

- `ruff format --check`: PASS.
- `ruff check`: PASS.
- `mypy src/autotrade/application`: PASS, 20 source files.
- `pytest tests/application tests/phase4 -q`: PASS, 17 passed.
- P4-06 hash manifest: PASS after closing `FIND-P4-09-002`.
- P4-07 hash manifest: PASS.
- P4-08 hash manifest: PASS.
- Fixture hash: PASS, `sha256:aeb03df1eef3ea836d176a8b0443c45b6bc7f6d01e455fd6026cabf16c536fa4`.
- Core diff from the P4 scope baseline: 0.
- P4-08 Playwright result: 6 expected, 0 unexpected, 0 skipped; 42 screenshots.
- Local documentation links: PASS.
- `git diff --check`: PASS at the final review checkpoint.

## Boundary verification

- No external Data、Broker、Paper、Live、Cloud、Secret value、real Risk／Account／OMS, or HTTP transport was added.
- No DB creation, migration execution, repository generation, WSL quality run, or dependency installation was performed by P4-09.
- Existing source-level Secret/path checks remain fail-closed; strings mentioning Secret／token are boundary rules or test labels, not credentials.
- `UNK-P4-04D-004` and `UNK-P4-UI-002` remain Unknown and are not counted as PASS.

## Gate conclusion

Technical local quality and coverage checks have no unresolved Critical／High implementation or design finding. P4-09 is recorded as complete for the review work, but the P4-H2 candidate is blocked by the required Unknown host-isolation evidence, the unresolved formal UI baseline, and the absence of user approval. P4-10 remains prohibited.
