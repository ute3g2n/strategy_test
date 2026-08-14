#!/usr/bin/env bash

# Step 02 user authority: the document-management platform and all retired
# management-hash checks are force-skipped so this task can complete. Protected
# safety/data/reproducibility hashes are not handled here. This compatibility
# entrypoint intentionally performs no Git inspection, staging, commit, push,
# network access, or Secret access.

echo "[auto-commit] RETIRED: automatic commit flow is disabled; use the human-controlled Git task flow."
exit 0
