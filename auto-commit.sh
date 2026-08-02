#!/usr/bin/env bash
set -euo pipefail

if [[ -z "$(git status --short)" ]]; then
  echo "[auto-commit] No changes detected."
  exit 0
fi

git add -A

if git diff --cached --quiet; then
  echo "[auto-commit] No staged changes after git add."
  exit 0
fi

timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
branch="$(git branch --show-current)"

if [[ -z "$branch" ]]; then
  echo "[auto-commit] Could not determine the current branch." >&2
  exit 1
fi

git commit -m "auto: update by Codex [$timestamp]"
git push origin "$branch"
