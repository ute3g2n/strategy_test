# P3-07R-03 recovery/debug log

## Run

- Run ID: `RUN-P3-BT-REPAIR-003`
- Scope: `Manifest → ResultRow/audit → Snapshot → commit marker → atomic publish → read/recover`
- External E-drive write: not used; tests injected a temporary absolute regular directory.

## Failure injection and recovery observations

1. A relative, UNC, root, or traversal result path is rejected before publication.
2. A temporary symlink root is rejected as a reparse point.
3. Missing `snapshot.json` leaves the run unpublished and raises the structured partial-commit path.
4. A commit-marker watermark mutation fails marker integrity verification and `read_published` returns `STOPPED / RECOVERY_RECONCILIATION_FAILED`.
5. A duplicate delivery of the committed event is excluded from the replay suffix. Only events after the last committed occurrence are returned.
6. A secret/vendor/noncanonical ResultRow fails before snapshot and commit-marker creation.

## Recovery rule

Only a run containing the immutable manifest, canonical result bytes, audit bytes, snapshot, and last commit marker is readable as a committed run. Missing files, changed hashes, changed bindings, incomplete snapshot fields, unknown fields, reparse paths, and marker mismatch stop recovery. No Signal, Directive, Fill, or ResultRow is appended during read-only recovery.

## Debug outcome

No unresolved implementation failure remained after the bounded correction loop. The final targeted persistence tests, Phase Backtest/Strategy scope, full test scope, Ruff, compileall, and diff check are PASS.
